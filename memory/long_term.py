"""Long-term memory (Milestone 3).

Long-term memory is knowledge that outlives a single request: an employee's
history of leave interactions. It is persisted in the ``interaction_memory``
SQLite table (created by ``database/schema.sql``) and recalled on future
requests so agents can reason with context ("this employee has been escalated
twice before"), which the milestone doc calls *context-aware decision-making
through shared memory repositories*.

The store follows the same conventions as :mod:`tools.leave_tools`: it opens a
connection per operation and honours the ``db_path`` override, so tests point it
at a temp database via ``settings.db_path`` transparently. Only completed
interactions are written, and only by the write-privileged Notification agent —
consistent with the least-privilege boundary from Milestone 2.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from database import db


class LongTermMemory:
    """SQLite-backed store of per-employee interaction history."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path

    def record_interaction(
        self,
        *,
        employee_id: str,
        request_id: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        days_requested: float,
        outcome: str,
        confidence: float,
        summary: str,
        flags: list[str] | None = None,
    ) -> str:
        """Persist one completed interaction; returns the new memory id."""
        memory_id = f"MEM-{uuid.uuid4().hex[:8].upper()}"
        conn = db.get_connection(self.db_path)
        try:
            db.save_interaction(
                conn,
                {
                    "memory_id": memory_id,
                    "employee_id": employee_id,
                    "request_id": request_id,
                    "leave_type": leave_type,
                    "start_date": start_date,
                    "end_date": end_date,
                    "days_requested": days_requested,
                    "outcome": outcome,
                    "confidence": confidence,
                    "summary": summary,
                    "flags_json": json.dumps(flags or []),
                },
            )
        finally:
            conn.close()
        return memory_id

    def history(self, employee_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Most recent interactions for an employee (newest first)."""
        conn = db.get_connection(self.db_path)
        try:
            rows = db.fetch_interactions(conn, employee_id, limit)
        finally:
            conn.close()
        for row in rows:
            raw = row.get("flags_json")
            row["flags"] = json.loads(raw) if raw else []
        return rows

    def stats(self, employee_id: str) -> dict[str, Any]:
        """Aggregate signals over an employee's full history.

        Used by the Analysis/Decision agents as an informational (non-blocking)
        signal for context-aware decisions.
        """
        rows = self.history(employee_id, limit=100)
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["outcome"]] = counts.get(row["outcome"], 0) + 1
        return {
            "total_interactions": len(rows),
            "outcome_counts": counts,
            "last_outcome": rows[0]["outcome"] if rows else None,
        }
