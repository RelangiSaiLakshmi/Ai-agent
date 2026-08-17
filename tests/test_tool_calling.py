"""Milestone 2 tests — LangChain @tool wrappers and the tool-calling loop."""
from __future__ import annotations

import json

from llm.mock import MockLLM
from schemas.state import LeaveRequest, LeaveState
from tools.langchain_tools import (
    EMPLOYEE_DATA_TOOLS,
    POLICY_TOOLS,
    READ_TOOLS,
    get_employee,
    get_policy,
)


def test_read_tools_have_schemas():
    assert set(READ_TOOLS) == {
        "get_employee",
        "get_leave_balance",
        "get_overlapping_requests",
        "get_policy",
        "get_company_holidays",
    }
    assert "employee_id" in get_employee.args
    assert "leave_type" in get_policy.args
    # db_path must never be model-controllable
    for t in READ_TOOLS.values():
        assert "db_path" not in t.args


def test_tool_invocation_direct(seeded_db):
    emp = get_employee.invoke({"employee_id": "E001"})
    assert emp["name"] == "Asha Rao"
    assert get_policy.invoke({"leave_type": "casual"})["manager_required"] in (0, 1, False, True)


def test_run_with_tools_loop_records_results(seeded_db):
    llm = MockLLM()
    loop = llm.run_with_tools(
        json.dumps({"leave_type": "earned"}),
        tools=POLICY_TOOLS,
        system="You are the Policy agent.",
    )
    assert loop.text  # loop terminated with a final text
    assert loop.last_result("get_policy")["leave_type"] == "earned"


def test_run_with_tools_multiple_tools(seeded_db):
    llm = MockLLM()
    loop = llm.run_with_tools(
        json.dumps(
            {
                "employee_id": "E001",
                "leave_type": "casual",
                "start_date": "2026-08-17",
                "end_date": "2026-08-19",
                "exclude_request_id": "REQ-X",
            }
        ),
        tools=EMPLOYEE_DATA_TOOLS,
    )
    assert {r.name for r in loop.tool_results} == {
        "get_employee",
        "get_leave_balance",
        "get_overlapping_requests",
    }
    assert loop.last_result("get_employee")["employee_id"] == "E001"
    assert loop.last_result("get_overlapping_requests") == []


def test_agents_ground_state_in_tool_results(seeded_db, future_range):
    """End-to-end: the agents drive the tool-calling loop and still build
    the same structured state as the direct-call Milestone 1 path."""
    from agents import EmployeeDataAgent, PolicyAgent

    start, end = future_range()
    state = LeaveState(request=LeaveRequest("E002", "earned", start, end))
    PolicyAgent(llm=MockLLM()).run(state)
    EmployeeDataAgent(llm=MockLLM()).run(state)

    assert state.policy is not None and state.policy.leave_type == "earned"
    assert state.employee is not None and state.employee.employee_id == "E002"
    assert state.balance is not None
