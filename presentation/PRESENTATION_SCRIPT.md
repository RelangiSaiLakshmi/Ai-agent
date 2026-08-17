# Presentation Script & Speaker Guide
### AI Agent Coordination & Decision Engine — Leave Approval System

**Deck:** `presentation/AI_Leave_Approval_Demo.pptx` (12 slides, 16:9)
**Target length:** 10–13 minutes + Q&A
**Delivery mode:** offline demo (MockLLM — no API key needed)

> The full speaker notes are also embedded in the `.pptx` itself (Notes pane
> under each slide). This document adds timing, transitions, a demo runbook,
> and a Q&A bank. Everything here is grounded in the actual code in this repo.

---

## 0. Before you present — 3-minute setup checklist

```bash
cd /home/bhlp0213/Desktop/AI/Ai-agent
source .venv/bin/activate          # or: python -m venv .venv && pip install -r requirements.txt
python main.py --init-db           # reset to clean, deterministic seed data
python main.py --list              # sanity-check the 6 employees appear
pytest tests/ -q                   # optional flex: "29 passed"
```

- **Re-run `--init-db` right before the demo.** Each run persists its request, so
  repeating the same dates would be detected as an overlap and escalate (by design).
- Have **two terminals** ready: one for the demo, one as backup.
- Font in the deck is Calibri (safe on Windows/Office). Present in 16:9.

---

## 1. Timing map (≈11 min core)

| Slide | Section | Time | Cumulative |
|---|---|---|---|
| 1 | Title | 0:40 | 0:40 |
| 2 | Problem & Solution | 1:00 | 1:40 |
| 3 | Objectives & Features | 0:45 | 2:25 |
| 4 | Architecture & Stack | 1:00 | 3:25 |
| 5 | The 7 Agents | 1:00 | 4:25 |
| 6 | Communication & Flow | 1:00 | 5:25 |
| 7 | Tool Integration & Reliability (M2) | 1:00 | 6:25 |
| 8 | Decision Engine | 0:50 | 7:15 |
| 9 | Database & Security | 0:50 | 8:05 |
| 10 | **Live Demo** | 2:00–3:00 | ~10:30 |
| 11 | Roadmap | 0:35 | ~11:05 |
| 12 | Conclusion & Q&A | 0:35 | ~11:40 |

**Running short?** Slides 3 and 9 are reference-dense — skim them. **Running long?**
Cut the demo narration detail and just run `--demo` once, then jump to the results.

---

## 2. Per-slide script

Each slide: **what's on screen**, the **spoken script**, and the **transition** into the
next slide. (The spoken script matches the notes embedded in the `.pptx`; use whichever
medium you prefer.)

### Slide 1 — Title
**On screen:** Project title, one-line pitch, "LangChain · 7 agents · tool-calling · offline".
**Say:** "Good [morning/afternoon]. This is the *AI Agent Coordination & Decision
Engine* — an intelligent Leave Approval System. In one sentence: it takes an employee's
leave request and, like a real HR team, checks the policy, balances, and eligibility, then
automatically **Approves, Rejects, or Escalates** it — and writes the reply. Three things
to remember: it's built on **LangChain**, uses **seven specialized agents**, and runs
**fully offline** for this demo."
**Transition:** "Let's start with the problem."

### Slide 2 — Problem & Solution
**On screen:** Pain points + "we need…" panel (top); the 7-agent pipeline (bottom).
**Say:** "Leave approval hides a lot of rules. Today it's manual, inconsistent,
error-prone — easy to miss a balance, notice period, or overlap — and opaque. The tempting
fix, one LLM prompt that 'just decides,' is a black box: it can hallucinate rules, can't be
audited, and shouldn't touch the HR database. So the real requirement — top right — is
decisions that are **automated AND auditable AND grounded AND safe**, all four. Our
solution, at the bottom: instead of one giant prompt, a team of **seven single-purpose
agents** on an assembly line, sharing one state object — producing Approve, Reject, or
Escalate, each with a confidence and a full `[agent]` trace."
**Transition:** "Here's what we built to deliver that."

### Slide 3 — Objectives & Features
**On screen:** Eight feature tiles.
**Say:** "These eight tiles are our objectives and how we deliver them. Seven collaborating
agents with a uniform contract. Native tool-calling — the data agents let the model choose
tools. An auditable Decision Engine. Then the trust group: grounded, never invented; safe
by construction with least privilege; an enterprise connector; graceful degradation on
failures; and offline-first, backed by 29 passing tests."
**Transition:** "Let's see the architecture that holds it together."

### Slide 4 — Architecture & Stack
**On screen:** Six layers + vertical shared-state rail + stack chips.
**Say:** "Six clean layers — interface, orchestration, agents, reasoning/LLM,
tools/connectors, data. The most important decision: **the LLM is boxed in the reasoning
layer and only reaches data through read-only tools** — it never touches the database
directly and never writes. Running vertically is the `LeaveState`, enriched at each step.
The stack, along the bottom: Python, LangChain today with LangGraph for M4, Claude or the
offline mock, SQLite, and pytest."
**Transition:** "Now the stars — the agents."
**Visual note:** Point at the LLM layer when you say 'boxed in.'

### Slide 5 — The 7 Agents
**On screen:** Seven cards, each with role + a "Why" line.
**Say:** "Each agent has one job and a reason to exist — the 'Why' line. Coordinator is the
front door — validate, stamp an ID, persist, plan. Policy fetches the real rules.
Employee-Data pulls the record, balance, and overlaps. **Analysis** turns facts into boolean
signals and decides *nothing* — that separation is what keeps it auditable. **Decision** is
the engine — one clean job, output the outcome. **Notification** is the *only* agent that
writes to the DB — least privilege in action. Responder writes the final message. All seven
share one contract: `run(state) → state`."
**Transition:** "So how do they actually talk to each other?"

### Slide 6 — Communication & Flow
**On screen:** Blackboard diagram (left) + numbered end-to-end run (right).
**Say:** "Two things at once. Left — the agents *don't* call each other; they read and write
one shared `LeaveState`. That's the **blackboard pattern**. The orchestrator sequences; the
state carries context. The payoff: loose coupling — add or reorder an agent freely — and
auditability, because the final state is a replayable record. Right — the same thing as a
full run: Coordinator → Policy → Employee-Data → Analysis → Decision → Notification →
Responder. And if any step marks the state `FAILED`, the pipeline halts immediately."
**Transition:** "Let me show the Milestone 2 upgrade that made the data agents intelligent."

### Slide 7 — Tool Integration & Reliability (M2)
**On screen:** 4-step tool-loop + loop-back arrow; three reliability columns.
**Say:** "Before, the data agent hard-coded its DB calls; now it hands the read tools to the
LLM and lets it choose. The loop: agent calls `run_with_tools`, the model emits tool calls,
we execute and record each, we feed the result — or an error — back, and repeat until it
answers in text, bounded to 8 iterations. Three columns keep it safe: **intelligent
selection** (the mock reproduces the same loop deterministically); **grounded + validated**
(state from recorded results, each checked against the request); and **fails safe** (tool
errors return `ERROR` to the model, unknown tools are rejected, skipped tools re-fetched
directly). Philosophy: the model is an optimizer, **not a single point of failure**."
**Transition:** "Now the piece evaluators focus on — the Decision Engine."

### Slide 8 — The Decision Engine
**On screen:** 5-rung rule ladder with outcomes + confidences.
**Say:** "Be explicit: the final decision is **not** made by the LLM — it's this rule ladder,
highest-precedence first. Insufficient balance or over-max → REJECT (0.9). Manager-required
policy → ESCALATE (0.9). Notice not met or overlap → ESCALATE (0.6, human discretion). All
pass → APPROVE (0.95). Every outcome also emits a per-criterion pass/fail map. Why rules,
not the LLM? Deterministic, testable, explainable. The roadmap moves weights to config and
lets the LLM help on *borderline* cases — on top of this base, never replacing it."
**Transition:** "Quick word on the data and security model, then the demo."

### Slide 9 — Database & Security
**On screen:** Five tables (left) + six security cards (right).
**Say:** "Left — five normalized tables. `employees` has a self-referencing `manager_id`, so
the org chart lives in the table — that's how we know who to escalate to. `decisions` is the
audit table: outcome, confidence, rationale, and `criteria_json`, so any verdict is fully
reconstructable. SQLite now, Postgres-shaped for later. Right — security, all from **least
privilege**: the model only sees *read* tools; the two DB writes are direct calls in trusted
agents, so even a hallucinating model can't write. The DB path is never in a schema. Plus
grounding, bounded execution, an auditable trail, and secrets in the environment only."
**Transition:** "Now — the live demo."

### Slide 10 — Live Demo  ⟵ **SWITCH TO TERMINAL HERE**
**On screen:** Three commands + three scenario cards.
**Say (then run):** "Three commands: `--init-db` to reset, `--list` to show employees,
`--demo` to run all three paths. **APPROVE** — E001, casual, 3 days → 0.95. **REJECT** —
E002, earned, 5 days, only 1 left → 0.90. **ESCALATE** — E003, earned, eligible but
manager-required → 0.90. Watch for `[employee_data] Model selected 3 tool call(s)` — that's
the LLM choosing tools live."
**→ Run the demo (see runbook §3), narrate the trace, then advance.**
**Transition:** "So where does this go next?"

### Slide 11 — Roadmap
**On screen:** Done bar + M3/M4/M5 rows.
**Say:** "Done: M1 and M2 — the platform. **M3**: RAG — embed the policy doc into ChromaDB so
Policy cites real passages, plus long-term memory. **M4**: a LangGraph graph with conditional
edges and a real human-in-the-loop manager approval, exposed over FastAPI — agents unchanged,
only the orchestrator. **M5**: a Streamlit dashboard to watch the trace live. And it's not
wishful — every dependency is already in `requirements.txt`, and the seams were built for
exactly these upgrades."
**Transition:** "Let me wrap up."

### Slide 12 — Conclusion & Q&A
**On screen:** Four takeaways + anticipated-topic chips.
**Say:** "Four takeaways: (1) a working multi-agent decision engine, end to end; (2)
intelligent but safe — the LLM reasons, but is boxed in; (3) auditable by design — a rule
ladder, per-criterion scores, a full trace; (4) built to grow. Milestones 1 and 2 complete,
runs offline, 29 tests passing. Thank you — I'd love your questions."

---

## 3. Live demo runbook (Slide 10)

**Terminal script — type these live:**

```bash
python main.py --init-db          # "Resetting to clean seed data."
python main.py --list             # "Six employees; note E001, E002, E003 and their managers."
python main.py --demo             # "Now all three outcomes back to back."
```

**What to point at as the trace scrolls (real output):**

```
[coordinator] Request REQ-…: E001 wants 3 day(s) of casual … Plan: policy -> … -> responder
[policy]      Policy for 'casual': max 12.0d/yr, notice 2d, docs=no, manager_required=no.
[employee_data] Model selected 3 tool call(s): ['get_employee','get_leave_balance','get_overlapping_requests'].   ← "This is the LLM picking tools."
[employee_data] Asha Rao: 9 casual day(s) available, requesting 3, 0 overlap(s).
[analysis]    Signals: balance_ok=True, notice_ok=True, no_overlap=True, within_max=True. Flags: none.
[decision]    APPROVE (confidence 0.95) — All eligibility criteria satisfied; auto-approved.
[notification] Decision persisted; status -> COMPLETED. (mock) notified asha@example.com.
[responder]   Final response generated.
```

- **APPROVE (E001):** healthy balance → `APPROVE 0.95`, status `COMPLETED`.
- **REJECT (E002):** only 1 earned day left, wants 5 → `balance_ok=False` →
  `REJECT 0.90`, status `COMPLETED`.
- **ESCALATE (E003):** eligible, but earned leave is `manager_required` →
  `ESCALATE 0.90`, status `AWAITING_MANAGER`, "(mock) escalation sent to manager M002."

**Optional single-scenario / custom run (if asked):**
```bash
python main.py --scenario escalate
python main.py --employee-id E004 --leave-type casual --start 2026-08-24 --end 2026-08-26 --reason "wedding"
```

**If the demo misbehaves:** re-run `python main.py --init-db` (fixes the self-overlap
case), or fall back to the trace above / a pre-recorded screen capture.

---

## 4. Q&A bank — likely questions & strong answers

**Q1. Why seven agents? Isn't that over-engineered for leave approval?**
Each agent has one responsibility, which makes the system testable, auditable, and
extensible. The real payoff is *separation*: Analysis produces facts, Decision makes the
call — so I can change the decision rules without touching data-gathering, and I can add
RAG to just the Policy agent without touching the rest. It also maps 1:1 onto LangGraph
nodes in M4. The uniform `run(state)` contract keeps the "many agents" cost near zero.

**Q2. Why doesn't the LLM make the final decision?**
Because the decision must be deterministic, testable, and explainable to an auditor or
employee. The rule ladder in `agents/decision.py` gives a precise, reproducible outcome
with a per-criterion pass/fail map. The LLM's strength is *selecting and calling tools*
and *phrasing the response* — it optimizes; the rules decide. The roadmap lets the LLM
weigh in on genuinely borderline cases, but always on top of the auditable base.

**Q3. How do you stop the model from hallucinating data or rules?**
Three layers. (1) **Grounding** — state is built from recorded `ToolCallRecord` results,
never from the model's prose. (2) **Validation** — each result is checked against the
request (e.g., the policy must be for the requested `leave_type`, the employee record
must match the `employee_id`). (3) **Fallback** — on any mismatch or skip, we re-fetch
with a direct tool call. See `agents/policy.py::_fetch_policy` and
`agents/employee_data.py`.

**Q4. What happens if a tool throws / the model calls a tool that doesn't exist / loops
forever?**
All handled in `BaseLLM.run_with_tools`. A raising tool is caught and returned as
`ERROR: …` so the model can recover; an unknown-tool call is rejected the same way and
never executed; and the loop is bounded by `max_iterations=8`, after which it returns
`exhausted=True`. The workflow never crashes. Covered by `tests/test_tool_exceptions.py`.

**Q5. Is the model allowed to write to the database?**
No — by construction. Only *read* tools are wrapped as `@tool` and exposed to the model
(`tools/langchain_tools.py`). The two writes — persisting the request and the decision —
are direct calls inside the Coordinator and Notification agents. The `db_path` parameter
is deliberately excluded from every tool schema, so the model can't even choose which DB
to read.

**Q6. Mock vs. real Claude — is the mock "cheating"?**
No. The mock is a real LangChain `Runnable` that runs the *same* chain machinery
(`prompt | model | parser`) and the *same* tool-loop shape as the real provider — it's
just deterministic and offline. Set `LLM_PROVIDER=anthropic` and add an API key and the
identical agent code runs against `claude-sonnet-4-6` with **zero** code changes. The
mock exists so demos and CI are reproducible and free.

**Q7. How does it scale / go to production?**
Three moves, all seam-based: (1) SQLite → Postgres (schema is already Postgres-shaped;
only the connection helper changes); (2) the sequential runner → a LangGraph graph
(M4) for conditional routing and human-in-the-loop; (3) the file-based holiday
`Transport` → an HTTP transport, and mock notifications → real email/Slack at the
`NotificationAgent` seam. None of these touch agent logic.

**Q8. How is a decision auditable end to end?**
Every step appends to `state.logs` with an `[agent]` prefix and a timestamp
(`utils/logging.py`), and the final `decisions` row stores the outcome, confidence,
rationale, and `criteria_json`. So for any request you can reconstruct both the *trace*
(what each agent saw and did) and the *verdict* (which criteria passed/failed).

**Q9. How do you handle overlapping / concurrent leave requests?**
`get_overlapping_requests` runs a date-range-intersection SQL query filtered by status,
excluding the current request's own ID (so a request never overlaps itself). An overlap
sets `no_overlap=False` and escalates for review rather than silently approving.

**Q10. What's actually tested? "29 tests" of what?**
Four suites: `test_foundation.py` (state, config, LLM factory), `test_agents.py` (each
agent's behavior), `test_pipeline.py` (end-to-end scenarios + DB-write-vs-decision
parity), `test_tool_calling.py` (intelligent selection, tool-path vs direct-path
parity), and `test_tool_exceptions.py` (tool errors, unknown tools, bounded loops,
model-skips-tools fallback). Run `pytest tests/ -v`.

**Q11. Why LangChain / LangGraph specifically?**
LangChain gives us provider-agnostic chat models, prompt templating, `@tool` schemas,
and native tool-calling out of the box — so swapping Claude in is one line. LangGraph
(M4) is the natural next step because our agents already share a state object and a
uniform contract, which is exactly a graph of stateful nodes with conditional edges.

**Q12. Where would RAG fit, and why isn't it here yet?**
In the Policy agent. Today it reads structured rules from `policy_rules`; in M3 it also
embeds `data/leave_policy.md` into ChromaDB and retrieves the passage behind each rule
so rationales can *cite* policy text. It's scoped to M3 to keep M1–M2 focused on a
correct, safe foundation first — ChromaDB is already in `requirements.txt`.

**Q13. What are the current limitations?** (be honest)
Notifications are mocked (logged, not sent); the manager-approval step is a status
(`AWAITING_MANAGER`), not yet an interactive resume; the connector transport is a local
JSON file; and the LLM doesn't yet influence borderline decisions. All are explicit,
seam-ready roadmap items (M3–M5), not architectural blockers.

---

## 5. One-liners to have ready

- **Elevator pitch:** "Seven specialized AI agents collaborate over a shared state to
  approve, reject, or escalate a leave request — grounded in real data, auditable, and
  safe, built on LangChain and runnable fully offline."
- **The safety soundbite:** "The model can *look and suggest*, but it can't *act* — only
  read tools are exposed; every write is behind trusted code."
- **The auditability soundbite:** "There's no black box at the decision point — a
  transparent rule ladder with a pass/fail score for every criterion."
- **The extensibility soundbite:** "Swapping the LLM never touches an agent; adding an
  agent never touches the tools."
