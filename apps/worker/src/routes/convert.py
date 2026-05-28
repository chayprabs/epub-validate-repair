import io
import zipfile

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from src.core.calibre import convert_ebook
from src.core.validation import detect_drm_markers
from src.models import ConversionOptions, ConversionResult
from src.storage.jobs import JobStore

router = APIRouter(prefix="/v1", tags=["convert"])
job_store = JobStore()


@router.post("/convert")
async def convert_file(
    request: Request,
    file: UploadFile | None = File(default=None),
    jobId: str | None = Form(default=None),
    target: str | None = Form(default=None),
    tocDepth: int | None = Form(default=None),
    embedFonts: bool | None = Form(default=None),
    stripCss: bool | None = Form(default=None),
    pageSize: str | None = Form(default=None),
) -> dict:
    if file is not None or request.headers.get("content-type", "").startswith("multipart/form-data"):
        conversion_target = _parse_target(target)
        options = ConversionOptions(
            tocDepth=tocDepth,
            embedFonts=bool(embedFonts),
            stripCss=bool(stripCss),
            pageSize=pageSize,
        )
        source_path = await _resolve_uploaded_source(file)
    else:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Invalid conversion request.")
        job_id = payload.get("jobId")
        conversion_target = _parse_target(payload.get("target"))
        options = ConversionOptions.model_validate(payload.get("options") or {})
        try:
            source_path = job_store.resolve_input(job_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Source job not found.") from exc

    try:
        converted_bytes, log = convert_ebook(source_path, conversion_target, options)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=424, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=424, detail=str(exc)) from exc

    converted_job_id, _ = job_store.create_job(f"converted.{conversion_target}", converted_bytes)
    artifact_name = f"converted.{conversion_target}"
    job_store.write_binary_artifact(converted_job_id, artifact_name, converted_bytes)
    artifact_base_url = str(request.base_url).rstrip("/") + "/v1/artifacts"
    result = ConversionResult(
        jobId=converted_job_id,
        target=conversion_target,
        artifactUrl=f"{artifact_base_url}/{converted_job_id}/{artifact_name}",
        log=log,
    )
    return result.model_dump()


def _parse_target(value: str | None) -> str:
    if value not in {"epub", "mobi", "azw3", "pdf", "html"}:
        raise HTTPException(status_code=400, detail="Conversion target is required.")
    return value


async def _resolve_uploaded_source(file: UploadFile | None):
    if file is None:
        raise HTTPException(status_code=400, detail="Provide either a source job or a source file.")

    filename = file.filename or "upload.bin"
    payload = await file.read()
    if not filename.lower().endswith((".epub", ".mobi", ".azw3", ".html", ".htm", ".pdf")):
        raise HTTPException(status_code=415, detail="Unsupported conversion input format.")
    if filename.lower().endswith(".epub"):
        if _uploaded_epub_is_drm_protected(payload):
            raise HTTPException(
                status_code=400,
                detail="This ebook appears to be DRM-protected. EpubDoctor only works with DRM-free files.",
            )

    _, source_path = job_store.create_job(filename, payload)
    return source_path


def _uploaded_epub_is_drm_protected(payload: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            return detect_drm_markers(archive.namelist())
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Uploaded EPUB file is malformed.") from exc
