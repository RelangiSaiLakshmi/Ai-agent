"""LangGraph orchestration tests (Milestone 4).

The graph must (a) produce the same outcomes as the sequential reference runner,
(b) short-circuit invalid requests at the validation gate, and (c) route
escalations through the human-in-the-loop ``manager_review`` node.
"""
from __future__ import annotations

from llm.mock import MockLLM
from schemas.state import LeaveRequest, Outcome, Status
from workflows import run_leave_graph, run_leave_workflow


def test_graph_matches_sequential_outcomes(seeded_db, future_range):
    """Graph and sequential runner agree on every decision path."""
    # Distinct date windows so the two persisted requests never overlap each
    # other (an overlap would flip the second run's outcome).
    seq_range = future_range(days_ahead=21, span=2)
    graph_range = future_range(days_ahead=60, span=2)
    cases = [
        ("E001", "casual", Outcome.APPROVE, Status.COMPLETED),
        ("E002", "earned", Outcome.REJECT, Status.COMPLETED),
        ("E003", "earned", Outcome.ESCALATE, Status.AWAITING_MANAGER),
    ]
    for emp, lt, outcome, status in cases:
        seq = run_leave_workflow(LeaveRequest(emp, lt, *seq_range), MockLLM())
        graph = run_leave_graph(LeaveRequest(emp, lt, *graph_range), MockLLM())
        assert seq.decision.outcome == outcome
        assert graph.decision.outcome == outcome
        assert graph.status == status


def test_graph_runs_every_agent(seeded_db, future_range):
    start, end = future_range()
    state = run_leave_graph(LeaveRequest("E001", "casual", start, end), MockLLM())
    agents_seen = {entry["agent"] for entry in state.logs}
    for expected in {"coordinator", "policy", "employee_data", "analysis",
                     "decision", "notification", "responder"}:
        assert expected in agents_seen


def test_validation_gate_short_circuits(seeded_db):
    """An invalid date range ends at the gate — no decision, no downstream agents."""
    state = run_leave_graph(LeaveRequest("E001", "casual", "2026-05-10", "2026-05-01"), MockLLM())
    assert state.status == Status.FAILED
    assert state.decision is None
    agents_seen = {entry["agent"] for entry in state.logs}
    assert "decision" not in agents_seen
    assert "policy" not in agents_seen


def test_escalation_hits_manager_review_node(seeded_db, future_range):
    start, end = future_range()
    state = run_leave_graph(LeaveRequest("E003", "earned", start, end), MockLLM())
    agents_seen = {entry["agent"] for entry in state.logs}
    assert "manager_review" in agents_seen
    assert state.status == Status.AWAITING_MANAGER


def test_approve_skips_manager_review(seeded_db, future_range):
    start, end = future_range()
    state = run_leave_graph(LeaveRequest("E001", "casual", start, end), MockLLM())
    agents_seen = {entry["agent"] for entry in state.logs}
    assert "manager_review" not in agents_seen
