"""Nextflow integration for trace/config parsing and run context assembly."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from helios.core.audit_record import ContainerRecord
from helios.core.run_context import RunContext

TRACE_COLUMNS = [
    "task_id",
    "hash",
    "native_id",
    "name",
    "status",
    "exit",
    "submit",
    "duration",
    "realtime",
    "%cpu",
    "peak_rss",
    "peak_vmem",
    "rchar",
    "wchar",
    "workdir",
    "script",
    "container",
]


@dataclass(slots=True)
class ProcessRecord:
    """Normalized process execution record from Nextflow trace."""

    process_name: str
    container: str
    status: str
    duration_ms: int
    input_files: list[Path]
    output_files: list[Path]


@dataclass(slots=True)
class PipelineConfig:
    """Pipeline metadata extracted from nextflow.config and log."""

    name: str
    version: str
    manifest_author: str
    nextflow_version: str


class NextflowRunParser:
    """Parser for Nextflow run artifacts in work and output directories."""

    def __init__(self, work_dir: Path, output_dir: Path) -> None:
        self.work_dir = work_dir
        self.output_dir = output_dir
        self.trace_file = work_dir / "trace.txt"
        self.config_file = work_dir / "nextflow.config"
        self.log_file = work_dir / ".nextflow.log"
        self.warnings: list[str] = []

    def parse_trace(self) -> list[ProcessRecord]:
        """Parse trace TSV; return empty list if trace file is unavailable."""
        if not self.trace_file.exists():
            self.warnings.append(f"Trace file not found at {self.trace_file}")
            return []

        with self.trace_file.open("r", encoding="utf-8", newline="") as handle:
            sample = handle.read(4096)
            handle.seek(0)
            delimiter = "," if sample.count(",") > sample.count("\t") else "\t"
            reader = csv.DictReader(handle, delimiter=delimiter)
            if reader.fieldnames is None:
                self.warnings.append(f"Trace file {self.trace_file} has no header row")
                return []
            rows = [self._normalize_row(dict(row)) for row in reader]

        process_records: list[ProcessRecord] = []
        for row in rows:
            process_name = row.get("name", row.get("process", "unknown")).strip()
            workdir = Path(row.get("workdir", "")) if row.get("workdir") else self.work_dir
            input_files = [p for p in workdir.glob("*.command.*") if p.is_file()]
            output_files = [p for p in self.output_dir.rglob("*") if p.is_file()]
            process_records.append(
                ProcessRecord(
                    process_name=process_name,
                    container=row.get("container", "").strip().strip("\""),
                    status=row.get("status", "UNKNOWN").strip(),
                    duration_ms=self._parse_duration_ms(row.get("duration", "0")),
                    input_files=input_files,
                    output_files=output_files,
                )
            )
        return process_records

    def parse_config(self) -> PipelineConfig:
        """Parse pipeline identity metadata from nextflow.config and log file."""
        name = "unknown-pipeline"
        version = "unknown"
        author = "unknown"
        nextflow_version = "unknown"
        if self.config_file.exists():
            config_text = self.config_file.read_text(encoding="utf-8")
            manifest = self._extract_manifest_block(config_text)
            name = (
                manifest.get("name")
                or self._extract_config_value(config_text, "manifest.name")
                or name
            )
            version = (
                manifest.get("version")
                or self._extract_config_value(config_text, "manifest.version")
                or version
            )
            author = (
                manifest.get("author")
                or self._extract_config_value(config_text, "manifest.author")
                or author
            )
        if self.log_file.exists():
            log_text = self.log_file.read_text(encoding="utf-8")
            match = re.search(r"nextflow version\s+([^\s]+)", log_text, flags=re.IGNORECASE)
            if match:
                nextflow_version = match.group(1)
        return PipelineConfig(
            name=name,
            version=version,
            manifest_author=author,
            nextflow_version=nextflow_version,
        )

    def get_containers(self) -> list[ContainerRecord]:
        """Extract unique containers from trace records with pinning status."""
        records: dict[str, ContainerRecord] = {}
        for process in self.parse_trace():
            container = process.container
            if not container:
                continue
            name, tag, digest = _split_container(container)
            records[container] = ContainerRecord(
                name=name,
                tag=tag,
                digest=digest,
                pinned=bool(digest) and tag not in {"", "latest"},
            )
        return list(records.values())

    def build_run_context(self) -> RunContext:
        """Assemble full run context for the parsed Nextflow run."""
        parsed_config = self.parse_config()
        process_records = self.parse_trace()
        artifacts = [path for path in self.output_dir.rglob("*") if path.is_file()]
        return RunContext(
            pipeline_name=parsed_config.name,
            executor="nextflow",
            work_dir=self.work_dir,
            output_dir=self.output_dir,
            artifacts=artifacts,
            metadata={
                "pipeline_version": parsed_config.version,
                "manifest_author": parsed_config.manifest_author,
                "nextflow_version": parsed_config.nextflow_version,
                "process_count": str(len(process_records)),
                "parser_warnings": "; ".join(self.warnings) if self.warnings else "",
            },
        )

    def _normalize_row(self, row: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for column in TRACE_COLUMNS:
            normalized[column] = row.get(column, "").strip()
        if not normalized["name"] and row.get("process"):
            normalized["name"] = row["process"].strip()
        return normalized

    def _extract_config_value(self, content: str, key: str) -> str | None:
        escaped = re.escape(key)
        pattern = rf"{escaped}\s*=\s*['\"]?([^'\"\n]+)['\"]?"
        match = re.search(pattern, content)
        return match.group(1).strip() if match else None

    def _extract_manifest_block(self, content: str) -> dict[str, str]:
        block_match = re.search(r"manifest\s*\{(?P<body>.*?)\}", content, flags=re.DOTALL)
        if block_match is None:
            return {}
        body = block_match.group("body")
        result: dict[str, str] = {}
        for key in ("name", "version", "author"):
            match = re.search(rf"{key}\s*=\s*['\"]?([^'\"\n]+)['\"]?", body)
            if match:
                result[key] = match.group(1).strip()
        return result

    def _parse_duration_ms(self, value: str) -> int:
        stripped = value.strip()
        if not stripped:
            return 0
        if stripped.isdigit():
            return int(stripped)
        match = re.match(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", stripped)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = float(match.group(3) or 0.0)
        return int((hours * 3600 + minutes * 60 + seconds) * 1000)


def parse_trace(trace_file: Path) -> list[dict[str, str]]:
    """Compatibility parser returning raw row dictionaries."""
    parser = NextflowRunParser(trace_file.parent, trace_file.parent)
    parser.trace_file = trace_file
    return [row.__dict__ for row in parser.parse_trace()]


def extract_containers(rows: list[dict[str, str]]) -> list[ContainerRecord]:
    """Extract container records from trace-like row dictionaries."""
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
    """Build a run context from parsed Nextflow artifacts."""
    parser = NextflowRunParser(work_dir=work_dir, output_dir=output_dir)
    context = parser.build_run_context()
    return context if context.pipeline_name != "unknown-pipeline" else context.__class__(
        pipeline_name=pipeline_name,
        executor=context.executor,
        work_dir=context.work_dir,
        output_dir=context.output_dir,
        parameters=context.parameters,
        artifacts=context.artifacts,
        metadata=context.metadata,
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

