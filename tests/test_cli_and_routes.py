"""Coverage-focused tests for CLI helpers and run routes."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from helios.cli import _run_streaming_command, app
from helios.config import HeliosSettings
from helios.core.audit_record import AuditRecord, CheckResult
from helios.dashboard.app import create_app


def test_cli_config_commands(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / "helios.toml"
    cfg.write_text(
        "[helios]\n"
        f"audit_db = \"{tmp_path / 'audit.db'}\"\n"
        f"signing_key = \"{tmp_path / 'signing.key'}\"\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    out = runner.invoke(app, ["config", "print", "--path", str(cfg)])
    assert out.exit_code == 0
    assert '"log_level"' in out.stdout

    ok = runner.invoke(app, ["config", "validate", "--path", str(cfg)])
    assert ok.exit_code == 0


def test_cli_streaming_command(monkeypatch, tmp_path: Path) -> None:
    class _Proc:
        def __init__(self) -> None:
            self.stdout = iter(["line-1\n", "line-2\n"])

        def wait(self) -> int:
            return 0

    monkeypatch.setattr("helios.cli.subprocess.Popen", lambda *a, **k: _Proc())
    assert _run_streaming_command(["echo", "x"], tmp_path) == 0


def test_cli_snakemake_wrap_paths(monkeypatch) -> None:
    runner = CliRunner()
    missing = runner.invoke(app, ["snakemake-wrap"])
    assert missing.exit_code != 0

    monkeypatch.setattr("helios.cli.run_wrapped_snakemake", lambda *a, **k: 0)
    ok = runner.invoke(app, ["snakemake-wrap", "--", "snakemake", "--cores", "1"])
    assert ok.exit_code == 0


def test_runs_routes_filters_and_delete(tmp_path: Path) -> None:
    settings = HeliosSettings(audit_db=tmp_path / "api.db", signing_key=tmp_path / "none.key")
    app_instance = create_app(settings=settings)
    with TestClient(app_instance) as client:
        good = AuditRecord(
            pipeline_name="nf",
            executor="nextflow",
            checks=[CheckResult(check_id="A", status="pass", message="ok", evidence={})],
        )
        bad = AuditRecord(
            pipeline_name="nf",
            executor="nextflow",
            checks=[CheckResult(check_id="B", status="fail", message="no", evidence={})],
        )
        for record in (good, bad):
            payload = record.to_json().encode("utf-8")
            resp = client.post(
                "/api/v1/runs/import",
                files={"file": ("record.json", payload, "application/json")},
            )
            assert resp.status_code == 200

        listed = client.get("/api/v1/runs", params={"status": "fail", "min_score": 0})
        assert listed.status_code == 200
        assert all(item["status"] == "fail" for item in listed.json())

        deleted = client.delete(f"/api/v1/runs/{good.run_id}")
        assert deleted.status_code == 200
        missing = client.delete(f"/api/v1/runs/{good.run_id}")
        assert missing.status_code == 404
