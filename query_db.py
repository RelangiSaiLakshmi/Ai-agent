"""Tiny helper to inspect the SQLite database from the terminal.

Usage:
    python query_db.py                       # list all tables + row counts
    python query_db.py employees             # show all rows in a table
    python query_db.py "SELECT * FROM decisions WHERE outcome='APPROVE'"
"""
from __future__ import annotations

import sqlite3
import sys

DB_PATH = "data/app.db"


def _print_rows(rows: list[sqlite3.Row]) -> None:
    if not rows:
        print("(no rows)")
        return
    headers = rows[0].keys()
    widths = {h: max(len(h), *(len(str(r[h])) for r in rows)) for h in headers}
    line = " | ".join(h.ljust(widths[h]) for h in headers)
    print(line)
    print("-" * len(line))
    for r in rows:
        print(" | ".join(str(r[h]).ljust(widths[h]) for h in headers))
    print(f"\n{len(rows)} row(s)")


def main() -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    arg = " ".join(sys.argv[1:]).strip()

    if not arg:  # overview: every table + row count
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        for t in tables:
            n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"{t:22} {n} row(s)")
        return

    # a bare word is treated as a table name; anything else as raw SQL
    sql = arg if " " in arg else f"SELECT * FROM {arg}"
    _print_rows(con.execute(sql).fetchall())


if __name__ == "__main__":
    main()
