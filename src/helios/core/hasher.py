"""Streaming SHA-256 hashing utilities for large genomic files."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path


def sha256_file(
    path: Path,
    progress_callback: Callable[[int], None] | None = None,
    chunk_size: int = 8 * 1024 * 1024,
) -> str:
    """Hash file content in chunks and optionally report processed bytes."""
    digest = hashlib.sha256()
    bytes_processed = 0
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
            bytes_processed += len(chunk)
            if progress_callback is not None:
                progress_callback(bytes_processed)
    return digest.hexdigest()
