# Company Leave Policy (Sample)

This document is the human-readable policy; the structured rules the agents
enforce live in the `policy_rules` table. (Chunking/embedding this text into a
vector store for RAG was considered for Milestone 3 but deferred — the M3 doc
scopes memory as conversational + long-term retention, not document RAG — so it
remains optional future work behind the `LongTermMemory` seam.)

## Leave Types

### Casual Leave
- Entitlement: 12 days per year.
- Notice: at least **2 working days** in advance.
- Documentation: none.
- Approval: auto-approved if balance and notice conditions are met.

### Sick Leave
- Entitlement: 10 days per year.
- Notice: may be applied for retroactively.
- Documentation: medical certificate required for absences longer than 2 days.
- Approval: auto-approved within entitlement.

### Earned Leave
- Entitlement: 20 days per year.
- Notice: at least **5 working days** in advance.
- Documentation: none.
- Approval: **requires manager approval** (always escalated).

## General Rules
- Requests exceeding the available balance are rejected.
- Overlapping approved/pending leave for the same employee is flagged.
- Blackout periods may restrict leave during critical business windows (future work).
