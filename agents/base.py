"""Base agent abstraction.

Every specialized agent subclasses this. An agent takes the shared `LeaveState`,
does its one job (optionally using the LLM and/or tools), mutates the state, and
returns it. This uniform contract is what lets the Coordinator sequence them and
what will map onto LangGraph nodes in Milestone 4.

Milestone 3 adds two shared capabilities on the base class:

* a **business role** (``role``) mapping every agent onto the roles named in the
  project doc — planning, research, analysis, decision, execution, response — so
  the specialization is explicit and auditable;
* **communication + memory helpers** (``post`` / ``inbox`` / ``remember`` and the
  injected :class:`~memory.shared.SharedMemory`) so agents exchange information
  over an explicit bus and reason with short- and long-term memory, instead of
  only mutating the shared state implicitly.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from llm.base import BaseLLM
from memory.short_term import ShortTermMemory
from schemas.state import LeaveState
from utils.logging import AgentLogger


class BaseAgent(ABC):
    #: short identifier used in prompts, logs and routing
    name: str = "agent"
    #: business role from the project doc (planning|research|analysis|decision|execution|response)
    role: str = "agent"

    def __init__(
        self,
        llm: BaseLLM,
        logger: AgentLogger | None = None,
        memory: "SharedMemory | None" = None,
    ) -> None:
        self.llm = llm
        self.logger = logger or AgentLogger()
        # Long-term memory is optional so agents can still run in isolation
        # (e.g. unit tests) without a wired-up repository.
        self.memory = memory

    @abstractmethod
    def run(self, state: LeaveState) -> LeaveState:
        """Execute this agent's step and return the (mutated) state."""
        raise NotImplementedError

    def log(self, state: LeaveState, message: str) -> None:
        self.logger.step(state, self.name, message)

    # ── Coordination / communication (Milestone 3) ───────────────────────────

    def post(self, state: LeaveState, content: str, *, to: str = "all", kind: str = "update") -> None:
        """Post a message to the inter-agent bus for other agents to read."""
        ShortTermMemory(state).post(self.name, self.role, content, to=to, kind=kind)

    def inbox(self, state: LeaveState) -> list[dict[str, str]]:
        """Messages addressed to this agent (or broadcast), excluding its own."""
        return ShortTermMemory(state).inbox(self.name)

    def remember(self, state: LeaveState, role: str, content: str) -> None:
        """Append a turn to short-term conversational memory."""
        ShortTermMemory(state).remember(role, content)


# Imported for typing only; kept at the bottom to avoid a circular import at
# module load (memory.shared imports schemas.state, not agents).
from memory.shared import SharedMemory  # noqa: E402
