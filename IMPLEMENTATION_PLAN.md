# Implementation Plan — Remaining Work

_Status as of 2026-08-09, after completing Milestone 4._

## Requirement coverage so far

### Milestone 1 — Agent Foundation (✅ complete)

| Task (from project doc) | Where it lives |
|---|---|
| Configure LangChain and required dependencies | `requirements.txt`; every LLM call is a LangChain chain (`llm/base.py`) |
| Develop foundational AI agents | 7 agents in `agents/` with a uniform `run(state)` contract |
| Implement prompt templates and interaction workflows | `prompts/registry.py` (ChatPromptTemplates), `workflows/pipeline.py` |
| Create basic testing interfaces | `main.py` CLI harness + pytest suite |

### Milestone 2 — Tool Integration & Action Execution (✅ complete)

| Task (from milestone doc) | Where it lives |
|---|---|
| Develop custom enterprise tools and API connectors | `tools/leave_tools.py`, `tools/langchain_tools.py` (`@tool` schemas), `tools/connectors.py` (holiday-calendar connector with swappable transport) |
| Implement intelligent tool selection mechanisms | `BaseLLM.run_with_tools` — the model selects/invokes tools natively; deterministic offline equivalent in `MockLLM._bind_tools`; Policy + Employee-Data agents drive it |
| Test tool invocation workflows and exception handling | `tests/test_tool_calling.py`, `tests/test_tool_exceptions.py` — tool errors, unknown tools, bounded loops, model-skips-tools fallback |
| Validate action execution accuracy | Result-vs-request validation in agents; DB write-back vs decision parity test; tool-path vs direct-path parity test |

### Milestone 3 — Agent Coordination & Memory Systems (✅ complete)

Requirements taken from the Milestone 3 doc (`ai coordination system milestone3.docx`,
Module 3 + Milestone 3 task list), not the earlier self-derived roadmap.

| Task (from milestone doc) | Where it lives |
|---|---|
| Develop specialized agents with defined business roles (Planning, Research, Analysis, Decision, …) | `role` on each agent in `agents/`; mapping documented in README. Existing seven agents were kept and tagged rather than renamed (the doc says "such as", i.e. illustrative) |
| Implement agent communication and coordination mechanisms | inter-agent message bus: `LeaveState.agent_messages` + `BaseAgent.post/inbox` + `ShortTermMemory`; Research→Analysis→Decision post/read findings |
| Configure short-term and long-term memory systems | `memory/short_term.py` (conversation + bus), `memory/long_term.py` (SQLite `interaction_memory`), `memory/shared.py` (`SharedMemory` repository) |
| Validate collaborative workflow execution | `tests/test_memory.py`, `tests/test_coordination.py` (roles, bus, cross-request recall, context-aware rationale) — 36 tests passing |

**Scope decision (flagged ambiguity):** the M3 doc scopes memory as
*short-term conversational* + *long-term knowledge retention* / *shared memory
repositories* — it does **not** mention RAG or a vector store (that was a
self-derived idea in the pre-M3 plan below). To stay offline-first and
dependency-light (the M1/M2 architecture), long-term memory is SQLite-backed;
`LongTermMemory` is the seam a vector store can slot behind later.

## M3 verification pass (2026-08-05)

Re-verified M3 against `ai coordination system milestone3.docx`. All 36 tests
pass and the workflow runs end-to-end with coordination + memory. Three
consistency issues found and fixed:

1. **`seed()` did not reset `interaction_memory`** — the M3 long-term table was
   omitted from the transactional-table cleanup, so `--init-db` left stale
   history behind and memory recall was non-deterministic across demos. ✅ Fixed
   in `database/seed.py`.
2. **Stale docstring in `agents/policy.py`** — claimed M3 would add a RAG/vector
   store, contradicting the documented M3 scope decision (RAG deferred). ✅
   Corrected to describe the agent's actual Research role + bus posting.
3. **M3 features invisible from the CLI** — the inter-agent bus and recalled
   long-term memory only appeared in debug logs, not the result summary, so a
   collaborative run couldn't be validated from the testing interface. ✅ Added
   `MEMORY CONTEXT` + `COORDINATION` sections to `main.py`.

## Gaps identified (and how they were / will be closed)

1. **`MockLLM.run_with_tools` was missing** — the M2 tests existed but the loop
   didn't. ✅ Closed: implemented provider-agnostically in `BaseLLM` (works with
   ChatAnthropic's native `bind_tools`) with a deterministic mock override.
2. **No API connector existed** (M2 explicitly asks for "API connectors", not
   just DB tools). ✅ Closed: `HolidayCalendarConnector` — offline JSON transport
   now, HTTP transport swaps in without touching agents/tools.
3. **No exception-handling story** for tool invocation. ✅ Closed: errors are
   recorded and fed back to the model; unknown tools rejected; loops bounded;
   agents fall back to direct calls.
4. **`tests/test_tool_calling.py` had been commented out** (to keep demo runs
   green while the loop was unimplemented). ✅ Restored and extended; suite is
   29 passing.
5. **README was empty** (M1 polish leftover). ✅ Written.
6. **Milestone 2 work is uncommitted** — all new files are untracked on
   `feature/milestone-1-agent-foundation`. ⚠️ Open: commit (ideally on a
   `feature/milestone-2-tool-integration` branch) when ready.
7. **Docs only define Milestones 1–2.** The project outcomes imply the rest
   (memory, workflow automation, REST API); the plan below is derived from
   those outcomes and the roadmap already noted in the codebase. Confirm exact
   M3+ task lists when the next milestone doc arrives.

## Remaining work (derived from project outcomes)

### Milestone 3 — done (see the completed section above)

_Superseded by the actual M3 doc._ Delivered: business-role agents, the
inter-agent bus, and short-term + long-term memory (SQLite). Items 2 and 3 of
the original self-derived plan below were built as described; item 1 (RAG over
policy docs via ChromaDB) was **deferred** — the M3 doc did not ask for a vector
store, so it is now optional future work behind the `LongTermMemory` seam.

### Milestone 4 — Workflow Automation & Deployment (✅ complete)

Requirements from the Milestone 4 doc (`ai coordination system milestone4.docx`,
Milestone 4 task list; covers Module 4 + Module 5).

| Task (from milestone doc) | Where it lives |
|---|---|
| Implement complex workflow orchestration | `workflows/graph.py` — LangGraph `StateGraph`: validation-gate short-circuit + `manager_review` human-in-the-loop node; agents unchanged. Sequential runner kept as reference (`workflows/pipeline.py`) |
| Develop APIs | `api/app.py` (FastAPI) + `api/schemas.py`; shared `workflows/service.py` (submit / get / pending / manager-decision / balances / history) |
| Develop monitoring dashboards | `frontend/dashboard.py` (Streamlit) — agent trace, coordination bus, memory, approval queue |
| Deploy to cloud infrastructure | `Dockerfile`, `docker-compose.yml`, `deploy/CLOUD.md` (Azure/AWS/GCP quick-starts) |
| Conduct performance testing & optimization | `perf/benchmark.py` + `tests/test_performance.py` (throughput / latency guardrail) |
| Human-in-the-loop manager approval | `AWAITING_MANAGER` pause + `service.apply_manager_decision` resume; retained in long-term memory |

Tests: `tests/test_graph.py`, `tests/test_service.py`, `tests/test_api.py`,
`tests/test_performance.py` — 55 tests passing overall.

**Scope decisions (flagged):** human-in-the-loop is a DB-backed pause/resume
(offline-first, replica-safe) rather than LangGraph's native `interrupt()`
+ checkpointer; cloud deployment ships as artifacts (no live target/account
available); the dashboard calls the shared service layer in-process while the
REST API exposes the identical operations for external integration. The
milestone doc folds Module 4 + Module 5 into "Milestone 4" — there is no
separate Milestone 5.

### Future / optional work (not required by any milestone doc)
- **RAG / vector store** — semantic policy recall behind `LongTermMemory` (M3
  scope decision deferred it).
- **Observability export** — per-run traces already on `state.logs`; a LangSmith
  exporter can attach behind the LangGraph runner.
- **Real connectors / delivery** — HTTP connectors and real email/Slack slot
  into the existing `Transport` / NotificationAgent seams.
- **Managed Postgres** — swap `database/db.py` for multi-replica cloud (schema
  already Postgres-shaped).
