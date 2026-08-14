"""Dashboard routes for compliance reports."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask

from helios.config import HeliosSettings
from helios.core.storage import AuditStorage
from helios.dashboard.deps import get_settings, get_storage
from helios.export.json_export import _build_ai_act_art11_fragment, export_json
from helios.export.pdf_export import export_pdf
from helios.export.rocrate import export_rocrate

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


STORAGE_DEP = Depends(get_storage)
SETTINGS_DEP = Depends(get_settings)


def _temp_path(prefix: str, suffix: str) -> Path:
    handle, name = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    os.close(handle)
    return Path(name)


def _cleanup(*paths: Path) -> None:
    for path in paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink(missing_ok=True)


@router.get("/{run_id}/json")
def report_json(
    run_id: UUID,
    storage: AuditStorage = STORAGE_DEP,
    settings: HeliosSettings = SETTINGS_DEP,
) -> FileResponse:
    """Download JSON compliance report."""
    record = storage.get_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    target = _temp_path(f"helios-{run_id}-", ".json")
    export_json(record, target, include_ai_act=settings.export.ai_act_fragment)
    return FileResponse(
        target,
        filename=f"{run_id}.json",
        media_type="application/json",
        background=BackgroundTask(_cleanup, target),
    )


@router.get("/{run_id}/pdf")
def report_pdf(run_id: UUID, storage: AuditStorage = STORAGE_DEP) -> FileResponse:
    """Download PDF compliance report."""
    record = storage.get_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    target = _temp_path(f"helios-{run_id}-", ".pdf")
    export_pdf(record, target)
    return FileResponse(
        target,
        filename=f"{run_id}.pdf",
        media_type="application/pdf",
        background=BackgroundTask(_cleanup, target),
    )


@router.get("/{run_id}/rocrate")
def report_rocrate(run_id: UUID, storage: AuditStorage = STORAGE_DEP) -> FileResponse:
    """Download RO-Crate export as a ZIP archive."""
    record = storage.get_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    crate_dir = Path(tempfile.mkdtemp(prefix=f"helios-{run_id}-rocrate-"))
    export_rocrate(record, crate_dir)
    zip_path = _temp_path(f"helios-{run_id}-", ".zip")
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
        for item in crate_dir.rglob("*"):
            if item.is_file():
                archive.write(item, arcname=item.relative_to(crate_dir))
    return FileResponse(
        zip_path,
        filename=f"{run_id}-rocrate.zip",
        media_type="application/zip",
        background=BackgroundTask(_cleanup, zip_path, crate_dir),
    )


@router.get("/{run_id}/ai-act")
def report_ai_act(run_id: UUID, storage: AuditStorage = STORAGE_DEP) -> JSONResponse:
    """Download AI Act Article 11 fragment (explicit request; not a risk classification)."""
    record = storage.get_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    payload = {"ai_act_art11_fragment": _build_ai_act_art11_fragment(record)}
    return JSONResponse(content=json.loads(json.dumps(payload, default=str)))
