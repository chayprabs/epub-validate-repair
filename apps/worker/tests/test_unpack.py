from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


def test_unpack_lists_archive_entries_and_previews_xhtml() -> None:
    client = TestClient(app)
    fixture_path = FIXTURE_DIR / "kdp-ready.epub"

    with fixture_path.open("rb") as handle:
        validation = client.post(
            "/v1/validate",
            files={"file": (fixture_path.name, handle, "application/epub+zip")},
        )

    assert validation.status_code == 200
    job_id = validation.json()["jobId"]

    unpack = client.get(f"/v1/unpack/{job_id}")
    assert unpack.status_code == 200
    entries = unpack.json()["entries"]
    paths = {entry["path"] for entry in entries}
    assert "EPUB/nav.xhtml" in paths
    assert "EPUB/images/cover.jpg" in paths

    preview = client.get(f"/v1/unpack/{job_id}/preview", params={"path": "EPUB/nav.xhtml"})
    assert preview.status_code == 200
    payload = preview.json()
    assert payload["kind"] == "xhtml"
    assert "<nav" in payload["text"]
