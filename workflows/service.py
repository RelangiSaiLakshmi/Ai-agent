"""Application service layer (Milestone 4).

A thin, framework-agnostic API over the workflow + persistence that both the
FastAPI layer (:mod:`api.app`) and the Streamlit dashboard
(:mod:`frontend.dashboard`) call. Keeping this logic here (rather than in the
web layer) means the REST API and the UI share one implementation and stay in
lockstep — and it keeps the human-in-the-loop *resume* in one place.

Functions here return plain JSON-serialisable dicts/lists so any transport can
wrap them directly.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from llm import get_llm
from memory import default_memory
from schemas.state import LeaveRequest, LeaveState, Outcome, Status
from tools import leave_tools
from utils.logging import AgentLogger
from workflows.graph import run_leave_graph


class ServiceError(Exception):
    """Raised for expected, client-facing failures (bad id, wrong state)."""


# ── Submitting + reading requests ────────────────────────────────────────────

def submit_leave_request(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str = "",
) -> dict[str, Any]:
    """Run the full orchestration graph for a new request; returns the state."""
    request = LeaveRequest(
        employee_id=employee_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
    )
    state = run_leave_graph(request, get_llm())
    return state.to_dict()


def get_request(request_id: str) -> dict[str, Any]:
    """Fetch a stored request together with its latest decision."""
    req = leave_tools.get_request(request_id)
    if req is None:
        raise ServiceError(f"Request '{request_id}' not found.")
    decision = leave_tools.get_latest_decision(request_id)
    if decision and decision.get("criteria_json"):
        try:
            decision["criteria"] = json.loads(decision["criteria_json"])
        except (ValueError, TypeError):
            decision["criteria"] = {}
    return {"request": req, "decision": decision, "status": req["status"]}


def list_pending_approvals() -> list[dict[str, Any]]:
    """Requests awaiting a manager decision (the approval queue)."""
    return leave_tools.list_requests_by_status(Status.AWAITING_MANAGER)


# ── Human-in-the-loop resume ─────────────────────────────────────────────────

def apply_manager_decision(
    request_id: str,
    approved: bool,
    manager_id: str = "manager",
    note: str = "",
) -> dict[str, Any]:
    """Resume an escalated request with a manager's final call.

    This is the resume half of the human-in-the-loop interrupt the graph pauses
    at (``manager_review`` node / ``AWAITING_MANAGER``). It records the manager's
    decision, completes the request, and retains the interaction in long-term
    memory so future requests carry the real outcome.
    """
    req = leave_tools.get_request(request_id)
    if req is None:
        raise ServiceError(f"Request '{request_id}' not found.")
    if req["status"] != Status.AWAITING_MANAGER:
        raise ServiceError(
            f"Request '{request_id}' is '{req['status']}', not awaiting a manager "
            f"decision; nothing to resume."
        )

    outcome = Outcome.APPROVE if approved else Outcome.REJECT
    verb = "approved" if approved else "rejected"
    rationale = f"Manager {manager_id} {verb} the escalated request." + (
        f" Note: {note}" if note else ""
    )

    leave_tools.record_decision(
        {
            "decision_id": f"DEC-{uuid.uuid4().hex[:8].upper()}",
            "request_id": request_id,
            "outcome": outcome,
            "confidence": 1.0,  # a human decision is authoritative
            "rationale": rationale,
            "criteria_json": json.dumps({"manager_review": "pass" if approved else "fail"}),
            "decided_by": manager_id,
        }
    )
    leave_tools.set_request_status(request_id, Status.COMPLETED)

    # Retain the final (human) outcome in long-term memory.
    try:
        default_memory().long_term.record_interaction(
            employee_id=req["employee_id"],
            request_id=request_id,
            leave_type=req["leave_type"],
            start_date=req["start_date"],
            end_date=req["end_date"],
            days_requested=float(req.get("days_requested") or 0.0),
            outcome=outcome,
            confidence=1.0,
            summary=f"Manager {verb} {req['leave_type']} {req['start_date']}..{req['end_date']}.",
            flags=["manager_decision"],
        )
    except Exception:  # memory write must never break the resume
        pass

    AgentLogger().step(
        LeaveState(request=LeaveRequest(req["employee_id"], req["leave_type"],
                                        req["start_date"], req["end_date"])),
        "manager_review",
        f"Manager {manager_id} {verb} {request_id}; status -> COMPLETED.",
    )
    return {"request_id": request_id, "outcome": outcome, "status": Status.COMPLETED,
            "decided_by": manager_id, "rationale": rationale}


# ── Employee reads ───────────────────────────────────────────────────────────

def list_employees() -> list[dict[str, Any]]:
    from database.db import get_connection, list_employees as _list

    conn = get_connection()
    try:
        return _list(conn)
    finally:
        conn.close()


def get_employee_balances(employee_id: str) -> list[dict[str, Any]]:
    """Leave balances with computed availability for one employee."""
    if leave_tools.get_employee(employee_id) is None:
        raise ServiceError(f"Employee '{employee_id}' not found.")
    balances = leave_tools.get_all_balances(employee_id)
    for b in balances:
        total = float(b.get("total_days") or 0.0)
        used = float(b.get("used_days") or 0.0)
        b["days_available"] = total - used
    return balances


def get_employee_history(employee_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Recalled long-term interaction history for an employee."""
    return default_memory().long_term.history(employee_id, limit=limit)
