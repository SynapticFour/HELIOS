"""Tests for key generation and record signing."""

from __future__ import annotations

from helios.core.audit_record import AuditRecord
from helios.core.signer import generate_keypair, sign_record, verify_record


def test_sign_and_verify_record(tmp_path, monkeypatch) -> None:
    private_key, public_key = generate_keypair(base_dir=tmp_path, name="testkey")
    assert private_key.exists()
    assert public_key.exists()

    record = AuditRecord(pipeline_name="pipeline", executor="nextflow")
    signed = sign_record(record, private_key)
    assert signed.signature is not None

    monkeypatch.setenv("HELIOS_KEY_DIR", str(tmp_path))
    (tmp_path / "testkey.pub").write_bytes(public_key.read_bytes())
    assert verify_record(signed) is True

