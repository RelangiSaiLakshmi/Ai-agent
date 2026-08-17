"""Create the schema and load a small, deterministic seed dataset.

Designed so the three decision paths are all demonstrable:
  * APPROVE   — E001 casual leave (ample balance, enough notice)
  * REJECT    — E002 earned leave (insufficient balance)
  * ESCALATE  — E003 earned leave (manager_required policy)

Run:  python -m database.seed        (or `python main.py --init-db`)
"""
from __future__ import annotations

from database.db import get_connection, init_schema

EMPLOYEES = [
    # Managers first so the manager_id foreign key resolves on insert.
    # id,    name,            email,                  dept,          manager_id, join_date
    ("M001", "Priya Menon",   "priya@example.com",    "Engineering", None,   "2019-04-01"),
    ("M002", "Sanjay Gupta",  "sanjay@example.com",   "Sales",       None,   "2018-08-05"),
    ("E001", "Asha Rao",      "asha@example.com",     "Engineering", "M001", "2023-01-15"),
    ("E002", "Ravi Kumar",    "ravi@example.com",     "Engineering", "M001", "2024-06-01"),
    ("E003", "Meera Nair",    "meera@example.com",    "Sales",       "M002", "2022-03-10"),
    ("E004", "John Fernandez","john@example.com",     "Support",     "M002", "2021-11-20"),
]

# (employee_id, leave_type, total_days, used_days)
BALANCES = [
    ("E001", "casual", 12, 3),
    ("E001", "sick",   10, 1),
    ("E001", "earned", 15, 5),
    ("E002", "casual", 12, 10),
    ("E002", "earned",  5, 4),    # only 1 day left -> REJECT for a multi-day request
    ("E003", "earned", 20, 2),
    ("E003", "casual", 12, 0),
    ("E004", "sick",   10, 0),
    ("E004", "casual", 12, 6),
]

# (leave_type, max_days_per_year, min_notice_days, requires_docs, manager_required, notes)
POLICY_RULES = [
    ("casual", 12, 2, 0, 0, "Casual leave needs 2 working days' notice."),
    ("sick",   10, 0, 1, 0, "Sick leave may be applied retroactively; medical proof for >2 days."),
    ("earned", 20, 5, 0, 1, "Earned leave needs 5 days' notice and manager approval."),
]


def seed(db_path: str | None = None) -> None:
    conn = get_connection(db_path)
    try:
        init_schema(conn)
        # Clear transactional tables so re-seeding gives a clean, deterministic
        # slate (reference tables below use INSERT OR REPLACE). interaction_memory
        # is long-term memory (M3) and must be reset too, or stale history from a
        # previous run leaks into a fresh demo and makes recall non-deterministic.
        conn.execute("DELETE FROM decisions")
        conn.execute("DELETE FROM leave_requests")
        conn.execute("DELETE FROM interaction_memory")
        conn.executemany(
            "INSERT OR REPLACE INTO employees "
            "(employee_id, name, email, department, manager_id, join_date) "
            "VALUES (?,?,?,?,?,?)",
            EMPLOYEES,
        )
        conn.executemany(
            "INSERT OR REPLACE INTO leave_balances "
            "(employee_id, leave_type, total_days, used_days) VALUES (?,?,?,?)",
            BALANCES,
        )
        conn.executemany(
            "INSERT OR REPLACE INTO policy_rules "
            "(leave_type, max_days_per_year, min_notice_days, requires_docs, "
            "manager_required, notes) VALUES (?,?,?,?,?,?)",
            POLICY_RULES,
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
    print("Seeded database.")
