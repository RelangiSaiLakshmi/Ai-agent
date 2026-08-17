"""Lightweight agent-aware logging.

Each step is printed with an `[AgentName]` prefix so the multi-agent execution
trace is visible in the CLI (a key requirement for demos), and also appended to
the workflow state's `logs` list for later inspection / the dashboard.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from utils.config import settings

_LEVELS = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING}


def get_logger(name: str = "ai-agent") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(_LEVELS.get(settings.log_level.upper(), logging.INFO))
    return logger


class AgentLogger:
    """Emits a step to stdout and records it on the state's log list."""

    def __init__(self, name: str = "ai-agent") -> None:
        self._logger = get_logger(name)

    def step(self, state, agent: str, message: str) -> None:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        entry = {"ts": ts, "agent": agent, "message": message}
        if state is not None and hasattr(state, "logs"):
            state.logs.append(entry)
        self._logger.info(f"[{agent}] {message}")
