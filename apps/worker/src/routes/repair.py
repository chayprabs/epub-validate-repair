from fastapi import APIRouter, HTTPException, Request

from src.core.repair import list_repair_recipes, repair_epub
from src.core.validation import validate_epub
from src.models import RepairRequest, RepairResult
from src.routes.validate import _render_html_report
from src.storage.jobs import JobStore

router = APIRouter(prefix="/v1", tags=["repair"])
job_store = JobStore()


@router.get("/repair/recipes")
def get_repair_recipes() -> dict:
    return {
        "recipes": [recipe.model_dump() for recipe in list_repair_recipes()]
    }


@router.post("/repair")
def repair_file(request: Request, payload: RepairRequest) -> dict:
    try:
        source_path = job_store.resolve_input(payload.jobId)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Source job not found.") from exc

    repaired_bytes = repair_epub(source_path.read_bytes(), payload.fixes)
    repaired_job_id, repaired_path = job_store.create_job(f"repaired-{source_path.name}", repaired_bytes)
    artifacts_base_url = str(request.base_url).rstrip("/") + "/v1/artifacts"
    validation = validate_epub(str(repaired_path), repaired_job_id, artifacts_base_url)
    job_store.write_json_artifact(repaired_job_id, "report.json", validation.model_dump(by_alias=True))
    job_store.write_text_artifact(repaired_job_id, "report.html", _render_html_report(validation.model_dump(by_alias=True)))

    result = RepairResult(
        jobId=repaired_job_id,
        appliedFixes=payload.fixes,
        validation=validation,
    )
    return result.model_dump(by_alias=True)
