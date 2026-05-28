from __future__ import annotations

import base64
import mimetypes
import zipfile
from pathlib import PurePosixPath

from src.models import UnpackEntry, UnpackPreview


def list_archive_entries(epub_path: str) -> list[UnpackEntry]:
    with zipfile.ZipFile(epub_path, "r") as archive:
        entries = [
            UnpackEntry(
                path=info.filename,
                kind=_classify_path(info.filename),
                size=info.file_size,
            )
            for info in archive.infolist()
            if not info.is_dir()
        ]
    return sorted(entries, key=lambda entry: entry.path)


def preview_archive_entry(epub_path: str, archive_path: str) -> UnpackPreview:
    with zipfile.ZipFile(epub_path, "r") as archive:
        payload = archive.read(archive_path)

    kind = _classify_path(archive_path)
    if kind == "image":
        mime_type = mimetypes.guess_type(archive_path)[0] or "application/octet-stream"
        return UnpackPreview(
            path=archive_path,
            kind=kind,
            dataUrl=f"data:{mime_type};base64,{base64.b64encode(payload).decode('ascii')}",
        )

    text = payload.decode("utf-8", errors="replace")
    return UnpackPreview(
        path=archive_path,
        kind=kind,
        text=text,
    )


def _classify_path(archive_path: str) -> str:
    suffix = PurePosixPath(archive_path).suffix.lower()
    if suffix in {".xhtml", ".html"}:
        return "xhtml"
    if suffix == ".css":
        return "css"
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
        return "image"
    if suffix == ".opf":
        return "opf"
    if suffix == ".ncx":
        return "ncx"
    if suffix in {".xml"}:
        return "xml"
    if suffix in {".ttf", ".otf", ".woff", ".woff2"}:
        return "font"
    if suffix in {".txt", ".md"}:
        return "text"
    return "binary"
