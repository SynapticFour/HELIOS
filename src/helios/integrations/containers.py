"""Shared container reference parsing for workflow integrations."""

from __future__ import annotations


def split_container(ref: str) -> tuple[str, str, str | None]:
    """Split an image reference into name, tag, and optional digest."""
    digest = None
    remainder = ref
    if "@sha256:" in remainder:
        remainder, digest = remainder.split("@sha256:", 1)
        digest = f"sha256:{digest}"
    if ":" in remainder:
        name, tag = remainder.rsplit(":", 1)
    else:
        name, tag = remainder, ""
    return name, tag, digest
