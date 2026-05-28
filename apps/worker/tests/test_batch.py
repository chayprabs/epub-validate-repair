from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient

from src.main import app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


def test_batch_endpoint_returns_csv_and_repaired_zip() -> None:
    client = TestClient(app)
    batch_payload = BytesIO()
    with ZipFile(batch_payload, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("notes.txt", "ignore me")
        archive.writestr("broken-manifest.epub", (FIXTURE_DIR / "broken-manifest.epub").read_bytes())
        archive.writestr("kdp-ready.epub", (FIXTURE_DIR / "kdp-ready.epub").read_bytes())

    response = client.post(
        "/v1/batch",
        files={"file": ("batch.zip", batch_payload.getvalue(), "application/zip")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["csvUrl"].endswith("/batch-report.csv")
    assert payload["repairedZipUrl"].endswith("/batch-repaired.zip")
    assert len(payload["items"]) == 3

    broken = next(item for item in payload["items"] if item["filename"] == "broken-manifest.epub")
    assert broken["status"] == "repaired"
    assert broken["originalErrors"] == 4
    assert broken["repairedErrors"] == 0

    clean = next(item for item in payload["items"] if item["filename"] == "kdp-ready.epub")
    assert clean["status"] == "passed"

    unsupported = next(item for item in payload["items"] if item["filename"] == "notes.txt")
    assert unsupported["status"] == "unsupported"

    csv_artifact = client.get(payload["csvUrl"])
    assert csv_artifact.status_code == 200
    assert "broken-manifest.epub,repaired,4,0" in csv_artifact.text

    repaired_zip = client.get(payload["repairedZipUrl"])
    assert repaired_zip.status_code == 200
    with ZipFile(BytesIO(repaired_zip.content), "r") as archive:
        assert archive.namelist() == ["broken-manifest-repaired.epub"]
