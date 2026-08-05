"""Memory subsystem (Milestone 3): Agent Coordination & Memory Systems.

Two kinds of memory, combined behind one shared repository:

* :class:`~memory.short_term.ShortTermMemory` — per-request conversational
  memory and the inter-agent message bus (working memory scoped to one request).
* :class:`~memory.long_term.LongTermMemory` — persistent per-employee
  interaction history in SQLite (knowledge that outlives a request).
* :class:`~memory.shared.SharedMemory` — the shared memory repository agents
  read/write; it binds short-term memory to the current request and exposes
  long-term context for context-aware decisions.

Design notes: memory is dependency-light and offline-first (SQLite + the
serialisable ``LeaveState``), matching the Milestone 1/2 architecture. A
vector-store-backed semantic recall can slot in behind ``LongTermMemory`` later
without changing agent code.
"""
from __future__ import annotations

from memory.long_term import LongTermMemory
from memory.shared import SharedMemory, default_memory
from memory.short_term import ShortTermMemory

__all__ = [
    "LongTermMemory",
    "ShortTermMemory",
    "SharedMemory",
    "default_memory",
]
