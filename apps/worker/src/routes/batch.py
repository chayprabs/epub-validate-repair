from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from src.core.batch import process_batch_archive
from src.storage.jobs import JobStore

router = APIRouter(prefix="/v1", tags=["batch"])
job_store = JobStore()


@router.post("/batch")
async def batch_validate_and_repair(request: Request, file: UploadFile = File(...)) -> dict:
    filename = file.filename or "batch.zip"
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=415, detail="Batch mode expects a ZIP archive of EPUB files.")

    payload = await file.read()
    batch_job_id, _ = job_store.create_job(filename, payload)
    artifact_base_url = str(request.base_url).rstrip("/") + "/v1/artifacts"
    result = process_batch_archive(payload, batch_job_id, artifact_base_url, job_store)
    return result.model_dump()
