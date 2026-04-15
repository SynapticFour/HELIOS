"""Pydantic response models for dashboard API contracts."""

from __future__ import annotations

from pydantic import BaseModel


class RunListItem(BaseModel):
    """Compact run summary item for overview tables."""

    run_id: str
    pipeline_name: str
    executor: str
    start_time: str
    score: int
    status: str


class RunImportResponse(BaseModel):
    """Run import endpoint response."""

    run_id: str


class DeleteResponse(BaseModel):
    """Deletion status response."""

    deleted: bool


class FailingCheckCount(BaseModel):
    """Failure frequency record for top failing checks."""

    check_id: str
    count: int


class DateRatePoint(BaseModel):
    """Date-aligned trend point."""

    date: str
    rate: float


class OverviewResponse(BaseModel):
    """Dashboard overview metrics."""

    total_runs: int
    avg_score: float
    failing_checks_top5: list[FailingCheckCount]
    grch38_adoption_rate: float
    mane_adoption_rate: float
    vus_rate_trend: list[DateRatePoint]
