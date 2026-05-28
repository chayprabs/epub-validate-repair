import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.core.diff import diff_epubs

router = APIRouter(prefix="/v1", tags=["diff"])


@router.post("/diff")
async def diff_files(fileA: UploadFile = File(...), fileB: UploadFile = File(...)) -> dict:
    if not fileA.filename or not fileA.filename.lower().endswith(".epub"):
        raise HTTPException(status_code=415, detail="fileA must be an EPUB.")
    if not fileB.filename or not fileB.filename.lower().endswith(".epub"):
        raise HTTPException(status_code=415, detail="fileB must be an EPUB.")

    payload_a = await fileA.read()
    payload_b = await fileB.read()

    with tempfile.TemporaryDirectory(prefix="epubdoctor-diff-") as temp_dir:
        path_a = Path(temp_dir) / "a.epub"
        path_b = Path(temp_dir) / "b.epub"
        path_a.write_bytes(payload_a)
        path_b.write_bytes(payload_b)
        result = diff_epubs(str(path_a), str(path_b))
    return result.model_dump()
