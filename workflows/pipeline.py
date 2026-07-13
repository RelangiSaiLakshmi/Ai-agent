"""Sequential multi-agent runner (Milestone 1).

Runs the agents in a fixed order and returns the final state. This is the
foundational "interaction workflow" from Milestone 1. In Milestone 4 it is
replaced by a LangGraph graph with conditional edges + human-in-the-loop, while
the agent classes themselves stay unchanged.
"""
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
from agents.base import BaseAgent
from llm.base import BaseLLM
from schemas.state import LeaveRequest, LeaveState, Status
from utils.logging import AgentLogger

# Order matches the Coordinator's plan.
AGENT_ORDER = [
    CoordinatorAgent,
    PolicyAgent,
    EmployeeDataAgent,
    AnalysisAgent,
    DecisionAgent,
    NotificationAgent,
    ResponderAgent,
]


def build_agents(llm: BaseLLM, logger: AgentLogger | None = None) -> list[BaseAgent]:
    logger = logger or AgentLogger()
    return [cls(llm=llm, logger=logger) for cls in AGENT_ORDER]


def run_leave_workflow(
    request: LeaveRequest, llm: BaseLLM, logger: AgentLogger | None = None
) -> LeaveState:
    logger = logger or AgentLogger()
    state = LeaveState(request=request)
    for agent in build_agents(llm, logger):
        state = agent.run(state)
        if state.status == Status.FAILED:
            logger.step(state, "pipeline", "Halting: state marked FAILED.")
            break
    return state
