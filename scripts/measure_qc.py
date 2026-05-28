from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def upload_validate(client: httpx.Client, worker_url: str, fixture_name: str) -> tuple[float, dict]:
    fixture_path = FIXTURES / fixture_name
    start = time.perf_counter()
    with fixture_path.open("rb") as handle:
        response = client.post(
            f"{worker_url}/v1/validate",
            files={"file": (fixture_path.name, handle, "application/epub+zip")},
        )
    elapsed = time.perf_counter() - start
    response.raise_for_status()
    return elapsed, response.json()


def convert_job(
    client: httpx.Client,
    worker_url: str,
    job_id: str,
    target: str,
) -> tuple[float, dict]:
    start = time.perf_counter()
    response = client.post(
        f"{worker_url}/v1/convert",
        json={"jobId": job_id, "target": target, "options": {}},
    )
    elapsed = time.perf_counter() - start
    response.raise_for_status()
    return elapsed, response.json()


def percentile_95(samples: list[float]) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = max(0, min(len(ordered) - 1, round(0.95 * (len(ordered) - 1))))
    return ordered[index]


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure EpubDoctor QC timings.")
    parser.add_argument("--worker-url", default="http://127.0.0.1:8000")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--validation-fixture", default="performance-5mb.epub")
    parser.add_argument("--conversion-fixture", default="kdp-ready.epub")
    args = parser.parse_args()

    validation_samples: list[float] = []
    epub_to_mobi_samples: list[float] = []
    mobi_to_epub_samples: list[float] = []

    with httpx.Client(timeout=args.timeout) as client:
        for _ in range(args.iterations):
            validate_elapsed, _ = upload_validate(client, args.worker_url, args.validation_fixture)
            validation_samples.append(validate_elapsed)

            _, conversion_validation = upload_validate(client, args.worker_url, args.conversion_fixture)

            convert_elapsed, mobi = convert_job(client, args.worker_url, conversion_validation["jobId"], "mobi")
            epub_to_mobi_samples.append(convert_elapsed)

            roundtrip_elapsed, _ = convert_job(client, args.worker_url, mobi["jobId"], "epub")
            mobi_to_epub_samples.append(roundtrip_elapsed)

    report = {
        "iterations": args.iterations,
        "workerUrl": args.worker_url,
        "validateSeconds": {
            "samples": validation_samples,
            "mean": statistics.mean(validation_samples),
            "p95": percentile_95(validation_samples),
        },
        "epubToMobiSeconds": {
            "samples": epub_to_mobi_samples,
            "mean": statistics.mean(epub_to_mobi_samples),
            "p95": percentile_95(epub_to_mobi_samples),
        },
        "mobiToEpubSeconds": {
            "samples": mobi_to_epub_samples,
            "mean": statistics.mean(mobi_to_epub_samples),
            "p95": percentile_95(mobi_to_epub_samples),
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
