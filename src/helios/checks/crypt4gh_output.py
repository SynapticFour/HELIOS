"""Crypt4GH output encryption presence check."""

from __future__ import annotations

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext


class Crypt4GHOutputCheck(BaseCheck):
    """Verify that output artifacts include encrypted Crypt4GH files."""

    check_id = "SEC-CRYPT4GH-004"
    name = "Crypt4GH Output Encryption"
    description = "Ensure sensitive outputs are encrypted in Crypt4GH format."
    severity = "error"
    standards = ["ISO15189:2022-5.8", "GA4GH-CRYPT4GH-1.0"]

    def run(self, context: RunContext) -> CheckResult:
        """Pass if at least one .c4gh file exists in produced artifacts."""
        encrypted = [str(p) for p in context.artifacts if p.suffix == ".c4gh"]
        if encrypted:
            return CheckResult(
                check_id=self.check_id,
                status="pass",
                message="Crypt4GH-encrypted artifacts present.",
                evidence={"files": ",".join(encrypted)},
            )
        return CheckResult(
            check_id=self.check_id,
            status="warn",
            message="No Crypt4GH outputs detected.",
            evidence={},
        )

