"""Typer-based command line interface for HELIOS."""

from __future__ import annotations

import logging
import os
import subprocess
import time
import webbrowser
from collections import deque
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

import typer
import uvicorn
from pydantic import ValidationError
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from helios.checks import CheckRegistry, get_check_registry
from helios.config import HeliosSettings, load_config
from helios.core.audit_record import AuditRecord
from helios.core.persist import SigningRequiredError, hash_files, persist_record
from helios.core.run_context import RunContext
from helios.core.signer import generate_keypair, public_key_fingerprint
from helios.core.storage import AuditStorage
from helios.dashboard.app import create_app
from helios.export.json_export import export_json
from helios.export.pdf_export import export_pdf
from helios.export.rocrate import export_rocrate
from helios.integrations.nextflow import NextflowRunParser
from helios.integrations.snakemake import SnakemakeRunParser
from helios.integrations.snakemake_wrapper import run_wrapped_snakemake

app = typer.Typer(help="HELIOS genomics pipeline audit and validation CLI.")
key_app = typer.Typer(help="Manage HELIOS signing keys.")
config_app = typer.Typer(help="Inspect and validate HELIOS configuration.")
app.add_typer(key_app, name="key")
app.add_typer(config_app, name="config")
console = Console()
logger = logging.getLogger("helios.cli")


def _settings_path(config: Path | None) -> str | None:
    if config is not None:
        return str(config)
    if Path("helios.toml").exists():
        return "helios.toml"
    return None


def _build_context_from_record(record: AuditRecord) -> RunContext:
    """Reconstruct a run context from a persisted audit record."""

    work_dir = Path(record.work_dir) if record.work_dir else Path(".")
    output_dir = Path(record.output_dir) if record.output_dir else Path(".")
    artifacts = [
        Path(file_hash.path) for file_hash in record.output_files if Path(file_hash.path).exists()
    ]
    return RunContext(
        pipeline_name=record.pipeline_name,
        executor=record.executor,
        work_dir=work_dir,
        output_dir=output_dir,
        parameters=record.parameters,
        artifacts=artifacts,
        project_dir=work_dir,
        container_refs=[
            f"{item.name}:{item.tag}@{item.digest}" if item.digest else f"{item.name}:{item.tag}"
            for item in record.containers
        ],
    )


@app.command()
def init(path: Path = Path("helios.toml")) -> None:
    """Initialize HELIOS configuration in the current directory."""
    cwd_example = Path("helios.toml.example")
    if cwd_example.exists():
        text = cwd_example.read_text(encoding="utf-8")
    else:
        text = (
            resources.files("helios.data")
            .joinpath("helios.toml.example")
            .read_text(encoding="utf-8")
        )
    path.write_text(text, encoding="utf-8")
    console.print(f"[green]Initialized config:[/green] {path}")


@app.command()
def run(
    pipeline: Annotated[str, typer.Option("--pipeline", "-p")],
    work_dir: Annotated[Path, typer.Option("--work-dir", "-w")] = Path("."),
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o")] = Path("./results"),
    config: Annotated[Path | None, typer.Option("--config", "-c")] = None,
    no_sign: Annotated[bool, typer.Option("--no-sign")] = False,
    export_format: Annotated[str | None, typer.Option("--export")] = None,
    command: Annotated[list[str] | None, typer.Argument()] = None,
) -> None:
    """Run or wrap a pipeline, audit artifacts, sign, store, and export report."""
    settings = load_config(_settings_path(config))
    logging.basicConfig(level=settings.log_level.upper())
    start_time = datetime.now(UTC)

    if command:
        return_code = _run_streaming_command(
            command, work_dir=work_dir, timeout=settings.command_timeout_seconds
        )
        if return_code != 0:
            console.print(
                f"[red]Wrapped command exited with code {return_code}.[/red] "
                "Check pipeline logs and retry with corrected parameters."
            )
            raise typer.Exit(code=return_code)

    extra_inputs: list[Path] = []
    parser_context: RunContext
    containers = []
    if pipeline == "nextflow":
        nextflow_parser = NextflowRunParser(work_dir=work_dir, output_dir=output_dir)
        parser_context = nextflow_parser.build_run_context()
        containers = nextflow_parser.get_containers()
        extra_inputs.extend(
            [nextflow_parser.trace_file, nextflow_parser.config_file, nextflow_parser.log_file]
        )
    elif pipeline == "snakemake":
        snakemake_parser = SnakemakeRunParser(snakemake_dir=work_dir, output_dir=output_dir)
        parser_context = snakemake_parser.build_run_context()
        containers = snakemake_parser.get_containers()
    else:
        raise typer.BadParameter("pipeline must be nextflow or snakemake")

    registry = CheckRegistry()
    try:
        enabled_ids = registry.resolve_enabled(settings.checks.enabled)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    checks = registry.run_all(parser_context, enabled=enabled_ids, settings=settings)
    param_paths = [
        Path(value) for value in parser_context.parameters.values() if isinstance(value, str)
    ]
    input_files = hash_files([*extra_inputs, *param_paths])
    output_files = hash_files(parser_context.artifacts)

    record = AuditRecord(
        pipeline_name=parser_context.pipeline_name,
        pipeline_version=parser_context.metadata.get("pipeline_version"),
        executor=parser_context.executor,
        start_time=start_time,
        end_time=datetime.now(UTC),
        input_files=input_files,
        output_files=output_files,
        containers=containers,
        parameters=parser_context.parameters,
        checks=checks,
        work_dir=str(work_dir),
        output_dir=str(output_dir),
    )
    try:
        record = persist_record(record, settings, sign=not no_sign)
    except SigningRequiredError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    log = logging.LoggerAdapter(logger, {"run_id": str(record.run_id)})
    log.info("Audit record persisted")

    format_name = export_format or settings.export.default_format
    report_path = _export_record(record, format_name, settings)
    score = registry.compute_score(record.checks)
    summary = Table(title="HELIOS Run Summary")
    summary.add_column("Run")
    summary.add_column("Pipeline")
    summary.add_column("Score")
    summary.add_column("Grade")
    summary.add_row(str(record.run_id), record.pipeline_name, str(score.score), score.grade)
    console.print(summary)
    console.print(
        Panel(
            f"Report: {report_path}\nChecks: {len(record.checks)}\n"
            f"Passed={score.passed}, Warned={score.warned}, Failed={score.failed}",
            title="Audit Completed",
            border_style="green" if score.failed == 0 else "yellow",
        )
    )
    if score.failed:
        raise typer.Exit(code=1)


@app.command("solum-audit")
def solum_audit(
    export: Annotated[
        Path,
        typer.Option("--export", "-e", help="Path to solum-audit-helios-chain-v1 JSON"),
    ],
    config: Annotated[Path | None, typer.Option("--config", "-c")] = None,
    no_sign: Annotated[bool, typer.Option("--no-sign")] = False,
    export_format: Annotated[str | None, typer.Option("--export-format")] = None,
) -> None:
    """Ingest a Solum clinical audit export, run CLIN-ACCESS-001, sign, and export."""
    if not export.is_file():
        raise typer.BadParameter(f"export not found: {export}")
    settings = load_config(_settings_path(config))
    logging.basicConfig(level=settings.log_level.upper())
    start_time = datetime.now(UTC)

    context = RunContext(
        pipeline_name="solum-clinical-audit",
        executor="unknown",
        work_dir=export.parent,
        output_dir=export.parent,
        parameters={"solum_audit_export": str(export.resolve())},
        artifacts=[export.resolve()],
    )
    registry = CheckRegistry()
    enabled_ids = ["CLIN-ACCESS-001"]
    checks = registry.run_all(context, enabled=enabled_ids, settings=settings)
    record = AuditRecord(
        pipeline_name=context.pipeline_name,
        executor=context.executor,
        start_time=start_time,
        end_time=datetime.now(UTC),
        input_files=hash_files([export]),
        output_files=[],
        containers=[],
        parameters=context.parameters,
        checks=checks,
        work_dir=str(export.parent),
        output_dir=str(export.parent),
    )
    try:
        record = persist_record(record, settings, sign=not no_sign)
    except SigningRequiredError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    format_name = export_format or settings.export.default_format
    report_path = _export_record(record, format_name, settings)
    score = registry.compute_score(record.checks)
    clin = next((c for c in checks if c.check_id == "CLIN-ACCESS-001"), None)
    console.print(
        Panel(
            f"Report: {report_path}\n"
            f"CLIN-ACCESS-001: {clin.status if clin else 'missing'} — "
            f"{clin.message if clin else ''}\n"
            f"Score={score.score} grade={score.grade}",
            title="Solum clinical evidence",
            border_style="green" if score.failed == 0 else "red",
        )
    )
    if clin is not None and clin.status == "fail":
        raise typer.Exit(code=1)


@app.command()
def validate(run_id: UUID) -> None:
    """Re-run checks against stored run artifact context."""
    settings = load_config(_settings_path(None))
    storage = AuditStorage(f"sqlite:///{settings.audit_db}")
    record = storage.get_record(run_id)
    if record is None:
        raise typer.BadParameter(f"Run {run_id} not found")
    if record.signature is None:
        console.print("[red]Stored record is unsigned; cannot validate integrity.[/red]")
        raise typer.Exit(code=1)
    if not record.verify_signature(trusted_keys_dir=settings.trusted_keys_dir):
        console.print(
            "[red]Signature is invalid or the signer is not in the trust store "
            f"({settings.trusted_keys_dir}).[/red]"
        )
        raise typer.Exit(code=1)

    context = _build_context_from_record(record)
    registry = CheckRegistry()
    try:
        enabled_ids = registry.resolve_enabled(settings.checks.enabled)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    rerun_results = registry.run_all(context, enabled=enabled_ids, settings=settings)
    status_counts = {"pass": 0, "warn": 0, "fail": 0, "skip": 0, "info": 0}
    for result in rerun_results:
        status_counts[result.status] += 1

    table = Table(title=f"Validation Results: {run_id}")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Message")
    for result in rerun_results:
        table.add_row(result.check_id, result.status, result.message)
    console.print(table)
    console.print(
        f"Re-run summary: {status_counts['pass']} pass, "
        f"{status_counts['warn']} warn, {status_counts['fail']} fail"
    )
    if status_counts["fail"]:
        raise typer.Exit(code=1)


@app.command()
def report(
    run_id: UUID,
    format: Literal["json", "pdf", "rocrate"] | None = typer.Option(None, "--format"),
) -> None:
    """Export report in JSON, PDF, or RO-Crate format."""
    settings = load_config(_settings_path(None))
    storage = AuditStorage(f"sqlite:///{settings.audit_db}")
    record = storage.get_record(run_id)
    if record is None:
        raise typer.BadParameter(f"Run {run_id} not found")

    format_name = format or settings.export.default_format
    out = _export_record(record, format_name, settings)
    console.print(f"[green]Report exported:[/green] {out}")


@app.command()
def status(limit: int = 10) -> None:
    """Show recent run compliance statuses."""
    settings = load_config(_settings_path(None))
    storage = AuditStorage(f"sqlite:///{settings.audit_db}")
    records = storage.list_records(limit=limit)
    registry = get_check_registry()
    table = Table(title="HELIOS Runs")
    table.add_column("Run ID")
    table.add_column("Pipeline")
    table.add_column("Start")
    table.add_column("Compliance")
    for record in records:
        status_value = "pass"
        if any(check.status == "fail" for check in record.checks):
            status_value = "fail"
        elif any(check.status == "warn" for check in record.checks):
            status_value = "warn"
        score = registry.compute_score(record.checks).score
        score_label = "n/a" if score is None else str(score)
        score_color = (
            "yellow"
            if score is None
            else "green"
            if score >= 80
            else "yellow"
            if score >= 60
            else "red"
        )
        table.add_row(
            str(record.run_id),
            record.pipeline_name,
            record.start_time.isoformat(),
            f"[{score_color}]{score_label}[/{score_color}] ({status_value})",
        )
    console.print(table)


@app.command("serve")
def serve(host: str | None = None, port: int | None = None, open_browser: bool = True) -> None:
    """Start the HELIOS dashboard web server (requires HELIOS_DASHBOARD_API_KEY)."""
    settings = load_config(_settings_path(None))
    try:
        settings.require_dashboard_api_key()
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    bind_host = host or settings.dashboard.host
    bind_port = port or settings.dashboard.port
    app_instance = create_app(settings=settings)
    if open_browser:
        webbrowser.open(f"http://{bind_host}:{bind_port}/static/index.html")
    uvicorn.run(app_instance, host=bind_host, port=bind_port, log_level=settings.log_level.lower())


@app.command("snakemake-wrap")
def snakemake_wrap(
    command: Annotated[list[str] | None, typer.Argument()] = None,
    work_dir: Annotated[Path, typer.Option("--work-dir")] = Path("."),
    output_dir: Annotated[Path, typer.Option("--output-dir")] = Path("./results"),
) -> None:
    """Wrap Snakemake execution and trigger post-run audit."""
    if not command:
        raise typer.BadParameter(
            "Provide command after -- e.g. helios snakemake-wrap -- snakemake --cores 4"
        )
    exit_code = run_wrapped_snakemake(command, work_dir=work_dir, output_dir=output_dir)
    if exit_code != 0:
        console.print(f"[red]Snakemake exited with code {exit_code}[/red]")
        raise typer.Exit(code=exit_code)
    console.print("[green]Snakemake wrapped audit complete[/green]")


@key_app.command("generate")
def key_generate(
    allow_unencrypted: Annotated[bool, typer.Option("--allow-unencrypted")] = False,
) -> None:
    """Generate Ed25519 signing key pair."""
    try:
        private_path, public_path = generate_keypair(allow_unencrypted=allow_unencrypted)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Private key:[/green] {private_path}")
    console.print(f"[green]Public key:[/green] {public_path}")
    if not os.environ.get("HELIOS_KEY_PASSPHRASE"):
        console.print(
            "[yellow]Private key is stored unencrypted (mode 0600). "
            "Set HELIOS_KEY_PASSPHRASE before `helios key generate` to encrypt it.[/yellow]"
        )


@key_app.command("show")
def key_show() -> None:
    """Show current public key fingerprint."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    public_path = Path("~/.helios/keys/helios.pub").expanduser()
    if not public_path.exists():
        raise typer.BadParameter("Public key not found, run 'helios key generate' first.")
    public_key = serialization.load_pem_public_key(public_path.read_bytes())
    if not isinstance(public_key, Ed25519PublicKey):
        raise typer.BadParameter("Configured public key is not Ed25519.")
    console.print(f"Fingerprint: {public_key_fingerprint(public_key)}")


@config_app.command("print")
def config_print(path: Path | None = None) -> None:
    """Print effective configuration as JSON."""
    settings = load_config(str(path) if path else None)
    console.print_json(data=settings.redacted_dump())


@config_app.command("validate")
def config_validate(path: Path | None = None) -> None:
    """Validate configuration file and environment settings."""
    try:
        settings = load_config(str(path) if path else None)
        console.print(f"[green]Configuration valid[/green] (log level: {settings.log_level})")
    except (ValidationError, FileNotFoundError, OSError, ValueError) as exc:
        console.print(f"[red]Configuration invalid:[/red] {exc}")
        raise typer.Exit(code=1) from exc


def _export_record(record: AuditRecord, format_name: str, settings: HeliosSettings) -> Path:
    """Export report in selected format and return generated path."""
    output_dir = settings.export.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    include_ai_act = settings.export.ai_act_fragment
    if format_name == "json":
        primary = export_json(
            record, output_dir / f"{record.run_id}.json", include_ai_act=include_ai_act
        )
    elif format_name == "pdf":
        primary = export_pdf(record, output_dir / f"{record.run_id}.pdf")
    elif format_name == "rocrate":
        primary = export_rocrate(record, output_dir / str(record.run_id))
    else:
        raise typer.BadParameter("export format must be json, pdf, or rocrate")
    if settings.export.include_rocrate and format_name != "rocrate":
        export_rocrate(record, output_dir / str(record.run_id))
    return primary


def _run_streaming_command(command: list[str], work_dir: Path, timeout: int = 86_400) -> int:
    """Run subprocess and stream stdout/stderr to terminal with Rich."""
    process = subprocess.Popen(
        command,
        cwd=work_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines: deque[str] = deque(maxlen=20)
    deadline = time.monotonic() + timeout
    with Live(console=console, refresh_per_second=8) as live:
        if process.stdout is not None:
            for line in process.stdout:
                if time.monotonic() > deadline:
                    process.kill()
                    process.wait()
                    return 124
                lines.append(line.rstrip("\n"))
                live.update(
                    Panel(
                        Text("\n".join(lines), style="cyan"),
                        title="Pipeline Output",
                        border_style="cyan",
                    )
                )
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        process.kill()
        process.wait()
        return 124
    try:
        return process.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return 124


if __name__ == "__main__":
    app()
