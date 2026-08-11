"""Sequential multi-agent runner (Milestones 1 & 3).

Runs the specialized agents in a fixed order and returns the final state. This
is the foundational "interaction workflow" from Milestone 1. Milestone 3 threads
a shared memory repository through the run: long-term history is recalled up
front so the Analysis/Decision agents have context, short-term memory is bound
to the request, and the interaction is retained at the end. In Milestone 4 the
orchestration moves to a LangGraph graph (``workflows/graph.py``) with
conditional edges + a human-in-the-loop node; this sequential runner is retained
as the equivalent reference implementation (``run_leave_graph`` matches it), and
the agent classes themselves stay unchanged between the two.
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
from memory import SharedMemory, default_memory
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


def build_agents(
    llm: BaseLLM,
    logger: AgentLogger | None = None,
    memory: SharedMemory | None = None,
) -> list[BaseAgent]:
    logger = logger or AgentLogger()
    return [cls(llm=llm, logger=logger, memory=memory) for cls in AGENT_ORDER]


def run_leave_workflow(
    request: LeaveRequest,
    llm: BaseLLM,
    logger: AgentLogger | None = None,
    memory: SharedMemory | None = None,
) -> LeaveState:
    logger = logger or AgentLogger()
    memory = memory or default_memory()

    state = LeaveState(request=request)
    memory.bind(state)  # short-term memory is scoped to this request

    # Recall long-term memory up front so context-aware agents can use it.
    state.history = memory.long_term.history(request.employee_id, limit=5)

    for agent in build_agents(llm, logger, memory):
        state = agent.run(state)
        if state.status == Status.FAILED:
            logger.step(state, "pipeline", "Halting: state marked FAILED.")
            break
    return state
