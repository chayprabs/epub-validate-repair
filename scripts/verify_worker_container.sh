#!/usr/bin/env bash
set -euo pipefail

workspace_root="${1:-/workspace}"
report_dir="${workspace_root}/.codex-tmp/worker-runtime"
fixture_epub="${workspace_root}/tests/fixtures/kdp-ready.epub"
epubcheck_report="${report_dir}/kdp-ready-epubcheck.json"
converted_mobi="${report_dir}/kdp-ready.mobi"
roundtrip_epub="${report_dir}/kdp-ready-roundtrip.epub"

mkdir -p "${report_dir}"

echo "worker runtime smoke: starting"
java -version
ebook-convert --version

java -jar /opt/epubcheck/epubcheck.jar "${fixture_epub}" --json "${epubcheck_report}"
python - <<'PY' "${epubcheck_report}"
import json
import pathlib
import sys

report_path = pathlib.Path(sys.argv[1])
report = json.loads(report_path.read_text(encoding="utf-8"))
assert isinstance(report.get("checker"), dict), "Missing checker metadata in epubcheck report"
assert isinstance(report.get("messages"), list), "Missing messages array in epubcheck report"
print(
    "epubcheck smoke:",
    json.dumps(
        {
            "messages": len(report["messages"]),
            "checkerKeys": sorted(report["checker"].keys())[:5],
        }
    ),
)
PY

ebook-convert "${fixture_epub}" "${converted_mobi}"
test -s "${converted_mobi}"

ebook-convert "${converted_mobi}" "${roundtrip_epub}"
test -s "${roundtrip_epub}"

python - <<'PY' "${converted_mobi}" "${roundtrip_epub}"
import pathlib
import sys

mobi_path = pathlib.Path(sys.argv[1])
epub_path = pathlib.Path(sys.argv[2])
print(
    "calibre smoke:",
    {
        "mobiBytes": mobi_path.stat().st_size,
        "roundtripEpubBytes": epub_path.stat().st_size,
    },
)
PY

echo "worker runtime smoke: complete"
