"""Solum clinical access / consent audit evidence (H2 clinical HELIOS type)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext

# Events Solum Deployment actually emits today (consent / CAP / crypto).
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
        "Verify solum-audit-helios-chain-v1 export and summarize consent / "
        "authorization / crypto access events for clinical evidence packs."
    )
    severity = "warning"
    standards = ["ISO27001:A.8.15", "EHDS-access-evidence"]

    def run(self, context: RunContext) -> CheckResult:
        path = self._resolve_export_path(context)
        if path is None:
            return CheckResult(
                check_id=self.check_id,
                status="pass",
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
        counts: Counter[str] = Counter()
        for rec in records:
            event = rec.get("event") or {}
            et = event.get("event_type") or rec.get("event_type") or ""
            if isinstance(et, str) and et.startswith(_CLINICAL_EVENT_PREFIXES):
                counts[et] += 1

        record_count = int(doc.get("record_count") or len(records))
        clinical_total = sum(counts.values())
        return CheckResult(
            check_id=self.check_id,
            status="pass",
            message=(
                f"Solum chain export OK ({record_count} records, "
                f"{clinical_total} clinical-plane events)."
            ),
            evidence={
                "path": str(path),
                "format": fmt,
                "generator": doc.get("generator"),
                "record_count": record_count,
                "clinical_event_total": clinical_total,
                "clinical_event_counts": dict(counts),
            },
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
