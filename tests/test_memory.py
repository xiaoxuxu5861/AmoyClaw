from __future__ import annotations

from memory.memory_manager import MemoryManager


def test_profile_and_assignment_persist(tmp_path):
    db_path = tmp_path / "amoyclaw.db"
    memory = MemoryManager(db_path)
    memory.upsert_profile("major", "人工智能")
    memory.add_course("计算机视觉", exam_date="2026-07-10", difficulty=4)
    assignment = memory.add_assignment("计算机视觉", "刷卷积例题", "2026-07-08", priority=4)

    reloaded = MemoryManager(db_path)
    assert reloaded.get_profile("major") == "人工智能"
    assert reloaded.get_course("计算机视觉")["difficulty"] == 4
    assert reloaded.get_assignment(assignment["id"])["title"] == "刷卷积例题"


def test_sensitive_profile_is_rejected(tmp_path):
    memory = MemoryManager(tmp_path / "amoyclaw.db")
    try:
        memory.upsert_profile("api_key", "sk-abcdefghijklmnopqrstuvwxyz")
    except ValueError as exc:
        assert "敏感" in str(exc)
    else:
        raise AssertionError("sensitive value should be rejected")
