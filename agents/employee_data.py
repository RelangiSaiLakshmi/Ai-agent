"""Employee-Data agent — fetches employee record, balance and overlaps.

Milestone 2: the LLM selects and invokes this agent's read tools via native
tool calling; the state is grounded in the recorded tool results. Each result
is validated against the request (accuracy guard) and any tool the model
skipped or bungled is re-fetched with a direct call, so the workflow never
loses data to a flaky model turn.
"""
from __future__ import annotations

import json
from typing import Any

from agents.base import BaseAgent
from llm.tool_loop import ToolLoopResult
from prompts import get_prompt
from schemas.state import BalanceInfo, EmployeeRecord, LeaveState
from tools import leave_tools
from tools.langchain_tools import EMPLOYEE_DATA_TOOLS


class EmployeeDataAgent(BaseAgent):
    name = "employee_data"
    role = "research"  # Research Agent — employee/balance retrieval (project-doc role)

    def _grounded(self, loop: ToolLoopResult, tool_name: str, fallback, *args) -> Any:
        """Take `tool_name`'s result from the loop, or re-fetch it directly."""
        try:
            return loop.last_result(tool_name)
        except KeyError:
            return fallback(*args)

    def run(self, state: LeaveState) -> LeaveState:
        req = state.request
        payload = {
            "employee_id": req.employee_id,
            "leave_type": req.leave_type,
            "start_date": req.start_date,
            "end_date": req.end_date,
        }
        if req.request_id:
            payload["exclude_request_id"] = req.request_id

        loop = self.llm.run_with_tools(
            json.dumps(payload),
            tools=EMPLOYEE_DATA_TOOLS,
            system=get_prompt("employee_data"),
        )
        if loop.errors:
            self.log(state, f"Tool errors during data lookup: {[e.error for e in loop.errors]}")
        self.log(
            state,
            f"Model selected {len(loop.tool_results)} tool call(s): "
            f"{sorted({r.name for r in loop.tool_results})}.",
        )

        emp = self._grounded(loop, "get_employee", leave_tools.get_employee, req.employee_id)
        # Accuracy guard: the record must belong to the requesting employee.
        if emp is not None and emp.get("employee_id") != req.employee_id:
            self.log(state, "Tool result validation failed for get_employee; re-fetching directly.")
            emp = leave_tools.get_employee(req.employee_id)
        if emp is None:
            # Leave state.employee/state.balance as None; the Analysis agent
            # treats missing data as a hard failure signal.
            self.log(state, f"Employee '{req.employee_id}' not found.")
            return state

        state.employee = EmployeeRecord(
            employee_id=emp["employee_id"],
            name=emp["name"],
            email=emp["email"],
            department=emp.get("department", ""),
            manager_id=emp.get("manager_id"),
        )

        days_requested = req.days_span()
        bal = self._grounded(
            loop, "get_leave_balance", leave_tools.get_leave_balance, req.employee_id, req.leave_type
        )
        total = float(bal["total_days"]) if bal else 0.0
        used = float(bal["used_days"]) if bal else 0.0
        available = total - used
        try:
            overlaps = loop.last_result("get_overlapping_requests")
        except KeyError:
            overlaps = leave_tools.get_overlapping_requests(
                req.employee_id, req.start_date, req.end_date, exclude_request_id=req.request_id
            )

        state.balance = BalanceInfo(
            leave_type=req.leave_type,
            total_days=total,
            used_days=used,
            days_available=available,
            days_requested=days_requested,
            after_balance=available - days_requested,
            overlaps=overlaps,
        )
        self.post(
            state,
            f"{state.employee.name}: {available:.0f} {req.leave_type} day(s) available, "
            f"requesting {days_requested}, {len(overlaps)} overlap(s).",
            to="analysis",
            kind="finding",
        )
        self.log(
            state,
            f"{state.employee.name}: {available:.0f} {req.leave_type} day(s) available, "
            f"requesting {days_requested}, {len(overlaps)} overlap(s).",
        )
        return state
