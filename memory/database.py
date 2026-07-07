from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from config import DB_PATH, SCHEMA_PATH


class Database:
    def __init__(self, db_path: Path | str = DB_PATH, schema_path: Path | str = SCHEMA_PATH) -> None:
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self) -> None:
        schema = self.schema_path.read_text(encoding="utf-8")
        conn = self.connect()
        try:
            conn.executescript(schema)
            conn.commit()
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params: Iterable[Any] = ()) -> int:
        with self.transaction() as conn:
            cursor = conn.execute(sql, tuple(params))
            return int(cursor.lastrowid)

    def executemany(self, sql: str, rows: Iterable[Iterable[Any]]) -> None:
        with self.transaction() as conn:
            conn.executemany(sql, rows)

    def query_one(self, sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
        conn = self.connect()
        try:
            row = conn.execute(sql, tuple(params)).fetchone()
        finally:
            conn.close()
        return dict(row) if row else None

    def query_all(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        conn = self.connect()
        try:
            rows = conn.execute(sql, tuple(params)).fetchall()
        finally:
            conn.close()
        return [dict(row) for row in rows]
