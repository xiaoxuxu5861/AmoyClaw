from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from memory.database import Database


SENSITIVE_PATTERNS = [
    re.compile(r"api[_-]?key", re.I),
    re.compile(r"password|passwd|密码", re.I),
    re.compile(r"\b\d{17}[\dXx]\b"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def contains_sensitive_text(value: str) -> bool:
    return any(pattern.search(value) for pattern in SENSITIVE_PATTERNS)


class MemoryManager:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db = Database(db_path) if db_path else Database()
        self.db.init_db()

    def upsert_profile(self, key: str, value: str) -> dict[str, Any]:
        if contains_sensitive_text(f"{key} {value}"):
            raise ValueError("拒绝保存疑似敏感信息")
        self.db.execute(
            """
            INSERT INTO user_profile(key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, value, utc_now()),
        )
        return {"key": key, "value": value}

    def get_profile(self, key: str) -> str | None:
        row = self.db.query_one("SELECT value FROM user_profile WHERE key = ?", (key,))
        return str(row["value"]) if row else None

    def get_profile_dict(self) -> dict[str, str]:
        rows = self.db.query_all("SELECT key, value FROM user_profile ORDER BY key")
        return {str(row["key"]): str(row["value"]) for row in rows}

    def add_course(
        self,
        name: str,
        teacher: str | None = None,
        exam_date: str | None = None,
        difficulty: int = 3,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not name.strip():
            raise ValueError("课程名不能为空")
        difficulty = min(5, max(1, int(difficulty)))
        existing = self.get_course(name)
        if existing:
            course_id = int(existing["id"])
            self.db.execute(
                """
                UPDATE courses
                SET teacher = COALESCE(?, teacher),
                    exam_date = COALESCE(?, exam_date),
                    difficulty = ?,
                    notes = COALESCE(?, notes)
                WHERE id = ?
                """,
                (teacher, exam_date, difficulty, notes, course_id),
            )
            return self.get_course_by_id(course_id) or {"id": course_id, "name": name}
        course_id = self.db.execute(
            "INSERT INTO courses(name, teacher, exam_date, difficulty, notes) VALUES (?, ?, ?, ?, ?)",
            (name.strip(), teacher, exam_date, difficulty, notes),
        )
        return self.get_course_by_id(course_id) or {"id": course_id, "name": name}

    def get_course(self, name: str) -> dict[str, Any] | None:
        return self.db.query_one("SELECT * FROM courses WHERE name = ?", (name.strip(),))

    def get_course_by_id(self, course_id: int) -> dict[str, Any] | None:
        return self.db.query_one("SELECT * FROM courses WHERE id = ?", (course_id,))

    def list_courses(self) -> list[dict[str, Any]]:
        return self.db.query_all("SELECT * FROM courses ORDER BY exam_date IS NULL, exam_date, name")

    def add_assignment(self, course: str, title: str, deadline: str | None, priority: int = 3) -> dict[str, Any]:
        if not title.strip():
            raise ValueError("任务标题不能为空")
        course_row = self.get_course(course)
        if not course_row:
            raise ValueError(f"课程不存在：{course}")
        now = utc_now()
        assignment_id = self.db.execute(
            """
            INSERT INTO assignments(course_id, title, deadline, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, 'todo', ?, ?, ?)
            """,
            (course_row["id"], title.strip(), deadline, min(5, max(1, int(priority))), now, now),
        )
        return self.get_assignment(assignment_id) or {"id": assignment_id, "title": title}

    def get_assignment(self, assignment_id: int) -> dict[str, Any] | None:
        return self.db.query_one(
            """
            SELECT a.*, c.name AS course
            FROM assignments a
            LEFT JOIN courses c ON c.id = a.course_id
            WHERE a.id = ?
            """,
            (assignment_id,),
        )

    def list_assignments(self, status: str = "todo", due_within_days: int | None = None) -> list[dict[str, Any]]:
        rows = self.db.query_all(
            """
            SELECT a.*, c.name AS course
            FROM assignments a
            LEFT JOIN courses c ON c.id = a.course_id
            WHERE (? = 'all' OR a.status = ?)
            ORDER BY a.deadline IS NULL, a.deadline, a.priority DESC, a.id
            """,
            (status, status),
        )
        if due_within_days is None:
            return rows
        today = datetime.now().date()
        limit = today + timedelta(days=int(due_within_days))
        filtered: list[dict[str, Any]] = []
        for row in rows:
            deadline = row.get("deadline")
            if not deadline:
                continue
            try:
                deadline_date = datetime.fromisoformat(str(deadline)).date()
            except ValueError:
                continue
            if today <= deadline_date <= limit:
                filtered.append(row)
        return filtered

    def update_assignment(
        self,
        assignment_id: int,
        status: str | None = None,
        deadline: str | None = None,
    ) -> dict[str, Any]:
        current = self.get_assignment(assignment_id)
        if not current:
            raise ValueError(f"任务不存在：{assignment_id}")
        new_status = status or str(current["status"])
        new_deadline = deadline if deadline is not None else current.get("deadline")
        if new_status not in {"todo", "doing", "done", "blocked"}:
            raise ValueError("任务状态必须是 todo、doing、done 或 blocked")
        self.db.execute(
            "UPDATE assignments SET status = ?, deadline = ?, updated_at = ? WHERE id = ?",
            (new_status, new_deadline, utc_now(), assignment_id),
        )
        return self.get_assignment(assignment_id) or {"id": assignment_id}

    def add_note(self, course: str, title: str, content: str, tags: list[str] | None = None) -> dict[str, Any]:
        course_row = self.get_course(course)
        if not course_row:
            raise ValueError(f"课程不存在：{course}")
        if contains_sensitive_text(content):
            raise ValueError("拒绝保存疑似敏感信息")
        note_id = self.db.execute(
            "INSERT INTO notes(course_id, title, content, tags, created_at) VALUES (?, ?, ?, ?, ?)",
            (course_row["id"], title.strip(), content.strip(), json.dumps(tags or [], ensure_ascii=False), utc_now()),
        )
        return self.db.query_one(
            """
            SELECT n.*, c.name AS course
            FROM notes n
            LEFT JOIN courses c ON c.id = n.course_id
            WHERE n.id = ?
            """,
            (note_id,),
        ) or {"id": note_id}

    def search_notes(self, keyword: str, course: str | None = None) -> list[dict[str, Any]]:
        like = f"%{keyword.strip()}%"
        params: tuple[Any, ...]
        if course:
            params = (like, like, course)
            sql = """
                SELECT n.*, c.name AS course
                FROM notes n
                LEFT JOIN courses c ON c.id = n.course_id
                WHERE (n.title LIKE ? OR n.content LIKE ?) AND c.name = ?
                ORDER BY n.created_at DESC
            """
        else:
            params = (like, like)
            sql = """
                SELECT n.*, c.name AS course
                FROM notes n
                LEFT JOIN courses c ON c.id = n.course_id
                WHERE n.title LIKE ? OR n.content LIKE ?
                ORDER BY n.created_at DESC
            """
        return self.db.query_all(sql, params)

    def remember_fact(self, category: str, content: str, importance: int = 3, source: str = "user") -> dict[str, Any]:
        if contains_sensitive_text(content):
            raise ValueError("拒绝保存疑似敏感信息")
        memory_id = self.db.execute(
            "INSERT INTO memories(category, content, importance, source, updated_at) VALUES (?, ?, ?, ?, ?)",
            (category, content.strip(), min(5, max(1, int(importance))), source, utc_now()),
        )
        return {"id": memory_id, "category": category, "content": content}

    def recall_memory(self, query: str, category: str | None = None) -> dict[str, list[dict[str, Any]]]:
        query = query.strip()
        like = f"%{query}%" if query else "%"
        category_clause = "AND category = ?" if category else ""
        params: tuple[Any, ...] = (like, category) if category else (like,)
        return {
            "profile": self.db.query_all(
                "SELECT key, value, updated_at FROM user_profile WHERE key LIKE ? OR value LIKE ? ORDER BY updated_at DESC",
                (like, like),
            ),
            "courses": self.db.query_all(
                "SELECT * FROM courses WHERE name LIKE ? OR COALESCE(notes, '') LIKE ? ORDER BY exam_date IS NULL, exam_date",
                (like, like),
            ),
            "assignments": self.db.query_all(
                """
                SELECT a.*, c.name AS course
                FROM assignments a
                LEFT JOIN courses c ON c.id = a.course_id
                WHERE a.title LIKE ? OR c.name LIKE ?
                ORDER BY a.deadline IS NULL, a.deadline
                """,
                (like, like),
            ),
            "notes": self.search_notes(query) if query else [],
            "memories": self.db.query_all(
                f"SELECT * FROM memories WHERE content LIKE ? {category_clause} ORDER BY importance DESC, updated_at DESC",
                params,
            ),
            "career": self.list_career_opportunities(keyword=query) if query else [],
            "places": self.list_campus_places(keyword=query) if query else [],
        }

    def add_career_opportunity(
        self,
        title: str,
        organization: str | None = None,
        opportunity_type: str = "internship",
        location: str | None = None,
        work_mode: str | None = None,
        deadline: str | None = None,
        status: str = "saved",
        fit_score: int = 60,
        tags: list[str] | None = None,
        source: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not title.strip():
            raise ValueError("机会标题不能为空")
        if status not in {"saved", "applying", "applied", "interview", "offered", "rejected", "archived"}:
            raise ValueError("机会状态不合法")
        opportunity_type = opportunity_type or "internship"
        now = utc_now()
        opportunity_id = self.db.execute(
            """
            INSERT INTO career_opportunities(
                title, organization, opportunity_type, location, work_mode, deadline,
                status, fit_score, tags, source, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title.strip(),
                organization,
                opportunity_type,
                location,
                work_mode,
                deadline,
                status,
                min(100, max(0, int(fit_score))),
                json.dumps(tags or [], ensure_ascii=False),
                source,
                notes,
                now,
                now,
            ),
        )
        return self.get_career_opportunity(opportunity_id) or {"id": opportunity_id, "title": title}

    def get_career_opportunity(self, opportunity_id: int) -> dict[str, Any] | None:
        return self.db.query_one("SELECT * FROM career_opportunities WHERE id = ?", (opportunity_id,))

    def list_career_opportunities(
        self,
        keyword: str | None = None,
        opportunity_type: str | None = None,
        status: str | None = None,
        min_fit_score: int | None = None,
        due_within_days: int | None = None,
    ) -> list[dict[str, Any]]:
        like = f"%{keyword.strip()}%" if keyword else "%"
        rows = self.db.query_all(
            """
            SELECT *
            FROM career_opportunities
            WHERE (title LIKE ? OR COALESCE(organization, '') LIKE ? OR COALESCE(tags, '') LIKE ? OR COALESCE(notes, '') LIKE ?)
              AND (? IS NULL OR opportunity_type = ?)
              AND (? IS NULL OR status = ?)
              AND (? IS NULL OR fit_score >= ?)
            ORDER BY deadline IS NULL, deadline, fit_score DESC, id DESC
            """,
            (
                like,
                like,
                like,
                like,
                opportunity_type,
                opportunity_type,
                status,
                status,
                min_fit_score,
                min_fit_score,
            ),
        )
        if due_within_days is None:
            return rows
        today = date.today()
        limit = today + timedelta(days=int(due_within_days))
        filtered = []
        for row in rows:
            deadline = row.get("deadline")
            if not deadline:
                continue
            try:
                deadline_date = datetime.fromisoformat(str(deadline)).date()
            except ValueError:
                continue
            if today <= deadline_date <= limit:
                filtered.append(row)
        return filtered

    def update_career_status(self, opportunity_id: int, status: str) -> dict[str, Any]:
        if status not in {"saved", "applying", "applied", "interview", "offered", "rejected", "archived"}:
            raise ValueError("机会状态不合法")
        if not self.get_career_opportunity(opportunity_id):
            raise ValueError(f"机会不存在：{opportunity_id}")
        self.db.execute(
            "UPDATE career_opportunities SET status = ?, updated_at = ? WHERE id = ?",
            (status, utc_now(), opportunity_id),
        )
        return self.get_career_opportunity(opportunity_id) or {"id": opportunity_id}

    def add_campus_place(
        self,
        name: str,
        category: str = "food",
        location: str | None = None,
        tags: list[str] | None = None,
        rating: int = 4,
        price_level: int = 2,
        mood: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not name.strip():
            raise ValueError("地点名称不能为空")
        now = utc_now()
        self.db.execute(
            """
            INSERT INTO campus_places(
                name, category, location, tags, rating, price_level, mood, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                category = excluded.category,
                location = excluded.location,
                tags = excluded.tags,
                rating = excluded.rating,
                price_level = excluded.price_level,
                mood = excluded.mood,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (
                name.strip(),
                category or "food",
                location,
                json.dumps(tags or [], ensure_ascii=False),
                min(5, max(1, int(rating))),
                min(5, max(1, int(price_level))),
                mood,
                notes,
                now,
                now,
            ),
        )
        return self.db.query_one("SELECT * FROM campus_places WHERE name = ?", (name.strip(),)) or {"name": name}

    def list_campus_places(
        self,
        keyword: str | None = None,
        category: str | None = None,
        mood: str | None = None,
        max_price_level: int | None = None,
    ) -> list[dict[str, Any]]:
        like = f"%{keyword.strip()}%" if keyword else "%"
        mood_like = f"%{mood.strip()}%" if mood else "%"
        return self.db.query_all(
            """
            SELECT *
            FROM campus_places
            WHERE (name LIKE ? OR COALESCE(location, '') LIKE ? OR COALESCE(tags, '') LIKE ? OR COALESCE(notes, '') LIKE ?)
              AND (? IS NULL OR category = ?)
              AND (? IS NULL OR COALESCE(mood, '') LIKE ? OR COALESCE(tags, '') LIKE ?)
              AND (? IS NULL OR price_level <= ?)
            ORDER BY last_picked_at IS NOT NULL, rating DESC, price_level, name
            """,
            (
                like,
                like,
                like,
                like,
                category,
                category,
                mood,
                mood_like,
                mood_like,
                max_price_level,
                max_price_level,
            ),
        )

    def mark_campus_place_picked(self, place_id: int) -> dict[str, Any]:
        current = self.db.query_one("SELECT * FROM campus_places WHERE id = ?", (place_id,))
        if not current:
            raise ValueError(f"地点不存在：{place_id}")
        self.db.execute(
            "UPDATE campus_places SET last_picked_at = ?, updated_at = ? WHERE id = ?",
            (utc_now(), utc_now(), place_id),
        )
        return self.db.query_one("SELECT * FROM campus_places WHERE id = ?", (place_id,)) or {"id": place_id}

    def log_tool(self, tool_name: str, arguments: dict[str, Any], result: dict[str, Any], status: str) -> None:
        self.db.execute(
            "INSERT INTO tool_logs(tool_name, arguments, result, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                tool_name,
                json.dumps(arguments, ensure_ascii=False, default=str),
                json.dumps(result, ensure_ascii=False, default=str),
                status,
                utc_now(),
            ),
        )

    def list_tool_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.db.query_all("SELECT * FROM tool_logs ORDER BY id DESC LIMIT ?", (int(limit),))
