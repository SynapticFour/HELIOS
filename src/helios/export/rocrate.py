"""RO-Crate 1.1 export for HELIOS audit artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from helios.checks import CheckRegistry
from helios.core.audit_record import AuditRecord


def export_rocrate(record: AuditRecord, output_dir: Path) -> Path:
    """Export an AuditRecord as an RO-Crate 1.1 package.

    Creates:
        output_dir/
        ├── ro-crate-metadata.json
        └── helios-audit.json

    Returns:
        Path to ro-crate-metadata.json.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = output_dir / "helios-audit.json"
    audit_path.write_text(record.to_json(), encoding="utf-8")

    check_entities = [
        {
            "@id": f"#check-{idx}",
            "@type": "PropertyValue",
            "name": check.check_id,
            "description": check.message,
            "value": check.status,
            "propertyID": ",".join(record_check_standard_map(check.check_id, record)),
        }
        for idx, check in enumerate(record.checks)
    ]
    input_entities = [
        {
            "@id": file.path,
            "@type": "File",
            "name": Path(file.path).name,
            "contentSize": str(file.size_bytes),
            "sha256": file.sha256,
        }
        for file in record.input_files
    ]
    output_entities = [
        {
            "@id": file.path,
            "@type": "File",
            "name": Path(file.path).name,
            "contentSize": str(file.size_bytes),
            "sha256": file.sha256,
        }
        for file in record.output_files
    ]
    software_entities = [
        {
            "@id": f"#container-{idx}",
            "@type": "SoftwareApplication",
            "name": container.name,
            "softwareVersion": container.tag,
            "identifier": container.digest or "",
            "additionalProperty": {
                "@type": "PropertyValue",
                "name": "pinned",
                "value": container.pinned,
            },
        }
        for idx, container in enumerate(record.containers)
    ]
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
                "hasPart": [{"@id": "helios-audit.json"}],
            },
            {
                "@id": "helios-audit.json",
                "@type": "File",
                "name": "HELIOS AuditRecord JSON",
                "encodingFormat": "application/json",
            },
            {
                "@id": f"#run-{record.run_id}",
                "@type": "CreateAction",
                "name": "Pipeline Run",
                "object": [{"@id": entity["@id"]} for entity in input_entities],
                "result": [{"@id": entity["@id"]} for entity in output_entities],
                "instrument": [{"@id": entity["@id"]} for entity in software_entities],
                "endTime": record.end_time.isoformat() if record.end_time else None,
                "startTime": record.start_time.isoformat(),
            },
            *software_entities,
            *input_entities,
            *output_entities,
            *check_entities,
        ],
    }
    out = output_dir / "ro-crate-metadata.json"
    out.write_text(json.dumps(crate, indent=2), encoding="utf-8")
    return out


def record_check_standard_map(check_id: str, record: AuditRecord) -> list[str]:
    """Map check standards to schema.org/bioschemas style identifiers."""
    registry = CheckRegistry()
    check_class = registry.get_registered_checks().get(check_id)
    if check_class is not None:
        mapped: list[str] = []
        for standard in check_class.standards:
            normalized = standard.lower()
            if "ga4gh" in normalized:
                mapped.append(f"https://schema.org/{standard}")
            elif "iso15189" in normalized or "iso 15189" in normalized:
                mapped.append(f"https://bioschemas.org/{standard}")
            elif "acmg" in normalized:
                mapped.append(f"https://schema.org/{standard}")
        if mapped:
            return mapped
    for check in record.checks:
        if check.check_id != check_id:
            continue
        mapping = []
        for standard in check.evidence.get("standards", []):
            mapping.append(f"https://bioschemas.org/{standard}")
        return mapping or ["https://schema.org/PropertyValue"]
    return ["https://schema.org/PropertyValue"]

