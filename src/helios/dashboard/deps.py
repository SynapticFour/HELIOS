"""Shared FastAPI dependencies for dashboard routes."""

from __future__ import annotations

from typing import cast

from fastapi import Request

from helios.config import HeliosSettings
from helios.core.storage import AuditStorage


def get_storage(request: Request) -> AuditStorage:
    return cast(AuditStorage, request.app.state.storage)


def get_settings(request: Request) -> HeliosSettings:
    return cast(HeliosSettings, request.app.state.settings)
