"""Employee-Data agent — fetches employee record, balance and overlaps (SQL)."""
from __future__ import annotations

from agents.base import BaseAgent
from schemas.state import BalanceInfo, EmployeeRecord, LeaveState
from tools import leave_tools


class EmployeeDataAgent(BaseAgent):
    name = "employee_data"

    def run(self, state: LeaveState) -> LeaveState:
        req = state.request
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
        bal = leave_tools.get_leave_balance(req.employee_id, req.leave_type)
        total = float(bal["total_days"]) if bal else 0.0
        used = float(bal["used_days"]) if bal else 0.0
        available = total - used
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
        self.log(
            state,
            f"{state.employee.name}: {available:.0f} {req.leave_type} day(s) available, "
            f"requesting {days_requested}, {len(overlaps)} overlap(s).",
        )
        return state
