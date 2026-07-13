"""Policy agent — retrieves the leave policy rules for the requested type.

Milestone 1: reads structured rules from the `policy_rules` table.
Milestone 3: will additionally retrieve policy passages from a vector store (RAG).
"""
from __future__ import annotations

from agents.base import BaseAgent
from schemas.state import LeaveState, PolicyContext
from tools import leave_tools


class PolicyAgent(BaseAgent):
    name = "policy"

    def run(self, state: LeaveState) -> LeaveState:
        leave_type = state.request.leave_type
        row = leave_tools.get_policy(leave_type)

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
