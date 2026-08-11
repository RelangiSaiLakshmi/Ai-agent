"""REST API tests (Milestone 4) via FastAPI's TestClient."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import app
from schemas.state import Outcome, Status


@pytest.fixture()
def client(seeded_db):
    # seeded_db points settings.db_path at a temp DB; the API reads that path.
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_employees(client):
    resp = client.get("/employees")
    assert resp.status_code == 200
    assert any(e["employee_id"] == "E001" for e in resp.json())


def test_submit_approve(client, future_range):
    start, end = future_range()
    resp = client.post(
        "/requests",
        json={"employee_id": "E001", "leave_type": "casual",
              "start_date": start, "end_date": end, "reason": "trip"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["outcome"] == Outcome.APPROVE
    assert body["status"] == Status.COMPLETED
    assert body["agent_trace"]          # the run trace is exposed
    assert body["response_to_employee"]


def test_escalation_flow_over_http(client, future_range):
    start, end = future_range()
    submit = client.post(
        "/requests",
        json={"employee_id": "E003", "leave_type": "earned",
              "start_date": start, "end_date": end},
    ).json()
    rid = submit["request_id"]
    assert submit["status"] == Status.AWAITING_MANAGER

    pending = client.get("/approvals/pending").json()
    assert rid in {p["request_id"] for p in pending}

    md = client.post(f"/requests/{rid}/manager-decision",
                     json={"approved": True, "manager_id": "M002"})
    assert md.status_code == 200
    assert md.json()["outcome"] == Outcome.APPROVE

    got = client.get(f"/requests/{rid}").json()
    assert got["status"] == Status.COMPLETED


def test_get_unknown_request_404(client):
    assert client.get("/requests/NOPE").status_code == 404


def test_double_manager_decision_conflict(client, future_range):
    start, end = future_range()
    rid = client.post(
        "/requests",
        json={"employee_id": "E003", "leave_type": "earned",
              "start_date": start, "end_date": end},
    ).json()["request_id"]
    client.post(f"/requests/{rid}/manager-decision", json={"approved": True})
    # second decision on a now-COMPLETED request conflicts
    second = client.post(f"/requests/{rid}/manager-decision", json={"approved": False})
    assert second.status_code == 409


def test_employee_balances_and_history(client, future_range):
    assert client.get("/employees/E001/balances").status_code == 200
    assert client.get("/employees/E999/balances").status_code == 404
    start, end = future_range()
    client.post(
        "/requests",
        json={"employee_id": "E001", "leave_type": "casual",
              "start_date": start, "end_date": end},
    )
    history = client.get("/employees/E001/history").json()
    assert len(history) >= 1
