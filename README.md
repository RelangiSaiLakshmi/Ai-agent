# AI Agent Coordination & Decision Engine — Leave Approval System

A multi-agent AI system that processes employee leave requests end to end.
Seven specialized agents collaborate — checking policy, balances, and
eligibility — to automatically **APPROVE, REJECT, or ESCALATE** a request and
write the response to the employee. Built on **LangChain**; runs fully offline
via a deterministic mock LLM, or online with Claude (`LLM_PROVIDER=anthropic`).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python main.py --init-db     # create + seed the SQLite database
python main.py --list        # show seeded employees
python main.py --demo        # run APPROVE / REJECT / ESCALATE scenarios
python main.py --employee-id E004 --leave-type casual \
               --start 2026-07-27 --end 2026-07-29 --reason "wedding"

pytest tests/ -v             # 36 tests
```

> Re-run `--init-db` before demos: each run persists its request, so a repeat
> of the same dates is detected as an overlap and escalates (by design).

## Architecture

```
LeaveRequest
   │
   ▼
Coordinator ─▶ Policy ─▶ EmployeeData ─▶ Analysis ─▶ Decision ─▶ Notification ─▶ Responder
   (plan &      (rules,    (record,        (eligibility  (APPROVE/    (persist +      (final
    persist)     via LLM    balance,        signals +     REJECT/      notify)         message)
                 tools)     overlaps,       holiday       ESCALATE)
                            via LLM tools)  flags)
```

- `schemas/state.py` — the shared `LeaveState` every agent reads and updates
  (plus the inter-agent message bus and recalled history, Milestone 3).
- `agents/` — one file per specialist; uniform `run(state) -> state` contract;
  each declares a business `role` (planning / research / analysis / decision /
  execution / response).
- `memory/` — short-term (conversation + agent bus) and long-term (per-employee
  history) memory behind a shared `SharedMemory` repository (Milestone 3).
- `workflows/pipeline.py` — sequential orchestrator (LangGraph planned).
- `tools/` — tool layer: SQLite read/write tools (`leave_tools.py`), LangChain
  `@tool` wrappers with JSON schemas (`langchain_tools.py`), and enterprise
  API connectors (`connectors.py`, offline-first holiday calendar).
- `llm/` — pluggable providers (`mock` / `anthropic`) plus the tool-calling
  loop (`BaseLLM.run_with_tools`) with exception handling and audit records.
- `prompts/registry.py` — central per-agent prompt templates.
- `database/` — SQLite schema, helpers, deterministic seed data.

### Tool calling (Milestone 2)

The Policy and Employee-Data agents hand their read tools to the LLM, which
selects and invokes them natively (`run_with_tools`). Key properties:

- **Least privilege** — only read tools are exposed to the model; writes stay
  behind trusted agents, and `db_path` is never model-controllable.
- **Grounding** — agent state is built from recorded tool results, never from
  model prose; results are validated against the request before being trusted.
- **Graceful degradation** — tool errors and unknown-tool calls are fed back
  to the model instead of crashing; skipped tools are re-fetched directly;
  runaway loops are bounded by `max_iterations`.

### Agent coordination & memory (Milestone 3)

The seven agents are specialized by **business role**, matching the roles named
in the project doc (Planning, Research, Analysis, Decision):

| Role | Agent(s) | Responsibility |
|---|---|---|
| planning | Coordinator | validate + plan the agent sequence |
| research | Policy, Employee-Data | retrieve policy rules + employee data/balance |
| analysis | Analysis | turn facts into eligibility signals |
| decision | Decision | APPROVE / REJECT / ESCALATE + rationale |
| execution | Notification | persist the decision, notify, retain memory |
| response | Responder | write the employee-facing message |

They coordinate two ways:

- **Explicit communication** — agents `post` structured messages to an
  inter-agent bus (`LeaveState.agent_messages`) and read their `inbox`; e.g. the
  Research agents post findings addressed to Analysis, which posts signals to
  Decision. This is in addition to the implicit sharing via `LeaveState`.
- **Shared memory** — `memory/` provides a `SharedMemory` repository combining
  **short-term** memory (per-request conversation + the agent bus) and
  **long-term** memory (per-employee interaction history in the
  `interaction_memory` SQLite table). The workflow recalls an employee's history
  up front, so the Analysis/Decision agents make **context-aware** decisions
  (history surfaces as an informational, non-blocking signal + rationale note);
  the Notification agent retains each completed interaction for next time.

Long-term memory is offline-first (SQLite), matching the M1/M2 architecture; a
vector-store-backed semantic recall can slot in behind `LongTermMemory` later
without touching agent code.

## Configuration

Copy `.env.example` to `.env`. Defaults work offline with no keys.

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `mock` | `mock` (offline) or `anthropic` (Claude) |
| `LLM_MODEL` | `claude-sonnet-4-6` | model id for the Anthropic provider |
| `ANTHROPIC_API_KEY` | — | required only for `anthropic` |
| `DB_PATH` | `data/app.db` | SQLite location |

## Milestones

| # | Scope | Status |
|---|---|---|
| 1 | Agent foundation: LangChain setup, 7 agents, prompts, workflow, CLI + tests | ✅ done |
| 2 | Tool integration: `@tool` schemas, intelligent tool selection, API connectors, exception handling, action-accuracy validation | ✅ done |
| 3 | Coordination & memory: business-role agents, inter-agent bus, short-term + long-term memory, context-aware decisions | ✅ done |
| 4 | LangGraph workflow, human-in-the-loop manager approval, FastAPI layer | ⏳ planned |
| 5 | Streamlit dashboard, observability | ⏳ planned |
