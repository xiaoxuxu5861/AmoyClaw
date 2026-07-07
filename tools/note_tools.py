from __future__ import annotations

from typing import Any

from memory.memory_manager import MemoryManager
from tools.file_tools import fail, ok


def save_note(
    course: str,
    title: str,
    content: str,
    tags: list[str] | None = None,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    try:
        note = memory.add_note(course, title, content, tags or [])
    except ValueError as exc:
        return fail(str(exc))
    return ok(note)


def search_notes(
    keyword: str,
    course: str | None = None,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    return ok(memory.search_notes(keyword, course=course))
