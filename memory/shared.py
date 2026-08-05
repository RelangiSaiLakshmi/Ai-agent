"""Shared memory repository (Milestone 3).

``SharedMemory`` is the single object agents use to read and write memory. It
composes the two halves the milestone doc calls for:

* **short-term** — per-request conversation + inter-agent bus
  (:class:`~memory.short_term.ShortTermMemory`), created fresh for each request;
* **long-term** — persistent per-employee history
  (:class:`~memory.long_term.LongTermMemory`), shared across all requests.

The long-term store is shareable (stateless, opens connections per op), so one
instance is threaded through every agent in a run. The short-term view is bound
to the current request's :class:`~schemas.state.LeaveState` via :meth:`bind`.
This is the "shared memory repository" that enables context-aware decisions.
"""
from __future__ import annotations

from typing import Any

from memory.long_term import LongTermMemory
from memory.short_term import ShortTermMemory
from schemas.state import LeaveState


class SharedMemory:
    def __init__(self, long_term: LongTermMemory | None = None) -> None:
        self.long_term = long_term or LongTermMemory()
        self._short_term: ShortTermMemory | None = None

    def bind(self, state: LeaveState) -> ShortTermMemory:
        """Attach short-term memory to the current request's state."""
        self._short_term = ShortTermMemory(state)
        return self._short_term

    @property
    def short_term(self) -> ShortTermMemory:
        if self._short_term is None:
            raise RuntimeError("SharedMemory.bind(state) must be called before use.")
        return self._short_term

    def context_for(self, employee_id: str, limit: int = 5) -> dict[str, Any]:
        """Aggregated long-term context for an employee, for decision support."""
        return {
            "history": self.long_term.history(employee_id, limit=limit),
            "stats": self.long_term.stats(employee_id),
        }


def default_memory() -> SharedMemory:
    """A SharedMemory backed by the configured database."""
    return SharedMemory(LongTermMemory())
