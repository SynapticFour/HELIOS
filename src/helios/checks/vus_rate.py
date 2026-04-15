"""VUS rate extraction check from VCF records."""

from __future__ import annotations

from typing import Literal

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext


class VUSRateCheck(BaseCheck):
    """Compute and evaluate variant of uncertain significance rate."""

    check_id = "ISO-INTERP-003"
    name = "VUS Rate"
    description = "Estimate VUS burden from ACMG annotations."
    severity = "info"
    standards = ["ISO15189:2022-7.3"]

    def run(self, context: RunContext) -> CheckResult:
        """Calculate VUS percentage across VCF artifacts."""
        vcfs = [p for p in context.artifacts if p.suffix == ".vcf"]
        vus = 0
        variants = 0
        for vcf in vcfs:
            for line in vcf.read_text(encoding="utf-8").splitlines():
                if line.startswith("#") or not line:
                    continue
                variants += 1
                if "UNCERTAIN_SIGNIFICANCE" in line or "VUS" in line:
                    vus += 1
        if variants == 0:
            return CheckResult(
                check_id=self.check_id,
                status="warn",
                message="No VCF variants available for VUS rate extraction.",
                evidence={},
            )
        rate = vus / variants
        status: Literal["pass", "warn", "fail"] = "pass" if rate <= 0.4 else "warn"
        return CheckResult(
            check_id=self.check_id,
            status=status,
            message=f"VUS rate is {rate:.2%} ({vus}/{variants}).",
            evidence={"vus_count": str(vus), "variant_count": str(variants)},
        )

