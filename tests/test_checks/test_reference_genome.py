"""Tests for reference genome compliance check."""

from __future__ import annotations

from pathlib import Path

from helios.checks.reference_genome import ReferenceGenomeCheck
from helios.core.run_context import RunContext


def test_reference_genome_pass_for_grch38_header(bam_header_path: Path, tmp_path: Path) -> None:
    check = ReferenceGenomeCheck()
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[bam_header_path],
    )
    result = check.run(context)
    assert result.status == "pass"
