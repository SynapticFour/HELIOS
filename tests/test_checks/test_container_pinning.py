"""Tests for container pinning check."""

from __future__ import annotations

from pathlib import Path

from helios.checks.container_pinning import ContainerPinningCheck
from helios.core.run_context import RunContext


def test_container_pinning_fail_when_digest_missing(tmp_path: Path) -> None:
    workflow = tmp_path / "main.nf"
    workflow.write_text("process X { container = 'docker.io/tool:1.0' }", encoding="utf-8")
    check = ContainerPinningCheck()
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[],
    )
    result = check.run(context)
    assert result.status == "fail"


def test_container_pinning_fail_when_none_found(tmp_path: Path) -> None:
    check = ContainerPinningCheck()
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[],
    )
    result = check.run(context)
    assert result.status == "fail"
    assert result.evidence["containers_scanned"] == "0"


def test_container_pinning_native_nextflow_space_syntax(tmp_path: Path) -> None:
    workflow = tmp_path / "main.nf"
    workflow.write_text("process X { container 'docker.io/tool:latest' }", encoding="utf-8")
    check = ContainerPinningCheck()
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[],
    )
    result = check.run(context)
    assert result.status == "fail"
    assert "latest" in result.message
    workflow = tmp_path / "nextflow.config"
    workflow.write_text("container = 'docker.io/tool:latest'", encoding="utf-8")
    check = ContainerPinningCheck()
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[],
    )
    result = check.run(context)
    assert result.status == "fail"
