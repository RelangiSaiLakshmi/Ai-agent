"""LLM factory — selects a provider from configuration."""
from __future__ import annotations

from llm.base import BaseLLM
from llm.mock import MockLLM
from utils.config import settings


def get_llm(provider: str | None = None) -> BaseLLM:
    provider = (provider or settings.llm_provider).lower()

    if provider == "mock":
        return MockLLM()

    if provider == "anthropic":
        # Imported lazily so `mock` mode needs no third-party packages.
        from llm.anthropic_provider import AnthropicLLM

        return AnthropicLLM(model=settings.llm_model, api_key=settings.anthropic_api_key)

    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'mock' or 'anthropic')")
