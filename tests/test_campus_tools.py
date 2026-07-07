from __future__ import annotations

from memory.memory_manager import MemoryManager
from tools.campus_tools import add_campus_place, decide_food


def test_campus_food_decision(tmp_path):
    memory = MemoryManager(tmp_path / "amoyclaw.db")
    added = add_campus_place(
        "南门沙茶面",
        location="南门",
        tags=["面", "热乎"],
        rating=5,
        price_level=2,
        mood="想吃热乎",
        memory=memory,
    )
    assert added["success"] is True

    picked = decide_food(mood="热乎", memory=memory)
    assert picked["success"] is True
    assert picked["data"]["picked"]["name"] == "南门沙茶面"
