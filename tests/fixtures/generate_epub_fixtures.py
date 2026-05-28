from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile


ROOT = Path(__file__).resolve().parent
BOOKS = {
    "broken-manifest.epub": {
        "opf": """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Broken Manifest</dc:title>
    <dc:creator>Fixture Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">9781234567890</dc:identifier>
  </metadata>
  <manifest>
    <item id="chapter-1" href="text/chapter1.xhtml" media-type="application/xhtml+xml" />
  </manifest>
  <spine>
    <itemref idref="chapter-1" />
    <itemref idref="missing-chapter" />
  </spine>
</package>
""",
        "files": {
            "EPUB/text/chapter1.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 1</title></head><body><h1>Chapter 1</h1></body></html>
""",
            "EPUB/text/chapter2.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 2</title></head><body><h1>Chapter 2</h1></body></html>
""",
        },
    },
    "kdp-ready.epub": {
        "opf": """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>KDP Ready</dc:title>
    <dc:creator>Fixture Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">9781234567890</dc:identifier>
    <dc:publisher>EpubDoctor Fixtures</dc:publisher>
    <dc:rights>CC-BY</dc:rights>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" />
    <item id="chapter-1" href="text/chapter1.xhtml" media-type="application/xhtml+xml" />
    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" />
  </manifest>
  <spine toc="nav">
    <itemref idref="chapter-1" />
  </spine>
</package>
""",
        "files": {
            "EPUB/nav.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Navigation</title></head><body><nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops"><ol><li><a href="text/chapter1.xhtml">Chapter 1</a></li></ol></nav></body></html>
""",
            "EPUB/text/chapter1.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 1</title></head><body><h1>Chapter 1</h1></body></html>
""",
            "EPUB/images/cover.jpg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9",
        },
    },
    "invalid-xhtml.epub": {
        "opf": """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Invalid XHTML</dc:title>
    <dc:creator>Fixture Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">9781234567890</dc:identifier>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" />
    <item id="chapter-1" href="text/chapter1.xhtml" media-type="application/xhtml+xml" />
    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" />
  </manifest>
  <spine toc="nav">
    <itemref idref="chapter-1" />
  </spine>
</package>
""",
        "files": {
            "EPUB/nav.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Navigation</title></head><body><nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops"><ol><li><a href="text/chapter1.xhtml">Chapter 1</a></li></ol></nav></body></html>
""",
            "EPUB/text/chapter1.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Broken</title></head><body><h1>Broken Chapter</h1><p>Missing close
""",
            "EPUB/images/cover.jpg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9",
        },
    },
    "kitchen-sink-broken.epub": {
        "mimetype": b"not-an-epub",
        "mimetype_first": False,
        "container_xml": """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml">
  </rootfiles>
</container>
""",
        "opf": """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Kitchen Sink Broken</dc:title>
    <dc:creator>Fixture Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">9781234567890</dc:identifier>
  </metadata>
  <manifest>
    <item id="chapter-1" href="text/chapter1.xhtml" media-type="application/xhtml+xml" />
  </manifest>
  <spine>
    <itemref idref="chapter-1" />
    <itemref idref="missing-item" />
  </spine>
</package>
""",
        "files": {
            "EPUB/text/chapter1.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Broken</title></head><body><h1>Broken Chapter</h1><p>Missing close
""",
            "EPUB/text/chapter2.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 2</title></head><body><h1>Chapter 2</h1></body></html>
""",
        },
    },
}


def write_epub(target: Path, book: dict) -> None:
    with ZipFile(target, "w") as archive:
        mimetype_bytes = book.get("mimetype", b"application/epub+zip")
        container_xml = book.get(
            "container_xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
        )
        if book.get("mimetype_first", True):
            archive.writestr("mimetype", mimetype_bytes, compress_type=ZIP_STORED)
        archive.writestr("EPUB/package.opf", book["opf"], compress_type=ZIP_DEFLATED)
        archive.writestr("META-INF/container.xml", container_xml, compress_type=ZIP_DEFLATED)
        if not book.get("mimetype_first", True):
            archive.writestr("mimetype", mimetype_bytes, compress_type=ZIP_DEFLATED)
        for filename, contents in book["files"].items():
            archive.writestr(filename, contents, compress_type=ZIP_DEFLATED)


def main() -> None:
    for filename, book in BOOKS.items():
        write_epub(ROOT / filename, book)


if __name__ == "__main__":
    main()
