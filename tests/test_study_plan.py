from __future__ import annotations

from memory.memory_manager import MemoryManager
from tools.study_plan_tools import create_study_plan


def test_study_plan_respects_daily_capacity(tmp_path):
    memory = MemoryManager(tmp_path / "amoyclaw.db")
    memory.add_course("计算机视觉", exam_date="2026-07-10", difficulty=4)
    memory.add_course("机器学习", exam_date="2026-07-12", difficulty=5)

    result = create_study_plan(
        ["计算机视觉", "机器学习"],
        "2026-07-04",
        "2026-07-06",
        weekday_hours=3,
        weekend_hours=5,
        memory=memory,
    )

    assert result["success"] is True
    for day in result["data"]["days"]:
        capacity = 5 if day["date"] in {"2026-07-04", "2026-07-05"} else 3
        assert day["total_hours"] <= capacity
        assert day["items"]
