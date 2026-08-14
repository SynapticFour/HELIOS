"""Abstract base class for all HELIOS checks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal

from helios.core.audit_record import CheckResult
from helios.core.run_context import RunContext

if TYPE_CHECKING:
    from helios.config import HeliosSettings


class BaseCheck(ABC):
    """Abstract compliance check contract."""

    check_id: str
    name: str
    description: str
    severity: Literal["info", "warning", "error"]
    standards: list[str]

    def __init__(self, settings: HeliosSettings | None = None) -> None:
        self.settings = settings

    @abstractmethod
    def run(self, context: RunContext) -> CheckResult:
        """Execute check against the run context."""
