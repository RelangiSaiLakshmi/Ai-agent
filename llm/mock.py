"""Offline mock LLM, implemented as a LangChain Runnable.

Deterministic, API-key-free stand-in for a real chat model so the whole
multi-agent pipeline runs offline while still exercising the real LangChain
chain machinery (``ChatPromptTemplate | model | StrOutputParser``). Swap in the
Anthropic provider (set ``LLM_PROVIDER=anthropic``) once a key is available — no
agent code changes.
"""
from __future__ import annotations

import json
from typing import Any, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompt_values import PromptValue
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.tools import BaseTool

from llm.base import BaseLLM


def _required_args(tool: BaseTool) -> list[str]:
    """Names of the tool's required (no-default) arguments, from its schema."""
    schema: Any = tool.args_schema
    if schema is None:
        return []
    if hasattr(schema, "model_json_schema"):
        schema = schema.model_json_schema()
    return list(schema.get("required", []))


class MockLLM(BaseLLM):
    provider = "mock"
    model = "mock-llm"

    def __init__(self) -> None:
        # Intent hint for the in-flight completion, read by the mock model.
        self._task: str | None = None
        super().__init__()

    def build_model(self) -> Runnable:
        """A LangChain Runnable that plays the role of a chat model, offline."""
        return RunnableLambda(self._respond)

    def _respond(self, prompt_value: PromptValue) -> AIMessage:
        human = prompt_value.to_messages()[-1].content
        text = human if isinstance(human, str) else str(human)
        # "polish" = the agent already composed a good draft; a real model would
        # refine tone. Offline we pass the draft through unchanged so the demo
        # output stays clean and readable.
        if self._task == "polish":
            return AIMessage(content=text.strip())
        # Generic deterministic fallback for any other call.
        head = (text.strip().splitlines() or [""])[0][:80]
        return AIMessage(content=f"[mock-llm] ({self._task or 'complete'}) {head}")

    def complete(self, user: str, *, system: str | None = None, task: str | None = None) -> str:
        self._task = task
        try:
            return super().complete(user, system=system, task=task)
        finally:
            self._task = None

    # ── Tool calling (Milestone 2) ──────────────────────────────────────────

    def _bind_tools(self, tools: Sequence[BaseTool]) -> Runnable:
        """Deterministic offline stand-in for a tool-calling chat model.

        Selection rule: on each turn, request every offered tool that (a) has
        not been called yet and (b) has all of its required arguments present
        in the JSON payload of the human message. Once nothing is left to
        call, answer with a final text summary — exactly the shape of turns a
        real tool-calling model produces, minus the nondeterminism.
        """
        tools = list(tools)

        def respond(messages: list[BaseMessage]) -> AIMessage:
            already_called = {
                call["name"]
                for m in messages
                if isinstance(m, AIMessage)
                for call in (m.tool_calls or [])
            }
            payload: dict[str, Any] = {}
            for m in messages:
                if isinstance(m, HumanMessage) and isinstance(m.content, str):
                    try:
                        payload = json.loads(m.content)
                    except (ValueError, TypeError):
                        payload = {}
                    break

            calls = []
            for tool in tools:
                if tool.name in already_called:
                    continue
                if any(arg not in payload for arg in _required_args(tool)):
                    continue
                args = {k: payload[k] for k in tool.args if k in payload}
                calls.append(
                    {"name": tool.name, "args": args, "id": f"call_{tool.name}", "type": "tool_call"}
                )

            if calls:
                return AIMessage(content="", tool_calls=calls)
            return AIMessage(
                content=f"[mock-llm] tool loop complete after {len(already_called)} tool call(s)."
            )

        return RunnableLambda(respond)
