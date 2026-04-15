"""Additional branch coverage tests for RO-Crate export helpers."""

from __future__ import annotations

from helios.core.audit_record import AuditRecord, CheckResult
from helios.export.rocrate import record_check_standard_map


def test_record_check_standard_map_fallback_from_evidence() -> None:
    record = AuditRecord(
        pipeline_name="x",
        executor="nextflow",
        checks=[
            CheckResult(
                check_id="NON-REG",
                status="warn",
                message="x",
                evidence={"standards": ["ISO15189", "GA4GH"]},
            )
        ],
    )
    mapped = record_check_standard_map("NON-REG", record)
    assert mapped
    assert mapped[0].startswith("https://bioschemas.org/")


def test_record_check_standard_map_default_when_missing() -> None:
    record = AuditRecord(pipeline_name="x", executor="nextflow", checks=[])
    assert record_check_standard_map("UNKNOWN", record) == ["https://schema.org/PropertyValue"]


def test_record_check_standard_map_from_registered_standards() -> None:
    record = AuditRecord(pipeline_name="x", executor="nextflow", checks=[])
    mapped = record_check_standard_map("GA4GH-MANE-001", record)
    assert any(item.startswith("https://schema.org/") for item in mapped)
