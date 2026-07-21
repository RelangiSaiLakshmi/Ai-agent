"""Milestone 2 tests — exception handling and action-execution accuracy.

Covers the tool loop's failure contract (tool errors, unknown tools, runaway
loops), the enterprise connector, and end-to-end validation that executed
actions (DB writes) match the decision the agents produced.
"""
from __future__ import annotations

import json

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool

from database import db
from llm.mock import MockLLM
from schemas.state import LeaveRequest, Outcome, Status
from tools.connectors import HolidayCalendarConnector, holiday_calendar
from tools.langchain_tools import get_company_holidays
from workflows import run_leave_workflow


@tool
def broken_tool(employee_id: str) -> dict:
    """A tool that always fails (test double for a downed enterprise system)."""
    raise ConnectionError("enterprise system unreachable")


class UnknownToolLLM(MockLLM):
    """Mock whose model first requests a tool that was never offered."""

    def _bind_tools(self, tools):
        inner = super()._bind_tools(tools)

        def respond(messages):
            asked_unknown = any(
                call["name"] == "drop_all_tables"
                for m in messages
                if isinstance(m, AIMessage)
                for call in (m.tool_calls or [])
            )
            if not asked_unknown:
                return AIMessage(
                    content="",
                    tool_calls=[
                        {"name": "drop_all_tables", "args": {}, "id": "call_bad", "type": "tool_call"}
                    ],
                )
            return inner.invoke(messages)

        return RunnableLambda(respond)


class RunawayLLM(MockLLM):
    """Mock whose model calls the same tool forever and never answers."""

    def _bind_tools(self, tools):
        def respond(messages):
            return AIMessage(
                content="",
                tool_calls=[
                    {"name": tools[0].name, "args": {"leave_type": "casual"}, "id": "c", "type": "tool_call"}
                ],
            )

        return RunnableLambda(respond)


# ── Tool loop exception handling ─────────────────────────────────────────────

def test_failing_tool_is_recorded_not_raised(seeded_db):
    loop = MockLLM().run_with_tools(
        json.dumps({"employee_id": "E001"}),
        tools=[broken_tool],
    )
    assert loop.text  # the loop still reached a final answer
    (err,) = loop.errors
    assert err.name == "broken_tool"
    assert "enterprise system unreachable" in err.error


def test_unknown_tool_call_is_rejected_gracefully(seeded_db):
    from tools.langchain_tools import POLICY_TOOLS

    loop = UnknownToolLLM().run_with_tools(
        json.dumps({"leave_type": "casual"}),
        tools=POLICY_TOOLS,
    )
    assert any("unknown tool" in (r.error or "") for r in loop.errors)
    # After the rejection the model recovered and used a real tool.
    assert loop.last_result("get_policy")["leave_type"] == "casual"
    assert loop.text


def test_runaway_loop_is_bounded(seeded_db):
    from tools.langchain_tools import POLICY_TOOLS

    loop = RunawayLLM().run_with_tools(
        json.dumps({"leave_type": "casual"}),
        tools=POLICY_TOOLS,
        max_iterations=3,
    )
    assert loop.exhausted
    assert loop.text == ""
    assert len(loop.tool_results) == 3


def test_agent_survives_model_that_never_calls_tools(seeded_db, future_range):
    """If the model skips its tools entirely, agents fall back to direct calls."""
    from agents import EmployeeDataAgent, PolicyAgent
    from schemas.state import LeaveState

    class LazyLLM(MockLLM):
        def _bind_tools(self, tools):
            return RunnableLambda(lambda messages: AIMessage(content="I refuse to use tools."))

    start, end = future_range()
    state = LeaveState(request=LeaveRequest("E001", "casual", start, end))
    PolicyAgent(llm=LazyLLM()).run(state)
    EmployeeDataAgent(llm=LazyLLM()).run(state)

    assert state.policy is not None and state.policy.leave_type == "casual"
    assert state.employee is not None and state.employee.name == "Asha Rao"
    assert state.balance is not None


# ── Enterprise connector ─────────────────────────────────────────────────────

def test_connector_filters_by_range():
    hits = holiday_calendar.holidays_between("2026-12-20", "2026-12-31")
    assert [h.name for h in hits] == ["Christmas Day"]
    assert holiday_calendar.holidays_between("2026-03-01", "2026-03-31") == []


def test_connector_transport_is_swappable():
    fake = HolidayCalendarConnector(
        transport=lambda: [{"date": "2026-07-20", "name": "Founders Day"}]
    )
    assert [h.name for h in fake.holidays_between("2026-07-01", "2026-07-31")] == ["Founders Day"]


def test_connector_tool_invalid_dates_surface_as_loop_error(seeded_db):
    loop = MockLLM().run_with_tools(
        json.dumps({"start_date": "not-a-date", "end_date": "2026-12-31"}),
        tools=[get_company_holidays],
    )
    (err,) = loop.errors
    assert err.name == "get_company_holidays"
    assert loop.text  # workflow-level: the failure did not crash the loop


# ── Action-execution accuracy ────────────────────────────────────────────────

def test_executed_actions_match_decision(seeded_db, future_range):
    """The persisted request status and decision row must equal what the
    Decision agent produced — validating write-action accuracy end to end."""
    start, end = future_range()
    state = run_leave_workflow(LeaveRequest("E001", "casual", start, end, "trip"), MockLLM())

    assert state.decision is not None and state.decision.outcome == Outcome.APPROVE
    assert state.status == Status.COMPLETED

    conn = db.get_connection()
    try:
        req_row = conn.execute(
            "SELECT status FROM leave_requests WHERE request_id = ?",
            (state.request.request_id,),
        ).fetchone()
        dec_row = conn.execute(
            "SELECT outcome, confidence, criteria_json FROM decisions WHERE request_id = ?",
            (state.request.request_id,),
        ).fetchone()
    finally:
        conn.close()

    assert req_row["status"] == state.status
    assert dec_row["outcome"] == state.decision.outcome
    assert dec_row["confidence"] == state.decision.confidence
    assert json.loads(dec_row["criteria_json"]) == state.decision.criteria_scores


def test_tool_driven_path_matches_direct_path(seeded_db, future_range):
    """Parity: grounding state through the tool loop yields the same facts as
    calling the tools directly (Milestone 1 behavior)."""
    from agents import EmployeeDataAgent, PolicyAgent
    from schemas.state import LeaveState
    from tools import leave_tools

    start, end = future_range()
    state = LeaveState(request=LeaveRequest("E003", "earned", start, end))
    PolicyAgent(llm=MockLLM()).run(state)
    EmployeeDataAgent(llm=MockLLM()).run(state)

    direct_policy = leave_tools.get_policy("earned")
    direct_emp = leave_tools.get_employee("E003")
    direct_bal = leave_tools.get_leave_balance("E003", "earned")

    assert state.policy.max_days_per_year == direct_policy["max_days_per_year"]
    assert state.policy.manager_required == bool(direct_policy["manager_required"])
    assert state.employee.name == direct_emp["name"]
    assert state.balance.total_days == float(direct_bal["total_days"])
    assert state.balance.used_days == float(direct_bal["used_days"])
