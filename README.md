# EpubDoctor

EpubDoctor validates, repairs, and converts EPUB, MOBI, and AZW3 ebooks using a server-side worker powered by epubcheck, Calibre, and Python repair routines.

## Status

The repository is in active v1 build-out against `PRODUCT_REQUIREMENTS.md` and `RELEASE_QUALIFICATION_CHECKLIST.md` Section 5. Current progress is focused on establishing the Pattern 1 monorepo and the first validation slice.

## Planned capabilities

- Validate EPUB files with epubcheck 5.x and export JSON/HTML reports.
- Repair manifest, spine, TOC, XHTML, MIME, cover, and `container.xml` issues.
- Convert between EPUB, MOBI, AZW3, PDF, and HTML with Calibre.
- Edit metadata, compare two books, and support Pro batch processing.

## Self-host

```bash
pnpm install
docker compose up
```

The eventual worker image will bundle JRE 17, Calibre, and epubcheck. Because Calibre is GPL and the application is licensed under AGPL-3.0, the final README will include the required combined-work notice and source availability details.
