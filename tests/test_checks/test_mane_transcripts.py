"""Tests for MANE transcript check."""

from __future__ import annotations

import gzip
from pathlib import Path
from unittest.mock import patch

from helios.checks.mane_transcripts import MANETranscriptCheck
from helios.core.run_context import RunContext


def _write_mane_summary(path: Path) -> None:
    content = (
        "symbol\tentrez\tensembl_gene\trefseq_nuc\tensembl_nuc\tMANE_status\n"
        "GENE1\t1\tENSG000001\tNM_000001.2\tENST000003\tMANE Select\n"
        "GENE2\t2\tENSG000002\tNM_000002.3\tENST000004\tMANE Plus Clinical\n"
    )
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(content)


def test_mane_transcripts_with_mocked_download_and_cache(tmp_path: Path) -> None:
    vcf = tmp_path / "annotated.vcf"
    vcf.write_text(
        (
            "##fileformat=VCFv4.2\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            "1\t100\t.\tA\tG\t100\tPASS\tCSQ=A|missense|GENE1|NM_000001.2\n"
            "1\t200\t.\tC\tT\t100\tPASS\tANN=T|missense|GENE3|NM_999999.1\n"
        ),
        encoding="utf-8",
    )
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    check = MANETranscriptCheck(cache_dir=cache_dir)

    def _fake_download() -> Path:
        downloaded = cache_dir / "MANE.GRCh38.v1.4.summary.txt.gz"
        _write_mane_summary(downloaded)
        return downloaded

    with patch.object(
        MANETranscriptCheck,
        "_download_mane_summary",
        side_effect=_fake_download,
    ) as mocked:
        context = RunContext(
            pipeline_name="test",
            executor="nextflow",
            work_dir=tmp_path,
            output_dir=tmp_path,
            artifacts=[vcf],
        )
        first = check.run(context)
        second = check.run(context)

    assert first.status == "warn"
    assert first.evidence["total_variants"] == 2
    assert "NM_999999" in first.evidence["non_mane_transcripts"]
    assert second.status == "warn"
    assert mocked.call_count == 1


def test_mane_transcripts_fail_without_annotations(tmp_path: Path) -> None:
    vcf = tmp_path / "plain.vcf"
    vcf.write_text(
        "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n1\t100\t.\tA\tT\t60\tPASS\tDP=20\n",
        encoding="utf-8",
    )
    cache_dir = tmp_path / "cache2"
    cache_dir.mkdir(parents=True, exist_ok=True)
    summary = cache_dir / "MANE.GRCh38.v1.4.summary.txt.gz"
    _write_mane_summary(summary)
    check = MANETranscriptCheck(cache_dir=cache_dir)
    with patch.object(MANETranscriptCheck, "_download_mane_summary", return_value=summary):
        context = RunContext(
            pipeline_name="test",
            executor="nextflow",
            work_dir=tmp_path,
            output_dir=tmp_path,
            artifacts=[vcf],
        )
        result = check.run(context)

    assert result.status == "fail"
    assert result.evidence["mane_annotated"] == 0


def test_mane_transcripts_pass(vcf_path: Path, tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache3"
    cache_dir.mkdir(parents=True, exist_ok=True)
    summary = cache_dir / "MANE.GRCh38.v1.4.summary.txt.gz"
    _write_mane_summary(summary)
    check = MANETranscriptCheck(cache_dir=cache_dir)
    with patch.object(MANETranscriptCheck, "_download_mane_summary", return_value=summary):
        patched = tmp_path / "sample.vcf"
        patched.write_text(
            (vcf_path.read_text(encoding="utf-8") + "\n").replace(
                "MANE_SELECT=NM_000001.1",
                "CSQ=A|missense|GENE1|NM_000001.2",
            ),
            encoding="utf-8",
        )
        context = RunContext(
            pipeline_name="test",
            executor="nextflow",
            work_dir=tmp_path,
            output_dir=tmp_path,
            artifacts=[patched],
        )
        result = check.run(context)

    assert result.status == "pass"
    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[vcf_path],
    )
    result = check.run(context)
    assert result.status == "pass"

