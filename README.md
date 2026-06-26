# Autonomous SQL Optimization Swarm

An intelligent, self-healing database operations system designed for the **Agents for Business** track. The swarm intercepts slow database queries in real-time, analyzes their execution plans, designs safe optimization indexes, rigorously validates safety policies to prevent locking or destructive commands, and presents findings on an interactive dashboard featuring a human-in-the-loop (HITL) authorization console.

```
                  [Telemetry Stream]
                           │
                           ▼
                 ┌───────────────────┐
                 │   Sentry Agent    │ (Alerts on query latency > 100ms)
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │  Architect Agent  │ (Retrieves EXPLAIN plan & proposes index)
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │  Security Guard   │ (Checks constraints: DROP, DELETE, etc.)
                 └─────────┬─────────┘
                           │
                  [Clearance Approved]
                           │
                           ▼
                 ┌───────────────────┐
                 │ Streamlit App     │ ◄───► [Human-in-the-Loop Operator]
                 └─────────┬─────────┘
                           │
                      [Approved]
                           │
                           ▼
                 ┌───────────────────┐
                 │ Mock PostgreSQL DB│ (DDL applied; subsequent queries run fast!)
                 └───────────────────┘
```

---

## 🌟 Key Features

1. **Multi-Agent Swarm Logic**:
   - **Sentry Agent (`agents/sentry.py`)**: Continuously monitors incoming telemetry query logs and flags performance anomalies (queries exceeding 100ms).
   - **Architect Agent (`agents/architect.py`)**: Inspects query bottlenecks (e.g. `Seq Scan` on unindexed tables) by calling database optimizer tools and constructs precise index DDL fixes.
   - **Security Guard Agent (`agents/security_guard.py`)**: Runs safety checks based on strict security skill configurations to ensure zero destructive commands reach the database.

2. **Telemetry & MCP Tooling (`mcp/`)**:
   - Mock PostgreSQL server (`mcp/server.py`) tracking active database indexes, database sizes, and generating simulated PostgreSQL query plan JSON.
   - Live telemetry stream (`mcp/telemetry_generator.py`) mimicking real-world user queries that adapt performance dynamically once the swarm applies optimizations.

3. **Observability Frontend (`app.py`)**:
   - A Streamlit dashboard to monitor live query flows and latency charts.
   - A step-by-step reasoning inspector showing Sentry, Architect, and Security Guard logs.
   - An interactive Human-in-the-Loop decision pane to Approve or Reject optimizations.
   - A Chaos Engineering Sandbox to test custom SQL optimizations against the Security Guard.

4. **Safety Skill Integration (`skills/security_guard/SKILL.md`)**:
   - Explicit Antigravity Skill configuration regulating the Security Guard agent.
   - Zero tolerance for stacked queries, SQL injections, or destructive operations (`DROP`, `DELETE`, `TRUNCATE`, etc.).
   - Mandates high-concurrency best practices (forcing `CREATE INDEX CONCURRENTLY`).

---

## 📂 Project Structure

```
.
├── README.md                          # Main project guide
├── requirements.txt                   # Project dependencies (streamlit, pandas, plotly, pydantic)
├── app.py                             # Streamlit Observability Frontend
├── mcp/
│   ├── __init__.py
│   ├── server.py                     # Mock PostgreSQL Telemetry & Tool Server
│   └── telemetry_generator.py        # Simulated slow & fast query generator
├── agents/
│   ├── __init__.py
│   ├── sentry.py                     # Sentry Agent (monitoring & alerting)
│   ├── architect.py                  # Architect Agent (query explain & plan optimizer)
│   └── security_guard.py             # Security Guard Agent (rules & threat check)
├── skills/
│   └── security_guard/
│       └── SKILL.md                  # Antigravity Skill Definition (rules & safety instructions)
└── tests/
    └── test_swarm.py                 # Swarm pipeline & security guard unit tests
```

---

## 🚀 Getting Started

### 1. Installation

Ensure Python (3.9+) is installed. Clone/navigate to the workspace directory and install the python packages:

```bash
pip install -r requirements.txt
```

### 2. Running Unit Tests

Run the comprehensive unit test suite to verify the multi-agent orchestration and security gatekeeping logic:

```bash
python -m unittest tests/test_swarm.py
```

### 3. Launching the Observability Dashboard

Start the Streamlit dashboard:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` to view the live dashboard.

---

## 🛡️ Security Policy Demonstration (Chaos Sandbox)

The Security Guard Agent enforces strict safety invariants defined in the `skills/security_guard/SKILL.md` skill configuration. To observe the safety filter, navigate to the **Chaos Engineering Sandbox** in the Streamlit dashboard and try submitting the following inputs:

*   **Destructive SQL Injection**: 
    `CREATE INDEX CONCURRENTLY idx_users_email ON users (email); DROP TABLE transactions;`
    *Result*: 🚨 **Blocked** due to stacked queries and the blacklisted keyword `DROP`.

*   **Blocking Index Creation (Non-Concurrent)**:
    `CREATE INDEX idx_users_email ON users (email);`
    *Result*: 🚨 **Blocked** because it lacks the `CONCURRENTLY` keyword, which would lock the table for writes in production.

*   **Safe Index Proposal**:
    `CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders (user_id);`
    *Result*: ✅ **Approved** and cleared for human-in-the-loop authorization.
