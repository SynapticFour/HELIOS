"""Integration tests for dashboard API endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from helios.config import HeliosSettings
from helios.core.audit_record import AuditRecord
from helios.dashboard.app import create_app


def test_dashboard_api_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "dashboard.db"
    settings = HeliosSettings(
        audit_db=db_path,
        signing_key=tmp_path / "none.key",
    )
    app = create_app(settings=settings)
    with TestClient(app) as client:
        record = AuditRecord(pipeline_name="api-test", executor="nextflow")
        upload = tmp_path / "record.json"
        upload.write_text(record.to_json(), encoding="utf-8")

        with upload.open("rb") as handle:
            response = client.post(
                "/api/runs/import",
                files={"file": ("record.json", handle, "application/json")},
            )
        assert response.status_code == 200

        listed = client.get("/api/runs")
        assert listed.status_code == 200
        runs = listed.json()
        assert any(run["run_id"] == str(record.run_id) for run in runs)

        fetched = client.get(f"/api/runs/{record.run_id}")
        assert fetched.status_code == 200
        assert fetched.json()["run_id"] == str(record.run_id)

        overview = client.get("/api/stats/overview")
        assert overview.status_code == 200
        assert "total_runs" in overview.json()

        report = client.get(f"/api/reports/{record.run_id}/json")
        assert report.status_code == 200
        assert "attachment" in report.headers.get("content-disposition", "")

