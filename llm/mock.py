"""Offline mock LLM, implemented as a LangChain Runnable.

Deterministic, API-key-free stand-in for a real chat model so the whole
multi-agent pipeline runs offline while still exercising the real LangChain
chain machinery (``ChatPromptTemplate | model | StrOutputParser``). Swap in the
Anthropic provider (set ``LLM_PROVIDER=anthropic``) once a key is available — no
agent code changes.
"""
from __future__ import annotations

from langchain_core.messages import AIMessage
from langchain_core.prompt_values import PromptValue
from langchain_core.runnables import Runnable, RunnableLambda

from llm.base import BaseLLM


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
