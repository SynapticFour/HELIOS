"""Tests for CLIN-ACCESS-001 Solum clinical audit check."""

from __future__ import annotations

import json
from pathlib import Path

from helios.checks.clinical_access import (
    SOLUM_GENESIS_HASH,
    ClinicalAccessCheck,
    solum_record_hash,
)
from helios.core.run_context import RunContext


def _chained_export(events: list[dict[str, object]]) -> dict[str, object]:
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


def test_clinical_access_from_solum_chain_export(tmp_path: Path) -> None:
    export = tmp_path / "pilot.solum-audit-helios-chain.json"
    export.write_text(
        json.dumps(
            _chained_export(
                [
                    {
                        "event_type": "consent.granted",
                        "actor": "practitioner/1",
                        "outcome": "success",
                    },
                    {
                        "event_type": "authorization.denied",
                        "actor": "attacker",
                        "outcome": "denied",
                    },
                    {"event_type": "data.encrypt", "actor": "practitioner/1", "outcome": "success"},
                ]
            )
        ),
        encoding="utf-8",
    )
    context = RunContext(
        pipeline_name="test",
        executor="unknown",
        work_dir=tmp_path,
        output_dir=tmp_path,
        parameters={"solum_audit_export": str(export)},
    )
    result = ClinicalAccessCheck().run(context)
    assert result.status == "pass"
    assert result.evidence["record_count"] == 3
    assert result.evidence["clinical_event_total"] == 3
    assert result.evidence["chain_ok"] is True


def test_clinical_access_fails_without_hash_chain(tmp_path: Path) -> None:
    export = tmp_path / "pilot.solum-audit-helios-chain.json"
    export.write_text(
        json.dumps(
            {
                "format": "solum-audit-helios-chain-v1",
                "records": [{"seq": 1, "event": {"event_type": "consent.granted"}}],
            }
        ),
        encoding="utf-8",
    )
    context = RunContext(
        pipeline_name="test",
        executor="unknown",
        work_dir=tmp_path,
        output_dir=tmp_path,
        parameters={"solum_audit_export": str(export)},
    )
    result = ClinicalAccessCheck().run(context)
    assert result.status == "fail"
    assert "hash" in result.message.lower()


def test_clinical_access_fails_with_zero_clinical_events(tmp_path: Path) -> None:
    export = tmp_path / "pilot.solum-audit-helios-chain.json"
    export.write_text(
        json.dumps(
            _chained_export([{"event_type": "identity.authenticated", "outcome": "success"}])
        ),
        encoding="utf-8",
    )
    context = RunContext(
        pipeline_name="test",
        executor="unknown",
        work_dir=tmp_path,
        output_dir=tmp_path,
        parameters={"solum_audit_export": str(export)},
    )
    result = ClinicalAccessCheck().run(context)
    assert result.status == "fail"


def test_clinical_access_skips_without_export(tmp_path: Path) -> None:
    context = RunContext(
        pipeline_name="test",
        executor="unknown",
        work_dir=tmp_path,
        output_dir=tmp_path,
    )
    result = ClinicalAccessCheck().run(context)
    assert result.status == "skip"
    assert result.evidence.get("skipped") is True


def test_clinical_access_rejects_wrong_format(tmp_path: Path) -> None:
    export = tmp_path / "bad.solum-audit.json"
    export.write_text(
        json.dumps({"format": "not-solum", "records": []}),
        encoding="utf-8",
    )
    context = RunContext(
        pipeline_name="test",
        executor="unknown",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[export],
    )
    result = ClinicalAccessCheck().run(context)
    assert result.status == "fail"
