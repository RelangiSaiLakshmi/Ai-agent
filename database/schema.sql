-- Leave Approval — relational schema (SQLite for dev, Postgres-compatible shapes).

CREATE TABLE IF NOT EXISTS employees (
    employee_id  TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    email        TEXT NOT NULL,
    department   TEXT,
    manager_id   TEXT REFERENCES employees(employee_id),
    join_date    DATE
);

CREATE TABLE IF NOT EXISTS leave_balances (
    employee_id  TEXT REFERENCES employees(employee_id),
    leave_type   TEXT,                 -- sick | casual | earned
    total_days   REAL,
    used_days    REAL,
    PRIMARY KEY (employee_id, leave_type)
);

CREATE TABLE IF NOT EXISTS leave_requests (
    request_id      TEXT PRIMARY KEY,
    employee_id     TEXT REFERENCES employees(employee_id),
    leave_type      TEXT,
    start_date      DATE,
    end_date        DATE,
    days_requested  REAL,
    reason          TEXT,
    status          TEXT,              -- RECEIVED | AWAITING_MANAGER | COMPLETED | FAILED
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id   TEXT PRIMARY KEY,
    request_id    TEXT REFERENCES leave_requests(request_id),
    outcome       TEXT,                -- APPROVE | REJECT | ESCALATE
    confidence    REAL,
    rationale     TEXT,
    criteria_json TEXT,
    decided_by    TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policy_rules (
    leave_type        TEXT PRIMARY KEY,
    max_days_per_year REAL,
    min_notice_days   INTEGER,
    requires_docs     INTEGER,         -- 0/1
    manager_required  INTEGER,         -- 0/1
    notes             TEXT
);

-- Long-term knowledge retention (Milestone 3): one row per completed
-- interaction, so agents can recall an employee's leave history across
-- requests for context-aware decisions. This is the persistent half of the
-- shared memory repository; short-term conversational memory lives on the
-- in-flight LeaveState.
CREATE TABLE IF NOT EXISTS interaction_memory (
    memory_id     TEXT PRIMARY KEY,
    employee_id   TEXT REFERENCES employees(employee_id),
    request_id    TEXT,
    leave_type    TEXT,
    start_date    DATE,
    end_date      DATE,
    days_requested REAL,
    outcome       TEXT,                -- APPROVE | REJECT | ESCALATE
    confidence    REAL,
    summary       TEXT,                -- human-readable recap of the interaction
    flags_json    TEXT,                -- eligibility flags captured at decision time
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_interaction_memory_employee
    ON interaction_memory (employee_id, created_at);
