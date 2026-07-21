"""Policy agent — retrieves the leave policy rules for the requested type.

Milestone 2: the agent hands its read tools to the LLM and lets the model
select and invoke them (native tool calling); the state is grounded in the
recorded tool results, never in model prose. If the loop fails to produce a
usable result, the agent falls back to calling the tool directly, so the
workflow degrades gracefully instead of stalling.
Milestone 3: will additionally retrieve policy passages from a vector store (RAG).
"""
from __future__ import annotations

import json

from agents.base import BaseAgent
from prompts import get_prompt
from schemas.state import LeaveState, PolicyContext
from tools import leave_tools
from tools.langchain_tools import POLICY_TOOLS


class PolicyAgent(BaseAgent):
    name = "policy"

    def _fetch_policy(self, state: LeaveState, leave_type: str) -> dict | None:
        """Fetch the policy via the LLM tool-calling loop, validated, with a
        direct-call fallback (action-execution accuracy guard)."""
        loop = self.llm.run_with_tools(
            json.dumps({"leave_type": leave_type}),
            tools=POLICY_TOOLS,
            system=get_prompt("policy"),
        )
        if loop.errors:
            self.log(state, f"Tool errors during policy lookup: {[e.error for e in loop.errors]}")
        try:
            row = loop.last_result("get_policy")
        except KeyError:
            self.log(state, "Model did not fetch the policy; falling back to direct tool call.")
            return leave_tools.get_policy(leave_type)
        # Validate the executed action matched the request before trusting it.
        if row is not None and row.get("leave_type") != leave_type:
            self.log(
                state,
                f"Tool result validation failed (got policy for {row.get('leave_type')!r}); "
                "falling back to direct tool call.",
            )
            return leave_tools.get_policy(leave_type)
        return row

    def run(self, state: LeaveState) -> LeaveState:
        leave_type = state.request.leave_type
        row = self._fetch_policy(state, leave_type)

        if row is None:
            # Policy silent — do NOT invent rules; flag for manager review downstream.
            state.policy = PolicyContext(
                leave_type=leave_type,
                max_days_per_year=0,
                min_notice_days=0,
                requires_docs=False,
                manager_required=True,
                notes="No policy found for this leave type; manager review required.",
            )
            self.log(state, f"No policy found for '{leave_type}'. Flagging for manager review.")
            return state

        state.policy = PolicyContext(
            leave_type=leave_type,
            max_days_per_year=row["max_days_per_year"],
            min_notice_days=row["min_notice_days"],
            requires_docs=bool(row["requires_docs"]),
            manager_required=bool(row["manager_required"]),
            notes=row.get("notes", ""),
        )
        self.log(
            state,
            f"Policy for '{leave_type}': max {state.policy.max_days_per_year}d/yr, "
            f"notice {state.policy.min_notice_days}d, "
            f"docs={'yes' if state.policy.requires_docs else 'no'}, "
            f"manager_required={'yes' if state.policy.manager_required else 'no'}.",
        )
        return state
