from __future__ import annotations

from datetime import datetime
from typing import Any

from memory.memory_manager import MemoryManager
from tools.file_tools import fail, ok


def _validate_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date().isoformat()
    except ValueError:
        return ""


def add_assignment(
    course: str,
    title: str,
    deadline: str | None,
    priority: int = 3,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    valid_deadline = _validate_date(deadline)
    if valid_deadline == "":
        return fail("截止日期必须使用 YYYY-MM-DD 格式")
    try:
        assignment = memory.add_assignment(course, title, valid_deadline, priority)
    except ValueError as exc:
        return fail(str(exc))
    return ok(assignment)


def list_assignments(
    status: str = "todo",
    due_within_days: int | None = None,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    if status not in {"todo", "doing", "done", "blocked", "all"}:
        return fail("任务状态必须是 todo、doing、done、blocked 或 all")
    return ok(memory.list_assignments(status=status, due_within_days=due_within_days))


def update_assignment(
    assignment_id: int,
    status: str | None = None,
    deadline: str | None = None,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    valid_deadline = _validate_date(deadline)
    if valid_deadline == "":
        return fail("截止日期必须使用 YYYY-MM-DD 格式")
    try:
        assignment = memory.update_assignment(assignment_id, status=status, deadline=valid_deadline)
    except ValueError as exc:
        return fail(str(exc))
    return ok(assignment)
