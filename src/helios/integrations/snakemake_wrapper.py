"""Snakemake wrapper utility that executes Snakemake and triggers HELIOS audit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from helios.checks import CheckRegistry
from helios.core.audit_record import AuditRecord
from helios.core.storage import AuditStorage
from helios.integrations.snakemake import SnakemakeRunParser


def run_wrapped_snakemake(command: list[str], work_dir: Path, output_dir: Path) -> int:
    """Execute Snakemake command and persist a HELIOS audit record."""
    process = subprocess.run(command, cwd=work_dir)
    parser = SnakemakeRunParser(snakemake_dir=work_dir, output_dir=output_dir)
    context = parser.build_run_context()
    checks = CheckRegistry().run_all(context)
    record = AuditRecord(
        pipeline_name=context.pipeline_name,
        executor="snakemake",
        containers=parser.get_containers(),
        parameters={"wrapped_command": command},
        checks=checks,
    )
    AuditStorage().save_record(record)
    return process.returncode


def main() -> None:
    """CLI entrypoint for snakemake wrapper module."""
    args = sys.argv[1:]
    if not args:
        raise SystemExit("Usage: python -m helios.integrations.snakemake_wrapper -- snakemake ...")
    if args[0] == "--":
        args = args[1:]
    code = run_wrapped_snakemake(args, Path("."), Path("./results"))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
