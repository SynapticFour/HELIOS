"""Tests for Snakemake wrapper and parser paths."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from helios.integrations.snakemake import SnakemakeRunParser
from helios.integrations.snakemake_wrapper import run_wrapped_snakemake


def test_snakemake_parser_metadata_and_wrapper(tmp_path: Path, monkeypatch) -> None:
    snk_root = tmp_path / "project"
    out_dir = snk_root / "results"
    meta_dir = snk_root / ".snakemake" / "metadata"
    log_dir = snk_root / ".snakemake" / "log"
    meta_dir.mkdir(parents=True)
    log_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    (out_dir / "out.vcf").write_text("##fileformat=VCFv4.2\n", encoding="utf-8")
    (snk_root / "report.html").write_text("<html/>", encoding="utf-8")
    (meta_dir / "rule.json").write_text(
        json.dumps(
            {
                "rule": "call",
                "conda_env": "envs/call.yaml",
                "container_img_url": "docker.io/tool:1.0@sha256:abc",
                "input": ["in.vcf"],
                "output": ["out.vcf"],
            }
        ),
        encoding="utf-8",
    )
    parser = SnakemakeRunParser(snakemake_dir=snk_root, output_dir=out_dir)
    records = parser.parse_metadata()
    assert records and records[0].rule_name == "call"
    assert parser.get_containers()
    context = parser.build_run_context()
    assert context.metadata["rule_count"] == "1"

    monkeypatch.setattr(
        "helios.integrations.snakemake_wrapper.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    class _Storage:
        def save_record(self, _record: object) -> None:
            return None

    monkeypatch.setattr("helios.integrations.snakemake_wrapper.AuditStorage", _Storage)
    monkeypatch.setattr(
        "helios.integrations.snakemake_wrapper.CheckRegistry.run_all",
        lambda _self, _ctx: [],
    )
    code = run_wrapped_snakemake(["snakemake", "--cores", "1"], snk_root, out_dir)
    assert code == 0
