"""FastAPI application factory for HELIOS dashboard."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from helios import __version__
from helios.config import HeliosSettings
from helios.core.storage import AuditStorage
from helios.dashboard.routes.reports import router as reports_router
from helios.dashboard.routes.runs import router as runs_router
from helios.dashboard.routes.stats import router as stats_router


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: HeliosSettings = app.state.settings
    app.state.storage = AuditStorage(f"sqlite:///{settings.audit_db}")
    yield


def create_app(settings: HeliosSettings | None = None) -> FastAPI:
    """Create the HELIOS dashboard FastAPI application."""
    resolved = settings or HeliosSettings()
    app = FastAPI(
        title="HELIOS Dashboard API",
        version=__version__,
        lifespan=_lifespan,
    )
    app.state.settings = resolved
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.dashboard.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(FileNotFoundError)
    async def not_found_error_handler(_: Request, exc: FileNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.include_router(runs_router)
    app.include_router(reports_router)
    app.include_router(stats_router)

    @app.get("/")
    async def dashboard_index() -> JSONResponse:
        return JSONResponse({"message": "HELIOS dashboard served at /static/index.html"})

    return app

