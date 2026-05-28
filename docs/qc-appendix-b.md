# QC Appendix B - EpubDoctor

Repo: `https://github.com/chayprabs/epub-validate-repair`  
Branch: `cursor/epub-doctor-build`

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

### Passing remote CI checks

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

### Product behaviors verified in tests

- `broken-manifest.epub` validates with 4 errors and those errors map to repair recipes.
- `kdp-ready.epub` validates with zero errors.
- `invalid-xhtml.epub` surfaces a fixable XHTML error.
- `drm-protected.epub` is refused with a friendly DRM-free message.
- EPUB -> MOBI -> EPUB round-trip preserves title, contributors, and identifiers through the fake converter path.
- Batch ZIP processing returns CSV plus repaired ZIP output.
- Two-EPUB diff returns structure, metadata, and chapter content changes.

## Remaining qualification work

### Runtime and hosting

- Run `docker compose up --build -d` and capture health evidence.
- Confirm worker warm-up log line and `/health` runtime readiness output.
- Measure cold and warm validation latency.
- Worker image size budget is now qualified in remote CI: `1146627595` bytes, which is below the `1.5 GB` gate.
- Current status for local container runtime remains `VERIFY-DEFERRED` on this host because Docker Desktop lost the Linux engine pipe during image build attempts.
- Current status: host Python is `3.14.3`, and a disposable worker venv failed to install `lxml`, `Pillow`, and `pydantic-core`, so non-Docker local worker startup is not a viable substitute on this machine.

### Performance

- Measure p95 validate for a 5 MB EPUB.
- Measure p95 EPUB -> MOBI conversion.
- Measure p95 MOBI -> EPUB conversion.
- Prepared helper: `python scripts/measure_qc.py --worker-url http://127.0.0.1:8000 --iterations 5`
- Local web Lighthouse on `http://127.0.0.1:3000` with `npx lighthouse ... --output-path=.codex-tmp/lighthouse-4.json`:
  - Performance: `96`
  - Accessibility: `100`
  - Best Practices: `100`
  - SEO: `100`

### UX and hosted checks

- Run Lighthouse against the local or hosted app and record all four scores.
- Verify mobile usability with screenshots.
- Verify hosted URLs and SEO sub-routes.

### Documentation

- Add final screenshot evidence to the README or docs set.
- Link the final release PR and qualification SHA once Section 5 is fully green.
