from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.storage.jobs import JobStore

router = APIRouter(prefix="/v1/artifacts", tags=["artifacts"])
job_store = JobStore()


@router.get("/{job_id}/{artifact_name}")
def get_artifact(job_id: str, artifact_name: str) -> FileResponse:
    try:
        artifact_path = job_store.resolve_artifact(job_id, artifact_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Artifact not found.") from exc

    media_type = "application/json" if artifact_path.suffix == ".json" else "text/html"
    return FileResponse(Path(artifact_path), media_type=media_type)
