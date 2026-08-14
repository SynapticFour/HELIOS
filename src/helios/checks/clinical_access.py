"""Solum clinical access / consent audit evidence (H2 clinical HELIOS type)."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext

SOLUM_GENESIS_HASH = "0" * 64
_CLINICAL_EVENT_PREFIXES = (
    "consent.",
    "authorization.",
    "data.encrypt",
    "data.decrypt",
    "access.",
)


class ClinicalAccessCheck(BaseCheck):
    """Validate a Solum HELIOS chain export for clinical-plane audit events."""

    check_id = "CLIN-ACCESS-001"
    name = "Solum clinical access audit"
    description = (
        "Verify solum-audit-helios-chain-v1 hash chain and summarize consent / "
        "authorization / crypto access events for clinical evidence packs."
    )
    severity = "warning"
    standards = ["ISO27001:A.8.15", "EHDS-access-evidence"]

    def run(self, context: RunContext) -> CheckResult:
        path = self._resolve_export_path(context)
        if path is None:
            return CheckResult(
                check_id=self.check_id,
                status="skip",
                message=(
                    "No Solum audit export supplied "
                    "(parameters.solum_audit_export or *.solum-audit*.json); skipped."
                ),
                evidence={"skipped": True, "reason": "no_export"},
            )

        try:
            raw = path.read_text(encoding="utf-8")
            doc = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            return CheckResult(
                check_id=self.check_id,
                status="fail",
                message=f"Unreadable Solum audit export {path}: {exc}",
                evidence={"path": str(path)},
            )

        fmt = doc.get("format")
        if fmt != "solum-audit-helios-chain-v1":
            return CheckResult(
                check_id=self.check_id,
                status="fail",
                message=f"Unexpected Solum export format {fmt!r}; want solum-audit-helios-chain-v1",
                evidence={"path": str(path), "format": fmt},
            )

        records = doc.get("records") or []
        if not isinstance(records, list):
            return CheckResult(
                check_id=self.check_id,
                status="fail",
                message="Solum export records field is not a list.",
                evidence={"path": str(path)},
            )

        chain_error = _verify_solum_chain(records)
        counts: Counter[str] = Counter()
        for rec in records:
            if not isinstance(rec, dict):
                continue
            event = rec.get("event") or {}
            et = event.get("event_type") or rec.get("event_type") or ""
            if isinstance(et, str) and et.startswith(_CLINICAL_EVENT_PREFIXES):
                counts[et] += 1

        record_count = int(doc.get("record_count") or len(records))
        clinical_total = sum(counts.values())
        evidence = {
            "path": str(path),
            "format": fmt,
            "generator": doc.get("generator"),
            "record_count": record_count,
            "clinical_event_total": clinical_total,
            "clinical_event_counts": dict(counts),
            "chain_ok": chain_error is None,
        }
        if chain_error is not None:
            evidence["chain_error"] = chain_error
            return CheckResult(
                check_id=self.check_id,
                status="fail",
                message=f"Solum hash chain failed: {chain_error}",
                evidence=evidence,
            )
        if clinical_total == 0:
            return CheckResult(
                check_id=self.check_id,
                status="fail",
                message=(
                    f"Solum chain export OK ({record_count} records) but no "
                    "clinical-plane consent/authorization/crypto events were found."
                ),
                evidence=evidence,
            )
        return CheckResult(
            check_id=self.check_id,
            status="pass",
            message=(
                f"Solum chain export OK ({record_count} records, "
                f"{clinical_total} clinical-plane events, hash chain verified)."
            ),
            evidence=evidence,
        )

    @staticmethod
    def _resolve_export_path(context: RunContext) -> Path | None:
        param = context.parameters.get("solum_audit_export")
        if isinstance(param, str) and param:
            p = Path(param)
            if p.is_file():
                return p
        for art in context.artifacts:
            name = art.name.lower()
            if art.suffix == ".json" and (
                "solum-audit" in name
                or "solum_audit" in name
                or name.endswith("-helios-chain.json")
            ):
                return art
        return None


def solum_record_hash(seq: int, prev_hash: str, event: dict[str, Any]) -> str:
    """SHA-256 over seq (u64 BE) || prev_hash || compact JSON event (Solum store.rs)."""
    event_json = json.dumps(event, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256()
    digest.update(seq.to_bytes(8, "big"))
    digest.update(prev_hash.encode("utf-8"))
    digest.update(event_json.encode("utf-8"))
    return digest.hexdigest()


def _verify_solum_chain(records: list[object]) -> str | None:
    expected_prev = SOLUM_GENESIS_HASH
    for index, rec in enumerate(records):
        if not isinstance(rec, dict):
            return f"record {index} is not an object"
        raw_seq = rec.get("seq")
        if not isinstance(raw_seq, int):
            return f"record {index} missing integer seq"
        seq = raw_seq
        if seq != index + 1:
            return f"expected seq {index + 1}, found {seq}"
        prev_hash = rec.get("prev_hash")
        stored_hash = rec.get("hash")
        event = rec.get("event")
        if not isinstance(prev_hash, str) or not isinstance(stored_hash, str):
            return f"seq {seq} missing hash/prev_hash"
        if not isinstance(event, dict):
            return f"seq {seq} missing event object"
        if prev_hash != expected_prev:
            return f"seq {seq} prev_hash does not match preceding record"
        recomputed = solum_record_hash(seq, prev_hash, event)
        if recomputed != stored_hash:
            return f"seq {seq} stored hash does not match recomputed hash"
        expected_prev = stored_hash
    return None
