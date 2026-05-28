import os
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"
FAKE_CONVERTER = FIXTURE_DIR / "fake_ebook_convert.py"


def test_convert_endpoint_runs_fake_ebook_convert_and_returns_download() -> None:
    os.environ["EPUBDOCTOR_EBOOK_CONVERT"] = str(FAKE_CONVERTER)
    client = TestClient(app)
    fixture_path = FIXTURE_DIR / "kdp-ready.epub"

    with fixture_path.open("rb") as handle:
        validation = client.post(
            "/v1/validate",
            files={"file": (fixture_path.name, handle, "application/epub+zip")},
        )

    assert validation.status_code == 200
    job_id = validation.json()["jobId"]
    response = client.post(
        "/v1/convert",
        json={
            "jobId": job_id,
            "target": "html",
            "options": {
                "tocDepth": 2,
                "embedFonts": True,
                "stripCss": True,
                "pageSize": "a4",
            },
        },
    )
    os.environ.pop("EPUBDOCTOR_EBOOK_CONVERT", None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["target"] == "html"
    assert payload["artifactUrl"].endswith("/converted.html")
    assert "--epubdoctor-toc-depth 2" in payload["log"]


def test_fake_round_trip_preserves_core_metadata() -> None:
    os.environ["EPUBDOCTOR_EBOOK_CONVERT"] = str(FAKE_CONVERTER)
    client = TestClient(app)
    fixture_path = FIXTURE_DIR / "kdp-ready.epub"

    with fixture_path.open("rb") as handle:
        validation = client.post(
            "/v1/validate",
            files={"file": (fixture_path.name, handle, "application/epub+zip")},
        )

    original = validation.json()
    mobi = client.post(
        "/v1/convert",
        json={"jobId": original["jobId"], "target": "mobi", "options": {}},
    )
    assert mobi.status_code == 200

    converted_job_id = mobi.json()["jobId"]
    roundtrip = client.post(
        "/v1/convert",
        json={"jobId": converted_job_id, "target": "epub", "options": {}},
    )
    os.environ.pop("EPUBDOCTOR_EBOOK_CONVERT", None)
    assert roundtrip.status_code == 200

    roundtrip_artifact = client.get(roundtrip.json()["artifactUrl"])
    assert roundtrip_artifact.status_code == 200

    validate_roundtrip = client.post(
        "/v1/validate",
        files={"file": ("roundtrip.epub", roundtrip_artifact.content, "application/epub+zip")},
    )
    assert validate_roundtrip.status_code == 200
    metadata = validate_roundtrip.json()["metadata"]
    assert metadata["title"] == original["metadata"]["title"]
    assert metadata["contributors"] == original["metadata"]["contributors"]
    assert metadata["identifiers"] == original["metadata"]["identifiers"]


def test_convert_endpoint_accepts_direct_mobi_upload() -> None:
    os.environ["EPUBDOCTOR_EBOOK_CONVERT"] = str(FAKE_CONVERTER)
    client = TestClient(app)
    fixture_path = FIXTURE_DIR / "mobi-sample.mobi"

    with fixture_path.open("rb") as handle:
        response = client.post(
            "/v1/convert",
            data={
                "target": "epub",
                "tocDepth": "3",
                "embedFonts": "true",
                "stripCss": "false",
                "pageSize": "a5",
            },
            files={"file": (fixture_path.name, handle, "application/x-mobipocket-ebook")},
        )
    os.environ.pop("EPUBDOCTOR_EBOOK_CONVERT", None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["target"] == "epub"
    assert payload["artifactUrl"].endswith("/converted.epub")
    assert "--epubdoctor-toc-depth 3" in payload["log"]
