from __future__ import annotations

import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

LOGGER = logging.getLogger("epubdoctor.runtime")


@dataclass
class RuntimeStatus:
    epubcheck_ready: bool
    calibre_ready: bool
    java_ready: bool
    message: str


def prewarm_runtime() -> RuntimeStatus:
    jar_path = Path(os.environ.get("EPUBDOCTOR_EPUBCHECK_JAR", "/opt/epubcheck/epubcheck.jar"))
    java_executable = shutil.which("java")
    calibre_executable = shutil.which(os.environ.get("EPUBDOCTOR_EBOOK_CONVERT", "ebook-convert"))

    java_ready = java_executable is not None
    calibre_ready = calibre_executable is not None
    epubcheck_ready = False

    if java_ready and jar_path.exists():
        try:
            process = subprocess.run(
                [java_executable, "-jar", str(jar_path), "--version"],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            epubcheck_ready = process.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            epubcheck_ready = False

    message = (
        f"runtime warm-up: java={'ok' if java_ready else 'missing'}, "
        f"calibre={'ok' if calibre_ready else 'missing'}, "
        f"epubcheck={'ok' if epubcheck_ready else 'missing'}"
    )
    LOGGER.info(message)
    return RuntimeStatus(
        epubcheck_ready=epubcheck_ready,
        calibre_ready=calibre_ready,
        java_ready=java_ready,
        message=message,
    )
