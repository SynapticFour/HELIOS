"""Tests for Nextflow integration parsing."""

from __future__ import annotations

from pathlib import Path

from helios.integrations.nextflow import extract_containers, parse_trace


def test_parse_nextflow_trace(nextflow_trace_path: Path) -> None:
    rows = parse_trace(nextflow_trace_path)
    assert len(rows) == 2
    assert rows[0]["process"] == "ALIGN"


def test_extract_containers(nextflow_trace_path: Path) -> None:
    rows = parse_trace(nextflow_trace_path)
    containers = extract_containers(rows)
    assert len(containers) == 2
    assert any(item.pinned for item in containers)

