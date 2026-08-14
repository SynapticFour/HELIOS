"""Shared VCF artifact discovery and streaming INFO-column reads."""

from __future__ import annotations

import gzip
from collections.abc import Iterator
from pathlib import Path
from typing import TextIO

from helios.core.run_context import RunContext


def is_vcf_path(path: Path) -> bool:
    """Return True for uncompressed or bgzipped VCF filenames."""
    name = path.name.lower()
    return name.endswith(".vcf") or name.endswith(".vcf.gz") or name.endswith(".vcf.bgz")


def vcf_artifacts(context: RunContext) -> list[Path]:
    """Return VCF artifacts from the run context (includes .vcf.gz)."""
    return [path for path in context.artifacts if is_vcf_path(path)]


def iter_info_fields(path: Path) -> Iterator[str]:
    """Yield INFO column strings, streaming gzip/bgzip or plain text.

    pysam is used for BAM/CRAM headers elsewhere. Annotation checks need
    undeclared INFO tags (ANN/CSQ/CLNSIG) that VariantFile drops without a
    matching header, so this path streams the INFO column directly.
    """
    name = path.name.lower()
    if name.endswith(".gz") or name.endswith(".bgz"):
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            yield from _info_lines(handle)
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        yield from _info_lines(handle)


def _info_lines(handle: TextIO) -> Iterator[str]:
    for line in handle:
        if not line or line.startswith("#"):
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 8:
            yield parts[7]
