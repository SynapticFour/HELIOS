"""Dashboard routes for pipeline runs."""

from __future__ import annotations

from datetime import datetime
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

from helios.checks import CheckRegistry
from helios.core.audit_record import AuditRecord
from helios.core.storage import AuditStorage
from helios.dashboard.models import DeleteResponse, RunImportResponse, RunListItem

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


def _get_storage(request: Request) -> AuditStorage:
    return cast(AuditStorage, request.app.state.storage)


STORAGE_DEP = Depends(_get_storage)
IMPORT_FILE = File(...)


@router.get("")
def list_runs(
    request: Request,
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    pipeline: str | None = Query(None),
    status: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    min_score: int | None = Query(None, ge=0, le=100),
) -> list[RunListItem]:
    """List runs with pagination and optional filters."""
    storage = _get_storage(request)
    records = storage.list_records(limit=limit)
    if pipeline:
        records = [record for record in records if record.pipeline_name == pipeline]
    if status:
        records = [record for record in records if _status_for_record(record) == status]
    if start_date:
        start = datetime.fromisoformat(start_date)
        records = [record for record in records if record.start_time >= start]
    if end_date:
        end = datetime.fromisoformat(end_date)
        records = [record for record in records if record.start_time <= end]
    records = records[offset:]
    payload: list[RunListItem] = []
    for record in records:
        score = CheckRegistry().compute_score(record.checks).score
        payload.append(
            RunListItem(
                run_id=str(record.run_id),
                pipeline_name=record.pipeline_name,
                executor=record.executor,
                start_time=record.start_time.isoformat(),
                score=score,
                status=_status_for_record(record),
            )
        )
    if min_score is not None:
        payload = [item for item in payload if item.score >= min_score]
    return payload


@router.get("/{run_id}")
def get_run(run_id: UUID, storage: AuditStorage = STORAGE_DEP) -> dict[str, object]:
    """Return full AuditRecord for a run."""
    record = storage.get_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return record.model_dump(mode="json")


@router.get("/{run_id}/score")
def get_run_score(run_id: UUID, storage: AuditStorage = STORAGE_DEP) -> dict[str, object]:
    """Return compliance score payload for a run."""
    record = storage.get_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return CheckRegistry().compute_score(record.checks).model_dump(mode="json")


@router.post("/import")
async def import_run(
    file: UploadFile = IMPORT_FILE,
    storage: AuditStorage = STORAGE_DEP,
) -> RunImportResponse:
    """Import an AuditRecord JSON file."""
    raw = await file.read()
    record = AuditRecord.model_validate_json(raw)
    storage.save_record(record)
    return RunImportResponse(run_id=str(record.run_id))


@router.delete("/{run_id}")
def delete_run(run_id: UUID, storage: AuditStorage = STORAGE_DEP) -> DeleteResponse:
    """Delete a run record by ID."""
    deleted = storage.delete_record(run_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Run not found")
    return DeleteResponse(deleted=True)


def _status_for_record(record: AuditRecord) -> str:
    if any(check.status == "fail" for check in record.checks):
        return "fail"
    if any(check.status == "warn" for check in record.checks):
        return "warn"
    return "pass"

