from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


def test_repairing_broken_manifest_fixture_produces_passing_epub() -> None:
    client = TestClient(app)
    fixture_path = FIXTURE_DIR / "broken-manifest.epub"

    with fixture_path.open("rb") as handle:
        validation = client.post(
            "/v1/validate",
            files={"file": (fixture_path.name, handle, "application/epub+zip")},
        )

    assert validation.status_code == 200
    job_id = validation.json()["jobId"]

    repair = client.post(
        "/v1/repair",
        json={
            "jobId": job_id,
            "fixes": [
                "manifest-mismatch",
                "spine-reference",
                "toc-document",
                "missing-cover",
            ],
        },
    )
    assert repair.status_code == 200
    payload = repair.json()
    assert payload["validation"]["counts"]["error"] == 0
    assert payload["validation"]["pass"] is True


def test_kitchen_sink_fixture_repairs_all_supported_categories() -> None:
    client = TestClient(app)
    fixture_path = FIXTURE_DIR / "kitchen-sink-broken.epub"

    with fixture_path.open("rb") as handle:
        validation = client.post(
            "/v1/validate",
            files={"file": (fixture_path.name, handle, "application/epub+zip")},
        )

    assert validation.status_code == 200
    job_id = validation.json()["jobId"]

    repair = client.post(
        "/v1/repair",
        json={
            "jobId": job_id,
            "fixes": [
                "container-xml",
                "mimetype-entry",
                "manifest-mismatch",
                "spine-reference",
                "toc-document",
                "invalid-xhtml",
                "missing-cover",
            ],
        },
    )
    assert repair.status_code == 200
    payload = repair.json()
    assert set(payload["appliedFixes"]) == {
        "container-xml",
        "mimetype-entry",
        "manifest-mismatch",
        "spine-reference",
        "toc-document",
        "invalid-xhtml",
        "missing-cover",
    }
    assert payload["validation"]["counts"]["error"] == 0
    assert payload["validation"]["pass"] is True


def test_recipe_catalog_lists_all_required_fix_categories() -> None:
    client = TestClient(app)
    response = client.get("/v1/repair/recipes")

    assert response.status_code == 200
    recipe_ids = {recipe["id"] for recipe in response.json()["recipes"]}
    assert recipe_ids == {
        "manifest-mismatch",
        "spine-reference",
        "toc-document",
        "invalid-xhtml",
        "mimetype-entry",
        "missing-cover",
        "container-xml",
    }
