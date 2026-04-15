"""Compliance check registry with auto-discovery and scoring."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Literal

from pydantic import BaseModel

from helios.checks.base import BaseCheck
from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext


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

    def run_all(self, context: RunContext, enabled: list[str] | None = None) -> list[CheckResult]:
        """Run all enabled checks and return results."""
        selected_ids = set(enabled) if enabled else set(self._checks.keys())
        results: list[CheckResult] = []
        for check_id, check_cls in sorted(self._checks.items()):
            if check_id not in selected_ids:
                continue
            check = check_cls()
            results.append(check.run(context))
        return results

    def get_registered_checks(self) -> dict[str, type[BaseCheck]]:
        """Return a copy of check registry keyed by check_id."""
        return dict(self._checks)

    def compute_score(self, results: list[CheckResult]) -> ComplianceScore:
        """Compute weighted compliance score and letter grade."""
        weights = {"info": 1, "warning": 2, "error": 3}
        status_points = {"pass": 1.0, "info": 1.0, "skip": 1.0, "warn": 0.5, "fail": 0.0}
        passed = sum(1 for result in results if result.status in {"pass", "info"})
        warned = sum(1 for result in results if result.status == "warn")
        failed = sum(1 for result in results if result.status == "fail")

        numerator = 0.0
        denominator = 0.0
        for result in results:
            check_cls = self._checks.get(result.check_id)
            severity = check_cls.severity if check_cls else "warning"
            weight = weights[severity]
            denominator += weight
            numerator += weight * status_points[result.status]
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
            if module_info.name in {"base"}:
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


__all__ = ["CheckRegistry", "ComplianceScore"]

