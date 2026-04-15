"""JSON export for machine-readable compliance reports."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from helios import __version__
from helios.core.audit_record import AuditRecord


def export_json(record: AuditRecord, output_path: Path) -> Path:
    """Write audit record JSON report with optional AI Act Article 11 fragment.

    Article 11(1)(a-b) requires system description and intended purpose.
    Article 11(1)(d-e) requires data governance and technical documentation.
    Article 11(1)(f) requires traceable post-market audit references.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = record.model_dump(mode="json")
    if _includes_ai_components(record):
        payload["ai_act_art11_fragment"] = _build_ai_act_art11_fragment(record)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def _includes_ai_components(record: AuditRecord) -> bool:
    keywords = {"ai", "ml", "model", "inference", "classifier", "predict"}
    params_text = " ".join(f"{k} {v}" for k, v in record.parameters.items()).lower()
    container_text = " ".join(container.name for container in record.containers).lower()
    return any(term in params_text or term in container_text for term in keywords)


def _build_ai_act_art11_fragment(record: AuditRecord) -> dict[str, object]:
    """Build Article 11 technical documentation fragment for AI-enabled runs."""
    return {
        "schema_version": "EU-AI-ACT-2024/1689-ART11-v1",
        "system_description": (
            "HELIOS-audited genomic analysis pipeline with AI-assisted interpretation."
        ),
        "intended_purpose": "Clinical genomic variant interpretation",
        "risk_classification": "high_risk",
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

