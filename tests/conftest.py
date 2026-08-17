"""Shared pytest fixtures.

Every test runs against a fresh, isolated SQLite database in a temp dir, so
tests never touch the developer's real `data/app.db`.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from database.seed import seed
from utils.config import settings


@pytest.fixture()
def seeded_db(tmp_path):
    db_file = tmp_path / "test.db"
    original = settings.db_path
    settings.db_path = str(db_file)
    seed(str(db_file))
    yield str(db_file)
    settings.db_path = original


def _next_weekday(d: date) -> date:
    while d.weekday() >= 5:
        d = date.fromordinal(d.toordinal() + 1)
    return d


@pytest.fixture()
def future_range():
    """Return (start, end) ISO strings a safe number of business days ahead,
    so notice-period checks pass regardless of when the test runs."""

    def _make(days_ahead: int = 21, span: int = 2) -> tuple[str, str]:
        start = _next_weekday(date.today() + timedelta(days=days_ahead))
        end = _next_weekday(start + timedelta(days=span))
        return start.isoformat(), end.isoformat()

    return _make
