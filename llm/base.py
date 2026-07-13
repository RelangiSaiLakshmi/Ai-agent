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

from abc import ABC, abstractmethod

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable


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

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<{type(self).__name__} provider={self.provider} model={self.model}>"
