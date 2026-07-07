from __future__ import annotations

import random
from typing import Any

from memory.memory_manager import MemoryManager
from tools.file_tools import fail, ok


def add_campus_place(
    name: str,
    category: str = "food",
    location: str | None = None,
    tags: list[str] | None = None,
    rating: int = 4,
    price_level: int = 2,
    mood: str | None = None,
    notes: str | None = None,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    try:
        place = memory.add_campus_place(
            name=name,
            category=category,
            location=location,
            tags=tags,
            rating=rating,
            price_level=price_level,
            mood=mood,
            notes=notes,
        )
    except ValueError as exc:
        return fail(str(exc))
    return ok(place)


def list_campus_places(
    keyword: str | None = None,
    category: str | None = None,
    mood: str | None = None,
    max_price_level: int | None = None,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    return ok(memory.list_campus_places(keyword=keyword, category=category, mood=mood, max_price_level=max_price_level))


def decide_food(
    mood: str | None = None,
    max_price_level: int | None = None,
    memory: MemoryManager | None = None,
) -> dict[str, Any]:
    memory = memory or MemoryManager()
    places = memory.list_campus_places(category="food", mood=mood, max_price_level=max_price_level)
    if not places:
        return fail("还没有符合条件的校园美食地点")
    pool: list[dict[str, Any]] = []
    for place in places[:12]:
        weight = max(1, int(place.get("rating") or 3))
        pool.extend([place] * weight)
    picked = random.choice(pool)
    try:
        updated = memory.mark_campus_place_picked(int(picked["id"]))
    except ValueError:
        updated = picked
    reason_parts = [
        f"评分 {picked.get('rating')}/5",
        f"价格等级 {picked.get('price_level')}/5",
    ]
    if picked.get("mood"):
        reason_parts.append(f"适合：{picked['mood']}")
    return ok({"picked": updated, "reason": "；".join(reason_parts), "candidate_count": len(places)})
