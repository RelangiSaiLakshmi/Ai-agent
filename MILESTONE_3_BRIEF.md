# Milestone 3 — Agent Coordination & Memory (Brief)

**Goal:** Turn the pipeline of agents into a *coordinated team* that also
*remembers* past interactions, so decisions become context-aware.

## What we added (3 things)

### 1. Business roles for every agent
Each of the 7 agents now declares a business role (matching the project doc):

| Role | Agent(s) | Does what |
|---|---|---|
| planning | Coordinator | validates request + plans the agent sequence |
| research | Policy, Employee-Data | fetch policy rules + employee data/balance |
| analysis | Analysis | turns facts into eligibility signals |
| decision | Decision | APPROVE / REJECT / ESCALATE + rationale |
| execution | Notification | persists decision, notifies, saves memory |
| response | Responder | writes the employee-facing message |

### 2. Inter-agent communication (a message bus)
Agents now *talk to each other* explicitly, not just via shared state:
- Any agent can `post` a structured message and read its `inbox`.
- Flow: **Research agents → post findings to → Analysis → posts signals to → Decision**;
  Coordinator broadcasts the plan.
- Stored on `LeaveState.agent_messages`.

### 3. Memory (short-term + long-term)
- **Short-term** (`memory/short_term.py`): per-request conversation + the agent bus.
- **Long-term** (`memory/long_term.py`): per-employee interaction history saved in a
  new `interaction_memory` SQLite table.
- A `SharedMemory` repository (`memory/shared.py`) threads both through the run.
- The workflow **recalls an employee's history up front**, so Analysis/Decision are
  *context-aware* (history shows up as a non-blocking signal + rationale note).
  The Notification agent **retains** each completed interaction for next time.

## How to see it working
- Run the CLI — the result summary now shows a **COORDINATION** section (the bus
  messages) and a **MEMORY CONTEXT** section (recalled history).
- Tests: `tests/test_coordination.py` + `tests/test_memory.py` — **36 passing**.

## Design notes (if asked)
- Long-term memory is **offline-first (SQLite)**, matching M1/M2. A vector-store
  semantic recall can slot in behind `LongTermMemory` later with no agent changes.
- `--init-db` reseed now resets `interaction_memory` for clean, deterministic demos.

## Files touched
`agents/base.py` (roles + post/inbox), `agents/{analysis,decision,notification,...}.py`,
`memory/{short_term,long_term,shared}.py`, `database/{schema.sql,db.py,seed.py}`,
`schemas/state.py` (agent_messages), `workflows/pipeline.py`, `main.py`, plus tests.
