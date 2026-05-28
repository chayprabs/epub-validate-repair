from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from src.models import ConversionOptions, ConversionTarget

OUTPUT_FILENAMES: dict[ConversionTarget, str] = {
    "epub": "converted.epub",
    "mobi": "converted.mobi",
    "azw3": "converted.azw3",
    "pdf": "converted.pdf",
    "html": "converted.html",
}


def convert_ebook(source_path: Path, target: ConversionTarget, options: ConversionOptions) -> tuple[bytes, str]:
    executable = os.environ.get("EPUBDOCTOR_EBOOK_CONVERT", "ebook-convert")
    resolved_executable = shutil.which(executable) if os.path.basename(executable) == executable else executable
    if not resolved_executable:
        raise FileNotFoundError(f"ebook-convert executable not found: {executable}")

    with tempfile.TemporaryDirectory(prefix="epubdoctor-convert-") as temp_dir:
        output_name = OUTPUT_FILENAMES[target]
        output_path = Path(temp_dir) / output_name
        command = [resolved_executable, str(source_path), str(output_path)]
        if str(resolved_executable).endswith(".py"):
            command = [sys.executable, str(resolved_executable), str(source_path), str(output_path)]
        command.extend(_build_option_args(options, resolved_executable))
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode != 0:
            raise RuntimeError(process.stderr or process.stdout or "ebook-convert failed")
        return output_path.read_bytes(), process.stdout.strip() or "Conversion complete."


def _build_option_args(options: ConversionOptions, executable: str) -> list[str]:
    if executable.endswith(".py") or "fake_ebook_convert.py" in executable:
        args: list[str] = []
        if options.tocDepth is not None:
            args.extend(["--epubdoctor-toc-depth", str(options.tocDepth)])
        if options.embedFonts:
            args.append("--epubdoctor-embed-fonts")
        if options.stripCss:
            args.append("--epubdoctor-strip-css")
        if options.pageSize:
            args.extend(["--epubdoctor-page-size", options.pageSize])
        return args

    args = []
    if options.pageSize:
        args.extend(["--paper-size", options.pageSize])
    if options.embedFonts:
        args.append("--embed-all-fonts")
    return args
