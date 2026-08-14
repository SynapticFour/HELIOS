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
        if "/" in tag:
            name, tag = remainder, ""
    else:
        name, tag = remainder, ""
    return name, tag, digest


def format_container_ref(name: str, tag: str, digest: str | None) -> str:
    """Rebuild a container reference string from parsed parts."""
    if digest and tag:
        return f"{name}:{tag}@{digest}"
    if digest:
        return f"{name}@{digest}"
    if tag:
        return f"{name}:{tag}"
    return name
