from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parent
FIXTURE_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
VALID_COVER_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x05\x03\x04\x04"
    b"\x04\x03\x05\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07\x07\x07\x0f\x0b\x0b\t\x0c\x11\x0f\x12\x12"
    b"\x11\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11\x11\x18!\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17\"$\"\x1e"
    b"$\x1c\x1e\x1f\x1e\xff\xdb\x00C\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e\x1e\x14\x11\x14\x1e\x1e\x1e\x1e"
    b"\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e"
    b"\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc0\x00\x11\x08"
    b"\x00\n\x00\n\x03\x01\"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01"
    b"\x01\x01\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02"
    b"\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\""
    b"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZ"
    b"cdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7"
    b"\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7"
    b"\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f"
    b"\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08"
    b"\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03"
    b"\x11\x04\x05!1\x06\x12AQ\x07aq\x13\"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17"
    b"\x18\x19\x1a&'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94"
    b"\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4"
    b"\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4"
    b"\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfa\xce\x8a(\xa0\x0f\xff\xd9"
)
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
    <meta property="dcterms:modified">2026-01-01T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />
    <item id="chapter-1" href="text/chapter1.xhtml" media-type="application/xhtml+xml" />
    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image" />
  </manifest>
  <spine>
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
            "EPUB/images/cover.jpg": VALID_COVER_JPEG,
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
            "EPUB/images/cover.jpg": VALID_COVER_JPEG,
        },
    },
    "drm-protected.epub": {
        "opf": """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>DRM Protected</dc:title>
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
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 1</title></head><body><h1>Locked Chapter</h1></body></html>
""",
            "EPUB/images/cover.jpg": VALID_COVER_JPEG,
            "META-INF/encryption.xml": """<?xml version="1.0" encoding="utf-8"?>
<encryption xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <EncryptedData>
    <CipherData />
  </EncryptedData>
</encryption>
""",
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
            "EPUB/images/cover.jpg": VALID_COVER_JPEG,
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
            "EPUB/images/cover.jpg": VALID_COVER_JPEG,
        },
    },
    "legacy-epub2.epub": {
        "opf": """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Legacy EPUB2</dc:title>
    <dc:creator>Fixture Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">9781234567890</dc:identifier>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
    <item id="chapter-1" href="text/chapter1.xhtml" media-type="application/xhtml+xml" />
    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" />
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter-1" />
  </spine>
</package>
""",
        "files": {
            "EPUB/toc.ncx": """<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head />
  <docTitle><text>Legacy EPUB2</text></docTitle>
  <navMap>
    <navPoint id="chapter-1" playOrder="1">
      <navLabel><text>Chapter 1</text></navLabel>
      <content src="text/chapter1.xhtml" />
    </navPoint>
  </navMap>
</ncx>
""",
            "EPUB/text/chapter1.xhtml": """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Chapter 1</title></head><body><h1>Legacy Chapter</h1></body></html>
""",
            "EPUB/images/cover.jpg": VALID_COVER_JPEG,
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
