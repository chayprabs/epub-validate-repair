import base64
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"
SMALL_PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5W8ncAAAAASUVORK5CYII="
)


def test_metadata_update_rewrites_opf_fields_and_cover() -> None:
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
        "/v1/metadata",
        json={
            "jobId": job_id,
            "coverPreset": "apple",
            "coverImageDataUrl": SMALL_PNG_DATA_URL,
            "metadata": {
                "title": "Updated Title",
                "subtitle": "Updated Subtitle",
                "contributors": [
                    {"name": "Primary Author", "role": "aut"},
                    {"name": "Editorial Partner", "role": "edt"},
                ],
                "language": "en-US",
                "identifiers": [
                    {"type": "isbn-13", "value": "9781111111111"},
                    {"type": "doi", "value": "10.1234/epubdoctor"},
                ],
                "publisher": "EpubDoctor Press",
                "publishedAt": "2026-05-29",
                "description": "Updated description",
                "subjects": ["Fiction / Literary", "Indie"],
                "rights": "All rights reserved",
                "series": "The Testing Saga",
                "seriesIndex": "2",
                "custom": {
                    "calibre:rating": "5",
                    "source-system": "codex",
                },
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    metadata = payload["validation"]["metadata"]
    assert payload["validation"]["pass"] is True
    assert metadata["title"] == "Updated Title"
    assert metadata["subtitle"] == "Updated Subtitle"
    assert metadata["contributors"] == [
        {"name": "Primary Author", "role": "aut"},
        {"name": "Editorial Partner", "role": "edt"},
    ]
    assert metadata["identifiers"] == [
        {"type": "isbn-13", "value": "9781111111111"},
        {"type": "doi", "value": "10.1234/epubdoctor"},
    ]
    assert metadata["series"] == "The Testing Saga"
    assert metadata["seriesIndex"] == "2"
    assert metadata["custom"] == {
        "calibre:rating": "5",
        "source-system": "codex",
    }

    unpack = client.get(f"/v1/unpack/{payload['jobId']}/preview", params={"path": "EPUB/package.opf"})
    assert unpack.status_code == 200
    assert "calibre:series" in unpack.json()["text"]
