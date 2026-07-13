"""Decision agent — the Decision Engine.

Milestone 1 uses a transparent, config-free rule set to produce an auditable
outcome (APPROVE / REJECT / ESCALATE) with a confidence and rationale. In later
milestones the criteria/weights move to config and the LLM contributes to the
rationale and borderline judgement.
"""
from __future__ import annotations

from agents.base import BaseAgent
from schemas.state import Decision, LeaveState, Outcome


class DecisionAgent(BaseAgent):
    name = "decision"

    def run(self, state: LeaveState) -> LeaveState:
        a = state.analysis
        pol = state.policy
        if a is None or pol is None:
            state.decision = Decision(
                outcome=Outcome.ESCALATE,
                confidence=0.0,
                rationale="Insufficient data to decide; routing to a human.",
                criteria_scores={},
            )
            self.log(state, "ESCALATE (no analysis available).")
            return state

        criteria = {
            "balance_ok": "pass" if a.balance_ok else "fail",
            "within_max": "pass" if a.within_max else "fail",
            "notice_ok": "pass" if a.notice_ok else "fail",
            "no_overlap": "pass" if a.no_overlap else "fail",
            "docs_ok": "pass" if a.docs_ok else "fail",
        }

        # Rule ladder (highest precedence first).
        if not a.balance_ok or not a.within_max:
            reason = "insufficient leave balance" if not a.balance_ok else "request exceeds annual maximum"
            outcome, confidence, rationale = (
                Outcome.REJECT, 0.9, f"Rejected: {reason}."
            )
        elif pol.manager_required:
            outcome, confidence, rationale = (
                Outcome.ESCALATE, 0.9,
                "Policy requires manager approval for this leave type; escalating.",
            )
        elif not a.notice_ok:
            outcome, confidence, rationale = (
                Outcome.ESCALATE, 0.6,
                "Notice period not met; escalating for manager discretion.",
            )
        elif not a.no_overlap:
            outcome, confidence, rationale = (
                Outcome.ESCALATE, 0.6,
                "Overlaps with existing leave; escalating for review.",
            )
        else:
            outcome, confidence, rationale = (
                Outcome.APPROVE, 0.95,
                "All eligibility criteria satisfied; auto-approved.",
            )

        state.decision = Decision(
            outcome=outcome,
            confidence=confidence,
            rationale=rationale,
            criteria_scores=criteria,
        )
        self.log(state, f"{outcome} (confidence {confidence:.2f}) — {rationale}")
        return state
