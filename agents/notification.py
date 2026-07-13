"""Notification agent — persists the decision and (mock) notifies the employee.

This is the only agent with write access to the database (least privilege). The
email/Slack send is mocked in Milestone 1 (logged, not actually sent).
"""
from __future__ import annotations

import json
import uuid

from agents.base import BaseAgent
from schemas.state import LeaveState, Outcome, Status
from tools import leave_tools


class NotificationAgent(BaseAgent):
    name = "notification"

    def run(self, state: LeaveState) -> LeaveState:
        if state.decision is None:
            self.log(state, "No decision to record; skipping.")
            return state

        dec = state.decision
        req = state.request

        leave_tools.record_decision(
            {
                "decision_id": f"DEC-{uuid.uuid4().hex[:8].upper()}",
                "request_id": req.request_id,
                "outcome": dec.outcome,
                "confidence": dec.confidence,
                "rationale": dec.rationale,
                "criteria_json": json.dumps(dec.criteria_scores),
                "decided_by": dec.decided_by,
            }
        )

        new_status = Status.AWAITING_MANAGER if dec.outcome == Outcome.ESCALATE else Status.COMPLETED
        leave_tools.set_request_status(req.request_id, new_status)
        state.status = new_status

        recipient = state.employee.email if state.employee else req.employee_id
        self.log(state, f"Decision persisted; status -> {new_status}. (mock) notified {recipient}.")
        if dec.outcome == Outcome.ESCALATE and state.employee and state.employee.manager_id:
            self.log(state, f"(mock) escalation sent to manager {state.employee.manager_id}.")
        return state
