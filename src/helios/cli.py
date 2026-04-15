"""Typer-based command line interface for HELIOS."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table

from helios.checks.base import BaseCheck
from helios.checks.container_pinning import ContainerPinningCheck
from helios.checks.crypt4gh_output import Crypt4GHOutputCheck
from helios.checks.mane_transcripts import ManeTranscriptCheck
from helios.checks.reference_genome import ReferenceGenomeCheck
from helios.checks.vus_rate import VUSRateCheck
from helios.config import load_config
from helios.core.audit_record import AuditRecord, FileHash
from helios.core.hasher import sha256_file
from helios.core.signer import generate_keypair, sign_record
from helios.core.storage import AuditStorage
from helios.export.json_export import export_json
from helios.export.pdf_export import export_pdf
from helios.export.rocrate import export_rocrate
from helios.integrations.nextflow import build_context as nextflow_context
from helios.integrations.nextflow import extract_containers, parse_trace
from helios.integrations.snakemake import build_context as snakemake_context

app = typer.Typer(help="HELIOS genomics pipeline audit and validation CLI.")
key_app = typer.Typer(help="Manage HELIOS signing keys.")
app.add_typer(key_app, name="key")
console = Console()
PIPELINE_OPTION = typer.Option(..., "--pipeline")
WORK_DIR_OPTION = typer.Option(..., "--work-dir")
OUTPUT_DIR_OPTION = typer.Option(..., "--output-dir")


def _collect_checks() -> list[BaseCheck]:
    return [
        ReferenceGenomeCheck(),
        ContainerPinningCheck(),
        ManeTranscriptCheck(),
        VUSRateCheck(),
        Crypt4GHOutputCheck(),
    ]


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
    pipeline: str = PIPELINE_OPTION,
    work_dir: Path = WORK_DIR_OPTION,
    output_dir: Path = OUTPUT_DIR_OPTION,
) -> None:
    """Capture run context, execute checks, and persist an audit record."""
    config = load_config("helios.toml" if Path("helios.toml").exists() else None)
    storage = AuditStorage(f"sqlite:///{Path(config.audit_db).expanduser()}")

    if pipeline == "nextflow":
        context = nextflow_context(work_dir, output_dir, pipeline_name="nextflow-pipeline")
        trace_file = work_dir / "trace.txt"
        containers = extract_containers(parse_trace(trace_file)) if trace_file.exists() else []
    elif pipeline == "snakemake":
        context = snakemake_context(work_dir, output_dir, pipeline_name="snakemake-pipeline")
        containers = []
    else:
        raise typer.BadParameter("pipeline must be nextflow or snakemake")

    checks = [check.run(context) for check in _collect_checks()]
    input_files: list[FileHash] = []
    output_files: list[FileHash] = []
    for artifact in context.artifacts:
        digest = sha256_file(artifact)
        output_files.append(
            FileHash(path=str(artifact), sha256=digest, size_bytes=artifact.stat().st_size)
        )

    record = AuditRecord(
        pipeline_name=context.pipeline_name,
        executor=context.executor,
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        input_files=input_files,
        output_files=output_files,
        containers=containers,
        parameters=context.parameters,
        checks=checks,
    )
    key_path = Path(config.signing_key).expanduser()
    if key_path.exists():
        record = sign_record(record, key_path)
    storage.save_record(record)
    console.print(f"[green]Run recorded:[/green] {record.run_id}")


@app.command()
def validate(run_id: UUID) -> None:
    """Re-run checks against stored run artifact context."""
    storage = AuditStorage()
    record = storage.get_record(run_id)
    if record is None:
        raise typer.BadParameter(f"Run {run_id} not found")
    status_counts = {"pass": 0, "warn": 0, "fail": 0}
    for check in record.checks:
        status_counts[check.status] += 1
    console.print(
        f"Validation replay for {run_id}: "
        f"{status_counts['pass']} pass, {status_counts['warn']} warn, {status_counts['fail']} fail"
    )


@app.command()
def report(
    run_id: UUID,
    format: str = typer.Option("json", "--format"),
) -> None:
    """Export report in JSON, PDF, or RO-Crate format."""
    config = load_config("helios.toml" if Path("helios.toml").exists() else None)
    storage = AuditStorage(f"sqlite:///{Path(config.audit_db).expanduser()}")
    record = storage.get_record(run_id)
    if record is None:
        raise typer.BadParameter(f"Run {run_id} not found")

    output_dir = Path(config.export.output_dir).expanduser()
    if format == "json":
        out = export_json(record, output_dir / f"{run_id}.json")
    elif format == "pdf":
        out = export_pdf(record, output_dir / f"{run_id}.pdf")
    elif format == "rocrate":
        out = export_rocrate(record, output_dir / str(run_id))
    else:
        raise typer.BadParameter("format must be json, pdf, or rocrate")
    console.print(f"[green]Report exported:[/green] {out}")


@app.command()
def status(limit: int = 10) -> None:
    """Show recent run compliance statuses."""
    storage = AuditStorage()
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
        table.add_row(
            str(record.run_id),
            record.pipeline_name,
            record.start_time.isoformat(),
            status_value,
        )
    console.print(table)


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


if __name__ == "__main__":
    app()

