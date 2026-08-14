"""Dashboard routes for pipeline runs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

from helios.checks import get_check_registry
from helios.config import HeliosSettings
from helios.core.audit_record import AuditRecord
from helios.core.storage import AuditStorage
from helios.dashboard.deps import get_settings, get_storage
from helios.dashboard.models import DeleteResponse, RunImportResponse, RunListItem

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])

STORAGE_DEP = Depends(get_storage)
SETTINGS_DEP = Depends(get_settings)
IMPORT_FILE = File(...)


def _item_for_record(record: AuditRecord) -> RunListItem:
    registry = get_check_registry()
    computed = registry.compute_score(record.checks)
    return RunListItem(
        run_id=str(record.run_id),
        pipeline_name=record.pipeline_name,
        executor=record.executor,
        start_time=record.start_time.isoformat(),
        score=computed.score,
        status=_status_for_record(record),
    )


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
    storage = get_storage(request)
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    if status is None and min_score is None:
        records = storage.list_records(
            limit=limit,
            offset=offset,
            pipeline_filter=pipeline,
            start_time=start,
            end_time=end,
        )
        return [_item_for_record(record) for record in records]

    matched: list[RunListItem] = []
    scanned = 0
    page_size = 200
    page_offset = 0
    max_scan = 50_000
    while scanned < max_scan:
        batch = storage.list_records(
            limit=page_size,
            offset=page_offset,
            pipeline_filter=pipeline,
            start_time=start,
            end_time=end,
        )
        if not batch:
            break
        scanned += len(batch)
        page_offset += len(batch)
        for record in batch:
            item = _item_for_record(record)
            if status and item.status != status:
                continue
            if min_score is not None and (item.score is None or item.score < min_score):
                continue
            matched.append(item)
        if len(matched) >= offset + limit:
            break
    return matched[offset : offset + limit]


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
    return get_check_registry().compute_score(record.checks).model_dump(mode="json")


@router.post("/import")
async def import_run(
    file: UploadFile = IMPORT_FILE,
    storage: AuditStorage = STORAGE_DEP,
    settings: HeliosSettings = SETTINGS_DEP,
    allow_unsigned: bool = Query(False),
) -> RunImportResponse:
    """Import an AuditRecord JSON file.

    Signed records must verify against the operator trust store. Unsigned
    records require ``allow_unsigned=true``.
    """
    max_bytes = settings.dashboard.max_import_bytes
    raw = await file.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Import exceeds max_import_bytes ({max_bytes}).",
        )
    record = AuditRecord.model_validate_json(raw)
    if record.signature is None:
        if not allow_unsigned:
            raise HTTPException(
                status_code=400,
                detail="Unsigned audit records require allow_unsigned=true.",
            )
    elif not record.verify_signature(trusted_keys_dir=settings.trusted_keys_dir):
        raise HTTPException(
            status_code=400,
            detail="Audit record signature is invalid or the signer is not trusted.",
        )
    try:
        storage.save_record(record)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RunImportResponse(run_id=str(record.run_id))


@router.delete("/{run_id}")
def delete_run(
    run_id: UUID,
    storage: AuditStorage = STORAGE_DEP,
    settings: HeliosSettings = SETTINGS_DEP,
) -> DeleteResponse:
    """Delete a run record by ID when dashboard.allow_delete is enabled."""
    if not settings.dashboard.allow_delete:
        raise HTTPException(
            status_code=403,
            detail="Record deletion is disabled. Set dashboard.allow_delete = true to enable.",
        )
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
