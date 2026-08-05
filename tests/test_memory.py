"""Memory system tests (Milestone 3): short-term + long-term memory."""
from __future__ import annotations

from llm.mock import MockLLM
from memory import LongTermMemory, ShortTermMemory
from schemas.state import LeaveRequest, LeaveState, Outcome, Status
from workflows import run_leave_workflow


def test_long_term_memory_records_and_recalls(seeded_db):
    mem = LongTermMemory(seeded_db)
    assert mem.history("E001") == []

    mem.record_interaction(
        employee_id="E001", request_id="REQ-1", leave_type="casual",
        start_date="2026-09-01", end_date="2026-09-02", days_requested=2,
        outcome=Outcome.APPROVE, confidence=0.95, summary="approved",
        flags=["company_holidays_in_range(X)"],
    )
    history = mem.history("E001")
    assert len(history) == 1
    assert history[0]["outcome"] == Outcome.APPROVE
    assert history[0]["flags"] == ["company_holidays_in_range(X)"]


def test_long_term_memory_stats(seeded_db):
    mem = LongTermMemory(seeded_db)
    for outcome in (Outcome.ESCALATE, Outcome.APPROVE, Outcome.ESCALATE):
        mem.record_interaction(
            employee_id="E003", request_id=f"R-{outcome}", leave_type="earned",
            start_date="2026-09-01", end_date="2026-09-02", days_requested=2,
            outcome=outcome, confidence=0.9, summary="x",
        )
    stats = mem.stats("E003")
    assert stats["total_interactions"] == 3
    assert stats["outcome_counts"][Outcome.ESCALATE] == 2
    # Newest first -> last recorded outcome is APPROVE? order is ESCALATE,APPROVE,ESCALATE
    assert stats["last_outcome"] == Outcome.ESCALATE


def test_short_term_memory_bus_and_conversation():
    state = LeaveState(request=LeaveRequest("E001", "casual", "2026-09-01", "2026-09-02"))
    stm = ShortTermMemory(state)

    stm.post("policy", "research", "policy finding", to="analysis", kind="finding")
    stm.post("coordinator", "planning", "the plan", to="all", kind="plan")
    stm.remember("assistant", "hello")

    # analysis sees the addressed message + the broadcast, not its own posts
    inbox = stm.inbox("analysis")
    assert {m["sender"] for m in inbox} == {"policy", "coordinator"}
    assert stm.conversation()[-1]["content"] == "hello"


def test_workflow_persists_and_recalls_history(seeded_db, future_range):
    """Two requests by the same employee: the second recalls the first."""
    start, end = future_range(days_ahead=25, span=2)
    first = run_leave_workflow(LeaveRequest("E003", "earned", start, end, "Trip"), MockLLM())
    assert first.decision.outcome == Outcome.ESCALATE
    assert first.status == Status.AWAITING_MANAGER
    assert first.history == []  # nothing to recall on the first request

    start2, end2 = future_range(days_ahead=40, span=1)
    second = run_leave_workflow(LeaveRequest("E003", "casual", start2, end2, "Errand"), MockLLM())
    # long-term memory recalled the escalation
    assert len(second.history) == 1
    assert second.history[0]["outcome"] == Outcome.ESCALATE
    # context-aware rationale references prior history, without flipping outcome
    assert second.decision.outcome == Outcome.APPROVE
    assert "prior" in second.decision.rationale.lower()
    assert any(f.startswith("history(") for f in second.analysis.flags)
