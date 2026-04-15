"""Tests for Nextflow plugin observer hooks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from helios.integrations import nextflow_plugin


@dataclass
class _Session:
    workDir: str
    outputDir: str
    params: dict[str, str]


def test_plugin_hooks_generate_audit(tmp_path: Path, monkeypatch) -> None:
    work_dir = tmp_path / "work"
    out_dir = tmp_path / "out"
    work_dir.mkdir()
    out_dir.mkdir()
    (work_dir / "trace.txt").write_text(
        "task_id\thash\tnative_id\tname\tstatus\texit\tsubmit\tduration\trealtime\t%cpu\tpeak_rss\tpeak_vmem\trchar\twchar\tworkdir\tscript\tcontainer\n",
        encoding="utf-8",
    )
    (work_dir / "nextflow.config").write_text(
        "manifest { name = 'demo' ; version = '1' }",
        encoding="utf-8",
    )

    saved: list[object] = []

    class _Storage:
        def save_record(self, record: object) -> None:
            saved.append(record)

    monkeypatch.setattr(nextflow_plugin, "AuditStorage", _Storage)
    session = _Session(str(work_dir), str(out_dir), {"outdir": str(out_dir)})
    nextflow_plugin.onFlowCreate(session)
    nextflow_plugin.onFlowComplete(session)
    nextflow_plugin.onFlowError(session, RuntimeError("boom"))

    assert saved, "Expected plugin to persist records"
    assert any(getattr(record, "pipeline_name", "") == "demo" for record in saved)
