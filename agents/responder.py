"""Response agent — produces the final professional message to the employee.

The agent composes a grounded draft from the decision, then asks the LLM to
polish it via a LangChain chain. Under the offline MockLLM the draft passes
through unchanged; once a real provider is wired the same call rephrases it
naturally — no code change.
"""
from __future__ import annotations

from agents.base import BaseAgent
from prompts import get_prompt
from schemas.state import LeaveState, Outcome


class ResponderAgent(BaseAgent):
    name = "responder"
    role = "response"  # Response Agent (project-doc role)

    def run(self, state: LeaveState) -> LeaveState:
        dec = state.decision
        name = state.employee.name if state.employee else state.request.employee_id
        leave_type = state.request.leave_type

        if dec is None:
            draft = f"Hello {name}, we could not process your {leave_type} leave request. Please contact HR."
        elif dec.outcome == Outcome.APPROVE:
            draft = (
                f"Hello {name}, your {leave_type} leave request "
                f"({state.request.start_date} to {state.request.end_date}) has been "
                f"approved. {dec.rationale}"
            )
        elif dec.outcome == Outcome.REJECT:
            draft = (
                f"Hello {name}, unfortunately your {leave_type} leave request could not "
                f"be approved. Reason: {dec.rationale} Please review and resubmit if applicable."
            )
        else:  # ESCALATE
            draft = (
                f"Hello {name}, your {leave_type} leave request has been forwarded to "
                f"your manager for approval. {dec.rationale} You will be notified once a "
                f"decision is made."
            )

        polished = self.llm.complete(draft, system=get_prompt("responder"), task="polish")
        state.draft_response = polished
        self.remember(state, "assistant", polished)  # short-term conversational memory
        self.log(state, "Final response generated.")
        return state
