"""Immutable audit record models and cryptographic verification utilities."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class FileHash(BaseModel):
    """A file identity tuple used in audit records."""

    path: str
    sha256: str
    size_bytes: int


class ContainerRecord(BaseModel):
    """Container provenance attached to a pipeline run."""

    name: str
    tag: str
    digest: str | None = None
    pinned: bool


class CheckResult(BaseModel):
    """Result emitted by a compliance check."""

    check_id: str
    status: Literal["pass", "warn", "fail", "skip", "info"]
    message: str
    # Any is used for structured evidence payloads (lists/histograms/objects).
    evidence: dict[str, Any] = Field(default_factory=dict)


class ReferenceGenomeInfo(BaseModel):
    """Reference assembly metadata associated with a run."""

    assembly: str
    source_url: str
    sha256: str


class AuditSignature(BaseModel):
    """Signature envelope over canonical audit record payload."""

    algorithm: Literal["Ed25519"]
    public_key_fingerprint: str
    signature_b64: str
    signed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuditRecord(BaseModel):
    """Central immutable audit artifact for a single pipeline run."""

    model_config = ConfigDict(frozen=True)

    run_id: UUID = Field(default_factory=uuid4)
    pipeline_name: str
    pipeline_version: str | None = None
    executor: Literal["nextflow", "snakemake", "cwl", "unknown"] = "unknown"
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    input_files: list[FileHash] = Field(default_factory=list)
    output_files: list[FileHash] = Field(default_factory=list)
    containers: list[ContainerRecord] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)  # Any for heterogeneous user params.
    checks: list[CheckResult] = Field(default_factory=list)
    reference_genome: ReferenceGenomeInfo | None = None
    signature: AuditSignature | None = None
    schema_version: str = "1.0"

    def canonical_json(self) -> str:
        """Return canonical JSON payload used for signing."""
        payload = self.model_dump(mode="json")
        payload["signature"] = None
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def to_json(self) -> str:
        """Serialize the full record as indented JSON."""
        return self.model_dump_json(indent=2)

    def verify_signature(self) -> bool:
        """Verify attached signature against the canonical payload."""
        if self.signature is None:
            return False
        from helios.core.signer import verify_signature_bytes

        signature = base64.b64decode(self.signature.signature_b64.encode("utf-8"))
        return verify_signature_bytes(
            fingerprint=self.signature.public_key_fingerprint,
            payload=self.canonical_json().encode("utf-8"),
            signature=signature,
        )

