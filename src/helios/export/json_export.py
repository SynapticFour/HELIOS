"""JSON export for machine-readable compliance reports."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from helios import __version__
from helios.core.audit_record import AuditRecord


def export_json(
    record: AuditRecord,
    output_path: Path,
    *,
    include_ai_act: bool = False,
) -> Path:
    """Write audit record JSON report with optional AI Act Article 11 fragment.

    The fragment is included only when ``include_ai_act`` is true (config
    ``export.ai_act_fragment``). It is engineering orientation, not a risk
    classification.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = record.model_dump(mode="json")
    if include_ai_act:
        payload["ai_act_art11_fragment"] = _build_ai_act_art11_fragment(record)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def _build_ai_act_art11_fragment(record: AuditRecord) -> dict[str, object]:
    """Build Article 11 technical documentation fragment when opted in."""
    intended = record.parameters.get("intended_purpose")
    if not isinstance(intended, str) or not intended:
        intended = "Genomic pipeline audit evidence"
    return {
        "schema_version": "EU-AI-ACT-2024/1689-ART11-v1",
        "system_description": "HELIOS-audited genomic analysis pipeline.",
        "intended_purpose": intended,
        "risk_classification": "unspecified",
        "data_governance": {
            "training_data_sources": [],
            "validation_data_sources": [],
            "data_quality_measures": [],
            "representativeness_statement": None,
        },
        "technical_documentation": {
            "pipeline_version": record.pipeline_version or "unknown",
            "containers": [container.model_dump(mode="json") for container in record.containers],
            "reference_genome": (
                record.reference_genome.assembly if record.reference_genome else "unknown"
            ),
            "validation_metrics": {
                "checks_passed": sum(
                    1 for check in record.checks if check.status in {"pass", "info"}
                ),
                "checks_failed": sum(1 for check in record.checks if check.status == "fail"),
            },
        },
        "audit_trail_reference": {
            "run_id": str(record.run_id),
            "record_hash": hashlib.sha256(record.canonical_json().encode("utf-8")).hexdigest(),
            "signed_by": (
                record.signature.public_key_fingerprint if record.signature else "unsigned"
            ),
        },
        "generated_at": datetime.now(UTC).isoformat(),
        "generated_by": f"HELIOS {__version__}",
    }
