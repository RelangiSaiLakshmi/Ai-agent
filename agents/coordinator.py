"""Coordinator agent — validates the request and plans the agent sequence."""
from __future__ import annotations

import uuid

from agents.base import BaseAgent
from schemas.state import LeaveState, Status
from tools import leave_tools

PLANNED_SEQUENCE = ["policy", "employee_data", "analysis", "decision", "notification", "responder"]


class CoordinatorAgent(BaseAgent):
    name = "coordinator"

    def run(self, state: LeaveState) -> LeaveState:
        req = state.request
        if not req.request_id:
            req.request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"

        days = req.days_span()
        if days <= 0:
            state.status = Status.FAILED
            self.log(state, f"Invalid date range {req.start_date}..{req.end_date}; aborting.")
            return state

        # Persist the incoming request so it exists for downstream write-backs.
        leave_tools.record_request(
            {
                "request_id": req.request_id,
                "employee_id": req.employee_id,
                "leave_type": req.leave_type,
                "start_date": req.start_date,
                "end_date": req.end_date,
                "days_requested": days,
                "reason": req.reason,
                "status": Status.RECEIVED,
            }
        )
        state.status = Status.IN_PROGRESS
        self.log(
            state,
            f"Request {req.request_id}: {req.employee_id} wants {days} day(s) of "
            f"{req.leave_type} ({req.start_date}..{req.end_date}). "
            f"Plan: {' -> '.join(PLANNED_SEQUENCE)}",
        )
        return state
