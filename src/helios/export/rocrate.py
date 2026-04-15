"""RO-Crate export for FAIR audit metadata packaging."""

from __future__ import annotations

import json
from pathlib import Path

from helios.core.audit_record import AuditRecord


def export_rocrate(record: AuditRecord, output_dir: Path) -> Path:
    """Export minimal RO-Crate metadata from an audit record."""
    output_dir.mkdir(parents=True, exist_ok=True)
    crate = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "name": f"HELIOS Audit Record {record.run_id}",
                "identifier": str(record.run_id),
                "version": record.schema_version,
            },
        ],
    }
    out = output_dir / "ro-crate-metadata.json"
    out.write_text(json.dumps(crate, indent=2), encoding="utf-8")
    return out

