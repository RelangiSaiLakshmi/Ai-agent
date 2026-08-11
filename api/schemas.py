"""Pydantic request/response models for the REST API (Milestone 4)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LeaveRequestIn(BaseModel):
    employee_id: str = Field(..., examples=["E001"])
    leave_type: str = Field(..., examples=["casual"], description="sick | casual | earned")
    start_date: str = Field(..., examples=["2026-09-01"], description="ISO date YYYY-MM-DD")
    end_date: str = Field(..., examples=["2026-09-03"], description="ISO date YYYY-MM-DD")
    reason: str = ""


class ManagerDecisionIn(BaseModel):
    approved: bool
    manager_id: str = "manager"
    note: str = ""


class DecisionOut(BaseModel):
    outcome: str
    confidence: float
    rationale: str
    criteria_scores: dict[str, str] = {}


class SubmitResponse(BaseModel):
    request_id: str
    status: str
    outcome: str | None = None
    decision: DecisionOut | None = None
    response_to_employee: str | None = None
    agent_trace: list[dict[str, str]] = []
    coordination: list[dict[str, str]] = []
    memory_context: list[dict[str, Any]] = []


class RequestOut(BaseModel):
    request: dict[str, Any]
    decision: dict[str, Any] | None = None
    status: str


class ManagerDecisionResponse(BaseModel):
    request_id: str
    outcome: str
    status: str
    decided_by: str
    rationale: str
