"""Nextflow observer bridge for HELIOS auditing.

Python lifecycle hooks (`onFlowCreate`, `onFlowComplete`, `onFlowError`) that a
custom process can call after a Nextflow run. This is not a Nextflow Groovy
plugin: `plugins { id 'nf-helios' }` will not load this module. Wire it from
your own observer, or use `helios run --pipeline nextflow`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from helios.checks import CheckRegistry
from helios.config import load_config
from helios.core.audit_record import AuditRecord
from helios.core.persist import hash_files, persist_record
from helios.integrations.nextflow import NextflowRunParser


@dataclass(slots=True)
class _PluginState:
    """In-memory lifecycle state for a single plugin session."""

    start_time: datetime | None = None
    # Any mirrors Nextflow runtime parameter value types.
    parameters: dict[str, Any] = field(default_factory=dict)
    failed: bool = False
    error_message: str | None = None


_SESSIONS: dict[str, _PluginState] = {}


def _session_key(session: Any) -> str:
    return str(getattr(session, "workDir", "default"))


def _state_for(session: Any) -> _PluginState:
    key = _session_key(session)
    return _SESSIONS.setdefault(key, _PluginState())


def _drop_session(session: Any) -> None:
    _SESSIONS.pop(_session_key(session), None)


def onFlowCreate(session: Any) -> None:
    """Record run start and capture Nextflow session parameters."""
    state = _state_for(session)
    state.start_time = datetime.now(UTC)
    params = getattr(session, "params", {}) or {}
    if isinstance(params, dict):
        state.parameters = params
    else:
        state.parameters = {"raw_params": str(params)}


def onFlowComplete(session: Any) -> None:
    """Generate audit record after successful Nextflow execution."""
    try:
        _generate_audit(session=session)
    finally:
        _drop_session(session)


def onFlowError(session: Any, error: Exception) -> None:
    """Do not sign an audit for a failed Nextflow execution."""
    state = _state_for(session)
    state.failed = True
    state.error_message = str(error)
    _drop_session(session)


def _generate_audit(session: Any) -> None:
    state = _state_for(session)
    work_dir = Path(str(getattr(session, "workDir", ".")))
    output_dir = Path(str(getattr(session, "outputDir", ".")))
    parser = NextflowRunParser(work_dir=work_dir, output_dir=output_dir)
    context = parser.build_run_context()
    context.parameters.update(state.parameters)

    settings = load_config()
    registry = CheckRegistry()
    enabled = registry.resolve_enabled(settings.checks.enabled)
    results = registry.run_all(context, enabled=enabled, settings=settings)
    config = parser.parse_config()
    output_hashes = hash_files(context.artifacts)
    input_hashes = hash_files(
        [
            parser.trace_file,
            parser.config_file,
            parser.log_file,
            *[Path(str(value)) for value in context.parameters.values() if isinstance(value, str)],
        ]
    )
    record = AuditRecord(
        pipeline_name=config.name,
        pipeline_version=config.version,
        executor="nextflow",
        start_time=state.start_time or datetime.now(UTC),
        end_time=datetime.now(UTC),
        input_files=input_hashes,
        output_files=output_hashes,
        containers=parser.get_containers(),
        parameters=context.parameters,
        checks=results,
        work_dir=str(work_dir),
        output_dir=str(output_dir),
    )
    persist_record(record, settings, sign=True)
