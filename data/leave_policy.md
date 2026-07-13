# Company Leave Policy (Sample)

This document is the human-readable policy. In Milestone 3 it will also be chunked
and embedded into a vector store so the Policy agent can retrieve passages (RAG).
For Milestone 1 the structured rules live in the `policy_rules` table.

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
