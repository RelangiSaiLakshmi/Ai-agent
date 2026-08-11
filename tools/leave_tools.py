"""Tool layer for the Leave Approval workflow.

Each function is a self-contained "tool" an agent can call: it opens a
connection, runs one operation, and returns plain dicts. In Milestone 2 these
become LangChain `@tool`-decorated callables with JSON schemas; the signatures
here are chosen so that wrapping is trivial.

Read tools back the Employee-Data / Policy agents.
Write tools back the Notification agent (least-privilege: only it writes).
"""
from __future__ import annotations

from typing import Any

from database import db


def get_employee(employee_id: str, db_path: str | None = None) -> dict[str, Any] | None:
    conn = db.get_connection(db_path)
    try:
        return db.fetch_employee(conn, employee_id)
    finally:
        conn.close()


def get_leave_balance(employee_id: str, leave_type: str, db_path: str | None = None) -> dict[str, Any] | None:
    conn = db.get_connection(db_path)
    try:
        return db.fetch_balance(conn, employee_id, leave_type)
    finally:
        conn.close()


def get_overlapping_requests(
    employee_id: str,
    start_date: str,
    end_date: str,
    exclude_request_id: str | None = None,
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    conn = db.get_connection(db_path)
    try:
        return db.fetch_overlaps(conn, employee_id, start_date, end_date, exclude_request_id)
    finally:
        conn.close()


def get_policy(leave_type: str, db_path: str | None = None) -> dict[str, Any] | None:
    conn = db.get_connection(db_path)
    try:
        return db.fetch_policy(conn, leave_type)
    finally:
        conn.close()


def get_request(request_id: str, db_path: str | None = None) -> dict[str, Any] | None:
    conn = db.get_connection(db_path)
    try:
        return db.fetch_request(conn, request_id)
    finally:
        conn.close()


def get_latest_decision(request_id: str, db_path: str | None = None) -> dict[str, Any] | None:
    conn = db.get_connection(db_path)
    try:
        return db.fetch_latest_decision(conn, request_id)
    finally:
        conn.close()


def get_all_balances(employee_id: str, db_path: str | None = None) -> list[dict[str, Any]]:
    conn = db.get_connection(db_path)
    try:
        return db.fetch_all_balances(conn, employee_id)
    finally:
        conn.close()


def list_requests_by_status(status: str, db_path: str | None = None) -> list[dict[str, Any]]:
    conn = db.get_connection(db_path)
    try:
        return db.list_requests_by_status(conn, status)
    finally:
        conn.close()


def record_request(req: dict[str, Any], db_path: str | None = None) -> None:
    conn = db.get_connection(db_path)
    try:
        db.save_request(conn, req)
    finally:
        conn.close()


def set_request_status(request_id: str, status: str, db_path: str | None = None) -> None:
    conn = db.get_connection(db_path)
    try:
        db.update_request_status(conn, request_id, status)
    finally:
        conn.close()


def record_decision(decision: dict[str, Any], db_path: str | None = None) -> None:
    conn = db.get_connection(db_path)
    try:
        db.save_decision(conn, decision)
    finally:
        conn.close()
