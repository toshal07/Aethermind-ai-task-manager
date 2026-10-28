import sqlite3
from pathlib import Path
from app.config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                deadline TEXT NULL,
                priority TEXT NOT NULL CHECK(priority IN ('Low', 'Medium', 'High')),
                category TEXT NOT NULL DEFAULT 'Personal',
                status TEXT NOT NULL DEFAULT 'Pending'
                    CHECK(status IN ('Pending', 'In Progress', 'Completed')),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
            )
        """)
        conn.commit()


def row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def create_task(task: dict) -> dict:
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO tasks (title, description, deadline, priority, category)
            VALUES (?, ?, ?, ?, ?)
        """, (
            task["title"], task.get("description", ""), task.get("deadline"),
            task["priority"], task.get("category", "Personal")
        ))
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row)


def list_tasks() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM tasks
            ORDER BY
              CASE status WHEN 'Pending' THEN 0 WHEN 'In Progress' THEN 1 ELSE 2 END,
              CASE priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END,
              CASE WHEN deadline IS NULL THEN 1 ELSE 0 END,
              deadline ASC,
              id DESC
        """).fetchall()
        return [row_to_dict(row) for row in rows]


def update_task_status(task_id: int, status: str) -> dict | None:
    with get_connection() as conn:
        cursor = conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        conn.commit()
        if cursor.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return row_to_dict(row)


def delete_task(task_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0
