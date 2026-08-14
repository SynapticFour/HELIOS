"""VUS reporting rate metrics from VCF ACMG and ClinVar annotations."""

from __future__ import annotations

from collections import Counter

from helios.checks.base import BaseCheck
from helios.checks.vcf_io import iter_info_fields, vcf_artifacts
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext


class VUSRateCheck(BaseCheck):
    """Compute and evaluate variant of uncertain significance rate."""

    check_id = "CLIN-VUS-001"
    name = "VUS Reporting Rate"
    description = "Extract VUS percentage from CLNSIG/ACMG/CSQ classifications."
    severity = "info"
    standards = ["ACMG-2015", "ISO15189:2022-7.3.2"]

    def run(self, context: RunContext) -> CheckResult:
        """Calculate VUS percentage across VCF artifacts."""
        vcfs = vcf_artifacts(context)
        vus_count = 0
        total_classified = 0
        distribution: Counter[str] = Counter()
        for vcf in vcfs:
            for info in iter_info_fields(vcf):
                label = self._classify_variant(info)
                if label is None:
                    continue
                distribution[label] += 1
                total_classified += 1
                if label == "VUS":
                    vus_count += 1
        if total_classified == 0:
            return CheckResult(
                check_id=self.check_id,
                status="skip",
                message="No classified variants available for VUS reporting metric.",
                evidence={
                    "total_classified": 0,
                    "vus_count": 0,
                    "vus_percentage": None,
                    "histogram": {},
                },
            )
        rate = vus_count / total_classified
        checks = self.settings.checks if self.settings is not None else None
        warn_threshold = checks.vus_warn_threshold if checks else 0.40
        fail_threshold = checks.vus_fail_threshold if checks else 0.70
        evidence = {
            "total_classified": total_classified,
            "vus_count": vus_count,
            "vus_percentage": round(rate * 100, 3),
            "histogram": dict(distribution),
            "warn_threshold": warn_threshold,
            "fail_threshold": fail_threshold,
        }
        if rate >= fail_threshold:
            return CheckResult(
                check_id=self.check_id,
                status="fail",
                message=(
                    f"VUS rate is {rate:.2%} ({vus_count}/{total_classified}), "
                    "above fail threshold."
                ),
                evidence=evidence,
            )
        if rate >= warn_threshold:
            return CheckResult(
                check_id=self.check_id,
                status="warn",
                message=(
                    f"VUS rate is {rate:.2%} ({vus_count}/{total_classified}), "
                    "above warn threshold."
                ),
                evidence=evidence,
            )
        return CheckResult(
            check_id=self.check_id,
            status="pass",
            message=f"VUS rate is {rate:.2%} ({vus_count}/{total_classified}).",
            evidence=evidence,
        )

    def _classify_variant(self, info: str) -> str | None:
        fields = {
            item.split("=", 1)[0]: item.split("=", 1)[1] for item in info.split(";") if "=" in item
        }
        clnsig = fields.get("CLNSIG", "").lower()
        acmg_class = fields.get("ACMG_CLASS", "").upper()
        csq = fields.get("CSQ", "").lower()
        if "uncertain_significance" in clnsig or acmg_class in {"VUS", "3"} or "uncertain" in csq:
            return "VUS"
        if "pathogenic" in clnsig or acmg_class in {"P", "LP", "5", "4"}:
            return "PATHOGENIC"
        if "benign" in clnsig or acmg_class in {"B", "LB", "1", "2"}:
            return "BENIGN"
        if clnsig:
            return "OTHER"
        return None
