"""Ferrum WES outputs must be DRS object IDs, not only local files."""

from __future__ import annotations

from pathlib import Path

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext

_DRS_META_KEYS = (
    "ferrum_wes_outputs",
    "wes_output_drs_ids",
    "output_drs_uris",
    "wes_outputs",
)
_WES_CONTEXT_KEYS = (
    "wes_run_id",
    "ferrum_wes_url",
    "wes_url",
    "FERRUM_WES_URL",
)


def _is_drs_ref(value: object) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if text.startswith("drs://"):
        return True
    return text.startswith("drs.")


def _collect(value: object, into: list[str]) -> None:
    if _is_drs_ref(value):
        into.append(str(value).strip())
        return
    if isinstance(value, list):
        for item in value:
            _collect(item, into)
        return
    if isinstance(value, dict):
        for item in value.values():
            _collect(item, into)


class FerrumWesDrsOutputCheck(BaseCheck):
    """When a Ferrum WES run is in context, outputs must be DRS IDs."""

    check_id = "GA4GH-WES-DRS-001"
    name = "Ferrum WES outputs are DRS IDs"
    description = (
        "WES outputs registered in Ferrum DRS (drs:// or object id list). "
        "Local file hashes alone are not a Ferrum join."
    )
    severity = "warning"
    standards = ["GA4GH-WES-1.1", "GA4GH-DRS-1.2"]

    def run(self, context: RunContext) -> CheckResult:
        refs: list[str] = []
        for key in _DRS_META_KEYS:
            if key in context.metadata:
                _collect(context.metadata[key], refs)
            if key in context.parameters:
                _collect(context.parameters[key], refs)
        for value in context.parameters.values():
            _collect(value, refs)
        for value in context.metadata.values():
            if _is_drs_ref(value):
                refs.append(value)

        wes_claimed = any(
            key in context.metadata or key in context.parameters for key in _WES_CONTEXT_KEYS
        ) or any(
            str(v).startswith("http") and "/ga4gh/wes/" in str(v)
            for v in list(context.parameters.values()) + list(context.metadata.values())
        )

        unique = sorted(set(refs))
        if unique:
            return CheckResult(
                check_id=self.check_id,
                status="pass",
                message="WES outputs include Ferrum DRS identifiers.",
                evidence={"drs_refs": unique},
            )

        local_suffixes = {".bam", ".cram", ".vcf", ".fastq", ".fq"}
        local_only = [
            str(p)
            for p in context.artifacts
            if isinstance(p, Path) and p.suffix.lower() in local_suffixes
        ]
        if wes_claimed:
            return CheckResult(
                check_id=self.check_id,
                status="fail",
                message=(
                    "Ferrum WES run in context but no DRS output ids "
                    "(set metadata ferrum_wes_outputs or wes_output_drs_ids)."
                ),
                evidence={"local_artifacts": local_only},
            )
        return CheckResult(
            check_id=self.check_id,
            status="skip",
            message="No Ferrum WES context and no DRS output ids (not applicable).",
            evidence={},
        )
