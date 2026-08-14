"""Compliance check registry with auto-discovery and scoring."""

from __future__ import annotations

import functools
import importlib
import inspect
import pkgutil
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext

if TYPE_CHECKING:
    from helios.config import HeliosSettings

CHECK_ALIASES: dict[str, str] = {
    "reference_genome": "GA4GH-REF-001",
    "container_pinning": "SEC-CONTAINER-001",
    "mane_transcripts": "GA4GH-MANE-001",
    "mane_transcript": "GA4GH-MANE-001",
    "vus_rate": "CLIN-VUS-001",
    "crypt4gh_output": "GA4GH-CRYPT-001",
    "clinical_access": "CLIN-ACCESS-001",
}


class ComplianceScore(BaseModel):
    """Aggregate compliance score and grade summary."""

    score: int
    grade: Literal["A", "B", "C", "D", "F"]
    breakdown: dict[str, int]
    passed: int
    warned: int
    failed: int


class CheckRegistry:
    """Discovers, registers, and executes compliance checks."""

    def __init__(self) -> None:
        self._checks: dict[str, type[BaseCheck]] = {}
        self._discover_checks()

    def register(self, check: type[BaseCheck]) -> None:
        """Register a check class by check identifier."""
        if not check.check_id:
            raise ValueError("Check classes must define check_id")
        self._checks[check.check_id] = check

    def run_all(
        self,
        context: RunContext,
        enabled: list[str] | None = None,
        settings: HeliosSettings | None = None,
    ) -> list[CheckResult]:
        """Run all enabled checks and return results.

        Exceptions inside a check become a fail result so one crash cannot
        abort the rest of the audit.
        """
        selected_ids = set(enabled) if enabled else set(self._checks.keys())
        results: list[CheckResult] = []
        for check_id, check_cls in sorted(self._checks.items()):
            if check_id not in selected_ids:
                continue
            try:
                check = check_cls(settings=settings)
                results.append(check.run(context))
            except Exception as exc:
                results.append(
                    CheckResult(
                        check_id=check_id,
                        status="fail",
                        message=f"Check crashed: {exc}",
                        evidence={"error_type": type(exc).__name__},
                    )
                )
        return results

    def get_registered_checks(self) -> dict[str, type[BaseCheck]]:
        """Return a copy of check registry keyed by check_id."""
        return dict(self._checks)

    def resolve_enabled(self, configured: list[str]) -> list[str]:
        """Resolve configured names or IDs to registered check identifiers.

        Unknown names raise ValueError. An empty list enables every registered
        check (explicit opt-in to the full suite).
        """
        registered = self.get_registered_checks()
        by_name = {
            cls.__name__.lower().replace("_", ""): check_id for check_id, cls in registered.items()
        }
        resolved: list[str] = []
        unknown: list[str] = []
        for entry in configured:
            if entry in registered:
                resolved.append(entry)
                continue
            aliased = CHECK_ALIASES.get(entry)
            if aliased and aliased in registered:
                resolved.append(aliased)
                continue
            key = entry.replace("-", "_").replace(" ", "_").lower().replace("_", "")
            if not key.endswith("check"):
                key = f"{key}check"
            matched = by_name.get(key)
            if matched:
                resolved.append(matched)
            else:
                unknown.append(entry)
        if unknown:
            raise ValueError(f"Unknown check name(s): {', '.join(unknown)}")
        return resolved or list(registered.keys())

    def compute_score(self, results: list[CheckResult]) -> ComplianceScore:
        """Compute weighted compliance score and letter grade.

        ``skip`` results are excluded from the denominator so not-applicable
        checks do not inflate the grade.
        """
        weights = {"info": 1, "warning": 2, "error": 3}
        status_points = {"pass": 1.0, "info": 1.0, "warn": 0.5, "fail": 0.0}
        scored = [result for result in results if result.status != "skip"]
        passed = sum(1 for result in scored if result.status in {"pass", "info"})
        warned = sum(1 for result in scored if result.status == "warn")
        failed = sum(1 for result in scored if result.status == "fail")

        numerator = 0.0
        denominator = 0.0
        for result in scored:
            check_cls = self._checks.get(result.check_id)
            severity = check_cls.severity if check_cls else "warning"
            weight = weights[severity]
            denominator += weight
            numerator += weight * status_points.get(result.status, 0.0)
        score = int(round((numerator / denominator) * 100)) if denominator else 100
        grade = self._grade_for_score(score)
        return ComplianceScore(
            score=score,
            grade=grade,
            breakdown={"pass": passed, "warn": warned, "fail": failed},
            passed=passed,
            warned=warned,
            failed=failed,
        )

    def _discover_checks(self) -> None:
        package_name = __name__
        package = importlib.import_module(package_name)
        for module_info in pkgutil.iter_modules(package.__path__):
            if module_info.name in {"base", "vcf_io"}:
                continue
            module = importlib.import_module(f"{package_name}.{module_info.name}")
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if not issubclass(obj, BaseCheck) or obj is BaseCheck:
                    continue
                if obj.__module__ != module.__name__:
                    continue
                self.register(obj)

    def _grade_for_score(self, score: int) -> Literal["A", "B", "C", "D", "F"]:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"


@functools.lru_cache(maxsize=1)
def get_check_registry() -> CheckRegistry:
    """Return a process-wide registry so scoring does not rediscover plugins."""
    return CheckRegistry()


__all__ = [
    "CHECK_ALIASES",
    "CheckRegistry",
    "ComplianceScore",
    "get_check_registry",
]
