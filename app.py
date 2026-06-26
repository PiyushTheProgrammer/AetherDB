# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime

# Import Swarm components
from mcp.server import db_instance
from mcp.telemetry_generator import TelemetryGenerator
from agents.sentry import SentryAgent
from agents.architect import ArchitectAgent
from agents.security_guard import SecurityGuardAgent

# Configure page settings
st.set_page_config(
    page_title="AetherDB Dashboard",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern glassmorphism/dark-theme aesthetics
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background-color: #0b0e14;
        font-family: 'Outfit', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
    }
    .main {
        background-color: #0b0e14;
        color: #c9d1d9;
    }
    
    /* Glassmorphic Metrics */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, #121824 0%, #0b0e14 100%);
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        border-color: #3b82f6;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #3b82f6;
        background: linear-gradient(90deg, #60a5fa, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    div[data-testid="stMetricLabel"] {
        font-family: 'Outfit', sans-serif;
        font-size: 0.9rem;
        font-weight: 500;
        color: #9ca3af;
    }
    
    /* Modern Premium Cards */
    .card {
        background: linear-gradient(135deg, #111827 0%, #0b0f19 100%);
        border: 1px solid #1f2937;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .card:hover {
        border-color: rgba(59, 130, 246, 0.3);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5), 0 0 15px rgba(59, 130, 246, 0.08);
        transform: translateY(-2px);
    }
    
    /* Badges */
    .badge-ok {
        background: rgba(16, 185, 129, 0.15) !important;
        color: #10b981 !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        display: inline-block;
    }
    .badge-slow {
        background: rgba(239, 68, 68, 0.15) !important;
        color: #ef4444 !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        display: inline-block;
    }
    .badge-alert {
        background: rgba(245, 158, 11, 0.15) !important;
        color: #f59e0b !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        display: inline-block;
    }
    
    /* Agent Headers */
    .agent-header {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        color: #f3f4f6;
        margin-bottom: 12px;
        border-bottom: 1px solid #1f2937;
        padding-bottom: 8px;
        letter-spacing: 0.03em;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Monospace Code font */
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
        background-color: #070a0f !important;
        border: 1px solid #1f2937 !important;
        color: #e5e7eb !important;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)


# Initialize Session State variables if not present
if "telemetry_history" not in st.session_state:
    st.session_state.telemetry_history = []
if "performance_metrics" not in st.session_state:
    # Seed with some initial history representing unoptimized state
    st.session_state.performance_metrics = {
        "timestamps": [time.time() - 300, time.time() - 240, time.time() - 180, time.time() - 120, time.time() - 60],
        "avg_latency": [480.2, 492.5, 475.1, 488.9, 482.3]
    }
if "pending_proposal" not in st.session_state:
    st.session_state.pending_proposal = None
if "streaming_active" not in st.session_state:
    st.session_state.streaming_active = False

# Initialize Swarm components (Cached in session)
if "swarm_sentry" not in st.session_state:
    st.session_state.swarm_sentry = SentryAgent(latency_threshold_ms=100.0)
if "swarm_architect" not in st.session_state:
    st.session_state.swarm_architect = ArchitectAgent()
if "swarm_security" not in st.session_state:
    st.session_state.swarm_security = SecurityGuardAgent()
if "telemetry_generator" not in st.session_state:
    st.session_state.telemetry_generator = TelemetryGenerator()

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6; font-family: \"Outfit\", sans-serif; font-weight: 700; margin-top: 0;'>AetherDB Swarm Control</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Live Stream Toggle
    st.markdown("### Telemetry Stream Control")
    if st.session_state.streaming_active:
        if st.button("⏸️ Pause Telemetry Stream", use_container_width=True):
            st.session_state.streaming_active = False
            st.rerun()
    else:
        if st.button("▶️ Start Telemetry Stream", type="primary", use_container_width=True):
            st.session_state.streaming_active = True
            st.rerun()
            
    st.markdown("---")
    
    # Active Indexes Registry View
    st.markdown("### Database Index Registry")
    indexes = db_instance.get_existing_indexes()
    if indexes:
        for idx in indexes:
            st.markdown(
                f"📎 **`{idx['name']}`**  \n"
                f"Table: `{idx['table']}` | Columns: `{', '.join(idx['columns'])}`"
            )
    else:
        st.info("No optimization indexes active.")
        
    st.markdown("---")
    
    # DB Engine Stats
    st.markdown("### Simulated Schema Sizes")
    for tbl_name, tbl_info in db_instance.tables.items():
        st.markdown(
            f"📊 **`{tbl_name}`**: {tbl_info['rows_count']:,} rows  \n"
            f"Columns: `{', '.join(tbl_info['columns'])}`"
        )

# ----------------- MAIN LAYOUT -----------------
col_logo, col_title = st.columns([1, 6], vertical_alignment="center")
with col_logo:
    st.image("logo.png", width=95)
with col_title:
    st.markdown(
        """
        <h1 style='color:#f0f6fc; font-family: "Outfit", sans-serif; font-size: 3rem; font-weight: 700; margin-top: 0; margin-bottom: 0; background: linear-gradient(90deg, #3b82f6, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            AetherDB
        </h1>
        <p style='color:#9ca3af; font-family: "Outfit", sans-serif; font-size: 1.25rem; font-weight: 400; margin-top: 5px; margin-bottom: 0;'>
            Autonomous Performance Tuning & Proactive Safety for Modern Datastores
        </p>
        """,
        unsafe_allow_html=True
    )

# Top Metrics Row
metrics_cols = st.columns(4)

total_queries = len(st.session_state.telemetry_history)
slow_queries = sum(1 for q in st.session_state.telemetry_history if q["status"] == "SLOW")
optimization_count = len(db_instance.executed_optimizations)

# Compute real-time average latency
if st.session_state.telemetry_history:
    recent_latencies = [q["execution_time_ms"] for q in st.session_state.telemetry_history[-50:]]
    current_avg_latency = sum(recent_latencies) / len(recent_latencies)
else:
    current_avg_latency = 480.0

with metrics_cols[0]:
    st.metric("Telemetry Scanned", f"{total_queries:,}")
with metrics_cols[1]:
    st.metric("Slow Queries Flagged", f"{slow_queries}")
with metrics_cols[2]:
    st.metric("Applied Indexes", f"{optimization_count}")
with metrics_cols[3]:
    st.metric("Recent Avg Latency", f"{current_avg_latency:.2f} ms")

# Main Split Panels: Left for Swarm & Actions, Right for Telemetry List
col_left, col_right = st.columns([7, 5])

# ----------------- LEFT PANEL: SWARM ALERT & HITL ACTIONS -----------------
with col_left:
    st.markdown("<h3 style='color:#58a6ff;'>Swarm Decision Hub</h3>", unsafe_allow_html=True)
    
    proposal = st.session_state.pending_proposal
    
    if proposal:
        st.markdown(
            f"<div class='card' style='border-color: #d29922;'>"
            f"<span class='badge-alert'>🚨 ACTIVE SWARM TASK: {proposal['query_id']}</span>"
            f"<h4 style='margin-top: 15px; color:#f0f6fc;'>Intercepted SQL Query:</h4>"
            f"<code>{proposal['original_query']}</code>"
            f"<p style='margin-top:10px; color:#da3633;'>Original Execution Latency: <b>{proposal['execution_time_ms']} ms</b></p>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Swarm Reasoning Tree
        st.markdown("#### Agent Reasoning Log")
        
        # 1. Sentry Agent
        st.markdown(
            f"<div class='card'>"
            f"<div class='agent-header'>🚨 SENTRY AGENT</div>"
            f"<p style='color:#8b949e;'>Log monitor detected database latency breach ({proposal['execution_time_ms']}ms > 100ms threshold). "
            f"Flagged query and dispatched to performance optimizer.</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # 2. Architect Agent
        st.markdown(
            f"<div class='card'>"
            f"<div class='agent-header'>📐 ARCHITECT AGENT</div>"
            f"<p><b>Bottleneck Detected:</b> {proposal['bottleneck']}</p>"
            f"<p><b>Proposed Indexing SQL:</b></p>"
            f"<code>{proposal['proposed_sql']}</code>"
            f"<p style='margin-top: 10px; color:#8b949e;'><b>Technical Reason:</b> {proposal['reasoning']}</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # 3. Security Guard Agent
        # Validate safety on-the-fly
        safety_report = st.session_state.swarm_security.validate_proposal(proposal)
        
        guard_status_color = "#58a6ff" if safety_report["approved"] else "#da3633"
        guard_status_text = "APPROVED ✅" if safety_report["approved"] else "REJECTED ❌"
        
        st.markdown(
            f"<div class='card' style='border-color: {guard_status_color};'>"
            f"<div class='agent-header'>🛡️ SECURITY GUARD AGENT</div>"
            f"<p><b>Safety Audit Status:</b> <span style='color:{guard_status_color}; font-weight:bold;'>{guard_status_text}</span></p>"
            f"<p><b>Security Report:</b> {safety_report['reason']}</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Human in the Loop Decisions
        if safety_report["approved"]:
            st.markdown("#### Human-in-the-Loop Action Authorization")
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ Approve & Deploy Index", type="primary", use_container_width=True):
                    # Execute the optimization index
                    result = db_instance.execute_ddl(proposal["proposed_sql"])
                    if result.get("success"):
                        st.success(result.get("message"))
                        st.session_state.pending_proposal = None
                        # Clear history of this query pattern to show immediate performance boost
                        st.toast("Swarm successfully executed index on database!")
                        time.sleep(1)
                    else:
                        st.error(result.get("error"))
                    st.rerun()
            with col_btn2:
                if st.button("❌ Reject Optimization", use_container_width=True):
                    st.session_state.pending_proposal = None
                    st.toast("Optimization proposal discarded.")
                    time.sleep(0.5)
                    st.rerun()
        else:
            st.markdown("#### Safety Clearance Rejected")
            st.error("The Security Guard Agent has blocked this recommendation. Optimization cannot be authorized.")
            if st.button("Discard Blocked Task", use_container_width=True):
                st.session_state.pending_proposal = None
                st.rerun()
    else:
        st.info("System healthy. No slow queries currently queued for swarm analysis.")
        
    # --- CHAOS ENGINEERING SANDBOX (Security Demonstration) ---
    st.markdown("---")
    st.markdown("<h3 style='color:#58a6ff;'>Chaos Engineering Sandbox</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;'>Simulate custom operations to test the Security Guard Agent's safety validation skill directly.</p>", unsafe_allow_html=True)
    
    sandbox_sql = st.text_area("Type SQL Optimization statement to evaluate:", value="CREATE INDEX CONCURRENTLY idx_users_email ON users (email);")
    
    if st.button("🔒 Run Security Guard Audit", use_container_width=True):
        mock_payload = {
            "query_id": "q_sandbox_test",
            "original_query": "SELECT * FROM users WHERE email = 'test@domain.com';",
            "proposed_sql": sandbox_sql,
            "execution_time_ms": 480.0,
            "bottleneck": "Manual sandbox injection testing.",
            "reasoning": "User initiated chaos validation test."
        }
        
        sandbox_report = st.session_state.swarm_security.validate_proposal(mock_payload)
        
        if sandbox_report["approved"]:
            st.success(f"🛡️ **Security Guard Approved!**  \n{sandbox_report['reason']}")
        else:
            st.error(f"🚨 **Security Guard Blocked!**  \n**Reason:** {sandbox_report['reason']}  \n**Violation:** {sandbox_report['violation_details']}")

# ----------------- RIGHT PANEL: REAL-TIME TELEMETRY STREAM -----------------
with col_right:
    st.markdown("<h3 style='color:#58a6ff;'>Telemetry Live Feed</h3>", unsafe_allow_html=True)
    
    # Telemetry Feed Display
    if st.session_state.telemetry_history:
        # Display last 8 queries in a clean log format
        for q in reversed(st.session_state.telemetry_history[-8:]):
            badge = "<span class='badge-slow'>SLOW</span>" if q["status"] == "SLOW" else "<span class='badge-ok'>OK</span>"
            st.markdown(
                f"<div style='border: 1px solid #21262d; border-radius: 6px; padding: 10px; margin-bottom: 8px; background-color: #0d1117;'>"
                f"<div style='display:flex; justify-content:space-between;'>"
                f"<span style='color:#8b949e; font-size:0.8rem;'>ID: {q['query_id']} | {datetime.fromtimestamp(q['timestamp']).strftime('%H:%M:%S')}</span>"
                f"{badge}"
                f"</div>"
                f"<div style='margin-top:5px; font-family: monospace; font-size:0.9rem; color:#f0f6fc; overflow-x:auto;'>{q['sql']}</div>"
                f"<div style='margin-top:5px; color:#58a6ff; font-size:0.8rem;'>Latency: {q['execution_time_ms']} ms</div>"
                f"</div>",
                unsafe_allow_html=True
            )
    else:
        st.info("Start the Telemetry Stream in the sidebar to begin receiving database query logs.")

# ----------------- DYNAMIC CHARTING & PERFORMANCE TRACKING -----------------
st.markdown("---")
st.markdown("<h3 style='color:#58a6ff;'>Performance Optimization Analysis</h3>", unsafe_allow_html=True)

if len(st.session_state.telemetry_history) > 5:
    # Prepare historical chart data
    df_history = pd.DataFrame(st.session_state.telemetry_history)
    df_history['Time'] = pd.to_datetime(df_history['timestamp'], unit='s')
    
    # Group into 10-query buckets to smooth average performance over time
    df_history['Group'] = df_history.index // 5
    df_grouped = df_history.groupby('Group').agg({
        'execution_time_ms': 'mean',
        'Time': 'first'
    }).reset_index()
    
    fig = px.line(
        df_grouped,
        x='Time',
        y='execution_time_ms',
        title="Average Database Latency Trend (ms)",
        labels={'execution_time_ms': 'Average Execution Latency (ms)'},
        template="plotly_dark"
    )
    fig.update_traces(line_color='#58a6ff', line_width=3)
    fig.update_layout(
        plot_bgcolor='#161b22',
        paper_bgcolor='#0d1117',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Additional query history needed to display performance analysis graphs.")

# ----------------- TELEMETRY STREAMING EXECUTION LOOP -----------------
if st.session_state.streaming_active:
    # Pull one telemetry log from the generator
    log_entry = next(st.session_state.telemetry_generator.generate_query_stream())
    
    # Record in history
    st.session_state.telemetry_history.append(log_entry)
    
    # Check with Sentry Agent
    sentry_alert = st.session_state.swarm_sentry.analyze_log_entry(log_entry)
    
    # If a slow query is intercepted, and we do not have an active proposal queued, trigger the swarm
    if sentry_alert and not st.session_state.pending_proposal:
        # Pass to Architect Agent
        proposal_payload = st.session_state.swarm_architect.analyze_slow_query(sentry_alert)
        # Store as pending in session
        st.session_state.pending_proposal = proposal_payload
        # Temporarily pause stream so user can inspect and act on proposal
        st.session_state.streaming_active = False
        st.toast("🚨 Slow query intercepted! Swarm optimization proposed.", icon="🚨")
        
    # Trigger Streamlit rerun to continue live streaming
    time.sleep(0.5)
    st.rerun()
