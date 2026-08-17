"""LangChain ``@tool`` wrappers for the Leave Approval tool layer (Milestone 2).

Each wrapper exposes one read operation from :mod:`tools.leave_tools` as a
LangChain tool with a generated JSON schema, so an LLM can request it via
native tool-calling. Only *read* tools are exposed to the model; the write
tools (persisting requests/decisions) stay direct-call-only behind the
Coordinator and Notification agents (least privilege).

The ``db_path`` parameter of the underlying functions is deliberately not part
of any tool schema — the model must never choose which database to hit.
"""
from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool, tool

from tools import connectors, leave_tools


@tool
def get_employee(employee_id: str) -> dict[str, Any] | None:
    """Look up an employee's record (name, email, department, manager_id) by employee ID."""
    return leave_tools.get_employee(employee_id)


@tool
def get_leave_balance(employee_id: str, leave_type: str) -> dict[str, Any] | None:
    """Fetch an employee's leave balance (total_days, used_days) for one leave type."""
    return leave_tools.get_leave_balance(employee_id, leave_type)


@tool
def get_overlapping_requests(
    employee_id: str,
    start_date: str,
    end_date: str,
    exclude_request_id: str | None = None,
) -> list[dict[str, Any]]:
    """List the employee's existing leave requests that overlap the given ISO date
    range. Pass the current request's id as exclude_request_id so it does not
    count as its own overlap."""
    return leave_tools.get_overlapping_requests(
        employee_id, start_date, end_date, exclude_request_id=exclude_request_id
    )


@tool
def get_policy(leave_type: str) -> dict[str, Any] | None:
    """Fetch the leave policy rules (max_days_per_year, min_notice_days,
    requires_docs, manager_required, notes) for one leave type."""
    return leave_tools.get_policy(leave_type)


@tool
def get_company_holidays(start_date: str, end_date: str) -> list[dict[str, str]]:
    """List company holidays (date, name) within the given ISO date range,
    inclusive. Backed by the enterprise HR-calendar connector."""
    return connectors.get_company_holidays(start_date, end_date)


#: Read tools available to the Employee-Data agent.
EMPLOYEE_DATA_TOOLS: list[BaseTool] = [get_employee, get_leave_balance, get_overlapping_requests]

#: Read tools available to the Policy agent.
POLICY_TOOLS: list[BaseTool] = [get_policy]

#: Connector-backed tools available to the Analysis agent.
CALENDAR_TOOLS: list[BaseTool] = [get_company_holidays]

#: All model-callable tools, by name.
READ_TOOLS: dict[str, BaseTool] = {
    t.name: t
    for t in [
        get_employee,
        get_leave_balance,
        get_overlapping_requests,
        get_policy,
        get_company_holidays,
    ]
}
