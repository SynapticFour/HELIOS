"""Tests for CLIN-ACCESS-001 Solum clinical audit check."""

from __future__ import annotations

import json
from pathlib import Path

from helios.checks.clinical_access import ClinicalAccessCheck
from helios.core.run_context import RunContext


def test_clinical_access_from_solum_chain_export(tmp_path: Path) -> None:
    export = tmp_path / "pilot.solum-audit-helios-chain.json"
    export.write_text(
        json.dumps(
            {
                "format": "solum-audit-helios-chain-v1",
                "generator": "solum-audit",
                "record_count": 3,
                "records": [
                    {
                        "seq": 1,
                        "event": {
                            "event_type": "consent.granted",
                            "actor": "practitioner/1",
                            "outcome": "success",
                        },
                    },
                    {
                        "seq": 2,
                        "event": {
                            "event_type": "authorization.denied",
                            "actor": "attacker",
                            "outcome": "denied",
                        },
                    },
                    {
                        "seq": 3,
                        "event": {
                            "event_type": "data.encrypt",
                            "actor": "practitioner/1",
                            "outcome": "success",
                        },
                    },
                ],
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
    assert result.status == "pass"
    assert result.evidence["record_count"] == 3
    assert result.evidence["clinical_event_total"] == 3
    assert result.evidence["clinical_event_counts"]["consent.granted"] == 1
    assert result.evidence["clinical_event_counts"]["authorization.denied"] == 1


def test_clinical_access_skips_without_export(tmp_path: Path) -> None:
    context = RunContext(
        pipeline_name="test",
        executor="unknown",
        work_dir=tmp_path,
        output_dir=tmp_path,
    )
    result = ClinicalAccessCheck().run(context)
    assert result.status == "pass"
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
