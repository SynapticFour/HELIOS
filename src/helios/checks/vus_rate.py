"""VUS reporting rate metrics from VCF ACMG and ClinVar annotations."""

from __future__ import annotations

from collections import Counter

from helios.checks.base import BaseCheck
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
        vcfs = [p for p in context.artifacts if p.suffix == ".vcf"]
        vus_count = 0
        total_classified = 0
        distribution: Counter[str] = Counter()
        for vcf in vcfs:
            for line in vcf.read_text(encoding="utf-8").splitlines():
                if line.startswith("#") or not line:
                    continue
                label = self._classify_variant(line)
                if label is None:
                    continue
                distribution[label] += 1
                total_classified += 1
                if label == "VUS":
                    vus_count += 1
        if total_classified == 0:
            return CheckResult(
                check_id=self.check_id,
                status="pass",
                message="No classified variants available for VUS reporting metric.",
                evidence={
                    "total_classified": 0,
                    "vus_count": 0,
                    "vus_percentage": 0.0,
                    "histogram": {},
                },
            )
        rate = vus_count / total_classified
        return CheckResult(
            check_id=self.check_id,
            status="pass",
            message=f"VUS rate is {rate:.2%} ({vus_count}/{total_classified}).",
            evidence={
                "total_classified": total_classified,
                "vus_count": vus_count,
                "vus_percentage": round(rate * 100, 3),
                "histogram": dict(distribution),
            },
        )

    def _classify_variant(self, line: str) -> str | None:
        info = line.split("\t", maxsplit=8)[7] if "\t" in line else ""
        fields = {
            item.split("=", 1)[0]: item.split("=", 1)[1]
            for item in info.split(";")
            if "=" in item
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

