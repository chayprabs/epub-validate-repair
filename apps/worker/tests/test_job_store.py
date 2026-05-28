import os
import time
from pathlib import Path

import pytest

from src.storage.jobs import JobStore


def _age_job(job_dir: Path, age_seconds: int) -> None:
    stale_time = time.time() - age_seconds
    for child in [job_dir, *job_dir.rglob("*")]:
        os.utime(child, (stale_time, stale_time))


def test_create_job_purges_expired_directories(tmp_path: Path) -> None:
    store = JobStore(root_dir=tmp_path, ttl_seconds=60)

    expired_job_dir = tmp_path / "expired"
    expired_job_dir.mkdir()
    expired_input = expired_job_dir / "old.epub"
    expired_input.write_bytes(b"old")
    _age_job(expired_job_dir, age_seconds=120)

    job_id, created_path = store.create_job("fresh.epub", b"fresh")

    assert job_id
    assert created_path.exists()
    assert not expired_job_dir.exists()


def test_resolve_input_refuses_expired_jobs(tmp_path: Path) -> None:
    store = JobStore(root_dir=tmp_path, ttl_seconds=60)
    job_id, created_path = store.create_job("fresh.epub", b"fresh")
    _age_job(created_path.parent, age_seconds=120)

    with pytest.raises(FileNotFoundError):
        store.resolve_input(job_id)
