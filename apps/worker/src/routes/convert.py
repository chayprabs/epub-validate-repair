import mimetypes

from fastapi import APIRouter, HTTPException, Request

from src.core.calibre import convert_ebook
from src.models import ConversionRequest, ConversionResult
from src.storage.jobs import JobStore

router = APIRouter(prefix="/v1", tags=["convert"])
job_store = JobStore()


@router.post("/convert")
def convert_file(request: Request, payload: ConversionRequest) -> dict:
    try:
        source_path = job_store.resolve_input(payload.jobId)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Source job not found.") from exc

    try:
        converted_bytes, log = convert_ebook(source_path, payload.target, payload.options)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=424, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=424, detail=str(exc)) from exc

    converted_job_id, _ = job_store.create_job(f"converted.{payload.target}", converted_bytes)
    artifact_name = f"converted.{payload.target}"
    job_store.write_binary_artifact(converted_job_id, artifact_name, converted_bytes)
    artifact_base_url = str(request.base_url).rstrip("/") + "/v1/artifacts"
    result = ConversionResult(
        jobId=converted_job_id,
        target=payload.target,
        artifactUrl=f"{artifact_base_url}/{converted_job_id}/{artifact_name}",
        log=log,
    )
    return result.model_dump()
