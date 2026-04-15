"""JSON export for machine-readable compliance reports."""

from __future__ import annotations

from pathlib import Path

from helios.core.audit_record import AuditRecord


def export_json(record: AuditRecord, output_path: Path) -> Path:
    """Write audit record JSON report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(record.to_json(), encoding="utf-8")
    return output_path

