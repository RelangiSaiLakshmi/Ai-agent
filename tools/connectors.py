"""Enterprise API connectors (Milestone 2).

A *connector* wraps one external system behind a small typed interface so
agents (and LangChain tools) never deal with transports directly. The default
transport here is a local JSON file standing in for the enterprise HR-calendar
service, which keeps demos and tests offline and deterministic; a real HTTP
transport can be swapped in without touching any agent or tool code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Sequence

from utils.config import PROJECT_ROOT

HOLIDAYS_PATH = PROJECT_ROOT / "data" / "holidays.json"

#: A transport returns the raw holiday records, e.g. from a file or an HTTP API.
Transport = Callable[[], Sequence[dict[str, Any]]]


def _file_transport(path: Path = HOLIDAYS_PATH) -> Sequence[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


@dataclass
class Holiday:
    date: str  # ISO date
    name: str


class HolidayCalendarConnector:
    """Connector to the company holiday calendar (external HR service).

    Offline by default (JSON-file transport). To integrate the real service,
    pass a transport that performs the HTTP call and returns the same
    ``[{"date": ..., "name": ...}, ...]`` records.
    """

    def __init__(self, transport: Transport = _file_transport) -> None:
        self._transport = transport

    def holidays_between(self, start_date: str, end_date: str) -> list[Holiday]:
        """Company holidays within [start_date, end_date], inclusive.

        Raises ValueError on malformed dates — callers (the tool-calling loop)
        surface that back to the model instead of crashing.
        """
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        found = []
        for rec in self._transport():
            d = date.fromisoformat(rec["date"])
            if start <= d <= end:
                found.append(Holiday(date=rec["date"], name=rec["name"]))
        return sorted(found, key=lambda h: h.date)


#: Default connector instance used by tools and agents.
holiday_calendar = HolidayCalendarConnector()


def get_company_holidays(start_date: str, end_date: str) -> list[dict[str, str]]:
    """Plain-function tool over the connector (LangChain-wrappable)."""
    return [
        {"date": h.date, "name": h.name}
        for h in holiday_calendar.holidays_between(start_date, end_date)
    ]
