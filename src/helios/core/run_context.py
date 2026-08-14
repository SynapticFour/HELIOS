"""Run context container used by checks and integrations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


@dataclass(slots=True)
class RunContext:
    """Execution context captured for a pipeline run."""

    pipeline_name: str
    executor: Literal["nextflow", "snakemake", "unknown"]
    work_dir: Path
    output_dir: Path
    parameters: dict[str, Any] = field(default_factory=dict)  # Any for arbitrary CLI/config values.
    artifacts: list[Path] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    # Pipeline source directory (nextflow.config / Snakefile), not task scratch.
    project_dir: Path | None = None
    # Container references already parsed from trace/metadata (may be empty).
    container_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.project_dir is None:
            object.__setattr__(self, "project_dir", self.work_dir)
