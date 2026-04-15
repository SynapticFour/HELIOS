"""Abstract base class for all HELIOS checks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext


class BaseCheck(ABC):
    """Abstract compliance check contract."""

    check_id: str
    name: str
    description: str
    severity: Literal["info", "warning", "error"]
    standards: list[str]

    @abstractmethod
    def run(self, context: RunContext) -> CheckResult:
        """Execute check against the run context."""
