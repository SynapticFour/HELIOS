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


def test_reference_genome_fail_without_bam(tmp_path: Path) -> None:
    check = ReferenceGenomeCheck()
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[],
    )
    assert check.run(context).status == "fail"


def test_reference_genome_fail_for_grch37(tmp_path: Path) -> None:
    header = tmp_path / "old.bam.header"
    header.write_text(
        "@SQ\tSN:chr1\tLN:249250621\tUR:ftp://example.org/grch37.fa\n",
        encoding="utf-8",
    )
    check = ReferenceGenomeCheck()
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[header],
    )
    assert check.run(context).status == "fail"
