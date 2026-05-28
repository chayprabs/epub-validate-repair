import json
import tempfile
import uuid
from pathlib import Path


class JobStore:
    def __init__(self, root_dir: Path | None = None) -> None:
        base_dir = root_dir or Path(tempfile.gettempdir()) / "epubdoctor"
        self.root_dir = base_dir.resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def create_job(self, filename: str, payload: bytes) -> tuple[str, Path]:
        job_id = uuid.uuid4().hex
        job_dir = self.root_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        file_path = job_dir / filename
        file_path.write_bytes(payload)
        return job_id, file_path

    def write_text_artifact(self, job_id: str, artifact_name: str, content: str) -> Path:
        artifact_path = self.root_dir / job_id / artifact_name
        artifact_path.write_text(content, encoding="utf-8")
        return artifact_path

    def write_json_artifact(self, job_id: str, artifact_name: str, payload: dict) -> Path:
        artifact_path = self.root_dir / job_id / artifact_name
        artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return artifact_path

    def write_binary_artifact(self, job_id: str, artifact_name: str, payload: bytes) -> Path:
        artifact_path = self.root_dir / job_id / artifact_name
        artifact_path.write_bytes(payload)
        return artifact_path

    def resolve_input(self, job_id: str) -> Path:
        job_dir = (self.root_dir / job_id).resolve()
        if self.root_dir != job_dir.parent or not job_dir.exists():
            raise FileNotFoundError(job_id)

        candidates = sorted(
            path
            for path in job_dir.iterdir()
            if path.is_file() and path.name not in {"report.json", "report.html"}
        )
        if not candidates:
            raise FileNotFoundError(job_id)
        return candidates[0]

    def resolve_artifact(self, job_id: str, artifact_name: str) -> Path:
        artifact_path = (self.root_dir / job_id / artifact_name).resolve()
        if self.root_dir not in artifact_path.parents:
            raise FileNotFoundError(artifact_name)
        if not artifact_path.exists():
            raise FileNotFoundError(artifact_name)
        return artifact_path
