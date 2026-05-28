from __future__ import annotations

import csv
import io
import tempfile
import zipfile
from pathlib import Path

from src.core.repair import repair_epub
from src.core.validation import DRMProtectedError, validate_epub
from src.models import BatchItemResult, BatchResult, RepairFixId
from src.storage.jobs import JobStore


def process_batch_archive(
    archive_bytes: bytes,
    batch_job_id: str,
    artifact_base_url: str,
    job_store: JobStore,
) -> BatchResult:
    items: list[BatchItemResult] = []
    repaired_files: dict[str, bytes] = {}

    with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as archive:
        entries = [info for info in archive.infolist() if not info.is_dir()]
        for entry in entries:
            if not entry.filename.lower().endswith(".epub"):
                items.append(
                    BatchItemResult(
                        filename=entry.filename,
                        status="unsupported",
                        originalErrors=0,
                        repairedErrors=0,
                    )
                )
                continue

            payload = archive.read(entry.filename)
            item, repaired_bytes = _process_epub_entry(entry.filename, payload)
            items.append(item)
            if repaired_bytes is not None:
                repaired_files[_repaired_filename(entry.filename)] = repaired_bytes

    csv_content = _render_csv(items)
    repaired_zip_bytes = _build_repaired_zip(repaired_files)
    job_store.write_text_artifact(batch_job_id, "batch-report.csv", csv_content)
    job_store.write_binary_artifact(batch_job_id, "batch-repaired.zip", repaired_zip_bytes)

    return BatchResult(
        jobId=batch_job_id,
        csvUrl=f"{artifact_base_url}/{batch_job_id}/batch-report.csv",
        repairedZipUrl=f"{artifact_base_url}/{batch_job_id}/batch-repaired.zip",
        items=items,
    )


def _process_epub_entry(filename: str, payload: bytes) -> tuple[BatchItemResult, bytes | None]:
    with tempfile.TemporaryDirectory(prefix="epubdoctor-batch-") as temp_dir:
        source_path = Path(temp_dir) / "source.epub"
        source_path.write_bytes(payload)
        try:
            validation = validate_epub(str(source_path), "batch-item", "http://batch.local/artifacts")
        except DRMProtectedError:
            return BatchItemResult(
                filename=filename,
                status="failed",
                originalErrors=0,
                repairedErrors=0,
                appliedFixes=[],
            ), None
        fix_ids = _collect_fix_ids(validation.messages)

        if validation.pass_:
            return BatchItemResult(
                filename=filename,
                status="passed",
                originalErrors=validation.counts["error"],
                repairedErrors=validation.counts["error"],
                appliedFixes=[],
            ), None

        if not fix_ids:
            return BatchItemResult(
                filename=filename,
                status="failed",
                originalErrors=validation.counts["error"],
                repairedErrors=validation.counts["error"],
                appliedFixes=[],
            ), None

        repaired_bytes = repair_epub(payload, fix_ids)
        repaired_path = Path(temp_dir) / "repaired.epub"
        repaired_path.write_bytes(repaired_bytes)
        repaired_validation = validate_epub(str(repaired_path), "batch-item-repaired", "http://batch.local/artifacts")
        item = BatchItemResult(
            filename=filename,
            status="repaired" if repaired_validation.pass_ else "failed",
            originalErrors=validation.counts["error"],
            repairedErrors=repaired_validation.counts["error"],
            appliedFixes=fix_ids,
        )
        return item, repaired_bytes if repaired_validation.pass_ else None


def _collect_fix_ids(messages: list) -> list[RepairFixId]:
    seen: list[RepairFixId] = []
    for message in messages:
        fixable_by = getattr(message, "fixableBy", None)
        if fixable_by and fixable_by not in seen:
            seen.append(fixable_by)
    return seen


def _render_csv(items: list[BatchItemResult]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["filename", "status", "original_errors", "repaired_errors", "applied_fixes"])
    for item in items:
        writer.writerow(
            [
                item.filename,
                item.status,
                item.originalErrors,
                item.repairedErrors,
                ";".join(item.appliedFixes),
            ]
        )
    return buffer.getvalue()


def _build_repaired_zip(repaired_files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for archive_name in sorted(repaired_files):
            archive.writestr(archive_name, repaired_files[archive_name])
    return buffer.getvalue()


def _repaired_filename(filename: str) -> str:
    path = Path(filename)
    stem = path.stem or "book"
    return f"{stem}-repaired.epub"
