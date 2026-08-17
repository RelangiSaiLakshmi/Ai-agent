"""Provider-agnostic LLM interface, built on LangChain.

Every agent talks to the LLM through this small interface, so the underlying
provider (MockLLM offline, Claude via ``langchain-anthropic`` online) can be
swapped without touching any agent code.

Under the hood each provider exposes a LangChain ``Runnable`` chat model as
``self._model``. Completions run as a LangChain chain::

    ChatPromptTemplate | self._model | StrOutputParser()

so prompt templating, model invocation, and output parsing all go through
LangChain — the same machinery LangGraph builds on in later milestones.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from llm.tool_loop import ToolCallRecord, ToolLoopResult


class BaseLLM(ABC):
    provider: str = "base"
    model: str = "base"

    #: LangChain chat model / Runnable[PromptValue -> BaseMessage].
    _model: Runnable

    def __init__(self) -> None:
        self._model = self.build_model()

    @abstractmethod
    def build_model(self) -> Runnable:
        """Return the underlying LangChain Runnable chat model."""
        raise NotImplementedError

    def chain(self, template: ChatPromptTemplate) -> Runnable:
        """Compose ``template | model | StrOutputParser()`` into a LangChain chain."""
        return template | self._model | StrOutputParser()

    def complete(self, user: str, *, system: str | None = None, task: str | None = None) -> str:
        """Return a text completion by running a LangChain chain.

        Args:
            user: the user/content prompt (passed as the ``{input}`` variable).
            system: optional system prompt describing the agent's role.
            task: optional intent hint (e.g. "polish"). Used by MockLLM to return
                sensible offline responses; ignored by real providers.
        """
        messages: list[tuple[str, str]] = []
        if system:
            messages.append(("system", system))
        messages.append(("human", "{input}"))
        template = ChatPromptTemplate.from_messages(messages)
        return self.chain(template).invoke({"input": user})

    # ── Tool calling (Milestone 2) ──────────────────────────────────────────

    def _bind_tools(self, tools: Sequence[BaseTool]) -> Runnable:
        """Return a model that can emit tool calls for `tools`.

        Real chat models (e.g. ChatAnthropic) support this natively; MockLLM
        overrides it with a deterministic offline implementation.
        """
        return self._model.bind_tools(list(tools))

    def run_with_tools(
        self,
        user: str,
        *,
        tools: Sequence[BaseTool],
        system: str | None = None,
        max_iterations: int = 8,
    ) -> ToolLoopResult:
        """Run the standard tool-calling loop until the model answers in text.

        The model decides which of `tools` to invoke (intelligent tool
        selection). Each requested call is executed here, and its result — or
        its error — is fed back as a ToolMessage so the model can recover or
        finish. The loop is bounded by `max_iterations` model turns.

        Exception handling contract:
        - a tool that raises is recorded with ``error`` set and reported back
          to the model as ``ERROR: ...`` instead of crashing the workflow;
        - a call to a tool name that was never offered is rejected the same way;
        - if the model never produces a final text answer, the result has
          ``exhausted=True`` and empty ``text``.
        """
        tool_map = {t.name: t for t in tools}
        messages: list[BaseMessage] = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=user))

        model = self._bind_tools(tools)
        records: list[ToolCallRecord] = []

        for _ in range(max_iterations):
            ai = model.invoke(messages)
            messages.append(ai)
            calls = getattr(ai, "tool_calls", None) or []

            if not calls:
                text = ai.content if isinstance(ai.content, str) else str(ai.content)
                return ToolLoopResult(text=text, tool_results=records, messages=messages)

            for call in calls:
                name, args = call["name"], dict(call.get("args") or {})
                if name not in tool_map:
                    rec = ToolCallRecord(name=name, args=args, error=f"unknown tool {name!r}")
                else:
                    try:
                        rec = ToolCallRecord(name=name, args=args, result=tool_map[name].invoke(args))
                    except Exception as exc:  # tool bugs must not kill the workflow
                        rec = ToolCallRecord(name=name, args=args, error=f"{type(exc).__name__}: {exc}")
                records.append(rec)
                content = (
                    json.dumps(rec.result, default=str) if rec.ok else f"ERROR: {rec.error}"
                )
                messages.append(ToolMessage(content=content, tool_call_id=call.get("id") or name))

        return ToolLoopResult(text="", tool_results=records, messages=messages, exhausted=True)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<{type(self).__name__} provider={self.provider} model={self.model}>"
