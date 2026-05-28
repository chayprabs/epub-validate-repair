from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile
from xml.etree import ElementTree


def extract_epub_metadata(source_path: Path) -> dict:
    with ZipFile(source_path, "r") as archive:
        container_root = ElementTree.fromstring(archive.read("META-INF/container.xml"))
        rootfile = container_root.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
        package_path = rootfile.attrib["full-path"]
        package_root = ElementTree.fromstring(archive.read(package_path))
        metadata_root = package_root.find("{http://www.idpf.org/2007/opf}metadata")
        title = metadata_root.find("{http://purl.org/dc/elements/1.1/}title").text
        creators = [
            {
                "name": element.text,
                "role": element.attrib.get("{http://www.idpf.org/2007/opf}role", "aut"),
            }
            for element in metadata_root.findall("{http://purl.org/dc/elements/1.1/}creator")
        ]
        identifiers = [
            {
                "type": "identifier",
                "value": element.text,
            }
            for element in metadata_root.findall("{http://purl.org/dc/elements/1.1/}identifier")
        ]
        return {
            "title": title,
            "contributors": creators,
            "identifiers": identifiers,
        }


def write_epub(target_path: Path, metadata: dict) -> None:
    with ZipFile(target_path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=ZIP_STORED)
        archive.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
            compress_type=ZIP_DEFLATED,
        )
        creators = "".join(
            f'<dc:creator opf:role="{contributor["role"]}">{contributor["name"]}</dc:creator>'
            for contributor in metadata["contributors"]
        )
        identifiers = "".join(
            f'<dc:identifier id="id-{index}">{identifier["value"]}</dc:identifier>'
            for index, identifier in enumerate(metadata["identifiers"], start=1)
        )
        archive.writestr(
            "EPUB/package.opf",
            f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" xmlns:opf="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{metadata["title"]}</dc:title>
    {creators}
    <dc:language>en</dc:language>
    {identifiers}
    <meta name="cover" content="cover-image" />
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />
    <item id="chapter-1" href="text/chapter1.xhtml" media-type="application/xhtml+xml" />
    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" />
  </manifest>
  <spine toc="nav">
    <itemref idref="chapter-1" />
  </spine>
</package>
""",
            compress_type=ZIP_DEFLATED,
        )
        archive.writestr(
            "EPUB/nav.xhtml",
            """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head><title>Navigation</title></head>
  <body><nav epub:type="toc"><ol><li><a href="text/chapter1.xhtml">Chapter 1</a></li></ol></nav></body>
</html>
""",
            compress_type=ZIP_DEFLATED,
        )
        archive.writestr(
            "EPUB/text/chapter1.xhtml",
            """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 1</title></head><body><h1>Chapter 1</h1></body></html>
""",
            compress_type=ZIP_DEFLATED,
        )
        archive.writestr(
            "EPUB/images/cover.jpg",
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9",
            compress_type=ZIP_DEFLATED,
        )


def main() -> None:
    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    extra_args = sys.argv[3:]
    option_summary = " ".join(extra_args)
    source_ext = source.suffix.lower()
    target_ext = target.suffix.lower()

    if source_ext == ".epub":
        metadata = extract_epub_metadata(source)
    else:
        metadata = json.loads(source.read_text(encoding="utf-8"))

    if target_ext == ".html":
        target.write_text(
            f"<html><body><h1>{metadata['title']}</h1><p>{option_summary}</p></body></html>",
            encoding="utf-8",
        )
    elif target_ext == ".pdf":
        target.write_bytes(b"%PDF-1.4\n%Fake PDF\n")
    elif target_ext == ".epub":
        write_epub(target, metadata)
    else:
        target.write_text(json.dumps(metadata), encoding="utf-8")

    print(f"Converted {source.name} -> {target.name} {option_summary}".strip())


if __name__ == "__main__":
    main()
