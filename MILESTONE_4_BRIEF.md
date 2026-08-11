# Milestone 4 — Workflow Automation & Deployment (Brief)

**Doc:** `ai coordination system milestone4.docx` — Milestone 4 (Weeks 7–8):
*Implement complex workflow orchestration · Develop APIs and monitoring
dashboards · Deploy the platform to cloud infrastructure · Conduct performance
testing and optimization.* (Covers Module 4 + Module 5 of the project doc.)

## What we added

### 1. Complex workflow orchestration — LangGraph (`workflows/graph.py`)
The Milestone 1/3 sequential pipeline is promoted to a LangGraph `StateGraph`
with real decision points; **the agent classes are unchanged** (each becomes a
node via a thin adapter, so all M3 coordination + memory behaviour carries over):
- **Validation gate** — an invalid request short-circuits from the Coordinator
  straight to `END` instead of running the whole pipeline.
- **Human-in-the-loop branch** — an `ESCALATE` outcome (`AWAITING_MANAGER`) is
  routed through a dedicated `manager_review` node; `APPROVE`/`REJECT` flow
  directly to the Responder.
The sequential runner is kept as an equivalent reference (`run_leave_workflow`);
`tests/test_graph.py` asserts the two agree on every path.

### 2. Human-in-the-loop resume (`workflows/service.py`)
Escalated requests pause at `AWAITING_MANAGER`. A manager resumes them via
`apply_manager_decision(...)`, which records the final (authoritative) decision,
completes the request, and **retains the real outcome in long-term memory** so
future requests carry it. A shared **service layer** backs both the API and the
dashboard, so they stay in lockstep.

### 3. Enterprise REST API — FastAPI (`api/app.py`)
`POST /requests`, `GET /requests/{id}`, `POST /requests/{id}/manager-decision`,
`GET /approvals/pending`, `GET /employees`, `GET /employees/{id}/balances`,
`GET /employees/{id}/history`, `GET /health`. Interactive docs at `/docs`.
Pydantic request/response models in `api/schemas.py`.

### 4. Monitoring dashboard — Streamlit (`frontend/dashboard.py`)
Submit a request and watch the agent trace, the inter-agent coordination bus and
recalled memory; work the manager approval queue (approve/reject); inspect
employee balances and interaction history.

### 5. Deployment (`Dockerfile`, `docker-compose.yml`, `deploy/CLOUD.md`)
One image runs either the API or the dashboard; compose runs both over a shared
SQLite volume. `deploy/CLOUD.md` has Azure Container Apps / AWS / GCP Cloud Run
quick-starts and production notes (managed Postgres seam, secret handling).

### 6. Performance testing (`perf/benchmark.py`, `tests/test_performance.py`)
`python -m perf.benchmark` reports throughput and avg/p50/p95/max latency
(≈49 req/s, ~20 ms avg with the MockLLM, in-process). A smoke test guards
against latency/throughput regressions.

## Tests
`tests/test_graph.py`, `tests/test_service.py`, `tests/test_api.py`,
`tests/test_performance.py` — **55 tests passing** (36 from M1–M3 + 19 new).

## Ambiguities & how they were handled
- **"Deploy to cloud."** No target cloud/account is provided and none is
  reachable from this environment, so we ship the deploy *artifacts* (Docker,
  compose, per-provider quick-starts) rather than a live deployment.
- **Human-in-the-loop mechanism.** Implemented as a DB-backed pause/resume
  (`AWAITING_MANAGER` + `apply_manager_decision`) rather than LangGraph's native
  `interrupt()`+checkpointer. This is offline-first (matching M1–M3), keeps
  resume state durable across API replicas, and needs no checkpoint store.
- **Dashboard vs API coupling.** The dashboard calls the shared service layer
  in-process (robust, no second process required) rather than over HTTP; the
  REST API exposes the identical operations for external integration.
- **Milestone vs Module mismatch.** The milestone doc folds Module 4 (workflow
  automation) and Module 5 (API/dashboard/deploy) into a single "Milestone 4:
  Workflow Automation & Deployment." We delivered both under M4; there is no
  separate Milestone 5 in the timeline.
