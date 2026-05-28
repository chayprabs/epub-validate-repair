from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parent
FIXTURE_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
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
    "volume-1.epub": {
        "opf": """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Volume One</dc:title>
    <dc:creator>Fixture Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">9781234567890</dc:identifier>
    <dc:publisher>EpubDoctor Fixtures</dc:publisher>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" />
    <item id="chapter-1" href="text/chapter1.xhtml" media-type="application/xhtml+xml" />
    <item id="chapter-2" href="text/chapter2.xhtml" media-type="application/xhtml+xml" />
    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" />
  </manifest>
  <spine toc="nav">
    <itemref idref="chapter-1" />
    <itemref idref="chapter-2" />
  </spine>
</package>
""",
        "files": {
            "EPUB/nav.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Navigation</title></head><body><nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops"><ol><li><a href="text/chapter1.xhtml">Chapter 1</a></li><li><a href="text/chapter2.xhtml">Chapter 2</a></li></ol></nav></body></html>
""",
            "EPUB/text/chapter1.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 1</title></head><body><h1>Arrival</h1><p>The first volume opens at dawn.</p></body></html>
""",
            "EPUB/text/chapter2.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 2</title></head><body><h1>Crossing</h1><p>The caravan reaches the old bridge.</p></body></html>
""",
            "EPUB/images/cover.jpg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9",
        },
    },
    "volume-2.epub": {
        "opf": """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Volume Two</dc:title>
    <dc:creator>Fixture Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">9781234567890</dc:identifier>
    <dc:publisher>EpubDoctor Fixtures</dc:publisher>
    <dc:rights>CC-BY-NC</dc:rights>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" />
    <item id="chapter-1" href="text/chapter1.xhtml" media-type="application/xhtml+xml" />
    <item id="appendix" href="text/appendix.xhtml" media-type="application/xhtml+xml" />
    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" />
  </manifest>
  <spine toc="nav">
    <itemref idref="chapter-1" />
    <itemref idref="appendix" />
  </spine>
</package>
""",
        "files": {
            "EPUB/nav.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Navigation</title></head><body><nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops"><ol><li><a href="text/chapter1.xhtml">Chapter 1</a></li><li><a href="text/appendix.xhtml">Appendix</a></li></ol></nav></body></html>
""",
            "EPUB/text/chapter1.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 1</title></head><body><h1>Return</h1><p>The second volume opens at dusk.</p></body></html>
""",
            "EPUB/text/appendix.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Appendix</title></head><body><h1>Appendix</h1><p>Field notes and maps.</p></body></html>
""",
            "EPUB/images/cover.jpg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9",
        },
    },
}


def write_entry(archive: ZipFile, filename: str, contents: bytes | str, compress_type: int) -> None:
    entry = ZipInfo(filename, date_time=FIXTURE_TIMESTAMP)
    entry.compress_type = compress_type
    archive.writestr(entry, contents)


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
            write_entry(archive, "mimetype", mimetype_bytes, ZIP_STORED)
        write_entry(archive, "EPUB/package.opf", book["opf"], ZIP_DEFLATED)
        write_entry(archive, "META-INF/container.xml", container_xml, ZIP_DEFLATED)
        if not book.get("mimetype_first", True):
            write_entry(archive, "mimetype", mimetype_bytes, ZIP_DEFLATED)
        for filename, contents in book["files"].items():
            write_entry(archive, filename, contents, ZIP_DEFLATED)


def main() -> None:
    for filename, book in BOOKS.items():
        write_epub(ROOT / filename, book)


if __name__ == "__main__":
    main()
