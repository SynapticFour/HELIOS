"""Typer-based command line interface for HELIOS."""

from __future__ import annotations

import logging
import subprocess
import webbrowser
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

import typer
import uvicorn
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from helios.checks import CheckRegistry
from helios.config import HeliosSettings, load_config
from helios.core.audit_record import AuditRecord, FileHash
from helios.core.hasher import sha256_file
from helios.core.run_context import RunContext
from helios.core.signer import generate_keypair, sign_record
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


def _build_context_from_record(record: AuditRecord) -> RunContext:
    """Reconstruct a run context from a persisted audit record."""

    artifacts = [
        Path(file_hash.path)
        for file_hash in record.output_files
        if Path(file_hash.path).exists()
    ]
    return RunContext(
        pipeline_name=record.pipeline_name,
        executor=record.executor,
        work_dir=Path("."),
        output_dir=Path("."),
        parameters=record.parameters,
        artifacts=artifacts,
    )


@app.command()
def init(path: Path = Path("helios.toml")) -> None:
    """Initialize HELIOS configuration in the current directory."""
    example = Path("helios.toml.example")
    if not example.exists():
        raise typer.BadParameter("helios.toml.example not found in current directory")
    path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    console.print(f"[green]Initialized config:[/green] {path}")


@app.command()
def run(
    pipeline: Annotated[str, typer.Option("--pipeline", "-p")],
    work_dir: Annotated[Path, typer.Option("--work-dir", "-w")] = Path("."),
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o")] = Path("./results"),
    config: Annotated[Path | None, typer.Option("--config", "-c")] = None,
    no_sign: Annotated[bool, typer.Option("--no-sign")] = False,
    export_format: Annotated[str, typer.Option("--export")] = "json",
    command: Annotated[list[str] | None, typer.Argument()] = None,
) -> None:
    """Run or wrap a pipeline, audit artifacts, sign, store, and export report."""
    if config:
        config_path = str(config)
    elif Path("helios.toml").exists():
        config_path = "helios.toml"
    else:
        config_path = None
    settings = load_config(config_path)
    logging.basicConfig(level=settings.log_level.upper())
    storage = AuditStorage(f"sqlite:///{settings.audit_db}")
    start_time = datetime.now(UTC)

    if command:
        return_code = _run_streaming_command(command, work_dir=work_dir)
        if return_code != 0:
            console.print(
                f"[red]Wrapped command exited with code {return_code}.[/red] "
                "Check pipeline logs and retry with corrected parameters."
            )

    parser_context: RunContext
    containers = []
    if pipeline == "nextflow":
        nextflow_parser = NextflowRunParser(work_dir=work_dir, output_dir=output_dir)
        parser_context = nextflow_parser.build_run_context()
        containers = nextflow_parser.get_containers()
    elif pipeline == "snakemake":
        snakemake_parser = SnakemakeRunParser(snakemake_dir=work_dir, output_dir=output_dir)
        parser_context = snakemake_parser.build_run_context()
        containers = snakemake_parser.get_containers()
    else:
        raise typer.BadParameter("pipeline must be nextflow or snakemake")

    registry = CheckRegistry()
    enabled_ids = _resolve_enabled_checks(registry, settings.checks.enabled)
    checks = registry.run_all(parser_context, enabled=enabled_ids)
    input_files = _hash_inputs_from_parameters(parser_context)
    output_files: list[FileHash] = []
    for artifact in parser_context.artifacts:
        digest = sha256_file(artifact)
        output_files.append(
            FileHash(path=str(artifact), sha256=digest, size_bytes=artifact.stat().st_size)
        )

    record = AuditRecord(
        pipeline_name=parser_context.pipeline_name,
        executor=parser_context.executor,
        start_time=start_time,
        end_time=datetime.now(UTC),
        input_files=input_files,
        output_files=output_files,
        containers=containers,
        parameters=parser_context.parameters,
        checks=checks,
    )
    if not no_sign and settings.signing_key.exists():
        record = sign_record(record, settings.signing_key)
    storage.save_record(record)
    log = logging.LoggerAdapter(logger, {"run_id": str(record.run_id)})
    log.info("Audit record persisted")

    report_path = _export_record(record, export_format, settings.export.output_dir)
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


@app.command()
def validate(run_id: UUID) -> None:
    """Re-run checks against stored run artifact context."""
    settings = load_config("helios.toml" if Path("helios.toml").exists() else None)
    storage = AuditStorage(f"sqlite:///{settings.audit_db}")
    record = storage.get_record(run_id)
    if record is None:
        raise typer.BadParameter(f"Run {run_id} not found")

    context = _build_context_from_record(record)
    registry = CheckRegistry()
    enabled_ids = _resolve_enabled_checks(registry, settings.checks.enabled)
    rerun_results = registry.run_all(context, enabled=enabled_ids)
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


@app.command()
def report(
    run_id: UUID,
    format: Literal["json", "pdf", "rocrate"] = typer.Option("json", "--format"),
) -> None:
    """Export report in JSON, PDF, or RO-Crate format."""
    settings = load_config("helios.toml" if Path("helios.toml").exists() else None)
    storage = AuditStorage(f"sqlite:///{settings.audit_db}")
    record = storage.get_record(run_id)
    if record is None:
        raise typer.BadParameter(f"Run {run_id} not found")

    out = _export_record(record, format, settings.export.output_dir)
    console.print(f"[green]Report exported:[/green] {out}")


@app.command()
def status(limit: int = 10) -> None:
    """Show recent run compliance statuses."""
    storage = AuditStorage(f"sqlite:///{HeliosSettings().audit_db}")
    records = storage.list_records(limit=limit)
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
        score = CheckRegistry().compute_score(record.checks).score
        score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
        table.add_row(
            str(record.run_id),
            record.pipeline_name,
            record.start_time.isoformat(),
            f"[{score_color}]{score}[/{score_color}] ({status_value})",
        )
    console.print(table)


@app.command("serve")
def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    """Start the HELIOS dashboard web server."""
    settings = HeliosSettings()
    app_instance = create_app(settings=settings)
    if open_browser:
        webbrowser.open(f"http://{host}:{port}/static/index.html")
    uvicorn.run(app_instance, host=host, port=port, log_level=settings.log_level.lower())


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
def key_generate() -> None:
    """Generate Ed25519 signing key pair."""
    private_path, public_path = generate_keypair()
    console.print(f"[green]Private key:[/green] {private_path}")
    console.print(f"[green]Public key:[/green] {public_path}")


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
    from helios.core.signer import _public_fingerprint

    console.print(f"Fingerprint: {_public_fingerprint(public_key)}")


@config_app.command("print")
def config_print(path: Path | None = None) -> None:
    """Print effective configuration as JSON."""
    settings = load_config(str(path) if path else None)
    console.print_json(settings.model_dump_json(indent=2))


@config_app.command("validate")
def config_validate(path: Path | None = None) -> None:
    """Validate configuration file and environment settings."""
    try:
        settings = load_config(str(path) if path else None)
        console.print(f"[green]Configuration valid[/green] (log level: {settings.log_level})")
    except Exception as exc:
        console.print(f"[red]Configuration invalid:[/red] {exc}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()


def _hash_inputs_from_parameters(context: RunContext) -> list[FileHash]:
    """Best-effort input hashing from context parameter file paths."""
    output: list[FileHash] = []
    for value in context.parameters.values():
        if not isinstance(value, str):
            continue
        path = Path(value)
        if path.exists() and path.is_file():
            output.append(
                FileHash(path=str(path), sha256=sha256_file(path), size_bytes=path.stat().st_size)
            )
    return output


def _export_record(record: AuditRecord, format_name: str, output_dir: Path) -> Path:
    """Export report in selected format and return generated path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if format_name == "json":
        return export_json(record, output_dir / f"{record.run_id}.json")
    if format_name == "pdf":
        return export_pdf(record, output_dir / f"{record.run_id}.pdf")
    if format_name == "rocrate":
        return export_rocrate(record, output_dir / str(record.run_id))
    raise typer.BadParameter("export format must be json, pdf, or rocrate")


def _run_streaming_command(command: list[str], work_dir: Path) -> int:
    """Run subprocess and stream stdout/stderr to terminal with Rich."""
    process = subprocess.Popen(
        command,
        cwd=work_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines: list[str] = []
    with Live(console=console, refresh_per_second=8) as live:
        if process.stdout is not None:
            for line in process.stdout:
                lines.append(line.rstrip("\n"))
                visible = "\n".join(lines[-20:])
                live.update(
                    Panel(
                        Text(visible, style="cyan"),
                        title="Pipeline Output",
                        border_style="cyan",
                    )
                )
    return process.wait()


def _resolve_enabled_checks(registry: CheckRegistry, configured: list[str]) -> list[str]:
    """Resolve configured check names or IDs to registered check identifiers."""
    registered = registry.get_registered_checks()
    by_name = {
        cls.__name__.lower().replace("_", ""): check_id
        for check_id, cls in registered.items()
    }
    resolved: list[str] = []
    for entry in configured:
        if entry in registered:
            resolved.append(entry)
            continue
        key = entry.replace("-", "_").replace(" ", "_").lower().replace("_", "")
        if not key.endswith("check"):
            key = f"{key}check"
        matched = by_name.get(key)
        if matched:
            resolved.append(matched)
    return resolved or list(registered.keys())

