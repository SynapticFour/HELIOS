"""Dashboard routes for compliance reports."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from helios.core.storage import AuditStorage

router = APIRouter(prefix="/reports", tags=["reports"])
storage = AuditStorage()


@router.get("/{run_id}")
def get_report(run_id: UUID) -> dict[str, object]:
    """Return full audit report for a run id."""
    record = storage.get_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return record.model_dump(mode="json")

