"""Dashboard analytics endpoints."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import cast

from fastapi import APIRouter, Depends, Request

from helios.checks import CheckRegistry
from helios.core.storage import AuditStorage
from helios.dashboard.models import DateRatePoint, FailingCheckCount, OverviewResponse

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


def _get_storage(request: Request) -> AuditStorage:
    return cast(AuditStorage, request.app.state.storage)


STORAGE_DEP = Depends(_get_storage)


@router.get("/overview")
def overview(storage: AuditStorage = STORAGE_DEP) -> OverviewResponse:
    """Return high-level dashboard metrics."""
    records = storage.list_records(limit=1000)
    if not records:
        return OverviewResponse(
            total_runs=0,
            avg_score=0,
            failing_checks_top5=[],
            grch38_adoption_rate=0.0,
            mane_adoption_rate=0.0,
            vus_rate_trend=[],
        )
    scores = [CheckRegistry().compute_score(record.checks).score for record in records]
    failing = Counter(
        check.check_id
        for record in records
        for check in record.checks
        if check.status == "fail"
    ).most_common(5)
    grch38_hits = sum(1 for record in records if _record_has_grch38(record))
    mane_checks = [
        check for record in records for check in record.checks if check.check_id == "GA4GH-MANE-001"
    ]
    mane_hits = sum(1 for check in mane_checks if check.status == "pass")
    vus_trend: dict[date, list[float]] = defaultdict(list)
    for record in records:
        for check in record.checks:
            if check.check_id == "CLIN-VUS-001":
                value = float(check.evidence.get("vus_percentage", 0.0))
                vus_trend[record.start_time.date()].append(value)
    return OverviewResponse(
        total_runs=len(records),
        avg_score=round(sum(scores) / len(scores), 2),
        failing_checks_top5=[
            FailingCheckCount(check_id=check_id, count=count)
            for check_id, count in failing
        ],
        grch38_adoption_rate=round((grch38_hits / len(records)) * 100, 2),
        mane_adoption_rate=round((mane_hits / max(len(mane_checks), 1)) * 100, 2),
        vus_rate_trend=[
            DateRatePoint(date=day.isoformat(), rate=round(sum(values) / len(values), 3))
            for day, values in sorted(vus_trend.items())
        ],
    )


@router.get("/trends")
def trends(storage: AuditStorage = STORAGE_DEP) -> dict[str, object]:
    """Return compliance score trends grouped by pipeline."""
    records = storage.list_records(limit=2000)
    by_pipeline: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        score = CheckRegistry().compute_score(record.checks).score
        by_pipeline[record.pipeline_name].append(
            {"date": record.start_time.isoformat(), "score": score}
        )
    return {"pipelines": by_pipeline}


def _record_has_grch38(record: object) -> bool:
    checks = getattr(record, "checks", [])
    return any("grch38" in str(getattr(check, "evidence", "")).lower() for check in checks)

