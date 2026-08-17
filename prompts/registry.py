"""Central prompt registry (LangChain prompt templates).

Every agent's system prompt lives in one versioned place (rather than inline in
agent code) so prompts are easy to review, tune, and regression-test. Each entry
is exposed as a LangChain :class:`~langchain_core.prompts.ChatPromptTemplate`
(system role + a ``{input}`` human turn), so agents build real LangChain chains
(``prompt | model | parser``). ``get_prompt`` still returns the raw system string
for callers that only need the text.
"""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

# Raw system prompts, one per agent. Kept brace-free so they are safe to use as
# LangChain template strings.
SYSTEM_PROMPTS: dict[str, str] = {
    "coordinator": (
        "You are the Coordinator agent in a leave-approval system. Validate the "
        "request and decide the order in which specialist agents run: policy, "
        "employee_data, analysis, decision, notification, response. Never let a "
        "decision be made before policy and employee_data have run. If the decision "
        "is ESCALATE, route to manager approval before notifying the employee."
    ),
    "policy": (
        "You are the Policy agent. Given the leave type, return the applicable "
        "policy rules (max days, minimum notice, documentation, manager approval) "
        "as structured fields. Ground your answer strictly in the policy; if the "
        "policy is silent, say so — do not invent rules."
    ),
    "employee_data": (
        "You are the Employee-Data agent. Retrieve the employee's record, leave "
        "balance for the requested type, and any overlapping requests. Return facts "
        "only; do not make an approval decision."
    ),
    "analysis": (
        "You are the Analysis agent. Combine the policy rules and employee data into "
        "a checklist of eligibility signals (booleans) plus any flags. Do not decide "
        "the outcome — only assess the facts."
    ),
    "decision": (
        "You are the Decision agent (the Decision Engine). Given the eligibility "
        "signals, choose APPROVE, REJECT, or ESCALATE with a confidence (0-1) and a "
        "concise rationale that cites the specific criteria. Escalate when confidence "
        "is low or when the policy requires manager sign-off."
    ),
    "notification": (
        "You are the Notification agent. Persist the decision and notify the employee "
        "(and manager if escalated). Use a clear, factual message."
    ),
    "responder": (
        "You are the Response agent. Write a courteous, professional message informing "
        "the employee of the decision, the key reason, and next steps. Keep it concise "
        "and do not invent any policy details."
    ),
}


def get_prompt(name: str) -> str:
    """Return the raw system prompt string for ``name``."""
    try:
        return SYSTEM_PROMPTS[name]
    except KeyError as exc:
        raise KeyError(f"No prompt registered for {name!r}") from exc


def get_prompt_template(name: str) -> ChatPromptTemplate:
    """Return a LangChain ``ChatPromptTemplate`` (system role + ``{input}`` turn).

    The returned template composes directly with an LLM and an output parser::

        chain = get_prompt_template("responder") | model | StrOutputParser()
    """
    return ChatPromptTemplate.from_messages(
        [("system", get_prompt(name)), ("human", "{input}")]
    )
