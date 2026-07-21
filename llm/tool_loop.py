"""Structured results of an LLM tool-calling loop (Milestone 2).

`BaseLLM.run_with_tools` returns a :class:`ToolLoopResult` so agents can ground
their state in exactly what the tools returned, and tests can assert on which
tools were selected, what they were called with, and whether any failed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import BaseMessage


@dataclass
class ToolCallRecord:
    """One tool invocation requested by the model: its args, and outcome."""

    name: str
    args: dict[str, Any]
    result: Any = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class ToolLoopResult:
    """Everything that happened during one run of the tool-calling loop."""

    #: the model's final text answer ("" if the loop hit max_iterations)
    text: str
    #: every tool invocation, in execution order (including failed ones)
    tool_results: list[ToolCallRecord] = field(default_factory=list)
    #: full message transcript (system/human/AI/tool), for audit and debugging
    messages: list[BaseMessage] = field(default_factory=list)
    #: True if the loop stopped because it hit max_iterations, not a final answer
    exhausted: bool = False

    def called(self, name: str) -> bool:
        return any(r.name == name for r in self.tool_results)

    def last_result(self, name: str) -> Any:
        """Return the most recent *successful* result of tool `name`.

        Raises KeyError if the tool was never called successfully, so callers
        must handle the "model didn't fetch this" case explicitly.
        """
        for rec in reversed(self.tool_results):
            if rec.name == name and rec.ok:
                return rec.result
        raise KeyError(f"No successful result recorded for tool {name!r}")

    @property
    def errors(self) -> list[ToolCallRecord]:
        return [r for r in self.tool_results if not r.ok]
