"""SQLite access helpers used by the tools/agents.

Read helpers back the Employee-Data and Policy agents; write helpers back the
Notification agent. Kept deliberately small and framework-free for Milestone 1.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from utils.config import settings

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _db_path(db_path: str | None = None) -> Path:
    if db_path is not None:
        return Path(db_path)
    return settings.resolved_db_path()


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    path = _db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


# ── Read helpers ────────────────────────────────────────────────────────────

def fetch_employee(conn: sqlite3.Connection, employee_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM employees WHERE employee_id = ?", (employee_id,)
    ).fetchone()
    return dict(row) if row else None


def fetch_balance(conn: sqlite3.Connection, employee_id: str, leave_type: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM leave_balances WHERE employee_id = ? AND leave_type = ?",
        (employee_id, leave_type),
    ).fetchone()
    return dict(row) if row else None


def fetch_overlaps(
    conn: sqlite3.Connection,
    employee_id: str,
    start_date: str,
    end_date: str,
    exclude_request_id: str | None = None,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT request_id, leave_type, start_date, end_date, status
        FROM leave_requests
        WHERE employee_id = ?
          AND status IN ('RECEIVED', 'AWAITING_MANAGER', 'COMPLETED')
          AND request_id != ?
          AND NOT (end_date < ? OR start_date > ?)
        """,
        (employee_id, exclude_request_id or "", start_date, end_date),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_policy(conn: sqlite3.Connection, leave_type: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM policy_rules WHERE leave_type = ?", (leave_type,)
    ).fetchone()
    return dict(row) if row else None


def list_employees(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT employee_id, name, department, manager_id FROM employees ORDER BY employee_id"
    ).fetchall()
    return [dict(r) for r in rows]


# ── Write helpers ───────────────────────────────────────────────────────────

def save_request(conn: sqlite3.Connection, req: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO leave_requests
            (request_id, employee_id, leave_type, start_date, end_date,
             days_requested, reason, status)
        VALUES (:request_id, :employee_id, :leave_type, :start_date, :end_date,
                :days_requested, :reason, :status)
        """,
        req,
    )
    conn.commit()


def update_request_status(conn: sqlite3.Connection, request_id: str, status: str) -> None:
    conn.execute(
        "UPDATE leave_requests SET status = ? WHERE request_id = ?", (status, request_id)
    )
    conn.commit()


def save_decision(conn: sqlite3.Connection, decision: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO decisions
            (decision_id, request_id, outcome, confidence, rationale,
             criteria_json, decided_by)
        VALUES (:decision_id, :request_id, :outcome, :confidence, :rationale,
                :criteria_json, :decided_by)
        """,
        decision,
    )
    conn.commit()
