"""End-to-end pipeline tests for the three decision paths."""
from __future__ import annotations

from llm.mock import MockLLM
from schemas.state import LeaveRequest, Outcome, Status
from workflows import run_leave_workflow


def test_approve_path(seeded_db, future_range):
    start, end = future_range(days_ahead=21, span=2)
    req = LeaveRequest("E001", "casual", start, end, "Family function")
    state = run_leave_workflow(req, MockLLM())

    assert state.decision.outcome == Outcome.APPROVE
    assert state.status == Status.COMPLETED
    assert state.draft_response and "approved" in state.draft_response.lower()


def test_reject_path_insufficient_balance(seeded_db, future_range):
    # E002 earned: available = 5 - 4 = 1, requesting 3 -> reject
    start, end = future_range(days_ahead=21, span=2)
    req = LeaveRequest("E002", "earned", start, end, "Vacation")
    state = run_leave_workflow(req, MockLLM())

    assert state.decision.outcome == Outcome.REJECT
    assert state.status == Status.COMPLETED


def test_escalate_path_manager_required(seeded_db, future_range):
    # E003 earned: balance ok but earned leave requires manager approval -> escalate
    start, end = future_range(days_ahead=21, span=2)
    req = LeaveRequest("E003", "earned", start, end, "Personal")
    state = run_leave_workflow(req, MockLLM())

    assert state.decision.outcome == Outcome.ESCALATE
    assert state.status == Status.AWAITING_MANAGER


def test_logs_capture_every_agent(seeded_db, future_range):
    start, end = future_range()
    req = LeaveRequest("E001", "casual", start, end)
    state = run_leave_workflow(req, MockLLM())

    agents_seen = {entry["agent"] for entry in state.logs}
    for expected in {"coordinator", "policy", "employee_data", "analysis", "decision", "notification", "responder"}:
        assert expected in agents_seen
