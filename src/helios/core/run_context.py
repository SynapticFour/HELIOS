"""Run context container used by checks and integrations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


@dataclass(slots=True)
class RunContext:
    """Execution context captured for a pipeline run."""

    pipeline_name: str
    executor: Literal["nextflow", "snakemake", "cwl", "unknown"]
    work_dir: Path
    output_dir: Path
    parameters: dict[str, Any] = field(default_factory=dict)  # Any for arbitrary CLI/config values.
    artifacts: list[Path] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

