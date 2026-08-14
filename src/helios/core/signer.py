"""Ed25519 signing of audit records. Verification lives in ``signature``."""

from __future__ import annotations

import base64
from pathlib import Path

from helios.core.audit_record import AuditRecord
from helios.core.signature import (
    AuditSignature,
    _key_dir,
    _public_key_pem,
    generate_keypair,
    load_private_key,
    public_key_fingerprint,
    verify_signature_bytes,
)

# Back-compat aliases used by the CLI and tests.
_public_fingerprint = public_key_fingerprint


def sign_record(record: AuditRecord, private_key_path: Path) -> AuditRecord:
    """Sign canonical record JSON and return a new immutable record."""
    private_key = load_private_key(private_key_path)
    public_key = private_key.public_key()
    payload = record.canonical_json().encode("utf-8")
    signature = private_key.sign(payload)
    signature_b64 = base64.b64encode(signature).decode("utf-8")
    fingerprint = public_key_fingerprint(public_key)

    return record.model_copy(
        update={
            "signature": AuditSignature(
                algorithm="Ed25519",
                public_key_fingerprint=fingerprint,
                signature_b64=signature_b64,
                public_key_pem=_public_key_pem(public_key),
            )
        }
    )


def verify_record(record: AuditRecord, trusted_keys_dir: Path | None = None) -> bool:
    """Verify attached signature against the operator trust store."""
    return record.verify_signature(trusted_keys_dir=trusted_keys_dir)


__all__ = [
    "generate_keypair",
    "public_key_fingerprint",
    "sign_record",
    "verify_record",
    "verify_signature_bytes",
    "_key_dir",
    "_public_fingerprint",
]
