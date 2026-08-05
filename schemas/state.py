"""Workflow state and the structured objects agents pass between each other.

Built on stdlib dataclasses so Milestone 1 runs with no dependencies. When
LangGraph is introduced (Milestone 2/4), this maps cleanly onto a Pydantic
state model — the field shapes stay the same.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from typing import Any


class Status:
    RECEIVED = "RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_MANAGER = "AWAITING_MANAGER"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Outcome:
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"


@dataclass
class LeaveRequest:
    employee_id: str
    leave_type: str            # sick | casual | earned
    start_date: str            # ISO date, e.g. "2026-07-20"
    end_date: str
    reason: str = ""
    request_id: str = ""

    def days_span(self) -> int:
        """Working days requested, inclusive, excluding weekends."""
        start = date.fromisoformat(self.start_date)
        end = date.fromisoformat(self.end_date)
        if end < start:
            return 0
        days = 0
        cur = start
        while cur <= end:
            if cur.weekday() < 5:  # Mon–Fri
                days += 1
            cur = date.fromordinal(cur.toordinal() + 1)
        return days


@dataclass
class EmployeeRecord:
    employee_id: str
    name: str
    email: str
    department: str = ""
    manager_id: str | None = None


@dataclass
class BalanceInfo:
    leave_type: str
    total_days: float
    used_days: float
    days_available: float
    days_requested: float
    after_balance: float
    overlaps: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PolicyContext:
    leave_type: str
    max_days_per_year: float
    min_notice_days: int
    requires_docs: bool
    manager_required: bool
    notes: str = ""


@dataclass
class AnalysisResult:
    balance_ok: bool
    notice_ok: bool
    no_overlap: bool
    within_max: bool
    docs_ok: bool
    flags: list[str] = field(default_factory=list)

    def all_pass(self) -> bool:
        return all([self.balance_ok, self.notice_ok, self.no_overlap, self.within_max, self.docs_ok])


@dataclass
class Decision:
    outcome: str                       # Outcome.*
    confidence: float                  # 0.0 – 1.0
    rationale: str
    criteria_scores: dict[str, str] = field(default_factory=dict)  # criterion -> pass|fail
    decided_by: str = "system"


@dataclass
class AgentMessage:
    """One message on the inter-agent bus (Milestone 3).

    Agents post structured messages here to share findings explicitly, rather
    than only mutating the shared state implicitly. ``to="all"`` broadcasts.
    """
    sender: str                        # agent name that posted the message
    role: str                          # sender's business role (planning/research/...)
    content: str
    to: str = "all"                    # recipient agent name, or "all"
    kind: str = "update"              # update | finding | decision | plan | alert

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class LeaveState:
    request: LeaveRequest
    employee: EmployeeRecord | None = None
    policy: PolicyContext | None = None
    balance: BalanceInfo | None = None
    analysis: AnalysisResult | None = None
    decision: Decision | None = None
    draft_response: str | None = None
    messages: list[dict[str, str]] = field(default_factory=list)   # short-term conversational memory
    agent_messages: list[dict[str, str]] = field(default_factory=list)  # inter-agent bus (M3)
    history: list[dict[str, Any]] = field(default_factory=list)     # recalled long-term memory (M3)
    status: str = Status.RECEIVED
    logs: list[dict[str, str]] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
