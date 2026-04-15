"""Ed25519 key management and audit record signing helpers."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from typing import TYPE_CHECKING

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

if TYPE_CHECKING:
    from helios.core.audit_record import AuditRecord


def _key_dir(base_dir: Path | None = None) -> Path:
    """Resolve key storage directory."""
    env_override = os.environ.get("HELIOS_KEY_DIR")
    if base_dir is not None:
        root = base_dir
    elif env_override:
        root = Path(env_override).expanduser()
    else:
        root = Path("~/.helios/keys").expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root


def generate_keypair(base_dir: Path | None = None, name: str = "helios") -> tuple[Path, Path]:
    """Generate an Ed25519 keypair and write PEM files."""
    directory = _key_dir(base_dir)
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_path = directory / f"{name}.key"
    public_path = directory / f"{name}.pub"

    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return private_path, public_path


def _public_fingerprint(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw).hexdigest()


def sign_record(record: AuditRecord, private_key_path: Path) -> AuditRecord:
    """Sign canonical record JSON and return a new immutable record."""
    from helios.core.audit_record import AuditSignature

    private_key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        raise TypeError("Provided key is not an Ed25519 private key")

    payload = record.canonical_json().encode("utf-8")
    signature = private_key.sign(payload)
    signature_b64 = base64.b64encode(signature).decode("utf-8")
    fingerprint = _public_fingerprint(private_key.public_key())

    return record.model_copy(
        update={
            "signature": AuditSignature(
                algorithm="Ed25519",
                public_key_fingerprint=fingerprint,
                signature_b64=signature_b64,
            )
        }
    )


def verify_signature_bytes(fingerprint: str, payload: bytes, signature: bytes) -> bool:
    """Verify signature against any public key matching fingerprint."""
    key_store = _key_dir()
    for path in key_store.glob("*.pub"):
        public_key = serialization.load_pem_public_key(path.read_bytes())
        if not isinstance(public_key, Ed25519PublicKey):
            continue
        if _public_fingerprint(public_key) != fingerprint:
            continue
        try:
            public_key.verify(signature, payload)
            return True
        except InvalidSignature:
            return False
    return False


def verify_record(record: AuditRecord) -> bool:
    """Verify attached signature for a full audit record."""
    return record.verify_signature()

