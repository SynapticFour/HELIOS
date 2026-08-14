"""RO-Crate 1.1 export for HELIOS audit artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from helios.checks import get_check_registry
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


STANDARD_IRIS: dict[str, str] = {
    "ISO15189:2022-5.3": "https://www.iso.org/standard/76677.html",
    "ISO15189:2022-5.6": "https://www.iso.org/standard/76677.html",
    "ISO15189:2022-7.3.2": "https://www.iso.org/standard/76677.html",
    "GA4GH-TRS-2.0": "https://www.ga4gh.org/product/tool-registry-service-trs/",
    "GA4GH-VRS-1.3": "https://www.ga4gh.org/product/variant-representation-specification-vrs/",
    "GA4GH-Crypt4GH-1.0": "https://www.ga4gh.org/product/crypt4gh/",
    "GA4GH-DRS-1.3": "https://www.ga4gh.org/product/data-repository-service-drs/",
    "GA4GH-GKS-1.0": "https://www.ga4gh.org/product/gks/",
    "ACMG-2015": "https://www.acmg.net/",
    "ACMG-2023-reporting": "https://www.acmg.net/",
    "ISO27001:A.8.15": "https://www.iso.org/standard/27001",
    "EHDS-access-evidence": "https://health.ec.europa.eu/ehealth-digital-health-and-care/european-health-data-space_en",
}


def record_check_standard_map(check_id: str, record: AuditRecord) -> list[str]:
    """Map check standards to canonical public identifiers (not invented URLs)."""
    registry = get_check_registry()
    check_class = registry.get_registered_checks().get(check_id)
    if check_class is not None:
        return [STANDARD_IRIS.get(standard, standard) for standard in check_class.standards]
    for check in record.checks:
        if check.check_id != check_id:
            continue
        mapping = []
        for standard in check.evidence.get("standards", []):
            mapping.append(STANDARD_IRIS.get(str(standard), str(standard)))
        return mapping or ["PropertyValue"]
    return ["PropertyValue"]
