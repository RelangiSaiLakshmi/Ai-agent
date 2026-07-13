"""Base agent abstraction.

Every specialized agent subclasses this. An agent takes the shared `LeaveState`,
does its one job (optionally using the LLM and/or tools), mutates the state, and
returns it. This uniform contract is what lets the Coordinator sequence them and
what will map onto LangGraph nodes in Milestone 2.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from llm.base import BaseLLM
from schemas.state import LeaveState
from utils.logging import AgentLogger


class BaseAgent(ABC):
    #: short identifier used in prompts, logs and routing
    name: str = "agent"

    def __init__(self, llm: BaseLLM, logger: AgentLogger | None = None) -> None:
        self.llm = llm
        self.logger = logger or AgentLogger()

    @abstractmethod
    def run(self, state: LeaveState) -> LeaveState:
        """Execute this agent's step and return the (mutated) state."""
        raise NotImplementedError

    def log(self, state: LeaveState, message: str) -> None:
        self.logger.step(state, self.name, message)
