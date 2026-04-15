"""Dashboard routes for pipeline runs."""

from __future__ import annotations

from fastapi import APIRouter

from helios.core.storage import AuditStorage

router = APIRouter(prefix="/runs", tags=["runs"])
storage = AuditStorage()


@router.get("/")
def list_runs(limit: int = 20) -> list[dict[str, str]]:
    """List recent runs."""
    records = storage.list_records(limit=limit)
    return [
        {
            "run_id": str(record.run_id),
            "pipeline_name": record.pipeline_name,
            "executor": record.executor,
            "start_time": record.start_time.isoformat(),
        }
        for record in records
    ]

