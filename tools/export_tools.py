from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from config import OUTPUTS_DIR
from tools.file_tools import fail, ok


def _safe_filename(filename: str, file_format: str) -> str:
    stem = Path(filename).name
    stem = re.sub(r"[^A-Za-z0-9_.\-\u4e00-\u9fff]+", "_", stem).strip("._")
    if not stem:
        stem = "amoyclaw_report"
    suffix = f".{file_format.lstrip('.').lower()}"
    if Path(stem).suffix.lower() not in {".md", ".txt"}:
        stem += suffix
    return stem


def export_report(
    filename: str,
    content: str,
    format: str = "md",
    overwrite: bool = False,
    outputs_dir: Path = OUTPUTS_DIR,
) -> dict[str, Any]:
    file_format = format.lower().lstrip(".")
    if file_format not in {"md", "txt"}:
        return fail("仅支持导出 md 或 txt")
    outputs_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(filename, file_format)
    target = (outputs_dir / safe_name).resolve()
    base = outputs_dir.resolve()
    if not target.is_relative_to(base):
        return fail("拒绝目录穿越")
    if target.exists() and not overwrite:
        return fail("文件已存在，覆盖前需要确认")
    target.write_text(content, encoding="utf-8")
    return ok({"filename": target.name, "path": str(target), "size": target.stat().st_size})
