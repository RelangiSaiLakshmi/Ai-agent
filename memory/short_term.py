"""Short-term memory (Milestone 3).

Short-term memory is everything scoped to a *single* request: the conversational
turns and the inter-agent message bus. It is a thin, serialisable view over the
in-flight :class:`~schemas.state.LeaveState` (its ``messages`` and
``agent_messages`` lists), so nothing new needs to be persisted and the whole
working set still round-trips through ``LeaveState.to_dict()``.

Two channels live here:

* **Conversational memory** — ``messages`` — the human/assistant turns, e.g. the
  final response drafted for the employee.
* **Agent bus** — ``agent_messages`` — structured :class:`AgentMessage` records
  agents post to share findings explicitly ("information exchange" in the
  milestone doc), addressed to one agent or broadcast to ``all``.
"""
from __future__ import annotations

from schemas.state import AgentMessage, LeaveState


class ShortTermMemory:
    """Per-request working memory: conversation + inter-agent bus."""

    def __init__(self, state: LeaveState) -> None:
        self.state = state

    # ── conversational memory ────────────────────────────────────────────────

    def remember(self, role: str, content: str) -> None:
        """Append a conversational turn (e.g. role='assistant')."""
        self.state.messages.append({"role": role, "content": content})

    def conversation(self, limit: int | None = None) -> list[dict[str, str]]:
        msgs = self.state.messages
        return msgs[-limit:] if limit else list(msgs)

    # ── inter-agent bus ──────────────────────────────────────────────────────

    def post(
        self, sender: str, role: str, content: str, *, to: str = "all", kind: str = "update"
    ) -> None:
        """Post a message to the bus so other agents can read it."""
        msg = AgentMessage(sender=sender, role=role, content=content, to=to, kind=kind)
        self.state.agent_messages.append(msg.to_dict())

    def inbox(self, agent: str) -> list[dict[str, str]]:
        """Messages addressed to ``agent`` or broadcast to all (not self-sent)."""
        return [
            m
            for m in self.state.agent_messages
            if m.get("sender") != agent and m.get("to") in (agent, "all")
        ]

    def bus(self) -> list[dict[str, str]]:
        return list(self.state.agent_messages)
