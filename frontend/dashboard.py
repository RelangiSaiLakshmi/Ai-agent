"""Monitoring dashboard (Milestone 4 / Module 5).

A Streamlit UI to operate and observe the AI coordination engine:

* **Submit** a leave request and watch the multi-agent orchestration run —
  the decision, the per-agent trace, the inter-agent coordination bus, and the
  long-term memory recalled for the employee.
* **Approvals** — the human-in-the-loop queue: escalated requests a manager can
  approve or reject, which resumes the workflow.
* **Employees** — balances and interaction history.

The dashboard talks to the same :mod:`workflows.service` layer the REST API
uses, so what you see here is exactly what an API client gets. Run it with:

    streamlit run frontend/dashboard.py
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

# `streamlit run frontend/dashboard.py` puts this file's folder on sys.path, not
# the project root, so make the project importable regardless of launch cwd.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from utils.config import settings
from workflows import service
from workflows.service import ServiceError

st.set_page_config(page_title="AI Coordination Engine", page_icon="🤖", layout="wide")

# Ensure a database exists so the dashboard is usable on first run.
if not settings.resolved_db_path().exists():
    from database.seed import seed

    seed()

_OUTCOME_STYLE = {
    "APPROVE": ("✅", "success"),
    "REJECT": ("❌", "error"),
    "ESCALATE": ("⏸️", "warning"),
}


def _employees():
    return service.list_employees()


def _show_outcome(outcome: str, text: str) -> None:
    icon, kind = _OUTCOME_STYLE.get(outcome, ("ℹ️", "info"))
    getattr(st, kind)(f"{icon} {text}")


st.title("🤖 AI Agent Coordination & Decision Engine")
st.caption("Multi-agent leave approval · orchestration · memory · human-in-the-loop")

tab_submit, tab_approvals, tab_employees = st.tabs(
    ["📝 Submit request", "🧑‍💼 Approvals queue", "👥 Employees"]
)

# ── Submit + observe ─────────────────────────────────────────────────────────
with tab_submit:
    employees = _employees()
    ids = [e["employee_id"] for e in employees]
    labels = {e["employee_id"]: f"{e['employee_id']} · {e['name']}" for e in employees}

    with st.form("submit_form"):
        c1, c2, c3 = st.columns(3)
        emp = c1.selectbox("Employee", ids, format_func=lambda i: labels.get(i, i))
        leave_type = c2.selectbox("Leave type", ["casual", "sick", "earned"])
        reason = c3.text_input("Reason", "Family function")
        c4, c5 = st.columns(2)
        start = c4.date_input("Start date", date.today() + timedelta(days=21))
        end = c5.date_input("End date", date.today() + timedelta(days=23))
        submitted = st.form_submit_button("Run workflow", type="primary")

    if submitted:
        with st.spinner("Coordinating agents…"):
            state = service.submit_leave_request(
                emp, leave_type, start.isoformat(), end.isoformat(), reason
            )
        decision = state.get("decision")
        st.subheader(f"Request `{state['request']['request_id']}` — status {state['status']}")
        if decision:
            _show_outcome(
                decision["outcome"],
                f"{decision['outcome']} (confidence {decision['confidence']:.0%}) — "
                f"{decision['rationale']}",
            )
        st.markdown("**Response to employee**")
        st.info(state.get("draft_response") or "(none)")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**🧩 Agent trace**")
            for log in state.get("logs", []):
                st.text(f"[{log['agent']}] {log['message']}")
        with col_b:
            st.markdown("**🔗 Coordination bus** (inter-agent messages)")
            for m in state.get("agent_messages", []):
                st.text(f"[{m['role']}] {m['sender']} → {m['to']} ({m['kind']}): {m['content']}")

        if state.get("history"):
            st.markdown("**🧠 Memory context** (recalled prior interactions)")
            st.dataframe(state["history"], use_container_width=True)

# ── Approvals queue (human-in-the-loop) ──────────────────────────────────────
with tab_approvals:
    st.subheader("Pending manager approvals")
    pending = service.list_pending_approvals()
    if not pending:
        st.success("No requests awaiting approval. 🎉")
    for req in pending:
        with st.container(border=True):
            st.markdown(
                f"**{req['request_id']}** · {req.get('employee_name', req['employee_id'])} · "
                f"{req['leave_type']} · {req['start_date']} → {req['end_date']} "
                f"({req.get('days_requested', '?')} day(s))"
            )
            note = st.text_input("Manager note", key=f"note_{req['request_id']}")
            mgr = req.get("manager_id") or "manager"
            a, r = st.columns(2)
            if a.button("✅ Approve", key=f"ap_{req['request_id']}"):
                service.apply_manager_decision(req["request_id"], True, mgr, note)
                st.rerun()
            if r.button("❌ Reject", key=f"rj_{req['request_id']}"):
                service.apply_manager_decision(req["request_id"], False, mgr, note)
                st.rerun()

# ── Employees ────────────────────────────────────────────────────────────────
with tab_employees:
    employees = _employees()
    ids = [e["employee_id"] for e in employees]
    labels = {e["employee_id"]: f"{e['employee_id']} · {e['name']}" for e in employees}
    who = st.selectbox("Employee", ids, format_func=lambda i: labels.get(i, i), key="emp_view")
    try:
        st.markdown("**Leave balances**")
        st.dataframe(service.get_employee_balances(who), use_container_width=True)
    except ServiceError as exc:
        st.error(str(exc))
    st.markdown("**Interaction history** (long-term memory)")
    history = service.get_employee_history(who, limit=20)
    if history:
        st.dataframe(history, use_container_width=True)
    else:
        st.caption("No prior interactions recorded.")
