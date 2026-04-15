"""End-to-end pipeline audit integration test."""

from __future__ import annotations

import json
import os
from pathlib import Path

from typer.testing import CliRunner

from helios.checks import CheckRegistry
from helios.cli import app
from helios.core.signer import generate_keypair, verify_record
from helios.core.storage import AuditStorage


def test_full_pipeline_audit(tmp_path: Path, monkeypatch) -> None:
    work_dir = tmp_path / "work"
    out_dir = tmp_path / "results"
    work_dir.mkdir()
    out_dir.mkdir()

    (out_dir / "sample.bam.header").write_text(
        "@SQ\tSN:chr1\tLN:248956422\tM5:6aef897c3d6ff0c78aff06ac189178dd\n",
        encoding="utf-8",
    )
    (out_dir / "sample.vcf").write_text(
        (
            "##fileformat=VCFv4.2\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            "1\t100\t.\tA\tG\t100\tPASS\tCSQ=A|missense|GENE1|NM_000001.2;CLNSIG=Pathogenic\n"
        ),
        encoding="utf-8",
    )
    (work_dir / "trace.txt").write_text(
        (
            "task_id\thash\tnative_id\tname\tstatus\texit\tsubmit\tduration\trealtime\t%cpu\tpeak_rss\tpeak_vmem\trchar\twchar\tworkdir\tscript\tcontainer\n"
            "1\tab/12\t1001\tALIGN\tCOMPLETED\t0\t2026-01-01T10:00:00Z\t40s\t41s\t90\t1G\t1.5G\t1\t1\t/work\t.run\tdocker.io/tool:1.0@sha256:abc\n"
        ),
        encoding="utf-8",
    )
    (work_dir / "nextflow.config").write_text(
        "manifest { name = 'synthetic' ; version = '0.0.1' ; author = 'test' }\n",
        encoding="utf-8",
    )

    signing_key, _public_key = generate_keypair(base_dir=tmp_path, name="helios")
    db_path = tmp_path / "helios.db"
    reports_dir = tmp_path / "reports"
    config_path = tmp_path / "helios.toml"
    config_path.write_text(
        (
            "[helios]\n"
            f"signing_key = \"{signing_key}\"\n"
            f"audit_db = \"{db_path}\"\n"
            "\n[helios.checks]\n"
            "enabled = [\"reference_genome\", \"container_pinning\", \"vus_rate\"]\n"
            "\n[helios.export]\n"
            f"output_dir = \"{reports_dir}\"\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    run_result = runner.invoke(
        app,
        [
            "run",
            "--pipeline",
            "nextflow",
            "--work-dir",
            str(work_dir),
            "--output-dir",
            str(out_dir),
            "--config",
            str(config_path),
            "--export",
            "json",
        ],
    )
    assert run_result.exit_code == 0, run_result.stdout

    storage = AuditStorage(f"sqlite:///{db_path}")
    records = storage.list_records(limit=1)
    assert records, "Expected at least one stored audit record"
    record = records[-1]
    score = CheckRegistry().compute_score(record.checks)
    assert score.score > 60
    os.environ["HELIOS_KEY_DIR"] = str(tmp_path)
    assert verify_record(record) is True

    validate_result = runner.invoke(app, ["validate", str(record.run_id)])
    assert validate_result.exit_code == 0

    json_report = reports_dir / f"{record.run_id}.json"
    assert json_report.exists()
    payload = json.loads(json_report.read_text(encoding="utf-8"))
    assert payload["run_id"] == str(record.run_id)
    assert "checks" in payload and payload["checks"]

