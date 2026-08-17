"""Role-based web app (Milestone 4 / Module 5).

A Streamlit front-end for the AI coordination engine with **login and roles**,
so each audience sees only what it should:

* **Employees** log in, raise a leave request, and see just their own outcome,
  status and past requests — the multi-agent internals are hidden from them.
* **Managers** log in to a separate **approvals** screen scoped to their own
  team, with the AI's decision analysis to inform each approve/reject, plus a
  team view of balances and history.

Both roles talk to the same :mod:`workflows.service` layer the REST API uses,
so the UI and API stay in lockstep. Run it with:

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

st.set_page_config(
    page_title="Enterprise Leave Platform", page_icon="🤖", layout="wide"
)

# Ensure a database exists so the app is usable on first run.
if not settings.resolved_db_path().exists():
    from database.seed import seed

    seed()

APP_TITLE = "🤖 Enterprise Workflow Platform · Leave & Decision Automation"

_OUTCOME_STYLE = {
    "APPROVE": ("✅", "success"),
    "REJECT": ("❌", "error"),
    "ESCALATE": ("⏳", "warning"),
}


def _show_outcome(outcome: str, text: str) -> None:
    icon, kind = _OUTCOME_STYLE.get(outcome, ("ℹ️", "info"))
    getattr(st, kind)(f"{icon} {text}")


def _policy_rows() -> list[dict]:
    """The enforced policy rules, formatted for display."""
    return [
        {
            "Leave type": r["leave_type"].title(),
            "Days / year": r["max_days_per_year"],
            "Notice (working days)": r["min_notice_days"],
            "Docs required": "Yes" if r["requires_docs"] else "No",
            "Needs manager approval": "Yes" if r["manager_required"] else "No",
            "Notes": r.get("notes") or "",
        }
        for r in service.list_policies()
    ]


# ── Login gate ───────────────────────────────────────────────────────────────

def login_screen() -> None:
    st.title(APP_TITLE)
    st.caption("Sign in to continue")
    col, _ = st.columns([1, 1])
    with col:
        with st.form("login"):
            user_id = st.text_input("Employee ID", placeholder="e.g. E001 or M001")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", type="primary"):
                user = service.authenticate(user_id, password)
                if user:
                    st.session_state.user = user
                    # Persist the session in the URL so a browser refresh keeps
                    # the user signed in (Streamlit clears session_state on a
                    # full page reload). Demo-grade only — not a signed token.
                    st.query_params["uid"] = user["employee_id"]
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please check your Employee ID and password.")


def sidebar(user: dict) -> None:
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        badge = "🧑‍💼 Manager" if user["role"] == "manager" else "🙋 Employee"
        st.caption(f"{badge} · {user['employee_id']} · {user.get('department', '')}")
        if st.button("Sign out"):
            del st.session_state.user
            st.query_params.clear()
            st.rerun()


# ── Employee experience ──────────────────────────────────────────────────────

def employee_view(user: dict) -> None:
    me = user["employee_id"]
    st.title(APP_TITLE)
    st.subheader(f"Welcome, {user['name']} 👋")

    tab_new, tab_mine, tab_bal, tab_policy = st.tabs(
        ["📝 New request", "📋 My requests", "🗓️ My balances", "📖 Leave policy"]
    )

    with tab_new:
        with st.expander("📖 Leave policy — know the rules before you apply"):
            st.dataframe(_policy_rows(), use_container_width=True, hide_index=True)
        with st.form("submit_form"):
            c1, c2 = st.columns(2)
            leave_type = c1.selectbox("Leave type", ["casual", "sick", "earned"])
            reason = c2.text_input("Reason", "Family function")
            c3, c4 = st.columns(2)
            start = c3.date_input("Start date", date.today() + timedelta(days=21))
            end = c4.date_input("End date", date.today() + timedelta(days=23))
            submitted = st.form_submit_button("Submit request", type="primary")

        if submitted:
            with st.spinner("Processing your request…"):
                state = service.submit_leave_request(
                    me, leave_type, start.isoformat(), end.isoformat(), reason
                )
            decision = state.get("decision")
            outcome = decision["outcome"] if decision else None
            st.markdown(f"**Reference:** `{state['request']['request_id']}`")

            # Employee-facing outcome only — no agent internals.
            if outcome == "ESCALATE":
                _show_outcome(
                    "ESCALATE",
                    "Your request has been sent to your manager for approval. "
                    "You'll be notified once they decide.",
                )
            elif outcome:
                _show_outcome(
                    outcome,
                    f"Your {leave_type} leave was {outcome.lower()}d.",
                )
            st.markdown("**Message**")
            st.info(state.get("draft_response") or "(none)")

    with tab_mine:
        requests = service.list_employee_requests(me)
        if not requests:
            st.caption("You haven't raised any requests yet.")
        for r in requests:
            icon, _ = _OUTCOME_STYLE.get(r.get("latest_outcome"), ("•", "info"))
            with st.container(border=True):
                st.markdown(
                    f"{icon} **{r['leave_type'].title()}** · {r['start_date']} → "
                    f"{r['end_date']} · {r.get('days_requested', '?')} day(s)"
                )
                st.caption(
                    f"`{r['request_id']}` · status **{r['status']}**"
                    + (f" · outcome **{r['latest_outcome']}**" if r.get("latest_outcome") else "")
                )

    with tab_bal:
        try:
            st.dataframe(
                service.get_employee_balances(me),
                use_container_width=True, hide_index=True,
            )
        except ServiceError as exc:
            st.error(str(exc))

    with tab_policy:
        st.markdown("#### Company leave policy")
        st.caption("These are the exact rules the AI applies to your request.")
        st.dataframe(_policy_rows(), use_container_width=True, hide_index=True)
        st.markdown(
            "- Requests over your available **balance** are rejected.\n"
            "- Overlapping leave you already have is flagged.\n"
            "- **Earned** leave always needs your manager's approval."
        )


# ── Manager experience ───────────────────────────────────────────────────────

def manager_view(user: dict) -> None:
    me = user["employee_id"]
    st.title(APP_TITLE)
    st.subheader(f"Manager console · {user['name']}")

    tab_approvals, tab_team = st.tabs(["✅ Approvals", "👥 My team"])

    with tab_approvals:
        st.markdown("#### Requests awaiting your approval")
        pending = service.list_pending_approvals(manager_id=me)
        if not pending:
            st.success("Nothing awaiting your approval. 🎉")
        for req in pending:
            rid = req["request_id"]
            with st.container(border=True):
                st.markdown(
                    f"**{req.get('employee_name', req['employee_id'])}** requests "
                    f"**{req['leave_type']}** leave · {req['start_date']} → "
                    f"{req['end_date']} ({req.get('days_requested', '?')} day(s))"
                )
                if req.get("reason"):
                    st.caption(f"Reason: {req['reason']}")

                # AI decision analysis — the internal reasoning surfaces here, for
                # the manager (not the employee), to inform the human decision.
                detail = service.get_request(rid)
                decision = detail.get("decision")
                with st.expander("🔍 AI decision analysis"):
                    if decision:
                        st.write(
                            f"**Recommendation:** {decision['outcome']} "
                            f"(confidence {float(decision['confidence']):.0%})"
                        )
                        st.write(f"**Rationale:** {decision.get('rationale', '')}")
                        criteria = decision.get("criteria") or {}
                        if criteria:
                            st.dataframe(
                                [{"criterion": k, "result": v} for k, v in criteria.items()],
                                use_container_width=True, hide_index=True,
                            )
                    else:
                        st.caption("No recorded analysis.")

                note = st.text_input("Note to employee (optional)", key=f"note_{rid}")
                a, r = st.columns(2)
                if a.button("✅ Approve", key=f"ap_{rid}"):
                    service.apply_manager_decision(rid, True, me, note)
                    st.rerun()
                if r.button("❌ Reject", key=f"rj_{rid}"):
                    service.apply_manager_decision(rid, False, me, note)
                    st.rerun()

    with tab_team:
        reports = [e for e in service.list_employees() if e.get("manager_id") == me]
        if not reports:
            st.caption("No direct reports.")
            return
        ids = [e["employee_id"] for e in reports]
        labels = {e["employee_id"]: f"{e['employee_id']} · {e['name']}" for e in reports}
        who = st.selectbox("Team member", ids, format_func=lambda i: labels.get(i, i))
        try:
            st.markdown("**Leave balances**")
            st.dataframe(
                service.get_employee_balances(who),
                use_container_width=True, hide_index=True,
            )
        except ServiceError as exc:
            st.error(str(exc))
        st.markdown("**Interaction history** (long-term memory)")
        history = service.get_employee_history(who, limit=20)
        if history:
            st.dataframe(history, use_container_width=True, hide_index=True)
        else:
            st.caption("No prior interactions recorded.")


# ── Router ───────────────────────────────────────────────────────────────────

user = st.session_state.get("user")
if not user:
    # Restore a signed-in user from the URL after a browser refresh.
    uid = st.query_params.get("uid")
    if uid:
        user = service.get_user(uid)
        if user:
            st.session_state.user = user

if not user:
    login_screen()
else:
    sidebar(user)
    if user["role"] == "manager":
        manager_view(user)
    else:
        employee_view(user)
