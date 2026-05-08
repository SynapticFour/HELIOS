"""Crypt4GH encryption verification for pipeline output artifacts."""

from __future__ import annotations

from pathlib import Path

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext

CRYPT4GH_MAGIC = bytes.fromhex("637279707434676801000000")
GENOMIC_SUFFIXES = {".bam", ".cram", ".vcf", ".fastq", ".fq"}


class Crypt4GHOutputCheck(BaseCheck):
    """Verify that output artifacts include encrypted Crypt4GH files."""

    check_id = "GA4GH-CRYPT-001"
    name = "Crypt4GH Output Encryption"
    description = "Verify Crypt4GH encryption for genomic outputs when required."
    severity = "warning"
    standards = ["GA4GH-Crypt4GH-1.0", "GA4GH-DRS-1.3"]

    def run(self, context: RunContext) -> CheckResult:
        """Assess output encryption state based on DRS input risk and file signatures."""
        drs_input = self._has_drs_input(context)
        genomic_outputs = [p for p in context.artifacts if self._is_genomic_output(p)]
        encrypted_files = [p for p in genomic_outputs if self._is_crypt4gh_file(p)]

        if encrypted_files and genomic_outputs and len(encrypted_files) == len(genomic_outputs):
            return CheckResult(
                check_id=self.check_id,
                status="pass",
                message="All genomic output files are Crypt4GH encrypted.",
                evidence={
                    "encrypted_files": [str(path) for path in encrypted_files],
                    "drs_input": drs_input,
                },
            )

        if drs_input and (not genomic_outputs or len(encrypted_files) < len(genomic_outputs)):
            return CheckResult(
                check_id=self.check_id,
                status="warn",
                message="DRS inputs detected but outputs are not fully Crypt4GH encrypted.",
                evidence={
                    "genomic_outputs": [str(path) for path in genomic_outputs],
                    "encrypted_files": [str(path) for path in encrypted_files],
                },
            )

        if encrypted_files:
            return CheckResult(
                check_id=self.check_id,
                status="info",
                message="Crypt4GH outputs detected.",
                evidence={"encrypted_files": [str(path) for path in encrypted_files]},
            )

        return CheckResult(
            check_id=self.check_id,
            status="skip",
            message="No DRS inputs and no Crypt4GH files detected (not applicable).",
            evidence={},
        )

    def _has_drs_input(self, context: RunContext) -> bool:
        for value in context.parameters.values():
            if isinstance(value, str) and value.startswith("drs://"):
                return True
            if isinstance(value, list) and any(
                isinstance(item, str) and item.startswith("drs://") for item in value
            ):
                return True
        return any(item.startswith("drs://") for item in context.metadata.values())

    def _is_genomic_output(self, path: Path) -> bool:
        text = str(path).lower()
        return any(
            text.endswith(suffix) or text.endswith(f"{suffix}.c4gh") for suffix in GENOMIC_SUFFIXES
        )

    def _is_crypt4gh_file(self, path: Path) -> bool:
        if path.suffix == ".c4gh":
            return True
        with path.open("rb") as handle:
            header = handle.read(12)
        return header == CRYPT4GH_MAGIC
