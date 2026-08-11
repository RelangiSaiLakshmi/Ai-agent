"""Service-layer tests (Milestone 4): submit, HITL resume, employee reads."""
from __future__ import annotations

import pytest

from schemas.state import Outcome, Status
from workflows import service
from workflows.service import ServiceError


def test_submit_and_get_request(seeded_db, future_range):
    start, end = future_range()
    state = service.submit_leave_request("E001", "casual", start, end, "trip")
    rid = state["request"]["request_id"]
    assert state["decision"]["outcome"] == Outcome.APPROVE

    fetched = service.get_request(rid)
    assert fetched["status"] == Status.COMPLETED
    assert fetched["decision"]["outcome"] == Outcome.APPROVE
    # criteria_json is decoded for convenience
    assert isinstance(fetched["decision"]["criteria"], dict)


def test_pending_queue_and_manager_approval(seeded_db, future_range):
    start, end = future_range()
    state = service.submit_leave_request("E003", "earned", start, end, "trip")
    rid = state["request"]["request_id"]
    assert state["status"] == Status.AWAITING_MANAGER

    pending = service.list_pending_approvals()
    assert rid in {p["request_id"] for p in pending}

    result = service.apply_manager_decision(rid, approved=True, manager_id="M002", note="ok")
    assert result["outcome"] == Outcome.APPROVE
    assert result["status"] == Status.COMPLETED

    # No longer pending; latest decision reflects the manager's call.
    assert rid not in {p["request_id"] for p in service.list_pending_approvals()}
    assert service.get_request(rid)["decision"]["decided_by"] == "M002"


def test_manager_decision_retained_in_memory(seeded_db, future_range):
    start, end = future_range()
    rid = service.submit_leave_request("E003", "earned", start, end)["request"]["request_id"]
    service.apply_manager_decision(rid, approved=False, manager_id="M002")
    history = service.get_employee_history("E003")
    outcomes = [h["outcome"] for h in history]
    # both the escalation and the final manager rejection are retained
    assert Outcome.REJECT in outcomes
    assert Outcome.ESCALATE in outcomes


def test_manager_decision_rejects_non_escalated(seeded_db, future_range):
    start, end = future_range()
    rid = service.submit_leave_request("E001", "casual", start, end)["request"]["request_id"]
    # E001 casual auto-approves; it is not awaiting a manager.
    with pytest.raises(ServiceError):
        service.apply_manager_decision(rid, approved=True)


def test_unknown_request_and_employee(seeded_db):
    with pytest.raises(ServiceError):
        service.get_request("REQ-DOESNOTEXIST")
    with pytest.raises(ServiceError):
        service.get_employee_balances("E999")


def test_employee_balances_compute_availability(seeded_db):
    balances = service.get_employee_balances("E001")
    casual = next(b for b in balances if b["leave_type"] == "casual")
    # seed: casual total 12, used 3 -> 9 available
    assert casual["days_available"] == 9.0
