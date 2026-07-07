from __future__ import annotations

from memory.memory_manager import MemoryManager
from tools.assignment_tools import add_assignment
from tools.career_tools import add_career_opportunity, filter_career_opportunities
from tools.deadline_tools import analyze_deadlines
from tools.document_tools import organize_document


def test_career_filter_and_deadline_analysis(tmp_path):
    memory = MemoryManager(tmp_path / "amoyclaw.db")
    memory.add_course("计算机网络")
    add_assignment("计算机网络", "完成实验报告", "2026-07-08", priority=5, memory=memory)
    add_career_opportunity(
        "Python 数据分析实习",
        organization="厦门某科技公司",
        deadline="2026-07-12",
        fit_score=86,
        tags=["Python", "数据"],
        memory=memory,
    )

    filtered = filter_career_opportunities(keyword="Python", min_fit_score=80, memory=memory)
    assert filtered["success"] is True
    assert len(filtered["data"]) == 1

    deadlines = analyze_deadlines(include_career=True, memory=memory)
    assert deadlines["success"] is True
    assert {item["type"] for item in deadlines["data"]["items"]} == {"assignment", "career"}


def test_document_organizer_extracts_dates():
    result = organize_document(
        "测试材料",
        "7 月 9 日提交实验报告。\n2026-07-12 前完成网申材料。\n记得更新简历。",
    )
    assert result["success"] is True
    assert "7月9日" in result["data"]["dates"]
    assert "2026-07-12" in result["data"]["dates"]
    assert "网申" in result["data"]["markdown"]
