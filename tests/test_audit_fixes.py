"""Regression tests for the staff Python audit fixes."""

from __future__ import annotations

import gzip
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from helios.checks import CheckRegistry
from helios.checks.mane_transcripts import MANETranscriptCheck
from helios.cli import app
from helios.config import HeliosSettings, load_config
from helios.core.audit_record import AuditRecord, CheckResult
from helios.core.run_context import RunContext
from helios.core.storage import AuditStorage
from helios.dashboard.app import create_app


def test_mane_transcripts_alias_resolves() -> None:
    registry = CheckRegistry()
    resolved = registry.resolve_enabled(["mane_transcripts", "reference_genome"])
    assert "GA4GH-MANE-001" in resolved
    assert "GA4GH-REF-001" in resolved
    with pytest.raises(ValueError, match="Unknown check"):
        registry.resolve_enabled(["not_a_real_check"])


def test_skip_only_suite_is_not_a_perfect_score() -> None:
    registry = CheckRegistry()
    skipped = [
        CheckResult(check_id="GA4GH-CRYPT-001", status="skip", message="n/a"),
        CheckResult(check_id="SEC-CONTAINER-001", status="skip", message="n/a"),
    ]
    score = registry.compute_score(skipped)
    assert score.scored is False
    assert score.score is None
    assert score.grade == "N/A"


def test_skip_does_not_inflate_score() -> None:
    registry = CheckRegistry()
    skipped = [
        CheckResult(check_id="GA4GH-CRYPT-001", status="skip", message="n/a"),
        CheckResult(check_id="SEC-CONTAINER-001", status="fail", message="latest"),
    ]
    score = registry.compute_score(skipped)
    assert score.failed == 1
    assert score.score < 50


def test_list_records_newest_first(tmp_path: Path) -> None:
    storage = AuditStorage(f"sqlite:///{tmp_path / 'order.db'}")
    older = AuditRecord(
        pipeline_name="a",
        executor="nextflow",
        start_time=datetime.now(UTC) - timedelta(hours=2),
    )
    newer = AuditRecord(
        pipeline_name="b",
        executor="nextflow",
        start_time=datetime.now(UTC),
    )
    storage.save_record(older)
    storage.save_record(newer)
    listed = storage.list_records(limit=1)
    assert listed[0].run_id == newer.run_id


def test_load_config_missing_path_errors(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "missing.toml"))


def test_init_uses_packaged_example(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["init"])
    assert result.exit_code == 0, result.stdout
    written = (tmp_path / "helios.toml").read_text(encoding="utf-8")
    assert "[helios.checks]" in written
    assert "pipeline_executor" not in written


def test_run_aborts_on_failed_wrap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("helios.cli._run_streaming_command", lambda *_a, **_k: 7)
    cfg = tmp_path / "helios.toml"
    cfg.write_text(
        (
            "[helios]\n"
            f'audit_db = "{tmp_path / "audit.db"}"\n'
            f'signing_key = "{tmp_path / "none.key"}"\n'
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        app,
        ["run", "--pipeline", "nextflow", "--config", str(cfg), "--", "false"],
    )
    assert result.exit_code == 7


def test_mane_reads_gzipped_vcf(tmp_path: Path) -> None:
    vcf = tmp_path / "annotated.vcf.gz"
    content = (
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
        "1\t100\t.\tA\tG\t100\tPASS\tCSQ=A|missense|GENE1|NM_000001.2\n"
    )
    with gzip.open(vcf, "wt", encoding="utf-8") as handle:
        handle.write(content)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    summary = cache_dir / "MANE.GRCh38.v1.4.summary.txt.gz"
    with gzip.open(summary, "wt", encoding="utf-8") as handle:
        handle.write(
            "symbol\tentrez\tensembl_gene\trefseq_nuc\tensembl_nuc\tMANE_status\n"
            "GENE1\t1\tENSG000001\tNM_000001.2\tENST000003\tMANE Select\n"
        )
    check = MANETranscriptCheck(cache_dir=cache_dir)
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[vcf],
    )
    result = check.run(context)
    assert result.status == "pass"
    assert result.evidence["total_variants"] == 1


def test_delete_forbidden_by_default(tmp_path: Path) -> None:
    api_key = "deny-delete"
    settings = HeliosSettings(
        audit_db=tmp_path / "api.db",
        signing_key=tmp_path / "none.key",
        dashboard_api_key=api_key,
    )
    app_instance = create_app(settings=settings)
    record = AuditRecord(pipeline_name="nf", executor="nextflow")
    with TestClient(app_instance) as client:
        imported = client.post(
            "/api/v1/runs/import",
            headers={"X-API-Key": api_key},
            params={"allow_unsigned": "true"},
            files={"file": ("record.json", record.to_json().encode(), "application/json")},
        )
        assert imported.status_code == 200
        denied = client.delete(f"/api/v1/runs/{record.run_id}", headers={"X-API-Key": api_key})
        assert denied.status_code == 403


def test_unsigned_import_requires_opt_in(tmp_path: Path) -> None:
    api_key = "import-key"
    settings = HeliosSettings(
        audit_db=tmp_path / "api.db",
        signing_key=tmp_path / "none.key",
        dashboard_api_key=api_key,
    )
    record = AuditRecord(pipeline_name="nf", executor="nextflow")
    payload = record.to_json().encode()
    with TestClient(create_app(settings=settings)) as client:
        denied = client.post(
            "/api/v1/runs/import",
            headers={"X-API-Key": api_key},
            files={"file": ("record.json", payload, "application/json")},
        )
        assert denied.status_code == 400
        assert "allow_unsigned" in denied.json()["detail"]

        allowed = client.post(
            "/api/v1/runs/import",
            headers={"X-API-Key": api_key},
            params={"allow_unsigned": "true"},
            files={"file": ("record.json", payload, "application/json")},
        )
        assert allowed.status_code == 200


def test_invalid_signature_import_rejected(tmp_path: Path) -> None:
    from helios.core.signer import generate_keypair, sign_record

    api_key = "import-key"
    private_path, _public_path = generate_keypair(
        base_dir=tmp_path, name="test", allow_unencrypted=True
    )
    settings = HeliosSettings(
        audit_db=tmp_path / "api.db",
        signing_key=tmp_path / "none.key",
        trusted_keys_dir=tmp_path,
        dashboard_api_key=api_key,
    )
    signed = sign_record(AuditRecord(pipeline_name="nf", executor="nextflow"), private_path)
    tampered = signed.model_copy(update={"pipeline_name": "tampered"})
    with TestClient(create_app(settings=settings)) as client:
        denied = client.post(
            "/api/v1/runs/import",
            headers={"X-API-Key": api_key},
            params={"allow_unsigned": "true"},
            files={"file": ("record.json", tampered.to_json().encode(), "application/json")},
        )
        assert denied.status_code == 400
        assert "signature" in denied.json()["detail"].lower()


def test_persist_requires_signing_key(tmp_path: Path) -> None:
    from helios.core.persist import SigningRequiredError, persist_record

    settings = HeliosSettings(
        audit_db=tmp_path / "audit.db",
        signing_key=tmp_path / "missing.key",
    )
    record = AuditRecord(pipeline_name="nf", executor="nextflow")
    with pytest.raises(SigningRequiredError):
        persist_record(record, settings, sign=True)
    stored = persist_record(record, settings, sign=False)
    assert stored.signature is None
    from helios.core.persist import persist_record

    settings = HeliosSettings(
        audit_db=tmp_path / "audit.db",
        signing_key=tmp_path / "none.key",
    )
    record = AuditRecord(
        pipeline_name="nf",
        executor="nextflow",
        checks=[
            CheckResult(
                check_id="GA4GH-REF-001",
                status="pass",
                message="ok",
                evidence={
                    "assembly": "GRCh38",
                    "header_source_match": "https://example.test/ref",
                    "measured_md5_chr1": "abc123",
                },
            )
        ],
    )
    stored = persist_record(record, settings, sign=False)
    assert stored.reference_genome is not None
    assert stored.reference_genome.assembly == "GRCh38"
    assert stored.reference_genome.source_url == "https://example.test/ref"
    assert stored.reference_genome.sha256 == ""
    assert stored.reference_genome.contig_md5["chr1"] == "abc123"


def test_legacy_db_run_id_unique_migration(tmp_path: Path) -> None:
    import sqlite3
    from uuid import uuid4

    db_path = tmp_path / "legacy.db"
    run_id = uuid4()
    older = AuditRecord(
        run_id=run_id,
        pipeline_name="old",
        executor="nextflow",
        start_time=datetime.now(UTC) - timedelta(hours=2),
    )
    newer = AuditRecord(
        run_id=run_id,
        pipeline_name="new",
        executor="nextflow",
        start_time=datetime.now(UTC),
    )
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE auditrecordrow ("
            "id CHAR(32) NOT NULL PRIMARY KEY, "
            "run_id CHAR(32) NOT NULL, "
            "start_time DATETIME NOT NULL, "
            "pipeline_name VARCHAR NOT NULL, "
            "record_json TEXT NOT NULL)"
        )
        conn.execute("CREATE INDEX ix_auditrecordrow_run_id ON auditrecordrow (run_id)")
        conn.execute(
            "INSERT INTO auditrecordrow "
            "(id, run_id, start_time, pipeline_name, record_json) VALUES (?,?,?,?,?)",
            (uuid4().hex, run_id.hex, older.start_time.isoformat(), "old", older.to_json()),
        )
        conn.execute(
            "INSERT INTO auditrecordrow "
            "(id, run_id, start_time, pipeline_name, record_json) VALUES (?,?,?,?,?)",
            (uuid4().hex, run_id.hex, newer.start_time.isoformat(), "new", newer.to_json()),
        )
        conn.commit()
    finally:
        conn.close()

    storage = AuditStorage(f"sqlite:///{db_path}")
    listed = storage.list_records(limit=10)
    assert len(listed) == 1
    assert listed[0].pipeline_name == "new"
    with pytest.raises(ValueError, match="already exists"):
        storage.save_record(listed[0])


def test_key_generate_requires_passphrase_or_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("HELIOS_KEY_PASSPHRASE", raising=False)
    monkeypatch.setenv("HELIOS_KEY_DIR", str(tmp_path))
    denied = CliRunner().invoke(app, ["key", "generate"])
    assert denied.exit_code == 1
    assert "HELIOS_KEY_PASSPHRASE" in denied.stdout

    result = CliRunner().invoke(app, ["key", "generate", "--allow-unencrypted"])
    assert result.exit_code == 0, result.stdout
    assert "unencrypted" in result.stdout
    assert "HELIOS_KEY_PASSPHRASE" in result.stdout
    private = tmp_path / "helios.key"
    assert private.exists()
    assert private.stat().st_mode & 0o777 == 0o600
