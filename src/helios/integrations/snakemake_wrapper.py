"""Snakemake wrapper utility that executes Snakemake and triggers HELIOS audit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from helios.checks import CheckRegistry
from helios.config import load_config
from helios.core.audit_record import AuditRecord
from helios.core.persist import hash_files, persist_record
from helios.integrations.snakemake import SnakemakeRunParser


def run_wrapped_snakemake(command: list[str], work_dir: Path, output_dir: Path) -> int:
    """Execute Snakemake command and persist a HELIOS audit record on success."""
    settings = load_config()
    try:
        process = subprocess.run(
            command,
            cwd=work_dir,
            timeout=settings.command_timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 124
    if process.returncode != 0:
        return process.returncode
    parser = SnakemakeRunParser(snakemake_dir=work_dir, output_dir=output_dir)
    context = parser.build_run_context()
    registry = CheckRegistry()
    enabled = registry.resolve_enabled(settings.checks.enabled)
    checks = registry.run_all(context, enabled=enabled, settings=settings)
    record = AuditRecord(
        pipeline_name=context.pipeline_name,
        executor="snakemake",
        containers=parser.get_containers(),
        parameters={"wrapped_command": command},
        checks=checks,
        input_files=hash_files([]),
        output_files=hash_files(context.artifacts),
        work_dir=str(work_dir),
        output_dir=str(output_dir),
    )
    persist_record(record, settings, sign=True)
    if any(check.status == "fail" for check in checks):
        return 1
    return 0


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
