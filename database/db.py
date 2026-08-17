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


def list_policies(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """All leave policy rules the agents enforce (backs the policy view)."""
    rows = conn.execute("SELECT * FROM policy_rules ORDER BY leave_type").fetchall()
    return [dict(r) for r in rows]


def list_employees(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT employee_id, name, department, manager_id FROM employees ORDER BY employee_id"
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_request(conn: sqlite3.Connection, request_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM leave_requests WHERE request_id = ?", (request_id,)
    ).fetchone()
    return dict(row) if row else None


def fetch_latest_decision(conn: sqlite3.Connection, request_id: str) -> dict[str, Any] | None:
    """The most recent decision for a request (an escalation may be followed by
    a manager decision; this returns the effective/latest one)."""
    row = conn.execute(
        """
        SELECT * FROM decisions
        WHERE request_id = ?
        ORDER BY created_at DESC, rowid DESC
        LIMIT 1
        """,
        (request_id,),
    ).fetchone()
    return dict(row) if row else None


def fetch_all_balances(conn: sqlite3.Connection, employee_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM leave_balances WHERE employee_id = ? ORDER BY leave_type",
        (employee_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def list_requests_by_employee(conn: sqlite3.Connection, employee_id: str) -> list[dict[str, Any]]:
    """All requests raised by one employee, newest first, with their latest
    outcome (backs the employee's "my requests" view)."""
    rows = conn.execute(
        """
        SELECT r.*,
               (SELECT d.outcome FROM decisions d
                WHERE d.request_id = r.request_id
                ORDER BY d.created_at DESC, d.rowid DESC LIMIT 1) AS latest_outcome
        FROM leave_requests r
        WHERE r.employee_id = ?
        ORDER BY r.created_at DESC, r.rowid DESC
        """,
        (employee_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def list_requests_by_status(conn: sqlite3.Connection, status: str) -> list[dict[str, Any]]:
    """Requests in a given status, newest first (backs the manager approval queue)."""
    rows = conn.execute(
        """
        SELECT r.*, e.name AS employee_name, e.manager_id AS manager_id
        FROM leave_requests r
        LEFT JOIN employees e ON e.employee_id = r.employee_id
        WHERE r.status = ?
        ORDER BY r.created_at DESC, r.rowid DESC
        """,
        (status,),
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


def add_balance_usage(
    conn: sqlite3.Connection, employee_id: str, leave_type: str, days: float
) -> None:
    """Increment used_days for a leave type when a request is approved.

    A no-op (0 rows) if the employee has no balance row for that type; the
    request would not have passed the balance check without one.
    """
    conn.execute(
        "UPDATE leave_balances SET used_days = used_days + ? "
        "WHERE employee_id = ? AND leave_type = ?",
        (days, employee_id, leave_type),
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


# ── Long-term memory helpers (Milestone 3) ───────────────────────────────────

def save_interaction(conn: sqlite3.Connection, memory: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO interaction_memory
            (memory_id, employee_id, request_id, leave_type, start_date,
             end_date, days_requested, outcome, confidence, summary, flags_json)
        VALUES (:memory_id, :employee_id, :request_id, :leave_type, :start_date,
                :end_date, :days_requested, :outcome, :confidence, :summary, :flags_json)
        """,
        memory,
    )
    conn.commit()


def fetch_interactions(
    conn: sqlite3.Connection, employee_id: str, limit: int = 5
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT memory_id, employee_id, request_id, leave_type, start_date,
               end_date, days_requested, outcome, confidence, summary,
               flags_json, created_at
        FROM interaction_memory
        WHERE employee_id = ?
        ORDER BY created_at DESC, rowid DESC
        LIMIT ?
        """,
        (employee_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]
