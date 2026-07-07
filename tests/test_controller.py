from __future__ import annotations

from agent.controller import DemoAgentController
from memory.memory_manager import MemoryManager


def test_controller_profile_and_safe_file_flow(tmp_path):
    memory = MemoryManager(tmp_path / "amoyclaw.db")
    courses = tmp_path / "courses"
    courses.mkdir()
    (courses / "computer_vision.md").write_text("# 计算机视觉\n- CNN\n- IoU", encoding="utf-8")

    controller = DemoAgentController(memory=memory)
    profile = controller.handle("我是人工智能专业大三学生，计算机视觉考试在 7 月 10 日，我喜欢先做例题再复习概念，请记住。")
    assert "已保存" in profile.answer
    assert memory.get_profile("major") == "人工智能"

    denied = controller.handle("读取 ../../etc/passwd。")
    assert "拒绝" in denied.answer or "失败" in denied.answer


def test_controller_study_plan_exports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    memory = MemoryManager(tmp_path / "amoyclaw.db")
    memory.upsert_profile("available_hours_weekday", "3")
    memory.add_course("计算机视觉", exam_date="2026-07-10", difficulty=4)
    controller = DemoAgentController(memory=memory)

    response = controller.handle("根据我的三门考试和每天可用时间，生成一周计划并导出。")
    assert "一周复习计划" in response.answer
    assert any(item["tool"] == "create_study_plan" for item in response.tool_trace)


def test_controller_campus_career_and_deadline_flows(tmp_path):
    memory = MemoryManager(tmp_path / "amoyclaw.db")
    memory.add_course("计算机网络")
    memory.add_assignment("计算机网络", "完成实验报告", "2026-07-08", priority=4)
    controller = DemoAgentController(memory=memory)

    career = controller.handle("添加 Python 数据分析实习，截止 7 月 12 日，匹配度 86。")
    assert "已保存机会" in career.answer

    food = controller.handle("标记“南门沙茶面”好吃，适合想吃热乎的时候。")
    assert "已记住校园美食" in food.answer

    decision = controller.handle("今天吃什么，帮我抽签。")
    assert "今天抽到" in decision.answer

    deadlines = controller.handle("梳理 DDL 的紧急程度。")
    assert "DDL 紧急程度排序" in deadlines.answer
