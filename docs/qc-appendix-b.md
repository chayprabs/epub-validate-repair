# QC Appendix B - EpubDoctor

Repo: `https://github.com/chayprabs/epub-validate-repair`  
Branch: `main`

This report is the running qualification ledger for `RELEASE_QUALIFICATION_CHECKLIST.md` Section 5. It should be updated with exact commands and evidence as checks are completed.

## Current evidence snapshot

### Passing local build checks

- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`
- `pnpm build`
- `docker run --rm -v "${PWD}:/workspace" -w /workspace/apps/worker python:3.12-slim bash -lc "pip install -r requirements.txt && python ../../tests/fixtures/generate_epub_fixtures.py && pytest -q"`
- `python -m py_compile scripts/measure_qc.py`
- `docker compose config`
- `python -m pytest apps/worker/tests -q` -> `18 passed in 5.12s`
- `python -m pytest apps/worker/tests/test_qualification_snapshots.py -q` -> `13 passed in 0.40s`
- `python -m pytest apps/worker/tests -q` -> `31 passed in 2.38s`

### Passing remote CI checks

- GitHub Actions run `26606506881` on commit `254dc07` completed successfully for `web`, `worker`, and `containers` on `main`.
- `web` job result:
  - `pnpm lint`
  - `pnpm typecheck`
  - `pnpm test`
  - `pnpm build`
- `worker` job result: `18 passed`
- `containers` job revalidated:
  - `docker compose config`
  - worker container build
  - web container build
  - live worker `/health` smoke
  - performance smoke
  - real-tool worker container smoke
  - image budget gate
- GitHub Actions run `26602899351` on commit `1cc08f2` completed successfully for `web`, `worker`, and `containers`.
- `worker` job used hosted Python `3.12.13`.
- `worker` job result: `16 passed in 0.77s`.
- `containers` job built both images successfully:
  - `docker build -f apps/worker/Dockerfile -t epubdoctor-worker:ci .`
  - `docker build -f apps/web/Dockerfile -t epubdoctor-web:ci .`
- `containers` job image budget check result:
  - `worker_size_bytes=1146627595`
  - Budget gate: `<= 1610612736` bytes (`1.5 GB`)
- Worker container build now uses `python:3.12-slim-bookworm`, which resolved the previous Debian package availability failure for `openjdk-17-jre-headless` on GitHub-hosted runners.
- GitHub Actions run `26604037563` on commit `33a8055` revalidated the `containers` job after fixing the EPUBCheck bundle and fixture covers.
- `containers` runtime smoke result inside the built worker image:
  - `openjdk version "17.0.19" 2026-04-21`
  - `ebook-convert (calibre 6.13.0)`
  - `Messages: 0 fatals / 0 errors / 0 warnings / 0 infos`
  - `epubcheck smoke: {"status": 0, "messages": 0, ...}`
  - `calibre smoke: {'mobiBytes': 10494, 'roundtripEpubBytes': 4066}`
  - `worker runtime smoke: complete`
- Latest remote worker image budget check result:
  - `worker_size_bytes=1180238441`
  - Budget gate: `<= 1610612736` bytes (`1.5 GB`)
- GitHub Actions run `26604210133` on commit `a0f2c73` revalidated the live worker service startup path.
- `containers` live worker readiness smoke result:
  - `worker health smoke: {"status": "ok", "runtime": {"javaReady": true, "calibreReady": true, "epubcheckReady": true, "message": "runtime warm-up: java=ok, calibre=ok, epubcheck=ok"}}`
  - Container log evidence:
    - `INFO:     Application startup complete.`
    - `INFO:     172.17.0.1:33128 - "GET /health HTTP/1.1" 200 OK`
- This now proves, in remote CI, that the built worker image can boot as a live HTTP service and report all three runtime dependencies ready through `/health`.
- GitHub Actions run `26604957591` on commit `0bffdf8` revalidated the live worker service and added the timed performance smoke against the dedicated `performance-5mb.epub` fixture.
- `containers` performance smoke result:
  - Fixture size: `tests/fixtures/performance-5mb.epub` = `5246468` bytes
  - `worker perf smoke: {"iterations": 5, "validate": {"samplesMs": [42, 40, 39, 39, 41], "meanMs": 40.2, "p95Ms": 42}, "epubToMobi": {"samplesMs": [620, 639, 614, 597, 591], "meanMs": 612.2, "p95Ms": 639}, "mobiToEpub": {"samplesMs": [531, 528, 529, 529, 531], "meanMs": 529.6, "p95Ms": 531}}`
  - Section 5.13 gates satisfied in CI:
    - validate p95 `42 ms` <= `10 s`
    - EPUB -> MOBI p95 `639 ms` <= `20 s`
    - MOBI -> EPUB p95 `531 ms` <= `25 s`
- Latest remote worker image budget check result:
  - `worker_size_bytes=1180239345`
  - Budget gate: `<= 1610612736` bytes (`1.5 GB`)
- GitHub Actions run `26606511137` on commit `254dc07` completed successfully for the `release` workflow.
- `release` job result:
  - authenticated to `ghcr.io`
  - generated metadata for `ghcr.io/chayprabs/epubdoctor-worker`
  - generated metadata for `ghcr.io/chayprabs/epubdoctor-web`
  - pushed both images successfully with `docker/build-push-action@v6`

### Passing release-surface checks

- README now includes a real homepage screenshot at `docs/screenshots/homepage.png`.
- The web build now prerenders the required SEO routes:
  - `/epub-validator-online`
  - `/epub-to-mobi`
  - `/mobi-to-epub`
  - `/epub-metadata-editor`
  - `/epub-cover-replace`
  - `/kdp-epub-check`
- The app also emits `robots.txt` and `sitemap.xml`.
- GitHub repository description matches the PRD one-liner.
- GitHub now recognizes the repository license as `AGPL-3.0`.
- GitHub repository topics now include 12 required discovery tags:
  - `azw3`
  - `calibre`
  - `ebook`
  - `ebook-converter`
  - `ebook-metadata`
  - `epub`
  - `epub-validator`
  - `epubcheck`
  - `kindle`
  - `mobi`
  - `online-tool`
  - `epub-repair`

### Product behaviors verified in tests

- `broken-manifest.epub` validates with 4 errors and those errors map to repair recipes.
- `kdp-ready.epub` validates with zero errors.
- `invalid-xhtml.epub` surfaces a fixable XHTML error.
- `drm-protected.epub` is refused with a friendly DRM-free message.
- EPUB -> MOBI -> EPUB round-trip preserves title, contributors, and identifiers through the fake converter path.
- Batch ZIP processing returns CSV plus repaired ZIP output.
- Two-EPUB diff returns structure, metadata, and chapter content changes.
- Job storage now enforces TTL cleanup; expired job directories are purged before new work and expired inputs become unreadable in `apps/worker/tests/test_job_store.py`.
- Validation report snapshots are now pinned for `broken-manifest.epub`, `kdp-ready.epub`, `invalid-xhtml.epub`, `legacy-epub2.epub`, `volume-1.epub`, and `volume-2.epub` in `tests/fixtures/snapshots/validation/`.
- Every repair recipe now has a checked golden result in `tests/fixtures/goldens/repair/`, covering manifest mismatch, spine refs, TOC generation, invalid XHTML recovery, mimetype rewrite, missing cover injection, and container.xml repair.
- The production web now proxies worker requests through `apps/web/app/api/worker/[...path]/route.ts`, which keeps validation, artifact downloads, and previews on the same origin and makes a public-web/private-worker deployment possible.
- Local production-mode smoke verified the proxy path:
  - web `http://127.0.0.1:3101`
  - worker `http://127.0.0.1:8100`
  - `broken-manifest.epub` validation completed successfully through `/api/worker/v1/validate`
  - report links were rewritten to `/api/worker/v1/artifacts/...`
  - "Open in viewer" switched into the Structure tab correctly

## Remaining qualification work

### Runtime and hosting

- Run `docker compose up --build -d` and capture health evidence on a healthy local Docker host.
- `docker compose up --build -d` remains the only unproven part of the local runtime path; the live worker `/health` readiness output and warm-up log line are now qualified in remote CI.
- A hosted deployment is still missing. The repo now includes `render.yaml` for a Render blueprint, but there is not yet a live public web URL or HTTPS certificate evidence for Section 5.14 / 5.16.
- Worker image size budget is now qualified in remote CI: latest passing result `1180238441` bytes, which is below the `1.5 GB` gate.
- Built worker container smoke is now qualified in remote CI for Java + EPUBCheck + Calibre execution against the acceptance fixture path.
- Built worker service readiness is now qualified in remote CI for live `/health` startup with `javaReady`, `calibreReady`, and `epubcheckReady` all `true`.
- Current status for local container runtime remains `VERIFY-DEFERRED` on this host because Docker Desktop intermittently loses the Linux engine pipe during direct local image execution attempts.
- Current status: host Python is `3.14.3`, and a disposable worker venv failed to install `lxml`, `Pillow`, and `pydantic-core`, so non-Docker local worker startup is not a viable substitute on this machine.

### Performance

- Remote CI now measures the Section 5.13 gates with `bash scripts/measure_worker_service.sh` against `tests/fixtures/performance-5mb.epub` for validation and `tests/fixtures/kdp-ready.epub` for conversion.
- Standalone helper remains available for reruns: `python scripts/measure_qc.py --worker-url http://127.0.0.1:8000 --iterations 5 --validation-fixture performance-5mb.epub --conversion-fixture kdp-ready.epub`
- Local web Lighthouse on `http://127.0.0.1:3000` with `npx lighthouse ... --output-path=.codex-tmp/lighthouse-4.json`:
  - Performance: `96`
  - Accessibility: `100`
  - Best Practices: `100`
  - SEO: `100`

### UX and hosted checks

- Run Lighthouse against the local or hosted app and record all four scores.
- Verify mobile usability with screenshots.
- Verify a hosted URL and the corresponding HTTPS certificate.
- Verify hosted SEO sub-routes against the public deployment.

### Documentation

- README now documents the `EPUBDOCTOR_RETENTION_TTL_SECONDS` override for self-hosted artifact retention.
- README now documents the Render blueprint path for a public web service plus a private worker service.
- Link the final qualification SHA once Section 5 is fully green.
