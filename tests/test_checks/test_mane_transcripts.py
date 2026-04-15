"""Tests for MANE transcript check."""

from __future__ import annotations

from pathlib import Path

from helios.checks.mane_transcripts import ManeTranscriptCheck
from helios.core.run_context import RunContext


def test_mane_transcripts_pass(vcf_path: Path, tmp_path: Path) -> None:
    check = ManeTranscriptCheck()
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[vcf_path],
    )
    result = check.run(context)
    assert result.status == "pass"

