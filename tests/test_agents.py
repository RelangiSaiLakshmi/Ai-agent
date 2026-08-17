"""Per-agent tests against the seeded database."""
from __future__ import annotations

from agents import EmployeeDataAgent, PolicyAgent
from llm.mock import MockLLM
from schemas.state import LeaveRequest, LeaveState


def test_employee_data_agent_computes_balance(seeded_db, future_range):
    start, end = future_range()
    state = LeaveState(request=LeaveRequest("E001", "casual", start, end))
    EmployeeDataAgent(llm=MockLLM()).run(state)

    assert state.employee is not None
    assert state.employee.name == "Asha Rao"
    # seed: total 12, used 3 -> 9 available
    assert state.balance.days_available == 9


def test_policy_agent_reads_rules(seeded_db):
    state = LeaveState(request=LeaveRequest("E003", "earned", "2026-08-24", "2026-08-26"))
    PolicyAgent(llm=MockLLM()).run(state)

    assert state.policy is not None
    assert state.policy.manager_required is True
    assert state.policy.min_notice_days == 5


def test_policy_agent_unknown_type_flags_manager_review(seeded_db):
    state = LeaveState(request=LeaveRequest("E001", "sabbatical", "2026-08-24", "2026-08-26"))
    PolicyAgent(llm=MockLLM()).run(state)

    assert state.policy.manager_required is True
    assert "No policy found" in state.policy.notes
