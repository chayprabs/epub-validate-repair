from fastapi import APIRouter, HTTPException, Request

from src.core.metadata import apply_metadata_updates
from src.core.validation import validate_epub
from src.models import MetadataUpdateRequest, MetadataUpdateResult
from src.routes.validate import _render_html_report
from src.storage.jobs import JobStore

router = APIRouter(prefix="/v1", tags=["metadata"])
job_store = JobStore()


@router.post("/metadata")
def update_metadata(request: Request, payload: MetadataUpdateRequest) -> dict:
    try:
        source_path = job_store.resolve_input(payload.jobId)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Source job not found.") from exc

    updated_bytes = apply_metadata_updates(
        source_path.read_bytes(),
        payload.metadata,
        cover_image_data_url=payload.coverImageDataUrl,
        cover_preset=payload.coverPreset,
    )
    updated_job_id, updated_path = job_store.create_job(f"metadata-{source_path.name}", updated_bytes)
    artifacts_base_url = str(request.base_url).rstrip("/") + "/v1/artifacts"
    validation = validate_epub(str(updated_path), updated_job_id, artifacts_base_url)
    job_store.write_json_artifact(updated_job_id, "report.json", validation.model_dump(by_alias=True))
    job_store.write_text_artifact(updated_job_id, "report.html", _render_html_report(validation.model_dump(by_alias=True)))

    result = MetadataUpdateResult(
        jobId=updated_job_id,
        validation=validation,
    )
    return result.model_dump(by_alias=True)
