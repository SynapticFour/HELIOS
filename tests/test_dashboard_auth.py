"""Tests for dashboard API-key authentication."""

from __future__ import annotations

from base64 import b64encode
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from helios.cli import app as cli_app
from helios.config import HeliosSettings
from helios.dashboard.app import create_app
from helios.dashboard.auth import extract_api_key

API_KEY = "test-dashboard-secret"


def _settings(tmp_path: Path, api_key: str | None = API_KEY) -> HeliosSettings:
    return HeliosSettings(
        audit_db=tmp_path / "auth.db",
        signing_key=tmp_path / "none.key",
        dashboard_api_key=api_key,
    )


def test_extract_api_key_sources() -> None:
    from starlette.requests import Request

    def make_request(headers: dict[str, str] | None = None, query: str = "") -> Request:
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/runs",
            "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
            "query_string": query.encode(),
            "client": ("127.0.0.1", 123),
            "server": ("test", 80),
            "scheme": "http",
            "root_path": "",
            "http_version": "1.1",
        }
        return Request(scope)

    assert extract_api_key(make_request({"x-api-key": "abc"})) == "abc"
    assert extract_api_key(make_request({"authorization": "Bearer tok"})) == "tok"
    basic = b64encode(b"user:basic-secret").decode()
    assert extract_api_key(make_request({"authorization": f"Basic {basic}"})) == "basic-secret"
    assert extract_api_key(make_request(query="api_key=from-query")) is None
    assert extract_api_key(make_request()) is None


def test_api_rejects_missing_and_wrong_key(tmp_path: Path) -> None:
    app = create_app(_settings(tmp_path))
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/static/index.html").status_code == 200

        denied = client.get("/api/v1/runs")
        assert denied.status_code == 401

        wrong = client.get("/api/v1/runs", headers={"X-API-Key": "nope"})
        assert wrong.status_code == 401

        ok = client.get("/api/v1/runs", headers={"X-API-Key": API_KEY})
        assert ok.status_code == 200

        bearer = client.get("/api/v1/runs", headers={"Authorization": f"Bearer {API_KEY}"})
        assert bearer.status_code == 200

        basic = b64encode(f"helios:{API_KEY}".encode()).decode()
        basic_ok = client.get("/api/v1/runs", headers={"Authorization": f"Basic {basic}"})
        assert basic_ok.status_code == 200

        query_rejected = client.get(f"/api/v1/runs?api_key={API_KEY}")
        assert query_rejected.status_code == 401


def test_api_unavailable_without_configured_key(tmp_path: Path) -> None:
    app = create_app(_settings(tmp_path, api_key=None))
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        missing = client.get("/api/v1/runs")
        assert missing.status_code == 503
        assert "HELIOS_DASHBOARD_API_KEY" in missing.json()["detail"]


def test_serve_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HELIOS_DASHBOARD_API_KEY", raising=False)
    monkeypatch.delenv("HELIOS_DASHBOARD__API_KEY", raising=False)
    runner = CliRunner()
    result = runner.invoke(cli_app, ["serve", "--no-open-browser"])
    assert result.exit_code == 1
    assert "HELIOS_DASHBOARD_API_KEY" in result.stdout


def test_settings_require_dashboard_api_key(tmp_path: Path) -> None:
    settings = _settings(tmp_path, api_key=None)
    with pytest.raises(ValueError, match="HELIOS_DASHBOARD_API_KEY"):
        settings.require_dashboard_api_key()
    assert _settings(tmp_path).require_dashboard_api_key() == API_KEY


def test_env_dashboard_api_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HELIOS_DASHBOARD_API_KEY", "from-env")
    settings = HeliosSettings(audit_db=tmp_path / "e.db", signing_key=tmp_path / "k.key")
    assert settings.dashboard_api_key == "from-env"
