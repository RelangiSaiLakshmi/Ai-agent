"""Milestone 1 foundation tests: schema/state, LLM interface, config."""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from llm import get_llm
from llm.mock import MockLLM
from prompts import get_prompt, get_prompt_template
from schemas.state import LeaveRequest


def test_days_span_excludes_weekends():
    # Mon 2026-07-13 .. Fri 2026-07-17 = 5 working days
    req = LeaveRequest("E001", "casual", "2026-07-13", "2026-07-17", "")
    assert req.days_span() == 5


def test_days_span_single_day():
    req = LeaveRequest("E001", "casual", "2026-07-13", "2026-07-13", "")
    assert req.days_span() == 1


def test_days_span_invalid_range_is_zero():
    req = LeaveRequest("E001", "casual", "2026-07-17", "2026-07-13", "")
    assert req.days_span() == 0


def test_factory_returns_mock_by_default():
    llm = get_llm("mock")
    assert isinstance(llm, MockLLM)
    assert llm.provider == "mock"


def test_mock_polish_passthrough():
    llm = MockLLM()
    assert llm.complete("Hello Asha, approved.", task="polish") == "Hello Asha, approved."


def test_mock_llm_is_backed_by_langchain_runnable():
    # The offline provider genuinely uses LangChain (not a hand-rolled stub).
    assert isinstance(MockLLM()._model, Runnable)


def test_prompt_registry_exposes_langchain_templates():
    template = get_prompt_template("responder")
    assert isinstance(template, ChatPromptTemplate)
    # The system turn carries the registered role prompt; {input} is the human turn.
    rendered = template.invoke({"input": "hello"}).to_messages()
    assert rendered[0].content == get_prompt("responder")
    assert rendered[-1].content == "hello"


def test_complete_runs_through_a_langchain_chain():
    # A completion with no special task exercises ChatPromptTemplate | model | parser.
    out = MockLLM().complete("Ping", system=get_prompt("responder"))
    assert out.startswith("[mock-llm]")
