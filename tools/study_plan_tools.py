from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from memory.memory_manager import MemoryManager
from tools.file_tools import fail, ok


def _date(value: str) -> date:
    return datetime.fromisoformat(value).date()


def _daterange(start: date, end: date) -> list[date]:
    days = (end - start).days
    return [start + timedelta(days=offset) for offset in range(days + 1)]


def _goal_for(distance: int, course: str) -> str:
    if distance <= 1:
        return f"{course}：限时模拟、错题复盘、整理最后疑问"
    if distance <= 4:
        return f"{course}：高频考点刷题，补齐薄弱章节"
    return f"{course}：梳理章节框架，完成例题和笔记复述"


def create_study_plan(
    course_names: list[str],
    start_date: str,
    end_date: str,
    weekday_hours: float,
    weekend_hours: float,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    try:
        start = _date(start_date)
        end = _date(end_date)
    except ValueError:
        return fail("开始和结束日期必须使用 YYYY-MM-DD 格式")
    if end < start:
        return fail("结束日期不能早于开始日期")
    if weekday_hours <= 0 or weekend_hours <= 0:
        return fail("每日可用时间必须大于 0")

    courses = []
    for name in course_names:
        row = memory.get_course(name)
        if row:
            courses.append(row)
    if not courses:
        return fail("没有找到可用于生成计划的课程")

    days: list[dict[str, Any]] = []
    for current in _daterange(start, end):
        capacity = weekend_hours if current.weekday() >= 5 else weekday_hours
        weighted: list[tuple[dict[str, Any], float, int]] = []
        for course in courses:
            exam_raw = course.get("exam_date")
            distance = 14
            if exam_raw:
                try:
                    exam_date = _date(str(exam_raw))
                except ValueError:
                    exam_date = current + timedelta(days=14)
                distance = (exam_date - current).days
                if distance < 0:
                    continue
            urgency = 1 + max(0, 14 - distance) / 4
            weight = float(course.get("difficulty") or 3) * urgency
            weighted.append((course, weight, distance))

        if not weighted:
            days.append({"date": current.isoformat(), "items": [], "total_hours": 0})
            continue

        total_weight = sum(item[1] for item in weighted)
        items: list[dict[str, Any]] = []
        used = 0.0
        for index, (course, weight, distance) in enumerate(weighted):
            if index == len(weighted) - 1:
                hours = max(0.25, round(capacity - used, 2))
            else:
                hours = max(0.25, round(capacity * weight / total_weight, 2))
                used += hours
            items.append(
                {
                    "course": course["name"],
                    "hours": hours,
                    "goal": _goal_for(distance, str(course["name"])),
                    "exam_date": course.get("exam_date"),
                    "difficulty": course.get("difficulty"),
                }
            )
        total_hours = round(sum(float(item["hours"]) for item in items), 2)
        if total_hours > capacity:
            overflow = round(total_hours - capacity, 2)
            items[-1]["hours"] = round(max(0.25, float(items[-1]["hours"]) - overflow), 2)
            total_hours = round(sum(float(item["hours"]) for item in items), 2)
        days.append({"date": current.isoformat(), "items": items, "total_hours": total_hours})

    return ok(
        {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "weekday_hours": weekday_hours,
            "weekend_hours": weekend_hours,
            "days": days,
            "course_count": len(courses),
        }
    )
