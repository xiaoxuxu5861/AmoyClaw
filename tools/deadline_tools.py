from __future__ import annotations

from datetime import date, datetime
from typing import Any

from memory.memory_manager import MemoryManager
from tools.file_tools import ok


def _days_left(deadline: str | None) -> int | None:
    if not deadline:
        return None
    try:
        return (datetime.fromisoformat(deadline).date() - date.today()).days
    except ValueError:
        return None


def _score(days_left: int | None, priority: int = 3, fit_score: int | None = None) -> tuple[int, str]:
    fit_bonus = int((fit_score or 0) / 20)
    if days_left is None:
        return 18 + priority + fit_bonus, "没有明确截止日期，先保持跟踪"
    if days_left < 0:
        return 100 + priority + fit_bonus, f"已逾期 {-days_left} 天，需要立即处理或改期"
    if days_left == 0:
        return 96 + priority + fit_bonus, "今天截止，优先级最高"
    if days_left == 1:
        return 88 + priority + fit_bonus, "明天截止，今天必须推进"
    if days_left <= 3:
        return 76 + priority + fit_bonus, f"{days_left} 天内截止，建议拆成今日行动"
    if days_left <= 7:
        return 58 + priority + fit_bonus, f"{days_left} 天内截止，需要排进本周"
    if days_left <= 14:
        return 38 + priority + fit_bonus, f"{days_left} 天后截止，适合提前准备"
    return 20 + priority + fit_bonus, "时间较远，低频跟踪即可"


def analyze_deadlines(
    include_career: bool = True,
    status: str = "todo",
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    rows: list[dict[str, Any]] = []
    for task in memory.list_assignments(status=status):
        days = _days_left(task.get("deadline"))
        urgency, reason = _score(days, priority=int(task.get("priority") or 3))
        rows.append(
            {
                "type": "assignment",
                "id": task["id"],
                "title": task["title"],
                "context": task.get("course"),
                "deadline": task.get("deadline"),
                "days_left": days,
                "urgency_score": urgency,
                "reason": reason,
                "next_action": "拆出 30-60 分钟可完成的小步骤",
            }
        )
    if include_career:
        for opportunity in memory.list_career_opportunities():
            if opportunity.get("status") in {"rejected", "archived"}:
                continue
            days = _days_left(opportunity.get("deadline"))
            urgency, reason = _score(days, priority=3, fit_score=int(opportunity.get("fit_score") or 0))
            rows.append(
                {
                    "type": "career",
                    "id": opportunity["id"],
                    "title": opportunity["title"],
                    "context": opportunity.get("organization"),
                    "deadline": opportunity.get("deadline"),
                    "days_left": days,
                    "urgency_score": urgency,
                    "reason": reason,
                    "next_action": "检查岗位要求，补简历关键词并决定是否投递",
                }
            )
    rows.sort(key=lambda item: item["urgency_score"], reverse=True)
    return ok({"items": rows, "count": len(rows)})
