"""Snakemake parsing integration and compatibility helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from helios.core.audit_record import ContainerRecord
from helios.core.run_context import RunContext


@dataclass(slots=True)
class RuleRecord:
    """Normalized Snakemake rule execution metadata."""

    rule_name: str
    conda_env: str | None
    container: str | None
    input_files: list[Path]
    output_files: list[Path]
    start_time: datetime | None
    end_time: datetime | None


class SnakemakeRunParser:
    """Parser for Snakemake log/metadata artifacts."""

    def __init__(self, snakemake_dir: Path, output_dir: Path) -> None:
        self.snakemake_dir = snakemake_dir
        self.output_dir = output_dir
        self.metadata_dir = snakemake_dir / ".snakemake" / "metadata"

    def parse_metadata(self) -> list[RuleRecord]:
        """Parse per-rule metadata emitted by Snakemake."""
        if not self.metadata_dir.exists():
            return []
        records: list[RuleRecord] = []
        for meta in self.metadata_dir.rglob("*"):
            if not meta.is_file():
                continue
            payload = self._load_metadata_file(meta)
            if payload is None:
                continue
            raw_input = payload.get("input", [])
            raw_output = payload.get("output", [])
            input_values = raw_input if isinstance(raw_input, list) else [str(raw_input)]
            output_values = raw_output if isinstance(raw_output, list) else [str(raw_output)]
            inputs = [Path(str(path)) for path in input_values]
            outputs = [Path(str(path)) for path in output_values]
            rule_name = str(payload.get("rule", meta.stem))
            conda_env_raw = payload.get("conda_env")
            container_raw = payload.get("container_img_url")
            records.append(
                RuleRecord(
                    rule_name=rule_name,
                    conda_env=str(conda_env_raw) if conda_env_raw is not None else None,
                    container=str(container_raw) if container_raw is not None else None,
                    input_files=inputs,
                    output_files=outputs,
                    start_time=_parse_optional_datetime(_as_optional_str(payload.get("starttime"))),
                    end_time=_parse_optional_datetime(_as_optional_str(payload.get("endtime"))),
                )
            )
        return records

    def get_containers(self) -> list[ContainerRecord]:
        """Return unique container references with pinning status."""
        found: dict[str, ContainerRecord] = {}
        for record in self.parse_metadata():
            container = record.container or ""
            if not container:
                continue
            name, tag, digest = _split_container(container)
            found[container] = ContainerRecord(
                name=name,
                tag=tag,
                digest=digest,
                pinned=bool(digest) and tag not in {"", "latest"},
            )
        return list(found.values())

    def build_run_context(self) -> RunContext:
        """Build RunContext from parsed Snakemake artifacts."""
        artifacts = [path for path in self.output_dir.rglob("*") if path.is_file()]
        rules = self.parse_metadata()
        log_count = len(list((self.snakemake_dir / ".snakemake" / "log").glob("*")))
        report_files = [
            path for path in self.snakemake_dir.glob("*.html") if "report" in path.name.lower()
        ]
        return RunContext(
            pipeline_name="snakemake-pipeline",
            executor="snakemake",
            work_dir=self.snakemake_dir,
            output_dir=self.output_dir,
            artifacts=artifacts,
            metadata={
                "rule_count": str(len(rules)),
                "log_files": str(log_count),
                "report_files": ",".join(str(path) for path in report_files),
            },
        )

    def _load_metadata_file(self, path: Path) -> dict[str, Any] | None:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            return None
        if path.suffix == ".json":
            try:
                payload = json.loads(text)
                if isinstance(payload, dict):
                    return payload
            except json.JSONDecodeError:
                return None
        parsed: dict[str, Any] = {}
        for line in text.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            parsed[key.strip()] = value.strip()
        return parsed or None


def build_context(work_dir: Path, output_dir: Path, pipeline_name: str) -> RunContext:
    """Create a run context from Snakemake output tree."""
    parser = SnakemakeRunParser(snakemake_dir=work_dir, output_dir=output_dir)
    context = parser.build_run_context()
    return RunContext(
        pipeline_name=pipeline_name,
        executor=context.executor,
        work_dir=context.work_dir,
        output_dir=context.output_dir,
        parameters=context.parameters,
        artifacts=context.artifacts,
        metadata=context.metadata,
    )


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _as_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


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
