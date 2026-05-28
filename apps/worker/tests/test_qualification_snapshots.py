import hashlib
import json
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from src.core.repair import repair_epub
from src.core.validation import validate_epub

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"
VALIDATION_SNAPSHOT_DIR = FIXTURE_DIR / "snapshots" / "validation"
REPAIR_GOLDEN_DIR = FIXTURE_DIR / "goldens" / "repair"

VALIDATION_SNAPSHOTS = [
    "broken-manifest.epub",
    "kdp-ready.epub",
    "invalid-xhtml.epub",
    "legacy-epub2.epub",
    "volume-1.epub",
    "volume-2.epub",
]

REPAIR_GOLDEN_CASES = [
    {
        "name": "manifest-mismatch",
        "fixture": "broken-manifest.epub",
        "fixes": ["manifest-mismatch"],
        "text_entries": ["EPUB/package.opf"],
    },
    {
        "name": "spine-reference",
        "fixture": "broken-manifest.epub",
        "fixes": ["spine-reference"],
        "text_entries": ["EPUB/package.opf"],
    },
    {
        "name": "toc-document",
        "fixture": "broken-manifest.epub",
        "fixes": ["toc-document"],
        "text_entries": ["EPUB/package.opf", "EPUB/nav.xhtml"],
    },
    {
        "name": "invalid-xhtml",
        "fixture": "kitchen-sink-broken.epub",
        "fixes": ["invalid-xhtml"],
        "text_entries": ["EPUB/text/chapter1.xhtml"],
    },
    {
        "name": "mimetype-entry",
        "fixture": "kitchen-sink-broken.epub",
        "fixes": ["mimetype-entry"],
        "text_entries": ["mimetype"],
        "order_prefix": [
            "mimetype",
            "EPUB/package.opf",
            "EPUB/text/chapter1.xhtml",
            "EPUB/text/chapter2.xhtml",
            "META-INF/container.xml",
        ],
        "compressions": {"mimetype": zipfile.ZIP_STORED},
    },
    {
        "name": "missing-cover",
        "fixture": "broken-manifest.epub",
        "fixes": ["missing-cover"],
        "text_entries": ["EPUB/package.opf"],
        "hash_entries": {"EPUB/images/cover.jpg": "EPUB/images/cover.jpg.sha256"},
    },
    {
        "name": "container-xml",
        "fixture": "kitchen-sink-broken.epub",
        "fixes": ["container-xml"],
        "text_entries": ["META-INF/container.xml"],
    },
]


def _golden_path(case_name: str, archive_name: str) -> Path:
    return REPAIR_GOLDEN_DIR / case_name / Path(*archive_name.split("/"))


def _normalize_text_snapshot(value: str) -> str:
    return value.rstrip("\n")


@pytest.mark.parametrize("fixture_name", VALIDATION_SNAPSHOTS)
def test_validation_reports_match_snapshots(fixture_name: str) -> None:
    fixture_path = FIXTURE_DIR / fixture_name
    snapshot_path = VALIDATION_SNAPSHOT_DIR / f"{fixture_path.stem}.json"

    with tempfile.TemporaryDirectory(prefix="epubdoctor-snapshot-") as temp_dir:
        local_path = Path(temp_dir) / fixture_name
        local_path.write_bytes(fixture_path.read_bytes())

        payload = validate_epub(
            str(local_path),
            "snapshot-job",
            "http://snapshot.local/v1/artifacts",
        ).model_dump(by_alias=True)

    payload["jobId"] = "<job-id>"
    payload["artifacts"] = {"htmlUrl": "<html-url>", "jsonUrl": "<json-url>"}

    assert payload == json.loads(snapshot_path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", REPAIR_GOLDEN_CASES, ids=lambda case: case["name"])
def test_each_repair_recipe_has_a_golden_result(case: dict[str, object]) -> None:
    repaired_bytes = repair_epub(
        (FIXTURE_DIR / str(case["fixture"])).read_bytes(),
        list(case["fixes"]),
    )

    with zipfile.ZipFile(BytesIO(repaired_bytes), "r") as archive:
        infos = {info.filename: info for info in archive.infolist()}

        order_prefix = case.get("order_prefix")
        if order_prefix:
            actual_prefix = [info.filename for info in archive.infolist()][: len(order_prefix)]
            assert actual_prefix == order_prefix

        for archive_name in case.get("text_entries", []):
            expected = _golden_path(str(case["name"]), str(archive_name)).read_text(encoding="utf-8")
            actual = archive.read(str(archive_name)).decode("utf-8")
            assert _normalize_text_snapshot(actual) == _normalize_text_snapshot(expected)

        for archive_name, snapshot_name in case.get("hash_entries", {}).items():
            expected_hash = _golden_path(str(case["name"]), str(snapshot_name)).read_text(encoding="utf-8").strip()
            actual_hash = hashlib.sha256(archive.read(archive_name)).hexdigest()
            assert actual_hash == expected_hash

        for archive_name, compression in case.get("compressions", {}).items():
            assert infos[archive_name].compress_type == compression
