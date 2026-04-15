"""Additional tests to raise core/checks coverage."""

from __future__ import annotations

from pathlib import Path

from helios.checks.crypt4gh_output import Crypt4GHOutputCheck
from helios.checks.vus_rate import VUSRateCheck
from helios.core.audit_record import AuditRecord
from helios.core.run_context import RunContext
from helios.core.storage import AuditStorage


def test_vus_rate_warn_when_no_variants(tmp_path: Path) -> None:
    empty_vcf = tmp_path / "empty.vcf"
    empty_vcf.write_text(
        "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n",
        encoding="utf-8",
    )
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[empty_vcf],
    )
    result = VUSRateCheck().run(context)
    assert result.status == "warn"


def test_crypt4gh_output_pass(tmp_path: Path) -> None:
    encrypted = tmp_path / "result.vcf.c4gh"
    encrypted.write_text("encrypted", encoding="utf-8")
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[encrypted],
    )
    result = Crypt4GHOutputCheck().run(context)
    assert result.status == "pass"


def test_storage_save_get_list(tmp_path: Path) -> None:
    db_path = tmp_path / "helios.db"
    storage = AuditStorage(f"sqlite:///{db_path}")
    record = AuditRecord(pipeline_name="demo", executor="nextflow")
    storage.save_record(record)

    fetched = storage.get_record(record.run_id)
    assert fetched is not None
    assert fetched.run_id == record.run_id

    listed = storage.list_records(limit=5, offset=0, pipeline_filter="demo")
    assert listed
