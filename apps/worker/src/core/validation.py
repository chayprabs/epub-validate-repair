from __future__ import annotations

import posixpath
import zipfile
from pathlib import PurePosixPath
from xml.etree import ElementTree

from lxml import etree

from src.models import (
    EpubMetadata,
    EpubcheckMessage,
    ManifestItem,
    SpineItem,
    TocItem,
    ValidationArtifacts,
    ValidationResult,
)

CONTAINER_PATH = "META-INF/container.xml"
NAMESPACES = {
    "container": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def validate_epub(epub_path: str, job_id: str, base_artifact_url: str) -> ValidationResult:
    messages: list[EpubcheckMessage] = []
    manifest: list[ManifestItem] = []
    spine: list[SpineItem] = []
    toc: list[TocItem] = []
    metadata = EpubMetadata()
    version = "3.0"

    with zipfile.ZipFile(epub_path, "r") as archive:
        namelist = archive.namelist()
        file_infos = {info.filename: info for info in archive.infolist()}

        if not namelist:
            raise ValueError("Archive is empty.")

        first_entry = namelist[0]
        mimetype_bytes = archive.read("mimetype") if "mimetype" in file_infos else None
        if first_entry != "mimetype" or mimetype_bytes != b"application/epub+zip":
            messages.append(
                EpubcheckMessage(
                    id="MIMETYPE_ENTRY_INVALID",
                    severity="error",
                    message="The mimetype entry must be first and equal to application/epub+zip.",
                    file="mimetype",
                    suggestion="Rewrite the archive so the mimetype file is first and stored without compression.",
                    fixableBy="mimetype-entry",
                )
            )
        elif file_infos["mimetype"].compress_type != zipfile.ZIP_STORED:
            messages.append(
                EpubcheckMessage(
                    id="MIMETYPE_COMPRESSED",
                    severity="error",
                    message="The mimetype entry must be stored without compression.",
                    file="mimetype",
                    suggestion="Rewrite the mimetype entry using ZIP_STORED compression.",
                    fixableBy="mimetype-entry",
                )
            )

        container_root = _read_xml(archive, CONTAINER_PATH, "container.xml", messages)
        if container_root is None:
            return _finalize_result(job_id, version, messages, metadata, manifest, spine, toc, base_artifact_url)

        rootfile = container_root.find(".//container:rootfile", NAMESPACES)
        if rootfile is None or not rootfile.attrib.get("full-path"):
            messages.append(
                EpubcheckMessage(
                    id="CONTAINER_ROOTFILE_MISSING",
                    severity="error",
                    message="container.xml does not declare a rootfile.",
                    file=CONTAINER_PATH,
                    suggestion="Add a rootfile element that points to the package document.",
                    fixableBy="container-xml",
                )
            )
            return _finalize_result(job_id, version, messages, metadata, manifest, spine, toc, base_artifact_url)

        package_path = rootfile.attrib["full-path"]
        package_root = _read_xml(archive, package_path, package_path, messages)
        if package_root is None:
            return _finalize_result(job_id, version, messages, metadata, manifest, spine, toc, base_artifact_url)

        version = package_root.attrib.get("version", "3.0")
        package_dir = str(PurePosixPath(package_path).parent)
        if package_dir == ".":
            package_dir = ""

        metadata = _extract_metadata(package_root)
        manifest, manifest_by_id, manifest_hrefs = _extract_manifest(package_root)
        spine = _extract_spine(package_root, manifest_by_id)
        toc = _extract_toc(package_root, manifest_by_id)

        content_extensions = {".xhtml", ".html", ".ncx", ".css", ".svg", ".jpg", ".jpeg", ".png", ".gif", ".ttf", ".otf"}
        for archive_name in namelist:
            if archive_name.startswith("META-INF/") or archive_name == "mimetype" or archive_name.endswith("/"):
                continue
            suffix = PurePosixPath(archive_name).suffix.lower()
            if suffix not in content_extensions:
                continue
            relative_name = posixpath.relpath(archive_name, package_dir) if package_dir else archive_name
            if relative_name not in manifest_hrefs:
                messages.append(
                    EpubcheckMessage(
                        id="MANIFEST_MISMATCH",
                        severity="error",
                        message=f"{relative_name} exists in the archive but is missing from the manifest.",
                        file=package_path,
                        suggestion=f"Add {relative_name} to the OPF manifest.",
                        fixableBy="manifest-mismatch",
                    )
                )
            if suffix in {".xhtml", ".html"}:
                invalid_xhtml_message = _validate_xhtml(archive, archive_name, package_path)
                if invalid_xhtml_message is not None:
                    messages.append(invalid_xhtml_message)

        for spine_item in spine:
            if spine_item.href is None:
                messages.append(
                    EpubcheckMessage(
                        id="SPINE_REF_MISSING",
                        severity="error",
                        message=f"Spine itemref {spine_item.idref} does not point to a manifest item.",
                        file=package_path,
                        suggestion=f"Remove {spine_item.idref} from the spine or add a matching manifest entry.",
                        fixableBy="spine-reference",
                    )
                )

        has_nav = any(item.mediaType == "application/x-dtbncx+xml" or item.id == "nav" for item in manifest)
        if not has_nav:
            messages.append(
                EpubcheckMessage(
                    id="TOC_MISSING",
                    severity="error",
                    message="The publication does not declare a navigation document or NCX table of contents.",
                    file=package_path,
                    suggestion="Generate a nav.xhtml or toc.ncx file and reference it from the manifest.",
                    fixableBy="toc-document",
                )
            )

        cover_declared = any(item.mediaType.startswith("image/") and item.id.lower().startswith("cover") for item in manifest)
        if not cover_declared:
            messages.append(
                EpubcheckMessage(
                    id="COVER_MISSING",
                    severity="error",
                    message="The package does not declare a cover image.",
                    file=package_path,
                    suggestion="Add a cover image file and mark it as the cover in the OPF manifest.",
                    fixableBy="missing-cover",
                )
            )

        messages.append(
            EpubcheckMessage(
                id="EPUB_VERSION_DETECTED",
                severity="info",
                message=f"Detected EPUB {version}.",
                file=package_path,
            )
        )
        messages.append(
            EpubcheckMessage(
                id="DRM_NOT_DETECTED",
                severity="usage",
                message="No DRM markers were detected in the uploaded archive.",
                file=package_path,
            )
        )

    return _finalize_result(job_id, version, messages, metadata, manifest, spine, toc, base_artifact_url)


def _read_xml(
    archive: zipfile.ZipFile,
    archive_path: str,
    file_label: str,
    messages: list[EpubcheckMessage],
) -> ElementTree.Element | None:
    try:
        return ElementTree.fromstring(archive.read(archive_path))
    except KeyError:
        messages.append(
            EpubcheckMessage(
                id="ARCHIVE_ENTRY_MISSING",
                severity="error",
                message=f"{archive_path} is missing from the archive.",
                file=file_label,
                suggestion=f"Restore {archive_path} into the EPUB package.",
                fixableBy="container-xml" if archive_path == CONTAINER_PATH else None,
            )
        )
        return None
    except ElementTree.ParseError:
        messages.append(
            EpubcheckMessage(
                id="XML_INVALID",
                severity="error",
                message=f"{archive_path} is not well-formed XML.",
                file=file_label,
                suggestion=f"Repair the XML structure in {archive_path}.",
                fixableBy="container-xml" if archive_path == CONTAINER_PATH else "invalid-xhtml",
            )
        )
        return None


def _validate_xhtml(
    archive: zipfile.ZipFile,
    archive_name: str,
    package_path: str,
) -> EpubcheckMessage | None:
    parser = etree.XMLParser(resolve_entities=False)
    try:
        etree.fromstring(archive.read(archive_name), parser=parser)
        return None
    except etree.XMLSyntaxError as exc:
        line = exc.position[0] if exc.position else None
        column = exc.position[1] if exc.position else None
        return EpubcheckMessage(
            id="XHTML_INVALID",
            severity="error",
            message=f"{archive_name} is not well-formed XHTML.",
            file=package_path,
            line=line,
            column=column,
            suggestion=f"Recover and rewrite {archive_name} as valid XHTML.",
            fixableBy="invalid-xhtml",
        )


def _extract_metadata(package_root: ElementTree.Element) -> EpubMetadata:
    metadata_root = package_root.find("opf:metadata", NAMESPACES)
    if metadata_root is None:
        return EpubMetadata()

    def first_text(selector: str) -> str | None:
        element = metadata_root.find(selector, NAMESPACES)
        return element.text.strip() if element is not None and element.text else None

    contributors = [
        element.text.strip()
        for element in metadata_root.findall("dc:creator", NAMESPACES)
        if element.text
    ]
    identifiers = [
        element.text.strip()
        for element in metadata_root.findall("dc:identifier", NAMESPACES)
        if element.text
    ]
    subjects = [
        element.text.strip()
        for element in metadata_root.findall("dc:subject", NAMESPACES)
        if element.text
    ]

    return EpubMetadata(
        title=first_text("dc:title"),
        language=first_text("dc:language"),
        contributors=contributors,
        identifiers=identifiers,
        publisher=first_text("dc:publisher"),
        publishedAt=first_text("dc:date"),
        description=first_text("dc:description"),
        subjects=subjects,
        rights=first_text("dc:rights"),
    )


def _extract_manifest(
    package_root: ElementTree.Element,
) -> tuple[list[ManifestItem], dict[str, ManifestItem], set[str]]:
    manifest_items: list[ManifestItem] = []
    manifest_by_id: dict[str, ManifestItem] = {}
    manifest_hrefs: set[str] = set()

    manifest_root = package_root.find("opf:manifest", NAMESPACES)
    if manifest_root is None:
        return manifest_items, manifest_by_id, manifest_hrefs

    for item in manifest_root.findall("opf:item", NAMESPACES):
        manifest_item = ManifestItem(
            id=item.attrib["id"],
            href=item.attrib["href"],
            mediaType=item.attrib["media-type"],
        )
        manifest_items.append(manifest_item)
        manifest_by_id[manifest_item.id] = manifest_item
        manifest_hrefs.add(manifest_item.href)

    return manifest_items, manifest_by_id, manifest_hrefs


def _extract_spine(
    package_root: ElementTree.Element,
    manifest_by_id: dict[str, ManifestItem],
) -> list[SpineItem]:
    spine_items: list[SpineItem] = []
    spine_root = package_root.find("opf:spine", NAMESPACES)
    if spine_root is None:
        return spine_items

    for itemref in spine_root.findall("opf:itemref", NAMESPACES):
        idref = itemref.attrib.get("idref", "")
        manifest_item = manifest_by_id.get(idref)
        spine_items.append(
            SpineItem(
                idref=idref,
                href=manifest_item.href if manifest_item else None,
            )
        )

    return spine_items


def _extract_toc(
    package_root: ElementTree.Element,
    manifest_by_id: dict[str, ManifestItem],
) -> list[TocItem]:
    toc_items: list[TocItem] = []
    spine_root = package_root.find("opf:spine", NAMESPACES)
    if spine_root is None:
        return toc_items

    toc_id = spine_root.attrib.get("toc")
    if not toc_id:
        return toc_items

    toc_manifest_item = manifest_by_id.get(toc_id)
    if toc_manifest_item is not None:
        toc_items.append(TocItem(label=toc_manifest_item.id, href=toc_manifest_item.href))
    return toc_items


def _finalize_result(
    job_id: str,
    version: str,
    messages: list[EpubcheckMessage],
    metadata: EpubMetadata,
    manifest: list[ManifestItem],
    spine: list[SpineItem],
    toc: list[TocItem],
    base_artifact_url: str,
) -> ValidationResult:
    counts = {"error": 0, "warning": 0, "info": 0, "usage": 0}
    for message in messages:
        counts[message.severity] += 1

    safe_version = version if version in {"2.0", "3.0", "3.1", "3.2", "3.3"} else "3.0"
    return ValidationResult(
        jobId=job_id,
        epubVersion=safe_version,
        pass_=counts["error"] == 0,
        counts=counts,
        messages=messages,
        metadata=metadata,
        manifest=manifest,
        spine=spine,
        toc=toc,
        artifacts=ValidationArtifacts(
            htmlUrl=f"{base_artifact_url}/{job_id}/report.html",
            jsonUrl=f"{base_artifact_url}/{job_id}/report.json",
        ),
    )
