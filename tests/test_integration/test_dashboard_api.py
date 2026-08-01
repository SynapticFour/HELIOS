"""Integration tests for dashboard API endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from helios.config import HeliosSettings
from helios.core.audit_record import AuditRecord
from helios.dashboard.app import create_app

_API_KEY = "integration-test-key"
_AUTH = {"X-API-Key": _API_KEY}


def test_dashboard_api_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "dashboard.db"
    settings = HeliosSettings(
        audit_db=db_path,
        signing_key=tmp_path / "none.key",
        dashboard_api_key=_API_KEY,
    )
    app = create_app(settings=settings)
    with TestClient(app) as client:
        record = AuditRecord(pipeline_name="api-test", executor="nextflow")
        upload = tmp_path / "record.json"
        upload.write_text(record.to_json(), encoding="utf-8")

        with upload.open("rb") as handle:
            response = client.post(
                "/api/v1/runs/import",
                headers=_AUTH,
                files={"file": ("record.json", handle, "application/json")},
            )
        assert response.status_code == 200

        listed = client.get("/api/v1/runs", headers=_AUTH)
        assert listed.status_code == 200
        runs = listed.json()
        assert any(run["run_id"] == str(record.run_id) for run in runs)

        fetched = client.get(f"/api/v1/runs/{record.run_id}", headers=_AUTH)
        assert fetched.status_code == 200
        assert fetched.json()["run_id"] == str(record.run_id)

        overview = client.get("/api/v1/stats/overview", headers=_AUTH)
        assert overview.status_code == 200
        assert "total_runs" in overview.json()

        trends = client.get("/api/v1/stats/trends", headers=_AUTH)
        assert trends.status_code == 200
        assert "pipelines" in trends.json()

        report = client.get(f"/api/v1/reports/{record.run_id}/json", headers=_AUTH)
        assert report.status_code == 200
        assert "attachment" in report.headers.get("content-disposition", "")

        pdf = client.get(f"/api/v1/reports/{record.run_id}/pdf", headers=_AUTH)
        assert pdf.status_code == 200
        assert pdf.content.startswith(b"%PDF")

        rocrate = client.get(f"/api/v1/reports/{record.run_id}/rocrate", headers=_AUTH)
        assert rocrate.status_code == 200
        assert rocrate.headers["content-type"] == "application/zip"

        ai_act = client.get(f"/api/v1/reports/{record.run_id}/ai-act", headers=_AUTH)
        assert ai_act.status_code == 200
        assert "ai_act_art11_fragment" in ai_act.json()
