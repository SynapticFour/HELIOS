"""Dashboard routes for compliance reports."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import cast
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from helios.core.storage import AuditStorage
from helios.export.json_export import _build_ai_act_art11_fragment, export_json
from helios.export.pdf_export import export_pdf
from helios.export.rocrate import export_rocrate

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


def _get_storage(request: Request) -> AuditStorage:
    return cast(AuditStorage, request.app.state.storage)


STORAGE_DEP = Depends(_get_storage)


@router.get("/{run_id}/json")
def report_json(run_id: UUID, storage: AuditStorage = STORAGE_DEP) -> FileResponse:
    """Download JSON compliance report."""
    record = storage.get_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    target = Path(tempfile.gettempdir()) / f"helios-{run_id}.json"
    export_json(record, target)
    return FileResponse(target, filename=f"{run_id}.json", media_type="application/json")


@router.get("/{run_id}/pdf")
def report_pdf(run_id: UUID, storage: AuditStorage = STORAGE_DEP) -> FileResponse:
    """Download PDF compliance report."""
    record = storage.get_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    target = Path(tempfile.gettempdir()) / f"helios-{run_id}.pdf"
    export_pdf(record, target)
    return FileResponse(target, filename=f"{run_id}.pdf", media_type="application/pdf")


@router.get("/{run_id}/rocrate")
def report_rocrate(run_id: UUID, storage: AuditStorage = STORAGE_DEP) -> FileResponse:
    """Download RO-Crate export as a ZIP archive."""
    record = storage.get_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    crate_dir = Path(tempfile.gettempdir()) / f"helios-{run_id}-rocrate"
    export_rocrate(record, crate_dir)
    zip_path = Path(tempfile.gettempdir()) / f"helios-{run_id}-rocrate.zip"
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
        for item in crate_dir.rglob("*"):
            if item.is_file():
                archive.write(item, arcname=item.relative_to(crate_dir))
    return FileResponse(zip_path, filename=f"{run_id}-rocrate.zip", media_type="application/zip")


@router.get("/{run_id}/ai-act")
def report_ai_act(run_id: UUID, storage: AuditStorage = STORAGE_DEP) -> JSONResponse:
    """Download AI Act Article 11 fragment."""
    record = storage.get_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    payload = {"ai_act_art11_fragment": _build_ai_act_art11_fragment(record)}
    return JSONResponse(content=json.loads(json.dumps(payload, default=str)))
