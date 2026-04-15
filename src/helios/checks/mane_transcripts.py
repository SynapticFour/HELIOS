"""MANE transcript coverage check for VCF annotations."""

from __future__ import annotations

from pathlib import Path

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext


class ManeTranscriptCheck(BaseCheck):
    """Check whether output VCF variants reference MANE transcripts."""

    check_id = "GA4GH-ANNOT-002"
    name = "MANE Transcript Coverage"
    description = "Ensure MANE Select/Plus Clinical references are present."
    severity = "warning"
    standards = ["ISO15189:2022-5.5", "GA4GH-VRSATILE-1.0"]

    def run(self, context: RunContext) -> CheckResult:
        """Scan VCF files for MANE transcript annotations."""
        vcfs = [p for p in context.artifacts if p.suffix in {".vcf", ".gz"} and "vcf" in p.name]
        if not vcfs:
            return CheckResult(
                check_id=self.check_id,
                status="warn",
                message="No VCF artifacts available for MANE transcript check.",
                evidence={},
            )

        mane_hits = 0
        total_variants = 0
        for vcf in vcfs:
            mane_hits += self._count_mane_mentions(vcf)
            total_variants += self._count_variants(vcf)

        if total_variants == 0:
            return CheckResult(
                check_id=self.check_id,
                status="warn",
                message="VCF contains no callable variants for MANE evaluation.",
                evidence={"mane_hits": str(mane_hits)},
            )
        if mane_hits > 0:
            return CheckResult(
                check_id=self.check_id,
                status="pass",
                message="MANE transcript annotations detected in variant output.",
                evidence={"mane_hits": str(mane_hits), "variant_count": str(total_variants)},
            )
        return CheckResult(
            check_id=self.check_id,
            status="fail",
            message="No MANE Select/Plus Clinical transcript references found.",
            evidence={"variant_count": str(total_variants)},
        )

    def _count_mane_mentions(self, path: Path) -> int:
        text = path.read_text(encoding="utf-8")
        return text.count("MANE_SELECT") + text.count("MANE_PLUS_CLINICAL")

    def _count_variants(self, path: Path) -> int:
        return sum(
            1
            for line in path.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        )

