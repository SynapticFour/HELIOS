"""Ed25519 key management and trust-store verification.

Embedded PEMs in audit records are informational. Verification only succeeds
when the signer fingerprint matches a public key in the configured trust store.
"""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, NoEncryption
from pydantic import BaseModel, Field


class AuditSignature(BaseModel):
    """Signature envelope over canonical audit record payload."""

    algorithm: Literal["Ed25519"]
    public_key_fingerprint: str
    signature_b64: str
    signed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # Embedded SPKI PEM is display-only; verification uses the trust store.
    public_key_pem: str | None = None


def _key_dir(base_dir: Path | None = None) -> Path:
    """Resolve key storage directory with restrictive permissions."""
    env_override = os.environ.get("HELIOS_KEY_DIR")
    if base_dir is not None:
        root = base_dir
    elif env_override:
        root = Path(env_override).expanduser()
    else:
        root = Path("~/.helios/keys").expanduser()
    root.mkdir(parents=True, exist_ok=True)
    root.chmod(0o700)
    return root


def _key_password() -> bytes | None:
    raw = os.environ.get("HELIOS_KEY_PASSPHRASE")
    if raw:
        return raw.encode("utf-8")
    return None


def generate_keypair(
    base_dir: Path | None = None,
    name: str = "helios",
    *,
    allow_unencrypted: bool = False,
) -> tuple[Path, Path]:
    """Generate an Ed25519 keypair and write PEM files (private key mode 0600)."""
    directory = _key_dir(base_dir)
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_path = directory / f"{name}.key"
    public_path = directory / f"{name}.pub"

    password = _key_password()
    if password is None and not allow_unencrypted:
        raise ValueError(
            "HELIOS_KEY_PASSPHRASE is required to encrypt the private key. "
            "Set it, or pass allow_unencrypted=True only for throwaway test keys."
        )
    encryption: BestAvailableEncryption | NoEncryption = (
        BestAvailableEncryption(password) if password else NoEncryption()
    )

    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption,
        )
    )
    private_path.chmod(0o600)
    public_path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    public_path.chmod(0o644)
    return private_path, public_path


def public_key_fingerprint(public_key: Ed25519PublicKey) -> str:
    """SHA-256 hex digest of the raw 32-byte Ed25519 public key."""
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw).hexdigest()


def _public_key_pem(public_key: Ed25519PublicKey) -> str:
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def load_private_key(private_key_path: Path) -> Ed25519PrivateKey:
    """Load an Ed25519 private key, using HELIOS_KEY_PASSPHRASE when set."""
    private_key = serialization.load_pem_private_key(
        private_key_path.read_bytes(), password=_key_password()
    )
    if not isinstance(private_key, Ed25519PrivateKey):
        raise TypeError("Provided key is not an Ed25519 private key")
    return private_key


def iter_trusted_public_keys(trusted_keys_dir: Path | None = None) -> list[Ed25519PublicKey]:
    """Load Ed25519 public keys from ``*.pub`` files in the trust store."""
    if trusted_keys_dir is not None:
        directory = trusted_keys_dir
    else:
        env_override = os.environ.get("HELIOS_KEY_DIR")
        directory = (
            Path(env_override).expanduser() if env_override else Path("~/.helios/keys").expanduser()
        )
    if not directory.is_dir():
        return []
    keys: list[Ed25519PublicKey] = []
    for path in sorted(directory.glob("*.pub")):
        loaded = serialization.load_pem_public_key(path.read_bytes())
        if isinstance(loaded, Ed25519PublicKey):
            keys.append(loaded)
    return keys


def _verify_with_key(
    public_key: Ed25519PublicKey, fingerprint: str, payload: bytes, signature: bytes
) -> bool:
    if public_key_fingerprint(public_key) != fingerprint:
        return False
    try:
        public_key.verify(signature, payload)
        return True
    except InvalidSignature:
        return False


def verify_signature_bytes(
    fingerprint: str,
    payload: bytes,
    signature: bytes,
    trusted_keys_dir: Path | None = None,
) -> bool:
    """Verify a signature against the operator trust store, never against an embedded PEM."""
    for public_key in iter_trusted_public_keys(trusted_keys_dir):
        if _verify_with_key(public_key, fingerprint, payload, signature):
            return True
    return False
