"""Analysis agent — turns policy + employee data into eligibility signals.

Produces booleans only; it does not decide the outcome (that's the Decision
agent's job). Keeping assessment separate from the decision keeps the Decision
Engine auditable.
"""
from __future__ import annotations

from datetime import date

from agents.base import BaseAgent
from schemas.state import AnalysisResult, LeaveState
from tools.connectors import holiday_calendar


def _working_days_between(from_date: date, to_date: date) -> int:
    """Working days from `from_date` (exclusive) up to `to_date` (exclusive)."""
    if to_date <= from_date:
        return 0
    days = 0
    cur = date.fromordinal(from_date.toordinal() + 1)
    while cur < to_date:
        if cur.weekday() < 5:
            days += 1
        cur = date.fromordinal(cur.toordinal() + 1)
    return days


class AnalysisAgent(BaseAgent):
    name = "analysis"

    def run(self, state: LeaveState) -> LeaveState:
        flags: list[str] = []

        # Missing data is a hard failure -> everything false, flag it.
        if state.employee is None or state.balance is None or state.policy is None:
            flags.append("missing_employee_or_balance_or_policy")
            state.analysis = AnalysisResult(
                balance_ok=False, notice_ok=False, no_overlap=False,
                within_max=False, docs_ok=False, flags=flags,
            )
            self.log(state, "Missing data; all eligibility signals set to fail.")
            return state

        bal, pol, req = state.balance, state.policy, state.request

        balance_ok = bal.after_balance >= 0
        within_max = bal.days_requested <= pol.max_days_per_year
        no_overlap = len(bal.overlaps) == 0

        notice_days = _working_days_between(date.today(), date.fromisoformat(req.start_date))
        notice_ok = notice_days >= pol.min_notice_days

        # Docs don't block in M1, but surface a flag when the policy needs them.
        docs_ok = True
        if pol.requires_docs and bal.days_requested > 2:
            flags.append("documentation_required")

        if not balance_ok:
            flags.append(f"insufficient_balance(short_by={-bal.after_balance:.0f}d)")
        if not within_max:
            flags.append("exceeds_annual_max")
        if not notice_ok:
            flags.append(f"insufficient_notice(have={notice_days}d,need={pol.min_notice_days}d)")
        if not no_overlap:
            flags.append(f"overlaps({len(bal.overlaps)})")
        if pol.manager_required:
            flags.append("manager_approval_required")

        # Informational only: company holidays inside the range don't consume
        # leave, so surface them for the responder/manager without blocking.
        holidays = holiday_calendar.holidays_between(req.start_date, req.end_date)
        if holidays:
            flags.append(f"company_holidays_in_range({', '.join(h.name for h in holidays)})")

        state.analysis = AnalysisResult(
            balance_ok=balance_ok,
            notice_ok=notice_ok,
            no_overlap=no_overlap,
            within_max=within_max,
            docs_ok=docs_ok,
            flags=flags,
        )
        self.log(
            state,
            f"Signals: balance_ok={balance_ok}, notice_ok={notice_ok}, "
            f"no_overlap={no_overlap}, within_max={within_max}. "
            f"Flags: {flags or 'none'}.",
        )
        return state
