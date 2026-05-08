"""Tests for RO-Crate export structure."""

from __future__ import annotations

import json
from pathlib import Path

from helios.core.audit_record import AuditRecord, CheckResult, ContainerRecord, FileHash
from helios.export.rocrate import export_rocrate


def test_rocrate_contains_required_entities(tmp_path: Path) -> None:
    record = AuditRecord(
        pipeline_name="demo",
        pipeline_version="1.0.0",
        executor="nextflow",
        input_files=[FileHash(path="input.vcf", sha256="a" * 64, size_bytes=10)],
        output_files=[FileHash(path="out.vcf", sha256="b" * 64, size_bytes=20)],
        containers=[
            ContainerRecord(name="biocontainer", tag="1.0", digest="sha256:abc", pinned=True)
        ],
        checks=[CheckResult(check_id="CHK-1", status="pass", message="ok", evidence={})],
    )
    metadata_path = export_rocrate(record, tmp_path / "crate")
    assert metadata_path.exists()

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["@context"] == "https://w3id.org/ro/crate/1.1/context"
    graph = metadata["@graph"]
    ids = {entity["@id"] for entity in graph}
    assert "./" in ids
    assert "ro-crate-metadata.json" in ids
    assert "helios-audit.json" in ids
    assert any(entity.get("@type") == "CreateAction" for entity in graph)
    assert any(entity.get("@type") == "SoftwareApplication" for entity in graph)
    assert (tmp_path / "crate" / "helios-audit.json").exists()
