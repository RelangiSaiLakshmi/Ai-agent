"""Claude provider via LangChain (``langchain-anthropic``).

Selected when ``LLM_PROVIDER=anthropic``. Requires:
    pip install langchain-anthropic     (in requirements.txt)
    ANTHROPIC_API_KEY set in .env

Only ``build_model`` is provider-specific; prompt templating, chain invocation
and output parsing are inherited from :class:`~llm.base.BaseLLM`.
"""
from __future__ import annotations

from langchain_core.runnables import Runnable

from llm.base import BaseLLM


class AnthropicLLM(BaseLLM):
    provider = "anthropic"

    def __init__(self, model: str, api_key: str) -> None:
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to .env or use LLM_PROVIDER=mock."
            )
        self.model = model
        self._api_key = api_key
        super().__init__()  # builds the LangChain model

    def build_model(self) -> Runnable:
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:  # pragma: no cover - depends on optional install
            raise RuntimeError(
                "langchain-anthropic is not installed. Run: pip install langchain-anthropic"
            ) from exc
        return ChatAnthropic(model=self.model, api_key=self._api_key, temperature=0)
