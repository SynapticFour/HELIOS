"""Tests for Nextflow integration parsing."""

from __future__ import annotations

from pathlib import Path

from helios.integrations.nextflow import NextflowRunParser


def test_parse_nextflow_trace(nextflow_trace_path: Path) -> None:
    parser = NextflowRunParser(
        work_dir=nextflow_trace_path.parent,
        output_dir=nextflow_trace_path.parent,
    )
    rows = parser.parse_trace()
    assert len(rows) == 2
    assert rows[0].process_name == "ALIGN"
    assert rows[0].duration_ms > 0


def test_extract_containers(nextflow_trace_path: Path) -> None:
    parser = NextflowRunParser(
        work_dir=nextflow_trace_path.parent,
        output_dir=nextflow_trace_path.parent,
    )
    containers = parser.get_containers()
    assert len(containers) == 2
    assert any(item.pinned for item in containers)


def test_missing_trace_file_is_graceful(tmp_path: Path) -> None:
    parser = NextflowRunParser(work_dir=tmp_path, output_dir=tmp_path)
    assert parser.parse_trace() == []
    assert parser.warnings
