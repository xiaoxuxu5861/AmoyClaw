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


def _infer_fit_score(text: str, target_keywords: list[str] | None, base_score: int = 60) -> int:
    if not target_keywords:
        return base_score
    lowered = text.lower()
    hits = sum(1 for keyword in target_keywords if keyword.lower() in lowered)
    return min(100, max(20, base_score + hits * 10 - (len(target_keywords) - hits) * 4))


def add_career_opportunity(
    title: str,
    organization: str | None = None,
    opportunity_type: str = "internship",
    location: str | None = None,
    work_mode: str | None = None,
    deadline: str | None = None,
    status: str = "saved",
    fit_score: int | None = None,
    tags: list[str] | None = None,
    source: str | None = None,
    notes: str | None = None,
    target_keywords: list[str] | None = None,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    valid_deadline = _validate_date(deadline)
    if valid_deadline == "":
        return fail("截止日期必须使用 YYYY-MM-DD 格式")
    full_text = " ".join([title, organization or "", " ".join(tags or []), notes or ""])
    score = fit_score if fit_score is not None else _infer_fit_score(full_text, target_keywords)
    try:
        opportunity = memory.add_career_opportunity(
            title=title,
            organization=organization,
            opportunity_type=opportunity_type,
            location=location,
            work_mode=work_mode,
            deadline=valid_deadline,
            status=status,
            fit_score=score,
            tags=tags,
            source=source,
            notes=notes,
        )
    except ValueError as exc:
        return fail(str(exc))
    return ok(opportunity)


def filter_career_opportunities(
    keyword: str | None = None,
    opportunity_type: str | None = None,
    status: str | None = None,
    min_fit_score: int | None = None,
    due_within_days: int | None = None,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    rows = memory.list_career_opportunities(
        keyword=keyword,
        opportunity_type=opportunity_type,
        status=status,
        min_fit_score=min_fit_score,
        due_within_days=due_within_days,
    )
    return ok(rows)


def update_career_status(
    opportunity_id: int,
    status: str,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    try:
        opportunity = memory.update_career_status(opportunity_id, status)
    except ValueError as exc:
        return fail(str(exc))
    return ok(opportunity)
