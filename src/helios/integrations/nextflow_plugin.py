"""Nextflow observer bridge for HELIOS auditing.

This module provides observer-like hooks that can be invoked by a Nextflow plugin
to notify HELIOS lifecycle events.

Example Nextflow wiring:

```groovy
plugins {
  id 'nf-helios'
}
helios {
  enabled = true
  outputDir = params.outdir
}
```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from helios.checks import CheckRegistry
from helios.core.audit_record import AuditRecord
from helios.core.storage import AuditStorage
from helios.integrations.nextflow import NextflowRunParser


@dataclass(slots=True)
class _PluginState:
    """In-memory lifecycle state for a single plugin process."""

    start_time: datetime | None = None
    # Any mirrors Nextflow runtime parameter value types.
    parameters: dict[str, Any] = field(default_factory=dict)
    failed: bool = False
    error_message: str | None = None


STATE = _PluginState()


def onFlowCreate(session: Any) -> None:
    """Record run start and capture Nextflow session parameters."""
    STATE.start_time = datetime.now(UTC)
    params = getattr(session, "params", {}) or {}
    if isinstance(params, dict):
        STATE.parameters = params
    else:
        STATE.parameters = {"raw_params": str(params)}


def onFlowComplete(session: Any) -> None:
    """Generate audit record after successful Nextflow execution."""
    _generate_audit(session=session, error=None)


def onFlowError(session: Any, error: Exception) -> None:
    """Generate partial audit record for failed Nextflow execution."""
    STATE.failed = True
    STATE.error_message = str(error)
    _generate_audit(session=session, error=error)


def _generate_audit(session: Any, error: Exception | None) -> None:
    work_dir = Path(str(getattr(session, "workDir", ".")))
    output_dir = Path(str(getattr(session, "outputDir", ".")))
    parser = NextflowRunParser(work_dir=work_dir, output_dir=output_dir)
    context = parser.build_run_context()
    context.parameters.update(STATE.parameters)
    if error is not None:
        context.metadata["nextflow_error"] = str(error)

    registry = CheckRegistry()
    results = registry.run_all(context)
    config = parser.parse_config()
    record = AuditRecord(
        pipeline_name=config.name,
        pipeline_version=config.version,
        executor="nextflow",
        start_time=STATE.start_time or datetime.now(UTC),
        end_time=datetime.now(UTC),
        containers=parser.get_containers(),
        parameters=context.parameters,
        checks=results,
    )
    storage = AuditStorage()
    storage.save_record(record)
