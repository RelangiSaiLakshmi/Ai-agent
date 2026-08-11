"""Enterprise REST API (Milestone 4 / Module 5).

A FastAPI layer that exposes the AI leave-coordination workflow to business
applications. It is a thin HTTP wrapper over :mod:`workflows.service` — all the
orchestration, decision, memory and human-in-the-loop logic lives there, so the
API and the Streamlit dashboard behave identically.

Run locally:
    uvicorn api.app:app --reload
    # interactive docs at http://127.0.0.1:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    LeaveRequestIn,
    ManagerDecisionIn,
    ManagerDecisionResponse,
    RequestOut,
    SubmitResponse,
)
from database.seed import seed
from utils.config import settings
from workflows import service
from workflows.service import ServiceError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Seed the database on first boot so the API is usable out of the box.
    if not settings.resolved_db_path().exists():
        seed()
    yield


app = FastAPI(
    title="AI Agent Coordination & Decision Engine",
    description="Multi-agent leave-approval workflow with memory and human-in-the-loop.",
    version="4.0.0",
    lifespan=lifespan,
)

# Permissive CORS so the dashboard / other front-ends can call the API in dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-coordination-engine", "version": app.version}


@app.get("/employees", tags=["employees"])
def list_employees() -> list[dict]:
    return service.list_employees()


@app.get("/employees/{employee_id}/balances", tags=["employees"])
def employee_balances(employee_id: str) -> list[dict]:
    try:
        return service.get_employee_balances(employee_id)
    except ServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/employees/{employee_id}/history", tags=["employees"])
def employee_history(employee_id: str, limit: int = 10) -> list[dict]:
    return service.get_employee_history(employee_id, limit=limit)


@app.post("/requests", response_model=SubmitResponse, tags=["requests"])
def submit_request(payload: LeaveRequestIn) -> SubmitResponse:
    """Submit a leave request; runs the full multi-agent orchestration graph."""
    state = service.submit_leave_request(
        employee_id=payload.employee_id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
    )
    decision = state.get("decision")
    return SubmitResponse(
        request_id=state["request"]["request_id"],
        status=state["status"],
        outcome=decision["outcome"] if decision else None,
        decision=decision,
        response_to_employee=state.get("draft_response"),
        agent_trace=state.get("logs", []),
        coordination=state.get("agent_messages", []),
        memory_context=state.get("history", []),
    )


@app.get("/requests/{request_id}", response_model=RequestOut, tags=["requests"])
def get_request(request_id: str) -> RequestOut:
    try:
        return RequestOut(**service.get_request(request_id))
    except ServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/approvals/pending", tags=["approvals"])
def pending_approvals() -> list[dict]:
    """Requests awaiting a manager decision (the human-in-the-loop queue)."""
    return service.list_pending_approvals()


@app.post(
    "/requests/{request_id}/manager-decision",
    response_model=ManagerDecisionResponse,
    tags=["approvals"],
)
def manager_decision(request_id: str, payload: ManagerDecisionIn) -> ManagerDecisionResponse:
    """Resume an escalated request with a manager's approve/reject (HITL)."""
    try:
        result = service.apply_manager_decision(
            request_id,
            approved=payload.approved,
            manager_id=payload.manager_id,
            note=payload.note,
        )
    except ServiceError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return ManagerDecisionResponse(**result)
