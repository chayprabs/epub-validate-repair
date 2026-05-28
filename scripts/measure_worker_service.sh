#!/usr/bin/env bash
set -euo pipefail

container_name="${1:-epubdoctor-worker-perf}"
host_port="${2:-18001}"
iterations="${3:-5}"
worker_url="http://127.0.0.1:${host_port}"
fixture_path="tests/fixtures/kdp-ready.epub"

cleanup() {
  docker rm -f "${container_name}" >/dev/null 2>&1 || true
}

now_ms() {
  python - <<'PY'
import time
print(int(time.perf_counter() * 1000))
PY
}

trap cleanup EXIT

docker run -d --name "${container_name}" -p "${host_port}:8000" epubdoctor-worker:ci >/dev/null

deadline=$((SECONDS + 45))
while [ "${SECONDS}" -lt "${deadline}" ]; do
  if curl -fsS "${worker_url}/health" >/dev/null; then
    break
  fi
  sleep 1
done

if ! curl -fsS "${worker_url}/health" >/dev/null; then
  echo "worker perf smoke: /health did not become ready"
  docker logs "${container_name}" || true
  exit 1
fi

validate_samples=()
epub_to_mobi_samples=()
mobi_to_epub_samples=()

for ((i = 1; i <= iterations; i += 1)); do
  start_ms=$(now_ms)
  validate_json=$(curl -fsS -F "file=@${fixture_path};type=application/epub+zip" "${worker_url}/v1/validate")
  end_ms=$(now_ms)
  validate_samples+=($((end_ms - start_ms)))
  validation_job_id=$(jq -r '.jobId' <<<"${validate_json}")

  start_ms=$(now_ms)
  mobi_json=$(curl -fsS -H "Content-Type: application/json" -d "{\"jobId\":\"${validation_job_id}\",\"target\":\"mobi\",\"options\":{}}" "${worker_url}/v1/convert")
  end_ms=$(now_ms)
  epub_to_mobi_samples+=($((end_ms - start_ms)))
  mobi_job_id=$(jq -r '.jobId' <<<"${mobi_json}")

  start_ms=$(now_ms)
  curl -fsS -H "Content-Type: application/json" -d "{\"jobId\":\"${mobi_job_id}\",\"target\":\"epub\",\"options\":{}}" "${worker_url}/v1/convert" >/tmp/epubdoctor-roundtrip.json
  end_ms=$(now_ms)
  mobi_to_epub_samples+=($((end_ms - start_ms)))
done

validate_csv=$(IFS=,; echo "${validate_samples[*]}")
epub_to_mobi_csv=$(IFS=,; echo "${epub_to_mobi_samples[*]}")
mobi_to_epub_csv=$(IFS=,; echo "${mobi_to_epub_samples[*]}")

python - <<'PY' "${iterations}" "${validate_csv}" "${epub_to_mobi_csv}" "${mobi_to_epub_csv}"
import json
import statistics
import sys


def parse_samples(raw: str) -> list[int]:
    return [int(part) for part in raw.split(",") if part]


def percentile_95(samples: list[int]) -> int:
    ordered = sorted(samples)
    index = max(0, min(len(ordered) - 1, round(0.95 * (len(ordered) - 1))))
    return ordered[index]


def summarize(samples: list[int]) -> dict[str, object]:
    return {
        "samplesMs": samples,
        "meanMs": round(statistics.mean(samples), 2),
        "p95Ms": percentile_95(samples),
    }


iterations = int(sys.argv[1])
validate_samples = parse_samples(sys.argv[2])
epub_to_mobi_samples = parse_samples(sys.argv[3])
mobi_to_epub_samples = parse_samples(sys.argv[4])

report = {
    "iterations": iterations,
    "validate": summarize(validate_samples),
    "epubToMobi": summarize(epub_to_mobi_samples),
    "mobiToEpub": summarize(mobi_to_epub_samples),
}
print("worker perf smoke:", json.dumps(report))

assert report["validate"]["p95Ms"] <= 10000, report
assert report["epubToMobi"]["p95Ms"] <= 20000, report
assert report["mobiToEpub"]["p95Ms"] <= 25000, report
PY
