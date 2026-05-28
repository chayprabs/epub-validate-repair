from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


def test_diff_reports_structure_metadata_and_chapter_changes() -> None:
    client = TestClient(app)
    fixture_a = FIXTURE_DIR / "volume-1.epub"
    fixture_b = FIXTURE_DIR / "volume-2.epub"

    with fixture_a.open("rb") as left, fixture_b.open("rb") as right:
        response = client.post(
            "/v1/diff",
            files={
                "fileA": (fixture_a.name, left, "application/epub+zip"),
                "fileB": (fixture_b.name, right, "application/epub+zip"),
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert any(change["path"] == "EPUB/package.opf" for change in payload["structure"])
    assert any(change["field"] == "title" for change in payload["metadata"])
    assert any(change["path"] == "text/chapter1.xhtml" for change in payload["chapters"])
