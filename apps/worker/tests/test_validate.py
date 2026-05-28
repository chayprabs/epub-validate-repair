from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


def test_broken_manifest_returns_four_fixable_errors() -> None:
    client = TestClient(app)
    fixture_path = FIXTURE_DIR / "broken-manifest.epub"

    with fixture_path.open("rb") as handle:
        response = client.post(
            "/v1/validate",
            files={"file": (fixture_path.name, handle, "application/epub+zip")},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["counts"]["error"] == 4
    assert payload["pass"] is False

    fix_ids = {message["fixableBy"] for message in payload["messages"] if message["severity"] == "error"}
    assert {
        "manifest-mismatch",
        "spine-reference",
        "toc-document",
        "missing-cover",
    } <= fix_ids
    assert payload["artifacts"]["jsonUrl"].endswith("/report.json")
    assert payload["artifacts"]["htmlUrl"].endswith("/report.html")


def test_kdp_ready_fixture_passes_validation() -> None:
    client = TestClient(app)
    fixture_path = FIXTURE_DIR / "kdp-ready.epub"

    with fixture_path.open("rb") as handle:
        response = client.post(
            "/v1/validate",
            files={"file": (fixture_path.name, handle, "application/epub+zip")},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["counts"]["error"] == 0
    assert payload["pass"] is True
