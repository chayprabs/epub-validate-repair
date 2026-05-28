from __future__ import annotations

import posixpath
import zipfile
from pathlib import PurePosixPath
from xml.etree import ElementTree

from lxml import html

from src.core.metadata import extract_metadata
from src.models import ChapterDiff, DiffResult, EpubMetadata, MetadataChange, StructureChange

CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"


def diff_epubs(path_a: str, path_b: str) -> DiffResult:
    snapshot_a = _snapshot_epub(path_a)
    snapshot_b = _snapshot_epub(path_b)
    return DiffResult(
        structure=_diff_structure(snapshot_a["files"], snapshot_b["files"]),
        metadata=_diff_metadata(snapshot_a["metadata"], snapshot_b["metadata"]),
        chapters=_diff_chapters(snapshot_a["chapters"], snapshot_b["chapters"]),
    )


def _snapshot_epub(epub_path: str) -> dict:
    with zipfile.ZipFile(epub_path, "r") as archive:
        files = {
            info.filename: archive.read(info.filename)
            for info in archive.infolist()
            if not info.is_dir()
        }
        package_path = _package_path(files)
        package_root = ElementTree.fromstring(files[package_path])
        metadata = extract_metadata(package_root)
        package_dir = str(PurePosixPath(package_path).parent)
        if package_dir == ".":
            package_dir = ""
        chapters = {}
        for archive_name, payload in files.items():
            suffix = PurePosixPath(archive_name).suffix.lower()
            if suffix not in {".xhtml", ".html"}:
                continue
            relative_name = posixpath.relpath(archive_name, package_dir) if package_dir else archive_name
            chapters[relative_name] = _chapter_text(payload)
        return {
            "files": files,
            "metadata": metadata,
            "chapters": chapters,
        }


def _package_path(files: dict[str, bytes]) -> str:
    container_root = ElementTree.fromstring(files["META-INF/container.xml"])
    rootfile = container_root.find(f".//{{{CONTAINER_NS}}}rootfile")
    if rootfile is None or not rootfile.attrib.get("full-path"):
        raise ValueError("EPUB is missing a package rootfile.")
    return rootfile.attrib["full-path"]


def _chapter_text(payload: bytes) -> str:
    document = html.fromstring(payload)
    return " ".join(part.strip() for part in document.xpath("//body//text()") if part.strip())


def _diff_structure(files_a: dict[str, bytes], files_b: dict[str, bytes]) -> list[StructureChange]:
    changes: list[StructureChange] = []
    for path in sorted(set(files_a) | set(files_b)):
        if path not in files_a:
            changes.append(StructureChange(path=path, change="added"))
        elif path not in files_b:
            changes.append(StructureChange(path=path, change="removed"))
        elif files_a[path] != files_b[path]:
            changes.append(StructureChange(path=path, change="changed"))
    return changes


def _diff_metadata(metadata_a: EpubMetadata, metadata_b: EpubMetadata) -> list[MetadataChange]:
    comparable_a = {
        "title": metadata_a.title,
        "subtitle": metadata_a.subtitle,
        "language": metadata_a.language,
        "publisher": metadata_a.publisher,
        "publishedAt": metadata_a.publishedAt,
        "description": metadata_a.description,
        "rights": metadata_a.rights,
        "series": metadata_a.series,
        "seriesIndex": metadata_a.seriesIndex,
        "contributors": "|".join(f"{item.name}:{item.role}" for item in metadata_a.contributors),
        "identifiers": "|".join(f"{item.type}:{item.value}" for item in metadata_a.identifiers),
        "subjects": "|".join(metadata_a.subjects),
        "custom": "|".join(f"{key}={value}" for key, value in sorted(metadata_a.custom.items())),
    }
    comparable_b = {
        "title": metadata_b.title,
        "subtitle": metadata_b.subtitle,
        "language": metadata_b.language,
        "publisher": metadata_b.publisher,
        "publishedAt": metadata_b.publishedAt,
        "description": metadata_b.description,
        "rights": metadata_b.rights,
        "series": metadata_b.series,
        "seriesIndex": metadata_b.seriesIndex,
        "contributors": "|".join(f"{item.name}:{item.role}" for item in metadata_b.contributors),
        "identifiers": "|".join(f"{item.type}:{item.value}" for item in metadata_b.identifiers),
        "subjects": "|".join(metadata_b.subjects),
        "custom": "|".join(f"{key}={value}" for key, value in sorted(metadata_b.custom.items())),
    }
    changes: list[MetadataChange] = []
    for field in comparable_a:
        if comparable_a[field] != comparable_b[field]:
            changes.append(
                MetadataChange(
                    field=field,
                    before=comparable_a[field],
                    after=comparable_b[field],
                )
            )
    return changes


def _diff_chapters(chapters_a: dict[str, str], chapters_b: dict[str, str]) -> list[ChapterDiff]:
    diffs: list[ChapterDiff] = []
    for path in sorted(set(chapters_a) | set(chapters_b)):
        before = chapters_a.get(path)
        after = chapters_b.get(path)
        if before != after:
            diffs.append(ChapterDiff(path=path, before=before, after=after))
    return diffs
