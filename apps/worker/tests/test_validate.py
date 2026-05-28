from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app
from src.routes import validate as validate_route

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


def test_invalid_xhtml_is_marked_fixable() -> None:
    client = TestClient(app)
    fixture_path = FIXTURE_DIR / "invalid-xhtml.epub"

    with fixture_path.open("rb") as handle:
        response = client.post(
            "/v1/validate",
            files={"file": (fixture_path.name, handle, "application/epub+zip")},
        )

    assert response.status_code == 200
    payload = response.json()
    xhtml_messages = [message for message in payload["messages"] if message["id"] == "XHTML_INVALID"]
    assert xhtml_messages
    assert xhtml_messages[0]["fixableBy"] == "invalid-xhtml"


def test_drm_protected_fixture_is_refused_with_friendly_message() -> None:
    client = TestClient(app)
    fixture_path = FIXTURE_DIR / "drm-protected.epub"

    with fixture_path.open("rb") as handle:
        response = client.post(
            "/v1/validate",
            files={"file": (fixture_path.name, handle, "application/epub+zip")},
        )

    assert response.status_code == 400
    assert "DRM-free files" in response.json()["detail"]


def test_validate_url_downloads_remote_epub(monkeypatch) -> None:
    client = TestClient(app)
    fixture_path = FIXTURE_DIR / "kdp-ready.epub"

    def fake_download(url: str) -> tuple[str, bytes]:
        assert url == "https://example.com/kdp-ready.epub"
        return "kdp-ready.epub", fixture_path.read_bytes()

    monkeypatch.setattr(validate_route, "_download_remote_epub", fake_download)

    response = client.post(
        "/v1/validate",
        data={"url": "https://example.com/kdp-ready.epub"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["counts"]["error"] == 0
    assert payload["metadata"]["title"] == "KDP Ready"
