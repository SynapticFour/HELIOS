"""Tests for VUS reporting metric extraction."""

from __future__ import annotations

from pathlib import Path

from helios.checks.vus_rate import VUSRateCheck
from helios.core.run_context import RunContext


def test_vus_rate_distribution_from_clnsig(tmp_path: Path) -> None:
    vcf = tmp_path / "vus.vcf"
    lines = [
        "##fileformat=VCFv4.2",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO",
    ]
    lines.extend([f"1\t{100 + i}\t.\tA\tG\t100\tPASS\tCLNSIG=Pathogenic" for i in range(5)])
    lines.extend(
        [f"1\t{200 + i}\t.\tA\tC\t100\tPASS\tCLNSIG=Uncertain_significance" for i in range(3)]
    )
    lines.extend([f"1\t{300 + i}\t.\tG\tT\t100\tPASS\tCLNSIG=Benign" for i in range(2)])
    vcf.write_text("\n".join(lines) + "\n", encoding="utf-8")

    context = RunContext(
        pipeline_name="test",
        executor="nextflow",
        work_dir=tmp_path,
        output_dir=tmp_path,
        artifacts=[vcf],
    )
    result = VUSRateCheck().run(context)

    assert result.status == "pass"
    assert result.evidence["total_classified"] == 10
    assert result.evidence["vus_count"] == 3
    assert result.evidence["histogram"]["PATHOGENIC"] == 5
    assert result.evidence["histogram"]["VUS"] == 3
    assert result.evidence["histogram"]["BENIGN"] == 2
