"""FastAPI application factory for HELIOS dashboard."""

from __future__ import annotations

from fastapi import FastAPI

from helios.dashboard.routes.reports import router as reports_router
from helios.dashboard.routes.runs import router as runs_router


def create_app() -> FastAPI:
    """Create configured FastAPI app."""
    app = FastAPI(title="HELIOS Dashboard", version="0.1.0")
    app.include_router(runs_router)
    app.include_router(reports_router)
    return app

