"""Shared hashing, signing, and persistence for audit records."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from helios.config import HeliosSettings
from helios.core.audit_record import AuditRecord, CheckResult, FileHash, ReferenceGenomeInfo
from helios.core.hasher import sha256_file
from helios.core.signer import sign_record
from helios.core.storage import AuditStorage


def hash_files(paths: Iterable[Path]) -> list[FileHash]:
    """Hash existing files; skip missing or non-file paths."""
    output: list[FileHash] = []
    seen: set[str] = set()
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        resolved = str(path)
        if resolved in seen:
            continue
        seen.add(resolved)
        output.append(
            FileHash(path=resolved, sha256=sha256_file(path), size_bytes=path.stat().st_size)
        )
    return output


def reference_genome_from_checks(checks: list[CheckResult]) -> ReferenceGenomeInfo | None:
    """Build ReferenceGenomeInfo from a passing GA4GH-REF-001 result."""
    for check in checks:
        if check.check_id != "GA4GH-REF-001" or check.status != "pass":
            continue
        evidence = check.evidence
        assembly = str(evidence.get("assembly") or evidence.get("required_assembly") or "GRCh38")
        source = str(evidence.get("header_source_match") or evidence.get("artifact") or "")
        digest = str(evidence.get("known_md5_chr1") or "")
        return ReferenceGenomeInfo(assembly=assembly, source_url=source, sha256=digest)
    return None


def persist_record(
    record: AuditRecord,
    settings: HeliosSettings,
    *,
    sign: bool = True,
) -> AuditRecord:
    """Attach derived fields, optionally sign, then persist."""
    stored = record
    if stored.reference_genome is None:
        info = reference_genome_from_checks(stored.checks)
        if info is not None:
            stored = stored.model_copy(update={"reference_genome": info})
    if sign and settings.signing_key.exists():
        stored = sign_record(stored, settings.signing_key)
    storage = AuditStorage(f"sqlite:///{settings.audit_db}")
    storage.save_record(stored)
    return stored
