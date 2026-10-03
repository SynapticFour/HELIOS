"""solum-audit --output-dir and opt-in signed static publish."""

from __future__ import annotations

import json
import os
from pathlib import Path

from typer.testing import CliRunner

from helios.checks.clinical_access import SOLUM_GENESIS_HASH, solum_record_hash
from helios.cli import PublishRefused, app, select_latest_signed_report
from helios.core.audit_record import AuditRecord
from helios.core.signer import generate_keypair, sign_record
from helios.export.json_export import export_json

runner = CliRunner()


def _chain(events: list[dict[str, object]]) -> dict[str, object]:
    records = []
    prev = SOLUM_GENESIS_HASH
    for index, event in enumerate(events, start=1):
        digest = solum_record_hash(index, prev, event)
        records.append({"seq": index, "event": event, "prev_hash": prev, "hash": digest})
        prev = digest
    return {
        "format": "solum-audit-helios-chain-v1",
        "generator": "solum-audit",
        "record_count": len(records),
        "records": records,
    }


def test_solum_audit_output_dir_and_failed_chain_writes_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("HELIOS_AUDIT_DB", str(tmp_path / "helios.db"))
    monkeypatch.setenv("HELIOS_KEY_DIR", str(tmp_path / "keys"))
    good = tmp_path / "good.json"
    good.write_text(
        json.dumps(
            _chain(
                [
                    {
                        "event_type": "consent.granted",
                        "actor": "practitioner/1",
                        "outcome": "success",
                    }
                ]
            )
        ),
        encoding="utf-8",
    )
    out = tmp_path / "reports"
    result = runner.invoke(
        app,
        [
            "solum-audit",
            "--export",
            str(good),
            "--no-sign",
            "--output-dir",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    written = list(out.glob("*.json"))
    assert len(written) == 1

    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps(
            {
                "format": "solum-audit-helios-chain-v1",
                "records": [{"seq": 1, "event": {"event_type": "consent.granted"}}],
            }
        ),
        encoding="utf-8",
    )
    missed = tmp_path / "missed"
    failed = runner.invoke(
        app,
        ["solum-audit", "--export", str(bad), "--output-dir", str(missed)],
    )
    assert failed.exit_code == 1
    assert not missed.exists()


def test_publish_report_copies_only_a_signed_report_without_the_api_key(tmp_path: Path) -> None:
    generate_keypair(base_dir=tmp_path, name="helios", allow_unencrypted=True)
    key = tmp_path / "helios.key"
    reports = tmp_path / "reports"
    unsigned = AuditRecord(pipeline_name="unsigned", executor="unknown")
    old_path = export_json(unsigned, reports / "old.json")
    signed = sign_record(AuditRecord(pipeline_name="signed", executor="unknown"), key)
    new_path = export_json(signed, reports / "new.json")
    os.utime(old_path, (1, 1_000))
    os.utime(new_path, (1, 2_000))

    dest = tmp_path / "public"
    source, text = select_latest_signed_report(reports, tmp_path, api_key="demo-key")
    dest.mkdir()
    (dest / source.name).write_text(text, encoding="utf-8")
    assert source.name == "new.json"
    assert "demo-key" not in text
    assert "unsigned" not in text

    leaked = sign_record(
        AuditRecord(pipeline_name="contains-demo-key-secret", executor="unknown"),
        key,
    )
    export_json(leaked, reports / "leaked.json")
    try:
        select_latest_signed_report(reports, tmp_path, api_key="demo-key-secret")
    except PublishRefused as exc:
        assert "API key" in str(exc)
    else:
        raise AssertionError("report containing the API key was accepted")
