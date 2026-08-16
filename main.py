"""CLI test harness for the AI Leave Approval System (Milestone 1).

Examples
--------
    python main.py --init-db                 # create + seed the database
    python main.py --list                    # list seeded employees
    python main.py --demo                     # run the 3 built-in scenarios
    python main.py --scenario approve         # run one built-in scenario
    python main.py --employee-id E001 --leave-type casual \
                   --start 2026-07-20 --end 2026-07-22 --reason "family trip"
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

from database.db import get_connection, list_employees
from database.seed import seed
from llm import get_llm
from schemas.state import LeaveRequest, LeaveState
from utils.config import settings
from workflows import run_leave_graph, run_leave_workflow

# Milestone 4 runs requests through the LangGraph orchestration graph by default;
# --sequential falls back to the equivalent Milestone 1/3 linear runner.
_USE_GRAPH = True


def _future(days_ahead: int, span: int = 2) -> tuple[str, str]:
    """A weekday-safe (start, end) a comfortable number of business days ahead.

    Dates are computed relative to *today* so the demo satisfies notice periods
    and never falls in the past — hardcoded dates would silently break the
    APPROVE path once the calendar moved past them.
    """
    def _weekday(d: date) -> date:
        while d.weekday() >= 5:
            d += timedelta(days=1)
        return d

    start = _weekday(date.today() + timedelta(days=days_ahead))
    end = _weekday(start + timedelta(days=span))
    return start.isoformat(), end.isoformat()


# Built-in scenarios that exercise each decision path against the seed data.
#   approve : E001 casual  — ample balance, enough notice        -> APPROVE
#   reject  : E002 earned  — only 1 day left, needs 3            -> REJECT (balance)
#   escalate: E003 earned  — ample balance, policy needs manager -> ESCALATE
SCENARIOS = {
    "approve": LeaveRequest("E001", "casual", *_future(21, 2), "Family function"),
    "reject": LeaveRequest("E002", "earned", *_future(21, 3), "Vacation"),
    "escalate": LeaveRequest("E003", "earned", *_future(25, 2), "Personal"),
}


def _ensure_db() -> None:
    if not settings.resolved_db_path().exists():
        seed()
        print(f"[setup] Seeded new database at {settings.resolved_db_path()}")


def _print_result(state: LeaveState) -> None:
    print("\n" + "=" * 68)
    d = state.decision
    if d:
        print(f"OUTCOME : {d.outcome}   (confidence {d.confidence:.2f})")
        print(f"REASON  : {d.rationale}")
        print(f"CRITERIA: {d.criteria_scores}")
    print(f"STATUS  : {state.status}")

    # Milestone 3: make coordination + memory visible so a collaborative run can
    # be validated from the CLI, not only from the debug logs.
    if state.history:
        print("-" * 68)
        print(f"MEMORY CONTEXT (recalled {len(state.history)} prior interaction(s)):")
        for h in state.history:
            print(
                f"  · {h['created_at']}  {h['leave_type']} "
                f"{h['start_date']}..{h['end_date']} -> {h['outcome']}"
            )
    if state.agent_messages:
        print("-" * 68)
        print(f"COORDINATION (inter-agent bus, {len(state.agent_messages)} message(s)):")
        for m in state.agent_messages:
            print(f"  [{m['role']}] {m['sender']} -> {m['to']} ({m['kind']}): {m['content']}")

    print("-" * 68)
    print("RESPONSE TO EMPLOYEE:")
    print(state.draft_response or "(none)")
    print("=" * 68 + "\n")


def _run(request: LeaveRequest) -> LeaveState:
    llm = get_llm()
    runner = run_leave_graph if _USE_GRAPH else run_leave_workflow
    orchestrator = "LangGraph graph" if _USE_GRAPH else "sequential runner"
    print(f"\n### Running workflow  (LLM: {llm.provider}/{llm.model}, orchestrator: {orchestrator})")
    state = runner(request, llm)
    _print_result(state)
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Leave Approval — CLI harness")
    parser.add_argument("--init-db", action="store_true", help="create + seed the database, then exit")
    parser.add_argument("--list", action="store_true", help="list seeded employees, then exit")
    parser.add_argument("--demo", action="store_true", help="run all built-in scenarios")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), help="run one built-in scenario")
    parser.add_argument("--employee-id")
    parser.add_argument("--leave-type", choices=["casual", "sick", "earned"])
    parser.add_argument("--start", help="start date YYYY-MM-DD")
    parser.add_argument("--end", help="end date YYYY-MM-DD")
    parser.add_argument("--reason", default="")
    parser.add_argument(
        "--sequential", action="store_true",
        help="use the Milestone 1/3 sequential runner instead of the LangGraph graph",
    )
    args = parser.parse_args()

    global _USE_GRAPH
    _USE_GRAPH = not args.sequential

    if args.init_db:
        seed()
        print(f"Seeded database at {settings.resolved_db_path()}")
        return

    _ensure_db()

    if args.list:
        conn = get_connection()
        try:
            for e in list_employees(conn):
                mgr = e["manager_id"] or "-"
                print(f"{e['employee_id']}  {e['name']:<16} {e['department']:<12} manager={mgr}")
        finally:
            conn.close()
        return

    if args.demo:
        for name in ("approve", "reject", "escalate"):
            print(f"\n########## SCENARIO: {name.upper()} ##########")
            _run(SCENARIOS[name])
        return

    if args.scenario:
        _run(SCENARIOS[args.scenario])
        return

    if args.employee_id and args.leave_type and args.start and args.end:
        _run(LeaveRequest(args.employee_id, args.leave_type, args.start, args.end, args.reason))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
