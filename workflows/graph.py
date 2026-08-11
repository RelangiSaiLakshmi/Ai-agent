"""LangGraph orchestration for the leave workflow (Milestone 4).

Milestone 1 ran the specialized agents as a fixed sequence
(:func:`workflows.pipeline.run_leave_workflow`). Milestone 4 promotes that
pipeline to a **LangGraph** ``StateGraph`` so the orchestration logic that
coordinates agents becomes explicit and *dynamic* — it has real decision points
and conditional edges rather than a straight line:

* a **validation gate** after the Coordinator: an invalid request
  short-circuits straight to the end instead of running the whole pipeline;
* a **human-in-the-loop branch** after the Notification agent: an ``ESCALATE``
  outcome (status ``AWAITING_MANAGER``) is routed through a dedicated
  ``manager_review`` node — the pause point where, in production, a manager
  approves/rejects (resumed via :func:`workflows.service.apply_manager_decision`);
* the ``APPROVE`` / ``REJECT`` outcomes flow directly to the responder.

The **agent classes are unchanged** — each becomes a graph node via a thin
adapter — so the coordination + memory behaviour built in Milestone 3 carries
over untouched. The sequential runner is kept as an equivalent reference
implementation (and is what ``tests/test_graph.py`` checks the graph against).
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from llm.base import BaseLLM
from memory import SharedMemory, default_memory
from memory.short_term import ShortTermMemory
from schemas.state import LeaveRequest, LeaveState, Status
from utils.logging import AgentLogger
from workflows.pipeline import build_agents


class GraphState(TypedDict):
    """Channel carried between nodes.

    A single key holds the live :class:`~schemas.state.LeaveState`; every node
    mutates it in place and returns it, so the graph reuses the exact same state
    object the sequential runner does (last-write-wins on the channel).
    """

    state: LeaveState


def _agent_node(agent):
    """Wrap an agent's ``run`` as a LangGraph node."""

    def node(gs: GraphState) -> GraphState:
        return {"state": agent.run(gs["state"])}

    return node


def _manager_review_node(logger: AgentLogger):
    """Human-in-the-loop pause point for escalated requests.

    This node represents the interrupt where a manager decision is required.
    The forward run records the pause and stops at ``AWAITING_MANAGER``; the
    request is resumed out-of-band by
    :func:`workflows.service.apply_manager_decision`.
    """

    def node(gs: GraphState) -> GraphState:
        state = gs["state"]
        logger.step(
            state,
            "manager_review",
            "Human-in-the-loop: request escalated; awaiting manager decision "
            "(status AWAITING_MANAGER).",
        )
        ShortTermMemory(state).post(
            "manager_review",
            "execution",
            "Escalated to manager; workflow paused for approval.",
            kind="alert",
        )
        return {"state": state}

    return node


# ── Conditional-edge routers ─────────────────────────────────────────────────

def _after_coordinator(gs: GraphState) -> str:
    """Validation gate: a request the Coordinator rejected ends immediately."""
    return "invalid" if gs["state"].status == Status.FAILED else "valid"


def _after_notification(gs: GraphState) -> str:
    """Route escalations through the human-in-the-loop node."""
    return "escalated" if gs["state"].status == Status.AWAITING_MANAGER else "resolved"


def build_leave_graph(
    llm: BaseLLM,
    logger: AgentLogger | None = None,
    memory: SharedMemory | None = None,
):
    """Compile the leave-approval orchestration graph."""
    logger = logger or AgentLogger()
    agents = {a.name: a for a in build_agents(llm, logger, memory)}

    g = StateGraph(GraphState)
    for name in ("coordinator", "policy", "employee_data", "analysis", "decision",
                 "notification", "responder"):
        g.add_node(name, _agent_node(agents[name]))
    g.add_node("manager_review", _manager_review_node(logger))

    g.add_edge(START, "coordinator")
    # Decision point 1 — validation gate.
    g.add_conditional_edges(
        "coordinator", _after_coordinator, {"invalid": END, "valid": "policy"}
    )
    # Research -> analysis -> decision (linear).
    g.add_edge("policy", "employee_data")
    g.add_edge("employee_data", "analysis")
    g.add_edge("analysis", "decision")
    # Decision is persisted, then the outcome decides the downstream path.
    g.add_edge("decision", "notification")
    # Decision point 2 — human-in-the-loop routing for escalations.
    g.add_conditional_edges(
        "notification",
        _after_notification,
        {"escalated": "manager_review", "resolved": "responder"},
    )
    g.add_edge("manager_review", "responder")
    g.add_edge("responder", END)
    return g.compile()


def run_leave_graph(
    request: LeaveRequest,
    llm: BaseLLM,
    logger: AgentLogger | None = None,
    memory: SharedMemory | None = None,
) -> LeaveState:
    """Run the leave workflow through the LangGraph orchestration graph.

    Signature mirrors :func:`workflows.pipeline.run_leave_workflow` so the two
    are drop-in interchangeable. Long-term memory is recalled up front and
    short-term memory is bound to the request, exactly as in Milestone 3.
    """
    logger = logger or AgentLogger()
    memory = memory or default_memory()

    state = LeaveState(request=request)
    memory.bind(state)  # short-term memory is scoped to this request
    # Recall long-term memory up front so context-aware agents can use it.
    state.history = memory.long_term.history(request.employee_id, limit=5)

    graph = build_leave_graph(llm, logger, memory)
    result = graph.invoke({"state": state})
    return result["state"]
