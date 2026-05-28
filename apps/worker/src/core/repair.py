from __future__ import annotations

import mimetypes
import posixpath
import zipfile
from io import BytesIO
from pathlib import PurePosixPath
from xml.etree import ElementTree

from lxml import etree, html

from src.models import RepairFixId, RepairRecipe

CONTAINER_PATH = "META-INF/container.xml"
OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
XHTML_NS = "http://www.w3.org/1999/xhtml"
SUPPORTED_REPAIR_RECIPES = [
    RepairRecipe(
        id="manifest-mismatch",
        label="Manifest mismatch",
        description="Add orphaned XHTML, image, font, CSS, NCX, and nav files back to the OPF manifest.",
    ),
    RepairRecipe(
        id="spine-reference",
        label="Broken spine references",
        description="Remove spine entries that point to missing manifest items.",
    ),
    RepairRecipe(
        id="toc-document",
        label="Missing TOC",
        description="Generate a nav.xhtml document and register it in the package manifest.",
    ),
    RepairRecipe(
        id="invalid-xhtml",
        label="Invalid XHTML",
        description="Recover malformed XHTML files using lxml and rewrite them as well-formed XHTML.",
    ),
    RepairRecipe(
        id="mimetype-entry",
        label="Bad mimetype entry",
        description="Rewrite the mimetype record so it is first in the archive and stored uncompressed.",
    ),
    RepairRecipe(
        id="missing-cover",
        label="Missing cover",
        description="Inject a placeholder cover image and declare it in the OPF manifest.",
    ),
    RepairRecipe(
        id="container-xml",
        label="Broken container.xml",
        description="Restore a valid META-INF/container.xml that points at the package document.",
    ),
]

CONTENT_EXTENSIONS = {".xhtml", ".html", ".ncx", ".css", ".svg", ".jpg", ".jpeg", ".png", ".gif", ".ttf", ".otf"}
PLACEHOLDER_COVER = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00" + b"\x08" * 64 + b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01"
    b"\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08"
    b"\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xd2\xcf \xff\xd9"
)


def list_repair_recipes() -> list[RepairRecipe]:
    return SUPPORTED_REPAIR_RECIPES


def repair_epub(epub_bytes: bytes, fixes: list[RepairFixId]) -> bytes:
    archive_map = _read_archive(epub_bytes)
    package_path = _infer_package_path(archive_map)

    if "container-xml" in fixes:
        archive_map[CONTAINER_PATH] = _build_container_xml(package_path).encode("utf-8")

    if "mimetype-entry" in fixes or "mimetype" not in archive_map:
        archive_map["mimetype"] = b"application/epub+zip"

    if package_path not in archive_map:
        raise ValueError("Package document could not be located.")

    package_root = _parse_xml(archive_map[package_path], recover=True)
    package_dir = str(PurePosixPath(package_path).parent)
    if package_dir == ".":
        package_dir = ""

    manifest_root = package_root.find(f"{{{OPF_NS}}}manifest")
    metadata_root = package_root.find(f"{{{OPF_NS}}}metadata")
    spine_root = package_root.find(f"{{{OPF_NS}}}spine")
    if manifest_root is None:
        manifest_root = ElementTree.SubElement(package_root, f"{{{OPF_NS}}}manifest")
    if metadata_root is None:
        metadata_root = ElementTree.SubElement(package_root, f"{{{OPF_NS}}}metadata")
    if spine_root is None:
        spine_root = ElementTree.SubElement(package_root, f"{{{OPF_NS}}}spine")

    manifest_items = manifest_root.findall(f"{{{OPF_NS}}}item")
    manifest_by_id = {item.attrib["id"]: item for item in manifest_items if item.attrib.get("id")}
    manifest_hrefs = {item.attrib["href"] for item in manifest_items if item.attrib.get("href")}

    if "invalid-xhtml" in fixes:
        for archive_name, payload in list(archive_map.items()):
            suffix = PurePosixPath(archive_name).suffix.lower()
            if suffix not in {".xhtml", ".html"}:
                continue
            archive_map[archive_name] = _recover_xhtml(payload)

    if "manifest-mismatch" in fixes:
        for archive_name in sorted(archive_map):
            if archive_name.startswith("META-INF/") or archive_name == "mimetype" or archive_name.endswith("/"):
                continue
            if archive_name == package_path:
                continue
            suffix = PurePosixPath(archive_name).suffix.lower()
            if suffix not in CONTENT_EXTENSIONS:
                continue
            relative_name = posixpath.relpath(archive_name, package_dir) if package_dir else archive_name
            if relative_name in manifest_hrefs:
                continue
            item = ElementTree.SubElement(
                manifest_root,
                f"{{{OPF_NS}}}item",
                {
                    "id": _next_manifest_id(manifest_by_id, PurePosixPath(relative_name).stem),
                    "href": relative_name,
                    "media-type": _guess_media_type(relative_name),
                },
            )
            if relative_name == "nav.xhtml":
                item.set("properties", "nav")
            manifest_by_id[item.attrib["id"]] = item
            manifest_hrefs.add(relative_name)

    if "spine-reference" in fixes:
        for itemref in list(spine_root.findall(f"{{{OPF_NS}}}itemref")):
            idref = itemref.attrib.get("idref")
            if not idref or idref not in manifest_by_id:
                spine_root.remove(itemref)

    if "toc-document" in fixes:
        has_nav = any(
            item.attrib.get("properties") == "nav"
            or item.attrib.get("id") == "nav"
            or item.attrib.get("media-type") == "application/x-dtbncx+xml"
            for item in manifest_root.findall(f"{{{OPF_NS}}}item")
        )
        if not has_nav:
            nav_href = "nav.xhtml"
            nav_archive_path = posixpath.join(package_dir, nav_href) if package_dir else nav_href
            archive_map[nav_archive_path] = _build_nav_document(package_root, manifest_by_id).encode("utf-8")
            item = ElementTree.SubElement(
                manifest_root,
                f"{{{OPF_NS}}}item",
                {
                    "id": _next_manifest_id(manifest_by_id, "nav"),
                    "href": nav_href,
                    "media-type": "application/xhtml+xml",
                    "properties": "nav",
                },
            )
            manifest_by_id[item.attrib["id"]] = item
            manifest_hrefs.add(nav_href)

    if "missing-cover" in fixes:
        has_cover = any(
            item.attrib.get("media-type", "").startswith("image/")
            and item.attrib.get("id", "").lower().startswith("cover")
            for item in manifest_root.findall(f"{{{OPF_NS}}}item")
        )
        if not has_cover:
            cover_href = "images/cover.jpg"
            cover_archive_path = posixpath.join(package_dir, cover_href) if package_dir else cover_href
            archive_map[cover_archive_path] = PLACEHOLDER_COVER
            item = ElementTree.SubElement(
                manifest_root,
                f"{{{OPF_NS}}}item",
                {
                    "id": _next_manifest_id(manifest_by_id, "cover-image"),
                    "href": cover_href,
                    "media-type": "image/jpeg",
                },
            )
            manifest_by_id[item.attrib["id"]] = item
            manifest_hrefs.add(cover_href)
            ElementTree.SubElement(
                metadata_root,
                f"{{{OPF_NS}}}meta",
                {"name": "cover", "content": item.attrib["id"]},
            )

    archive_map[package_path] = ElementTree.tostring(package_root, encoding="utf-8", xml_declaration=True)
    return _write_archive(archive_map)


def _read_archive(epub_bytes: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(BytesIO(epub_bytes), "r") as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.is_dir()}


def _write_archive(files: dict[str, bytes]) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("mimetype", files.get("mimetype", b"application/epub+zip"), compress_type=zipfile.ZIP_STORED)
        for archive_name in sorted(name for name in files if name != "mimetype"):
            archive.writestr(archive_name, files[archive_name], compress_type=zipfile.ZIP_DEFLATED)
    return buffer.getvalue()


def _infer_package_path(archive_map: dict[str, bytes]) -> str:
    container_bytes = archive_map.get(CONTAINER_PATH)
    if container_bytes:
        try:
            container_root = ElementTree.fromstring(container_bytes)
            rootfile = container_root.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
            if rootfile is not None and rootfile.attrib.get("full-path"):
                return rootfile.attrib["full-path"]
        except ElementTree.ParseError:
            pass

    for archive_name in archive_map:
        if archive_name.lower().endswith(".opf"):
            return archive_name
    raise ValueError("No OPF package found in archive.")


def _build_container_xml(package_path: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="{package_path}" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""


def _parse_xml(payload: bytes, recover: bool) -> ElementTree.Element:
    if recover:
        parser = etree.XMLParser(recover=True, resolve_entities=False)
        root = etree.fromstring(payload, parser=parser)
        return ElementTree.fromstring(etree.tostring(root, encoding="utf-8"))
    return ElementTree.fromstring(payload)


def _recover_xhtml(payload: bytes) -> bytes:
    xml_parser = etree.XMLParser(recover=True, resolve_entities=False)
    try:
        root = etree.fromstring(payload, parser=xml_parser)
    except etree.XMLSyntaxError:
        root = html.fromstring(payload)

    if root.tag.lower() != f"{{{XHTML_NS}}}html" and root.tag.lower() != "html":
        document = etree.Element(f"{{{XHTML_NS}}}html", nsmap={None: XHTML_NS})
        body = etree.SubElement(document, f"{{{XHTML_NS}}}body")
        body.append(root)
        root = document

    if root.find(f"{{{XHTML_NS}}}body") is None and root.find("body") is not None:
        root.tag = f"{{{XHTML_NS}}}html"

    return etree.tostring(root, encoding="utf-8", xml_declaration=True, method="xml", pretty_print=True)


def _next_manifest_id(existing: dict[str, ElementTree.Element], seed: str) -> str:
    base = seed.replace(" ", "-").replace("_", "-") or "item"
    candidate = base
    counter = 1
    while candidate in existing:
        counter += 1
        candidate = f"{base}-{counter}"
    return candidate


def _guess_media_type(href: str) -> str:
    if href.endswith(".xhtml") or href.endswith(".html"):
        return "application/xhtml+xml"
    if href.endswith(".ncx"):
        return "application/x-dtbncx+xml"
    guessed = mimetypes.guess_type(href)[0]
    return guessed or "application/octet-stream"


def _build_nav_document(package_root: ElementTree.Element, manifest_by_id: dict[str, ElementTree.Element]) -> str:
    title_node = package_root.find(f".//{{{DC_NS}}}title")
    title = title_node.text.strip() if title_node is not None and title_node.text else "Table of Contents"
    spine_root = package_root.find(f"{{{OPF_NS}}}spine")
    links = []
    if spine_root is not None:
        for itemref in spine_root.findall(f"{{{OPF_NS}}}itemref"):
            manifest_item = manifest_by_id.get(itemref.attrib.get("idref", ""))
            if manifest_item is None:
                continue
            href = manifest_item.attrib.get("href", "")
            label = PurePosixPath(href).stem.replace("-", " ").title() or href
            links.append((href, label))
    if not links:
        links.append(("text/chapter1.xhtml", "Start"))

    list_items = "".join(f'<li><a href="{href}">{label}</a></li>' for href, label in links)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head>
    <title>{title}</title>
  </head>
  <body>
    <nav epub:type="toc">
      <h1>{title}</h1>
      <ol>{list_items}</ol>
    </nav>
  </body>
</html>
"""
