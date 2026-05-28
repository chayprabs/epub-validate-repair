from __future__ import annotations

import base64
import mimetypes
import posixpath
import re
import zipfile
from io import BytesIO
from pathlib import PurePosixPath
from xml.etree import ElementTree

from PIL import Image, ImageOps

from src.models import Contributor, CoverPreset, EpubMetadata, Identifier

CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
NAMESPACES = {
    "container": CONTAINER_NS,
    "opf": OPF_NS,
    "dc": DC_NS,
}
KNOWN_META_NAMES = {
    "subtitle",
    "calibre:series",
    "calibre:series_index",
    "cover",
}
ROLE_ATTR = f"{{{OPF_NS}}}role"
FILE_AS_ATTR = f"{{{OPF_NS}}}file-as"
COVER_PRESETS: dict[CoverPreset, tuple[int, int]] = {
    "kdp": (1600, 2560),
    "apple": (1400, 1873),
    "kobo": (1600, 2400),
}


def extract_metadata(package_root: ElementTree.Element) -> EpubMetadata:
    metadata_root = package_root.find("opf:metadata", NAMESPACES)
    if metadata_root is None:
        return EpubMetadata()

    titles = [
        element.text.strip()
        for element in metadata_root.findall("dc:title", NAMESPACES)
        if element.text and element.text.strip()
    ]
    subtitle = _get_named_meta(metadata_root, "subtitle")
    contributors: list[Contributor] = []
    for selector, default_role in (("dc:creator", "aut"), ("dc:contributor", "ctb")):
        for element in metadata_root.findall(selector, NAMESPACES):
            if not element.text or not element.text.strip():
                continue
            contributors.append(
                Contributor(
                    name=element.text.strip(),
                    role=element.attrib.get(ROLE_ATTR, element.attrib.get("role", default_role)),
                )
            )
    identifiers = [
        Identifier(
            type=_detect_identifier_type(element.text.strip(), element.attrib.get("id")),
            value=element.text.strip(),
        )
        for element in metadata_root.findall("dc:identifier", NAMESPACES)
        if element.text and element.text.strip()
    ]
    subjects = [
        element.text.strip()
        for element in metadata_root.findall("dc:subject", NAMESPACES)
        if element.text and element.text.strip()
    ]
    custom = {
        element.attrib["name"]: element.attrib.get("content", "")
        for element in metadata_root.findall("opf:meta", NAMESPACES)
        if element.attrib.get("name") and element.attrib["name"] not in KNOWN_META_NAMES
    }

    return EpubMetadata(
        title=titles[0] if titles else None,
        subtitle=subtitle or (titles[1] if len(titles) > 1 else None),
        contributors=contributors,
        language=_first_text(metadata_root, "dc:language"),
        identifiers=identifiers,
        publisher=_first_text(metadata_root, "dc:publisher"),
        publishedAt=_first_text(metadata_root, "dc:date"),
        description=_first_text(metadata_root, "dc:description"),
        subjects=subjects,
        rights=_first_text(metadata_root, "dc:rights"),
        series=_get_named_meta(metadata_root, "calibre:series"),
        seriesIndex=_get_named_meta(metadata_root, "calibre:series_index"),
        custom=custom,
    )


def apply_metadata_updates(
    epub_bytes: bytes,
    metadata: EpubMetadata,
    cover_image_data_url: str | None = None,
    cover_preset: CoverPreset = "kdp",
) -> bytes:
    archive_map = _read_archive(epub_bytes)
    package_path = _infer_package_path(archive_map)
    package_root = ElementTree.fromstring(archive_map[package_path])
    package_dir = str(PurePosixPath(package_path).parent)
    if package_dir == ".":
        package_dir = ""

    metadata_root = package_root.find(f"{{{OPF_NS}}}metadata")
    manifest_root = package_root.find(f"{{{OPF_NS}}}manifest")
    if metadata_root is None:
        metadata_root = ElementTree.SubElement(package_root, f"{{{OPF_NS}}}metadata")
    if manifest_root is None:
        manifest_root = ElementTree.SubElement(package_root, f"{{{OPF_NS}}}manifest")

    _remove_existing_metadata(metadata_root)
    _write_dc_text(metadata_root, "title", metadata.title)
    _write_named_meta(metadata_root, "subtitle", metadata.subtitle)

    for contributor in metadata.contributors:
        tag = "creator" if contributor.role == "aut" else "contributor"
        element = ElementTree.SubElement(metadata_root, f"{{{DC_NS}}}{tag}")
        element.text = contributor.name
        element.set(ROLE_ATTR, contributor.role)

    _write_dc_text(metadata_root, "language", metadata.language)
    for index, identifier in enumerate(metadata.identifiers, start=1):
        element = ElementTree.SubElement(metadata_root, f"{{{DC_NS}}}identifier", {"id": f"id-{index}"})
        element.text = identifier.value
    _write_dc_text(metadata_root, "publisher", metadata.publisher)
    _write_dc_text(metadata_root, "date", metadata.publishedAt)
    _write_dc_text(metadata_root, "description", metadata.description)
    for subject in metadata.subjects:
        _write_dc_text(metadata_root, "subject", subject)
    _write_dc_text(metadata_root, "rights", metadata.rights)
    _write_named_meta(metadata_root, "calibre:series", metadata.series)
    _write_named_meta(metadata_root, "calibre:series_index", metadata.seriesIndex)

    for key, value in metadata.custom.items():
        if key in KNOWN_META_NAMES:
            continue
        _write_named_meta(metadata_root, key, value)

    if cover_image_data_url:
        cover_bytes = _resize_cover(_decode_data_url(cover_image_data_url), cover_preset)
        cover_href = _upsert_cover(metadata_root, manifest_root, archive_map, package_dir, cover_bytes)
        _write_named_meta(metadata_root, "cover", cover_href["id"])

    archive_map[package_path] = ElementTree.tostring(package_root, encoding="utf-8", xml_declaration=True)
    return _write_archive(archive_map)


def _first_text(metadata_root: ElementTree.Element, selector: str) -> str | None:
    element = metadata_root.find(selector, NAMESPACES)
    return element.text.strip() if element is not None and element.text and element.text.strip() else None


def _get_named_meta(metadata_root: ElementTree.Element, name: str) -> str | None:
    for element in metadata_root.findall("opf:meta", NAMESPACES):
        if element.attrib.get("name") == name:
            content = element.attrib.get("content", "").strip()
            return content or None
    return None


def _detect_identifier_type(value: str, element_id: str | None) -> str:
    normalized = value.lower().strip()
    digits_only = re.sub(r"[^0-9xX]", "", value)
    if normalized.startswith("10."):
        return "doi"
    if normalized.startswith("urn:uuid:") or re.fullmatch(r"[0-9a-fA-F-]{32,36}", value):
        return "uuid"
    if len(digits_only) == 13 and digits_only.isdigit():
        return "isbn-13"
    if len(digits_only) == 10:
        return "isbn-10"
    if element_id:
        return element_id
    return "identifier"


def _remove_existing_metadata(metadata_root: ElementTree.Element) -> None:
    for element in list(metadata_root):
        tag = element.tag
        if tag in {
            f"{{{DC_NS}}}title",
            f"{{{DC_NS}}}creator",
            f"{{{DC_NS}}}contributor",
            f"{{{DC_NS}}}language",
            f"{{{DC_NS}}}identifier",
            f"{{{DC_NS}}}publisher",
            f"{{{DC_NS}}}date",
            f"{{{DC_NS}}}description",
            f"{{{DC_NS}}}subject",
            f"{{{DC_NS}}}rights",
        }:
            metadata_root.remove(element)
            continue
        if tag == f"{{{OPF_NS}}}meta" and element.attrib.get("name"):
            metadata_root.remove(element)


def _write_dc_text(metadata_root: ElementTree.Element, tag_name: str, value: str | None) -> None:
    if not value:
        return
    element = ElementTree.SubElement(metadata_root, f"{{{DC_NS}}}{tag_name}")
    element.text = value


def _write_named_meta(metadata_root: ElementTree.Element, name: str, value: str | None) -> None:
    if not value:
        return
    ElementTree.SubElement(metadata_root, f"{{{OPF_NS}}}meta", {"name": name, "content": value})


def _read_archive(epub_bytes: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(BytesIO(epub_bytes), "r") as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.is_dir()}


def _write_archive(files: dict[str, bytes]) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        mimetype_payload = files.get("mimetype", b"application/epub+zip")
        archive.writestr("mimetype", mimetype_payload, compress_type=zipfile.ZIP_STORED)
        for archive_name in sorted(name for name in files if name != "mimetype"):
            archive.writestr(archive_name, files[archive_name], compress_type=zipfile.ZIP_DEFLATED)
    return buffer.getvalue()


def _infer_package_path(archive_map: dict[str, bytes]) -> str:
    container_bytes = archive_map.get("META-INF/container.xml")
    if container_bytes:
        try:
            container_root = ElementTree.fromstring(container_bytes)
            rootfile = container_root.find(".//container:rootfile", NAMESPACES)
            if rootfile is not None and rootfile.attrib.get("full-path"):
                return rootfile.attrib["full-path"]
        except ElementTree.ParseError:
            pass

    for archive_name in archive_map:
        if archive_name.lower().endswith(".opf"):
            return archive_name
    raise ValueError("No package document found.")


def _decode_data_url(data_url: str) -> bytes:
    if "," not in data_url:
        raise ValueError("Invalid data URL.")
    _, encoded = data_url.split(",", 1)
    return base64.b64decode(encoded)


def _resize_cover(payload: bytes, preset: CoverPreset) -> bytes:
    target_size = COVER_PRESETS[preset]
    source = Image.open(BytesIO(payload)).convert("RGB")
    fitted = ImageOps.fit(source, target_size, method=Image.Resampling.LANCZOS)
    output = BytesIO()
    fitted.save(output, format="JPEG", quality=90)
    return output.getvalue()


def _upsert_cover(
    metadata_root: ElementTree.Element,
    manifest_root: ElementTree.Element,
    archive_map: dict[str, bytes],
    package_dir: str,
    cover_bytes: bytes,
) -> dict[str, str]:
    cover_item = None
    for item in manifest_root.findall(f"{{{OPF_NS}}}item"):
        if item.attrib.get("id", "").lower().startswith("cover"):
            cover_item = item
            break

    if cover_item is None:
        cover_href = "images/cover.jpg"
        cover_item = ElementTree.SubElement(
            manifest_root,
            f"{{{OPF_NS}}}item",
            {
                "id": "cover-image",
                "href": cover_href,
                "media-type": "image/jpeg",
            },
        )
    else:
        cover_href = cover_item.attrib.get("href", "images/cover.jpg")
        cover_item.set("media-type", "image/jpeg")

    archive_path = posixpath.join(package_dir, cover_href) if package_dir else cover_href
    archive_map[archive_path] = cover_bytes
    return {"id": cover_item.attrib["id"], "href": cover_href}
