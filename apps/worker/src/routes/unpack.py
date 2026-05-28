from fastapi import APIRouter, HTTPException, Query

from src.core.unpack import list_archive_entries, preview_archive_entry
from src.storage.jobs import JobStore

router = APIRouter(prefix="/v1/unpack", tags=["unpack"])
job_store = JobStore()


@router.get("/{job_id}")
def get_unpack_entries(job_id: str) -> dict:
    try:
        source_path = job_store.resolve_input(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Source job not found.") from exc

    entries = list_archive_entries(str(source_path))
    return {
        "jobId": job_id,
        "entries": [entry.model_dump() for entry in entries],
    }


@router.get("/{job_id}/preview")
def get_unpack_preview(job_id: str, path: str = Query(...)) -> dict:
    try:
        source_path = job_store.resolve_input(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Source job not found.") from exc

    preview = preview_archive_entry(str(source_path), path)
    return preview.model_dump()
