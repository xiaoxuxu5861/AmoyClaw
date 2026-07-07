from __future__ import annotations

from memory.memory_manager import MemoryManager
from tools.assignment_tools import add_assignment, list_assignments, update_assignment


def test_assignment_tools(tmp_path):
    memory = MemoryManager(tmp_path / "amoyclaw.db")
    memory.add_course("计算机网络")

    added = add_assignment("计算机网络", "完成实验报告", "2026-07-08", memory=memory)
    assert added["success"] is True

    listed = list_assignments(status="todo", due_within_days=30, memory=memory)
    assert len(listed["data"]) == 1

    updated = update_assignment(added["data"]["id"], status="done", memory=memory)
    assert updated["success"] is True
    assert updated["data"]["status"] == "done"


def test_assignment_rejects_missing_course(tmp_path):
    memory = MemoryManager(tmp_path / "amoyclaw.db")
    result = add_assignment("不存在", "任务", "2026-07-08", memory=memory)
    assert result["success"] is False
    assert "课程不存在" in result["error"]
