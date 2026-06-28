# Autonomous SQL Optimization Swarm (AetherDB)

An intelligent, self-healing database operations system designed for autonomous performance tuning and proactive safety in modern datastores. The swarm intercepts slow database queries in real-time, analyzes their execution plans, designs safe optimization indexes, rigorously validates safety policies to prevent locking or destructive commands, and presents findings on an interactive dashboard featuring a human-in-the-loop (HITL) authorization console.

```
                        [Telemetry Stream]  or  [Manual Query Input]
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
                ┌─────────────────┴─────────────────┐
                ▼                                   ▼
      ┌───────────────────┐               ┌───────────────────┐
      │Mock PostgreSQL DB │               │Live PostgreSQL DB │
      │ (Simulated State) │               │ (psycopg2-binary) │
      └───────────────────┘               └───────────────────┘
```

---

## Key Features

### 1. Real-World Database Integration
- **Dynamic Database Connections**: Seamlessly switch between the simulated database and a live, real-world PostgreSQL database using a connection URI.
- **Active Schema Discovery**: Automatically queries the PostgreSQL system catalog (`information_schema.columns` and `pg_stat_user_tables`) to display active tables, column definitions, and live row counts.
- **Index Registry**: Queries the `pg_indexes` catalog table in real-time to keep track of all active indexes in the public schema.
- **Non-Blocking Index Execution**: Executes approved indexing DDL commands directly on the live database in autocommit mode, supporting concurrent, non-locking operations.

### 2. Query Interceptor & Execution Console
- Run any custom SQL statements on both simulated and connected live databases.
- Proactively intercepts every query before execution and routes it through a multi-agent safety and performance gatekeeper:
  - **Fast & Safe**: Runs automatically and displays structured results.
  - **Slow & Safe**: Architect designs a concurrent, non-locking index. The operator can apply the optimization or execute the query slow.
  - **Unsafe/Injection**: Blocks the query, showing the exact policy violation. Requires explicit Admin Bypass authorization to run.

### 3. Multi-Agent Swarm Logic
- **Sentry Agent (`agents/sentry.py`)**: Continuously monitors incoming telemetry query logs and flags performance anomalies (queries exceeding 100ms).
- **Architect Agent (`agents/architect.py`)**: Inspects query bottlenecks (e.g. sequential scans on unindexed tables) by calling database planner tools and constructs precise index DDL fixes.
- **Security Guard Agent (`agents/security_guard.py`)**: Proactively audits both console queries and proposed index DDLs against strict safety policy rules before execution.

### 4. Proactive Safety Gatekeeper
- **Unified Pre-execution Interception**: Checks query safety (stacked injections, blacklisted keywords) before the database adapter runs the query.
- **Safety Policy Enforcement**: Guided by strict safety rules, the Security Guard blocks destructive commands (`DROP`, `DELETE`, `TRUNCATE`, `ALTER TABLE`, etc.), stacked query injections, and non-concurrent index creations.
- **Autocommit Isolation**: Forces all live index DDLs to run concurrently (`CREATE INDEX CONCURRENTLY`), which prevents tables from being locked for writes in active environments.

### 5. Premium Observability Frontend (`app.py`)
- Clean, dark-mode and light-mode interfaces built with Streamlit.
- Features a step-by-step reasoning inspector showing Sentry, Architect, and Security Guard logs.
- Interactive Human-in-the-Loop decision pane to Approve or Reject optimizations.
- Query Interceptor Console to execute and analyze arbitrary queries on the fly.
- Chaos Engineering Sandbox to test custom index DDL statements against the Security Guard.


---

## Project Structure

```
.
├── README.md                          # Main project guide
├── requirements.txt                   # Project dependencies (streamlit, pandas, plotly, pydantic, psycopg2-binary)
├── app.py                             # Streamlit Observability Frontend
├── logo.png                           # AetherDB Logo
├── mcp/
│   ├── __init__.py
│   ├── server.py                     # Mock & Real PostgreSQL Operations Adapter
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

## Getting Started

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

## Security Policy Demonstration (Chaos Sandbox)

The Security Guard Agent enforces strict safety invariants defined in the `skills/security_guard/SKILL.md` skill configuration. To observe the safety filter, navigate to the **Chaos Engineering Sandbox** in the Streamlit dashboard and submit the following inputs:

*   **Destructive SQL Injection**: 
    `CREATE INDEX CONCURRENTLY idx_users_email ON users (email); DROP TABLE transactions;`
    *Result*: Blocked due to stacked queries and the blacklisted keyword `DROP`.

*   **Blocking Index Creation (Non-Concurrent)**:
    `CREATE INDEX idx_users_email ON users (email);`
    *Result*: Blocked because it lacks the `CONCURRENTLY` keyword, which would lock the table for writes in production.

*   **Safe Index Proposal**:
    `CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders (user_id);`
    *Result*: Approved and cleared for human-in-the-loop authorization.
