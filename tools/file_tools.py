from __future__ import annotations

from pathlib import Path
from typing import Any

from config import BASE_DIR, COURSES_DIR, MAX_FILE_BYTES


SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown"}


def ok(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data, "error": None}


def fail(message: str) -> dict[str, Any]:
    return {"success": False, "data": None, "error": message}


def _resolve_course_path(path: str, courses_dir: Path = COURSES_DIR) -> Path:
    base = courses_dir.resolve()
    raw = Path(path)
    if raw.is_absolute():
        candidate = raw
    elif len(raw.parts) >= 2 and raw.parts[0] == "data" and raw.parts[1] == "courses":
        candidate = BASE_DIR / raw
    else:
        candidate = base / raw
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(base):
        raise ValueError("拒绝访问 data/courses/ 之外的路径")
    return resolved


def read_course_file(path: str, courses_dir: Path = COURSES_DIR, max_bytes: int = MAX_FILE_BYTES) -> dict[str, Any]:
    try:
        resolved = _resolve_course_path(path, courses_dir)
    except ValueError as exc:
        return fail(str(exc))
    if resolved.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return fail("仅支持 TXT、Markdown 文件")
    if not resolved.exists() or not resolved.is_file():
        return fail(f"文件不存在：{resolved.name}")
    if resolved.stat().st_size > max_bytes:
        return fail("文件超过 2MB 限制")
    try:
        content = resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = resolved.read_text(encoding="gb18030")
    return ok(
        {
            "filename": resolved.name,
            "relative_path": str(resolved.relative_to(courses_dir.resolve())),
            "content": content,
            "size": resolved.stat().st_size,
        }
    )


def list_course_files(courses_dir: Path = COURSES_DIR) -> list[dict[str, Any]]:
    base = courses_dir.resolve()
    if not base.exists():
        return []
    files: list[dict[str, Any]] = []
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(
                {
                    "name": path.name,
                    "relative_path": str(path.relative_to(base)),
                    "size": path.stat().st_size,
                }
            )
    return files
