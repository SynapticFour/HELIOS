"""Tests for streaming file hasher."""

from __future__ import annotations

from pathlib import Path

from helios.core.hasher import sha256_file


def test_sha256_file_with_progress(tmp_path: Path) -> None:
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"A" * 1024 * 1024)
    progress_events: list[int] = []

    digest = sha256_file(sample, progress_callback=progress_events.append, chunk_size=1024)

    assert len(digest) == 64
    assert progress_events[-1] == sample.stat().st_size
