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


# ── Auth & roles ─────────────────────────────────────────────────────────────

def test_authenticate_and_roles(seeded_db):
    # M001 manages others -> manager; E001 reports to M001 -> employee.
    mgr = service.authenticate("M001", service.DEMO_PASSWORD)
    emp = service.authenticate("e001", service.DEMO_PASSWORD)  # case-insensitive
    assert mgr and mgr["role"] == "manager"
    assert emp and emp["role"] == "employee"
    # Bad password and unknown user both fail.
    assert service.authenticate("M001", "wrong") is None
    assert service.authenticate("E999", service.DEMO_PASSWORD) is None


def test_pending_queue_scoped_to_manager(seeded_db, future_range):
    start, end = future_range()
    # E003 reports to M002; the escalation should appear only in M002's queue.
    rid = service.submit_leave_request("E003", "earned", start, end)["request"]["request_id"]
    assert rid in {p["request_id"] for p in service.list_pending_approvals("M002")}
    assert rid not in {p["request_id"] for p in service.list_pending_approvals("M001")}


def test_employee_requests_listing(seeded_db, future_range):
    start, end = future_range()
    rid = service.submit_leave_request("E001", "casual", start, end)["request"]["request_id"]
    mine = service.list_employee_requests("E001")
    row = next(r for r in mine if r["request_id"] == rid)
    assert row["latest_outcome"] == Outcome.APPROVE


# ── Balance deduction on approval ────────────────────────────────────────────

def _casual_available(emp: str) -> float:
    return next(
        b for b in service.get_employee_balances(emp) if b["leave_type"] == "casual"
    )["days_available"]


def test_auto_approval_deducts_balance(seeded_db, future_range):
    start, end = future_range()
    before = _casual_available("E001")
    rid = service.submit_leave_request("E001", "casual", start, end)["request"]["request_id"]
    days = service.get_request(rid)["request"]["days_requested"]
    assert _casual_available("E001") == before - days


def test_manager_approval_deducts_balance_escalate_defers(seeded_db, future_range):
    start, end = future_range()
    earned_avail = lambda: next(  # noqa: E731
        b for b in service.get_employee_balances("E003") if b["leave_type"] == "earned"
    )["days_available"]
    before = earned_avail()
    rid = service.submit_leave_request("E003", "earned", start, end)["request"]["request_id"]
    # Escalated: nothing deducted yet.
    assert earned_avail() == before
    days = service.get_request(rid)["request"]["days_requested"]
    service.apply_manager_decision(rid, approved=True, manager_id="M002")
    assert earned_avail() == before - days


def test_list_policies(seeded_db):
    policies = {p["leave_type"]: p for p in service.list_policies()}
    assert set(policies) == {"casual", "sick", "earned"}
    # earned leave requires manager approval; casual does not.
    assert policies["earned"]["manager_required"] == 1
    assert policies["casual"]["manager_required"] == 0


def test_manager_rejection_deducts_nothing(seeded_db, future_range):
    start, end = future_range()
    earned_avail = lambda: next(  # noqa: E731
        b for b in service.get_employee_balances("E003") if b["leave_type"] == "earned"
    )["days_available"]
    before = earned_avail()
    rid = service.submit_leave_request("E003", "earned", start, end)["request"]["request_id"]
    service.apply_manager_decision(rid, approved=False, manager_id="M002")
    assert earned_avail() == before
