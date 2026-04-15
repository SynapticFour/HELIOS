"""Reference genome check for GRCh38/hg38 validation."""

from __future__ import annotations

from pathlib import Path

import pysam

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext

KNOWN_GRCH38_MD5 = {
    "chr1": "6aef897c3d6ff0c78aff06ac189178dd",
    "chr22": "a718acaa6135fdca8357d5bfe94211dd",
}


class ReferenceGenomeCheck(BaseCheck):
    """Detect whether BAM/CRAM headers indicate GRCh38/hg38."""

    check_id = "GA4GH-REF-001"
    name = "Reference Genome Validation"
    description = "Verify run uses GRCh38/hg38 reference."
    severity = "error"
    standards = ["ISO15189:2022-5.3", "GA4GH-VRS-1.3"]

    def run(self, context: RunContext) -> CheckResult:
        """Run reference genome check over BAM/CRAM artifacts."""
        bam_like = [
            path for path in context.artifacts if path.suffix in {".bam", ".cram", ".header"}
        ]
        if not bam_like:
            return CheckResult(
                check_id=self.check_id,
                status="warn",
                message="No BAM/CRAM artifact found for reference validation.",
                evidence={},
            )

        path = bam_like[0]
        header_dict = self._read_header(path)
        sq_entries = header_dict.get("SQ", [])
        sn_values = [entry.get("SN", "") for entry in sq_entries]
        joined = ",".join(sn_values).lower()

        has_chr_prefix = any(sn.startswith("chr") for sn in sn_values)
        has_numeric = any(sn in {"1", "22"} for sn in sn_values)
        mentions_grch38 = "grch38" in joined or "hg38" in joined
        mentions_grch37 = "grch37" in joined or "hg19" in joined

        evidence = {
            "artifact": str(path),
            "known_md5_chr1": KNOWN_GRCH38_MD5["chr1"],
            "known_md5_chr22": KNOWN_GRCH38_MD5["chr22"],
        }

        for entry in sq_entries:
            source = f"{entry.get('UR', '')}|{entry.get('M5', '')}".lower()
            if "grch38" in source or entry.get("M5") in KNOWN_GRCH38_MD5.values():
                evidence["header_source_match"] = source
                return CheckResult(
                    check_id=self.check_id,
                    status="pass",
                    message="GRCh38 evidence found in sequence dictionary metadata.",
                    evidence=evidence,
                )

        if mentions_grch37:
            return CheckResult(
                check_id=self.check_id,
                status="fail",
                message="Header indicates GRCh37/hg19 or older reference.",
                evidence=evidence,
            )

        has_source_fields = any("UR" in entry or "M5" in entry for entry in sq_entries)
        if mentions_grch38 or (has_chr_prefix and has_numeric):
            if has_source_fields:
                return CheckResult(
                    check_id=self.check_id,
                    status="warn",
                    message=(
                        "Reference naming resembles GRCh38/hg38, "
                        "but UR/M5 fields did not match known GRCh38 sources."
                    ),
                    evidence=evidence,
                )
            return CheckResult(
                check_id=self.check_id,
                status="warn",
                message=(
                    "Reference naming is compatible with GRCh38/hg38 but lacks UR/M5 provenance."
                ),
                evidence=evidence,
            )

        return CheckResult(
            check_id=self.check_id,
            status="warn",
            message="Reference assembly ambiguous; unable to prove GRCh38 usage.",
            evidence=evidence,
        )

    def _read_header(self, path: Path) -> dict[str, list[dict[str, str]]]:
        if path.suffix == ".header":
            header: dict[str, list[dict[str, str]]] = {"SQ": []}
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.startswith("@SQ"):
                    continue
                fields = line.split("\t")[1:]
                parsed: dict[str, str] = {}
                for field in fields:
                    if ":" in field:
                        key, value = field.split(":", 1)
                        parsed[key] = value
                header["SQ"].append(parsed)
            return header

        with pysam.AlignmentFile(str(path), "r") as alignment:
            return alignment.header.to_dict()
