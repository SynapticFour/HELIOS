"""Nextflow integration for trace parsing and run context discovery."""

from __future__ import annotations

import csv
from pathlib import Path

from helios.core.audit_record import ContainerRecord
from helios.core.run_context import RunContext


def parse_trace(trace_file: Path) -> list[dict[str, str]]:
    """Parse a Nextflow trace TSV file into rows."""
    with trace_file.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [dict(row) for row in reader]


def extract_containers(rows: list[dict[str, str]]) -> list[ContainerRecord]:
    """Extract container records from Nextflow trace rows."""
    records: dict[str, ContainerRecord] = {}
    for row in rows:
        container = row.get("container", "").strip()
        if not container:
            continue
        name, tag, digest = _split_container(container)
        records[container] = ContainerRecord(
            name=name,
            tag=tag,
            digest=digest,
            pinned=bool(digest) and tag not in {"latest", ""},
        )
    return list(records.values())


def build_context(work_dir: Path, output_dir: Path, pipeline_name: str) -> RunContext:
    """Build a run context from conventional Nextflow outputs."""
    artifacts = [path for path in output_dir.rglob("*") if path.is_file()]
    return RunContext(
        pipeline_name=pipeline_name,
        executor="nextflow",
        work_dir=work_dir,
        output_dir=output_dir,
        artifacts=artifacts,
    )


def _split_container(ref: str) -> tuple[str, str, str | None]:
    digest = None
    if "@sha256:" in ref:
        ref, digest = ref.split("@sha256:", 1)
        digest = f"sha256:{digest}"
    if ":" in ref:
        name, tag = ref.rsplit(":", 1)
    else:
        name, tag = ref, ""
    return name, tag, digest

