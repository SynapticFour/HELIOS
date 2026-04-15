"""Shared pytest fixtures for HELIOS tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def fixture_dir() -> Path:
    """Return path to static fixture source files."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture()
def bam_header_path(tmp_path: Path, fixture_dir: Path) -> Path:
    """Copy BAM header fixture into an isolated temp path."""
    target = tmp_path / "sample.bam.header"
    target.write_text(
        (fixture_dir / "sample.bam.header").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return target


@pytest.fixture()
def vcf_path(tmp_path: Path, fixture_dir: Path) -> Path:
    """Copy VCF fixture into an isolated temp path."""
    target = tmp_path / "sample.vcf"
    target.write_text((fixture_dir / "sample.vcf").read_text(encoding="utf-8"), encoding="utf-8")
    return target


@pytest.fixture()
def nextflow_trace_path(tmp_path: Path, fixture_dir: Path) -> Path:
    """Copy Nextflow trace fixture into an isolated temp path."""
    target = tmp_path / "trace.txt"
    target.write_text(
        (fixture_dir / "sample.nextflow.trace").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return target
