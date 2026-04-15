"""Snakemake integration hooks for HELIOS."""

from __future__ import annotations

from pathlib import Path

from helios.core.run_context import RunContext


def build_context(work_dir: Path, output_dir: Path, pipeline_name: str) -> RunContext:
    """Create a run context from Snakemake output tree."""
    artifacts = [path for path in output_dir.rglob("*") if path.is_file()]
    return RunContext(
        pipeline_name=pipeline_name,
        executor="snakemake",
        work_dir=work_dir,
        output_dir=output_dir,
        artifacts=artifacts,
    )

