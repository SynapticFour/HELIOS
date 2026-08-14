"""API-key authentication for the HELIOS dashboard."""

from __future__ import annotations

import secrets
from base64 import b64decode
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def extract_api_key(request: Request) -> str | None:
    """Extract an API key from X-API-Key, Bearer, or HTTP Basic password."""
    header_key = request.headers.get("x-api-key")
    if header_key:
        return header_key

    auth = request.headers.get("authorization")
    if auth:
        scheme, _, value = auth.partition(" ")
        scheme_lower = scheme.lower()
        if scheme_lower == "bearer" and value:
            return value.strip()
        if scheme_lower == "basic" and value:
            try:
                decoded = b64decode(value).decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                return None
            _username, sep, password = decoded.partition(":")
            if sep:
                return password
    return None


def _is_public_path(path: str) -> bool:
    """Paths that remain reachable without an API key (UI shell + health)."""
    return path in {"/health", "/"} or path.startswith("/static/")


class DashboardAuthMiddleware(BaseHTTPMiddleware):
    """Reject requests that do not present a matching dashboard API key."""

    def __init__(self, app: Any, api_key: str | None) -> None:
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _is_public_path(request.url.path):
            return await call_next(request)

        expected = self._api_key
        if not expected:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": (
                        "Dashboard API key not configured. "
                        "Set HELIOS_DASHBOARD_API_KEY before starting the dashboard."
                    )
                },
            )

        provided = extract_api_key(request)
        if provided is None or len(provided) != len(expected):
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized. Provide a valid API key."},
                headers={"WWW-Authenticate": 'Bearer realm="HELIOS Dashboard"'},
            )
        if not secrets.compare_digest(provided, expected):
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized. Provide a valid API key."},
                headers={"WWW-Authenticate": 'Bearer realm="HELIOS Dashboard"'},
            )
        return await call_next(request)
