"""Tests for PDF report generation."""

from __future__ import annotations

from pathlib import Path

from helios.core.audit_record import AuditRecord, CheckResult
from helios.export.pdf_export import export_pdf


def test_pdf_generation(tmp_path: Path) -> None:
    record = AuditRecord(
        pipeline_name="pipeline",
        executor="nextflow",
        checks=[CheckResult(check_id="CHK", status="pass", message="All good", evidence={})],
    )
    output = tmp_path / "report.pdf"
    export_pdf(record, output)
    assert output.exists()
    assert output.stat().st_size > 1024
    assert output.read_bytes().startswith(b"%PDF")

