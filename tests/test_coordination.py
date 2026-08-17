"""Agent coordination tests (Milestone 3): roles + inter-agent communication."""
from __future__ import annotations

from agents import (
    AnalysisAgent,
    CoordinatorAgent,
    DecisionAgent,
    EmployeeDataAgent,
    NotificationAgent,
    PolicyAgent,
    ResponderAgent,
)
from llm.mock import MockLLM
from schemas.state import LeaveRequest
from workflows import run_leave_workflow


def test_agents_declare_business_roles():
    """Every agent maps onto a project-doc business role."""
    roles = {
        CoordinatorAgent: "planning",
        PolicyAgent: "research",
        EmployeeDataAgent: "research",
        AnalysisAgent: "analysis",
        DecisionAgent: "decision",
        NotificationAgent: "execution",
        ResponderAgent: "response",
    }
    for cls, role in roles.items():
        assert cls.role == role
    # The four roles named explicitly in the milestone doc are all present.
    assert {"planning", "research", "analysis", "decision"} <= set(roles.values())


def test_bus_carries_information_between_agents(seeded_db, future_range):
    start, end = future_range()
    state = run_leave_workflow(LeaveRequest("E001", "casual", start, end), MockLLM())

    bus = state.agent_messages
    senders = {m["sender"] for m in bus}
    # planning, research (x2), analysis and decision all posted to the bus
    assert {"coordinator", "policy", "employee_data", "analysis", "decision"} <= senders

    # the coordinator broadcast a plan; the decision announced an outcome
    kinds = {(m["sender"], m["kind"]) for m in bus}
    assert ("coordinator", "plan") in kinds
    assert ("decision", "decision") in kinds


def test_analysis_receives_research_findings(seeded_db, future_range):
    """The Analysis agent's inbox contains the Research agents' findings."""
    start, end = future_range()
    state = run_leave_workflow(LeaveRequest("E001", "casual", start, end), MockLLM())

    # findings addressed to analysis came from the two research agents
    findings = [m for m in state.agent_messages if m["to"] == "analysis" and m["kind"] == "finding"]
    assert {m["sender"] for m in findings} == {"policy", "employee_data"}
