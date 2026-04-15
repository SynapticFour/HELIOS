"""Tests for immutable audit record model behavior."""

from __future__ import annotations

from helios.core.audit_record import AuditRecord


def test_audit_record_json_roundtrip() -> None:
    record = AuditRecord(pipeline_name="demo", executor="nextflow")
    payload = record.to_json()
    loaded = AuditRecord.model_validate_json(payload)
    assert loaded.run_id == record.run_id
    assert loaded.pipeline_name == "demo"


def test_verify_signature_false_without_signature() -> None:
    record = AuditRecord(pipeline_name="demo", executor="nextflow")
    assert record.verify_signature() is False

