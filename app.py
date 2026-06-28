# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime

# Import Swarm components
from mcp.server import db_instance, RealPostgreSQLDatabase
from mcp.telemetry_generator import TelemetryGenerator
from agents.sentry import SentryAgent
from agents.architect import ArchitectAgent
from agents.security_guard import SecurityGuardAgent

# Initialize UI Theme setting
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

# Configure page settings
st.set_page_config(
    page_title="AetherDB Dashboard",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern glassmorphism/dark-theme aesthetics
if st.session_state.theme == "Dark":
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
        
        /* Sidebar styling override */
        section[data-testid="stSidebar"] {
            background-color: #0b0e14 !important;
            border-right: 1px solid #1f2937 !important;
        }
        section[data-testid="stSidebar"] *, 
        section[data-testid="stSidebar"] p, 
        section[data-testid="stSidebar"] span, 
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] li {
            color: #c9d1d9 !important;
        }
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] h5,
        section[data-testid="stSidebar"] h6 {
            color: #f0f6fc !important;
        }
        
        /* Top Header styling override */
        header[data-testid="stHeader"] {
            background-color: rgba(11, 14, 20, 0.6) !important;
            backdrop-filter: blur(10px) !important;
            border-bottom: 1px solid #1f2937 !important;
        }
        header[data-testid="stHeader"] * {
            color: #f0f6fc !important;
        }
        
        /* Premium custom scrollbars for dark mode */
        ::-webkit-scrollbar {
            width: 8px !important;
            height: 8px !important;
        }
        ::-webkit-scrollbar-track {
            background: #0b0e14 !important;
        }
        ::-webkit-scrollbar-thumb {
            background: #1f2937 !important;
            border-radius: 4px !important;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #374151 !important;
        }
        
        /* Style expanders inside the sidebar for dark mode */
        section[data-testid="stSidebar"] div[data-testid="stExpander"] {
            background-color: #111827 !important;
            border: 1px solid #1f2937 !important;
            border-radius: 10px !important;
        }
        
        /* Hide Streamlit input instructions (Press Enter to apply) to prevent overlapping text */
        div[data-testid="InputInstructions"] {
            display: none !important;
        }
        
        /* Premium Button Styling for Dark Mode */
        /* Secondary / standard buttons in both sidebar and main area */
        div.stButton > button, 
        section[data-testid="stSidebar"] button {
            background-color: #111827 !important;
            color: #c9d1d9 !important;
            border: 1px solid #1f2937 !important;
            border-radius: 8px !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 500 !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            padding: 6px 16px !important;
        }
        div.stButton > button:hover, 
        section[data-testid="stSidebar"] button:hover {
            border-color: #3b82f6 !important;
            color: #3b82f6 !important;
            background-color: #1f2937 !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1) !important;
            transform: translateY(-1px) !important;
        }
        div.stButton > button:active, 
        section[data-testid="stSidebar"] button:active {
            transform: translateY(0px) !important;
        }
        
        /* Primary buttons in both sidebar and main area (forcing pure high-contrast white text) */
        div.stButton > button[kind="primary"],
        section[data-testid="stSidebar"] button[kind="primary"],
        div.stButton > button[kind="primary"] *,
        section[data-testid="stSidebar"] button[kind="primary"] * {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
        }
        div.stButton > button[kind="primary"]:hover,
        section[data-testid="stSidebar"] button[kind="primary"]:hover,
        div.stButton > button[kind="primary"]:hover *,
        section[data-testid="stSidebar"] button[kind="primary"]:hover * {
            background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%) !important;
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4), 0 0 10px rgba(59, 130, 246, 0.2) !important;
            color: #ffffff !important;
            transform: translateY(-1px) !important;
        }
        
        /* Premium Input & Textarea Styling for Dark Mode */
        div[data-testid="stTextInput"] div[data-baseweb="input"],
        div[data-testid="stTextArea"] div[data-baseweb="textarea"],
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }
        
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            color: #ffffff !important;
            font-family: 'JetBrains Mono', monospace !important;
            background-color: transparent !important;
        }
        
        /* Force high-contrast bright white text and solid dark-gray background for sidebar text inputs */
        section[data-testid="stSidebar"] div[data-testid="stTextInput"] input,
        section[data-testid="stSidebar"] div[data-testid="stTextInput"] div[data-baseweb="input"] {
            color: #ffffff !important;
            background-color: #161b22 !important;
            border-color: #30363d !important;
        }
        
        /* Input focus state */
        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
        div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 1px #3b82f6, 0 0 10px rgba(59, 130, 246, 0.15) !important;
        }
        
        /* Premium Selectbox Styling for Dark Mode */
        div[data-baseweb="select"] > div,
        div[data-baseweb="select"] {
            background-color: #111827 !important;
            border: 1px solid #1f2937 !important;
            color: #f0f6fc !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }
        div[data-baseweb="select"] * {
            color: #f0f6fc !important;
        }
        div[data-baseweb="select"] > div:focus-within {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 1px #3b82f6, 0 0 10px rgba(59, 130, 246, 0.15) !important;
        }
        
        /* Selectbox dropdown menu */
        div[data-baseweb="popover"] ul {
            background-color: #111827 !important;
            border: 1px solid #1f2937 !important;
            border-radius: 8px !important;
            padding: 4px 0 !important;
        }
        div[data-baseweb="popover"] li {
            background-color: #111827 !important;
            color: #c9d1d9 !important;
            transition: all 0.15s ease !important;
        }
        div[data-baseweb="popover"] li:hover {
            background-color: #1f2937 !important;
            color: #3b82f6 !important;
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
        
        /* Bulletproof overrides to force dark theme widgets and high-contrast text */
        textarea, 
        div[data-baseweb="textarea"], 
        div[data-baseweb="textarea"] textarea,
        .stTextArea textarea {
            background-color: #161b22 !important;
            color: #ffffff !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }
        
        /* Subtitles and text legibility overrides in dark mode */
        div[data-testid="stWidgetLabel"] p,
        div[data-testid="stWidgetLabel"] label,
        label,
        span[data-testid="stWidgetLabel"],
        .stWidgetLabel {
            color: #f0f6fc !important; /* bright readable off-white for labels */
            font-weight: 500 !important;
            font-family: 'Outfit', sans-serif !important;
        }
        
        div[data-testid="stMarkdownContainer"] strong,
        div[data-testid="stMarkdownContainer"] b,
        strong,
        b {
            color: #f0f6fc !important; /* bright readable bold markdown text */
        }
        
        div[data-testid="stMarkdownContainer"] p,
        .stMarkdown p {
            color: #c9d1d9 !important; /* clear readable light gray for body text */
        }
        
        /* Clean secondary button styling */
        .stButton button,
        div.stButton > button {
            background-color: #161b22 !important;
            color: #c9d1d9 !important;
            border: 1px solid #30363d !important;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
        
        /* Global Styles */
        .stApp {
            background-color: #f8fafc;
            font-family: 'Outfit', sans-serif;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
            color: #0f172a !important;
        }
        .main {
            background-color: #f8fafc;
            color: #334155;
        }
        
        /* Sidebar styling override */
        section[data-testid="stSidebar"] {
            background-color: #f1f5f9 !important;
            border-right: 1px solid #e2e8f0 !important;
        }
        section[data-testid="stSidebar"] *, 
        section[data-testid="stSidebar"] p, 
        section[data-testid="stSidebar"] span, 
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] li {
            color: #334155 !important;
        }
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] h5,
        section[data-testid="stSidebar"] h6 {
            color: #0f172a !important;
        }
        
        /* Top Header styling override */
        header[data-testid="stHeader"] {
            background-color: rgba(248, 250, 252, 0.6) !important;
            backdrop-filter: blur(10px) !important;
            border-bottom: 1px solid #e2e8f0 !important;
        }
        header[data-testid="stHeader"] * {
            color: #0f172a !important;
        }
        
        /* Style selectboxes, expanders, and buttons inside the sidebar for light mode */
        section[data-testid="stSidebar"] div[data-baseweb="select"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] * {
            color: #334155 !important;
        }
        section[data-testid="stSidebar"] button {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            color: #334155 !important;
        }
        section[data-testid="stSidebar"] button:hover {
            border-color: #2563eb !important;
            color: #2563eb !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stExpander"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
        }
        
        /* Glassmorphic Metrics */
        div[data-testid="metric-container"] {
            background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 4px 15px rgba(148, 163, 184, 0.1);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
        div[data-testid="metric-container"]:hover {
            transform: translateY(-4px);
            border-color: #2563eb;
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.15);
        }
        div[data-testid="stMetricValue"] {
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 700;
            color: #2563eb;
            background: linear-gradient(90deg, #3b82f6, #2563eb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        div[data-testid="stMetricLabel"] {
            font-family: 'Outfit', sans-serif;
            font-size: 0.9rem;
            font-weight: 500;
            color: #64748b;
        }
        
        /* Modern Premium Cards */
        .card {
            background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 22px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(148, 163, 184, 0.1);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .card:hover {
            border-color: rgba(37, 99, 235, 0.3);
            box-shadow: 0 8px 30px rgba(148, 163, 184, 0.15), 0 0 15px rgba(37, 99, 235, 0.05);
            transform: translateY(-2px);
        }
        
        /* Badges */
        .badge-ok {
            background: rgba(16, 185, 129, 0.1) !important;
            color: #059669 !important;
            border: 1px solid rgba(16, 185, 129, 0.2) !important;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            display: inline-block;
        }
        .badge-slow {
            background: rgba(239, 68, 68, 0.1) !important;
            color: #dc2626 !important;
            border: 1px solid rgba(239, 68, 68, 0.2) !important;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            display: inline-block;
        }
        .badge-alert {
            background: rgba(245, 158, 11, 0.1) !important;
            color: #d97706 !important;
            border: 1px solid rgba(245, 158, 11, 0.2) !important;
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
            color: #1e293b;
            margin-bottom: 12px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 8px;
            letter-spacing: 0.03em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* Monospace Code font */
        code, pre {
            font-family: 'JetBrains Mono', monospace !important;
            background-color: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
            color: #0f172a !important;
            border-radius: 6px;
        }
        
        /* Text overrides for Light mode card contents */
        .card p, .card b, .card span {
            color: #334155 !important;
        }
        .card h4 {
            color: #0f172a !important;
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
if "db_instance" not in st.session_state:
    st.session_state.db_instance = db_instance
if "console_status" not in st.session_state:
    st.session_state.console_status = None
if "console_query" not in st.session_state:
    st.session_state.console_query = ""
if "console_error" not in st.session_state:
    st.session_state.console_error = ""
if "console_proposal" not in st.session_state:
    st.session_state.console_proposal = None
if "console_result" not in st.session_state:
    st.session_state.console_result = None


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
    
    # Onboarding Guide (Moved to sidebar, completely emoji-free)
    with st.sidebar.expander("Quick Start & Swarm Agent Guide", expanded=True if not st.session_state.telemetry_history else False):
        st.markdown(
            """
            ### Welcome to AetherDB
            AetherDB is a self-healing database operations system that automatically intercepts slow queries, designs safe performance indexes to speed them up, audits them for safety, and requests human approval before deployment.
            
            ### How to Run the Demo:
            1. Click **Start Telemetry Stream** below to begin generating database queries.
            2. Watch queries flow in the **Telemetry Live Feed** on the right.
            3. When a slow query (> 100ms) is intercepted, the stream will pause, and the **Swarm Decision Hub** will show the agents' logs.
            4. Review their reasoning and click **Approve & Deploy Index** to speed up the database.
            
            ### Autonomous Swarm Agents:
            * **Sentry Agent**: The watchdog. Constantly monitors query latency and flags performance anomalies.
            * **Architect Agent**: The optimizer. Analyzes bottlenecks and designs tailored speed indexes.
            * **Security Guard Agent**: The firewall. Audits index DDL commands to block harmful queries and locking operations.
            """
        )
    
    st.markdown("---")
    
    # Database Engine Connection (completely emoji-free, professional styling)
    st.markdown("### Database Engine Connection")
    db_type_options = ["Simulated Database (Mock)", "Real PostgreSQL Database"]
    current_db_type_idx = 0
    if isinstance(st.session_state.db_instance, RealPostgreSQLDatabase):
        current_db_type_idx = 1
        
    selected_db_type = st.selectbox(
        "Database Engine Type",
        db_type_options,
        index=current_db_type_idx,
        key="db_type_selector_key"
    )
    
    if selected_db_type == "Real PostgreSQL Database":
        if not isinstance(st.session_state.db_instance, RealPostgreSQLDatabase):
            connection_uri = st.text_input(
                "PostgreSQL Connection URI",
                value=st.session_state.get("db_uri_input", "postgresql://postgres:postgres@localhost:5432/postgres"),
                help="Format: postgresql://username:password@hostname:port/database"
            )
            st.session_state.db_uri_input = connection_uri
            
            if st.button("Connect to Database", type="primary", use_container_width=True):
                if not connection_uri.strip():
                    st.error("Connection URI cannot be empty.")
                else:
                    try:
                        with st.spinner("Connecting to PostgreSQL..."):
                            new_db = RealPostgreSQLDatabase(connection_uri)
                            # Verify connection by calling tables property
                            _ = new_db.tables
                            st.session_state.db_instance = new_db
                            st.toast("Successfully connected to database.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Connection failed: {str(e)}")
        else:
            st.success("Connected to Live Database")
            raw_uri = st.session_state.db_instance.connection_uri
            masked_uri = raw_uri
            import re
            match = re.match(r"(postgresql://.*?):(.*?)@(.*?)$", raw_uri)
            if match:
                masked_uri = f"{match.group(1)}:******@{match.group(3)}"
            st.text(f"URI: {masked_uri}")
            
            if st.button("Disconnect Database", use_container_width=True):
                st.session_state.db_instance.close()
                st.session_state.db_instance = db_instance
                st.toast("Disconnected. Reverted to simulated database.")
                st.rerun()
    else:
        if isinstance(st.session_state.db_instance, RealPostgreSQLDatabase):
            st.session_state.db_instance.close()
            st.session_state.db_instance = db_instance
            st.toast("Reverted to simulated database.")
            st.rerun()
        st.info("Using simulated in-memory database schema.")
        
    st.markdown("---")
    
    # Live Stream Toggle
    st.markdown("### Telemetry Stream Control")
    if st.session_state.streaming_active:
        if st.button("Pause Telemetry Stream", use_container_width=True):
            st.session_state.streaming_active = False
            st.rerun()
    else:
        if st.button("Start Telemetry Stream", type="primary", use_container_width=True):
            st.session_state.streaming_active = True
            st.rerun()
            
    # Live Traffic Simulator for Real Database Interception Demo
    if isinstance(st.session_state.db_instance, RealPostgreSQLDatabase):
        st.markdown("### Live Traffic Simulator")
        st.caption("Simulate active database queries to test query interception, termination, and safety auditing.")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("Trigger Slow Query", use_container_width=True, help="Executes SELECT pg_sleep(5); in the background."):
                import threading
                def run_slow():
                    try:
                        import psycopg2
                        conn = psycopg2.connect(st.session_state.db_instance.connection_uri)
                        cursor = conn.cursor()
                        cursor.execute("SELECT pg_sleep(5);")
                        cursor.close()
                        conn.close()
                    except:
                        pass
                threading.Thread(target=run_slow, daemon=True).start()
                st.toast("Background slow query triggered.")
        with col_t2:
            if st.button("Trigger Unsafe Query", use_container_width=True, help="Executes an active query containing unsafe keywords."):
                import threading
                def run_unsafe():
                    try:
                        import psycopg2
                        conn = psycopg2.connect(st.session_state.db_instance.connection_uri)
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM users WHERE email = 'drop table users';")
                        cursor.close()
                        conn.close()
                    except:
                        pass
                threading.Thread(target=run_unsafe, daemon=True).start()
                st.toast("Background unsafe query triggered.")
            
    st.markdown("---")
    
    # Interface Preferences
    st.markdown("### Interface Preferences")
    theme_mode = st.selectbox(
        "UI Theme",
        ["Dark Mode", "Light Mode"],
        index=0 if st.session_state.theme == "Dark" else 1,
        help="Switch between Light and Dark interface styles."
    )
    new_theme = "Dark" if "Dark" in theme_mode else "Light"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()
        
    st.markdown("---")
    
    # Active Indexes Registry View
    st.markdown("### Database Index Registry")
    indexes = st.session_state.db_instance.get_existing_indexes()
    if indexes:
        for idx in indexes:
            st.markdown(
                f"**`{idx['name']}`**  \n"
                f"Table: `{idx['table']}` | Columns: `{', '.join(idx['columns'])}`"
            )
    else:
        st.info("No active indexes found.")
        
    st.markdown("---")
    
    # DB Engine Stats
    schema_title = "Active Database Schema" if isinstance(st.session_state.db_instance, RealPostgreSQLDatabase) else "Simulated Schema Sizes"
    st.markdown(f"### {schema_title}")
    tables_info = st.session_state.db_instance.tables
    if tables_info:
        for tbl_name, tbl_info in tables_info.items():
            st.markdown(
                f"**`{tbl_name}`**: {tbl_info['rows_count']:,} rows  \n"
                f"Columns: `{', '.join(tbl_info['columns'])}`"
            )
    else:
        st.info("No tables found in public schema.")

# ----------------- MAIN LAYOUT -----------------
# Theme-based color variables for custom HTML elements
if st.session_state.theme == "Dark":
    text_primary = "#f0f6fc"
    text_secondary = "#8b949e"
    pipeline_bg = "#111827"
    pipeline_border = "#1f2937"
    step_connector_idle = "#1f2937"
    title_color = "#3b82f6"
else:
    text_primary = "#0f172a"
    text_secondary = "#64748b"
    pipeline_bg = "#ffffff"
    pipeline_border = "#e2e8f0"
    step_connector_idle = "#e2e8f0"
    title_color = "#2563eb"

col_logo, col_title = st.columns([1, 6], vertical_alignment="center")
with col_logo:
    st.image("logo.png", width=95)
with col_title:
    st.markdown(
        f"""
        <h1 style='color:{title_color}; font-family: "Outfit", sans-serif; font-size: 3.2rem; font-weight: 700; margin-top: 0; margin-bottom: 0;'>
            AetherDB
        </h1>
        <p style='color:{text_secondary}; font-family: "Outfit", sans-serif; font-size: 1.25rem; font-weight: 400; margin-top: 5px; margin-bottom: 0;'>
            Autonomous Performance Tuning & Proactive Safety for Modern Datastores
        </p>
        """,
        unsafe_allow_html=True
    )

# 1. Visual Pipeline Tracker
st.markdown(f"<h3 style='color:{title_color}; margin-top: 20px; font-family: \"Outfit\", sans-serif; font-weight: 600;'>Real-Time Agent Swarm Status</h3>", unsafe_allow_html=True)

proposal = st.session_state.pending_proposal

# Step configurations
step_color_1 = "#10b981"
status_text_1 = "Monitoring Latency"

if proposal:
    step_connector_1 = "#10b981"
    step_color_2 = "#10b981"
    status_text_2 = "Proposing Index"
    
    # Run safety validation
    safety_report = st.session_state.swarm_security.validate_proposal(proposal)
    step_connector_2 = "#10b981"
    if safety_report["approved"]:
        step_color_3 = "#10b981"
        status_text_3 = "Audit Passed"
        step_connector_3 = "#f59e0b"
        step_color_4 = "#f59e0b"
        status_text_4 = "Decision Pending"
    else:
        step_color_3 = "#ef4444"
        status_text_3 = "Blocked"
        step_connector_3 = step_connector_idle
        step_color_4 = "#64748b"
        status_text_4 = "Idle"
else:
    step_connector_1 = step_connector_idle
    step_color_2 = "#64748b"
    status_text_2 = "Idle"
    
    step_connector_2 = step_connector_idle
    step_color_3 = "#64748b"
    status_text_3 = "Idle"
    
    step_connector_3 = step_connector_idle
    step_color_4 = "#64748b"
    status_text_4 = "Idle"

# Render custom visual pipeline HTML
st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: center; background: {pipeline_bg}; border: 1px solid {pipeline_border}; border-radius: 12px; padding: 18px 25px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
        <!-- Step 1: Sentry -->
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="background: {step_color_1}; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">1</span>
            <div>
                <div style="font-weight: 600; font-size: 0.9rem; color: {text_primary};">Sentry Agent</div>
                <div style="font-size: 0.75rem; color: #10b981; font-weight: 500;">{status_text_1}</div>
            </div>
        </div>
        <div style="flex-grow: 1; height: 3px; background: {step_connector_1}; margin: 0 15px; border-radius: 2px;"></div>
        <!-- Step 2: Architect -->
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="background: {step_color_2}; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">2</span>
            <div>
                <div style="font-weight: 600; font-size: 0.9rem; color: {text_primary};">Architect Agent</div>
                <div style="font-size: 0.75rem; color: {text_secondary}; font-weight: 500;">{status_text_2}</div>
            </div>
        </div>
        <div style="flex-grow: 1; height: 3px; background: {step_connector_2}; margin: 0 15px; border-radius: 2px;"></div>
        <!-- Step 3: Security Guard -->
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="background: {step_color_3}; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">3</span>
            <div>
                <div style="font-weight: 600; font-size: 0.9rem; color: {text_primary};">Security Guard</div>
                <div style="font-size: 0.75rem; color: {text_secondary}; font-weight: 500;">{status_text_3}</div>
            </div>
        </div>
        <div style="flex-grow: 1; height: 3px; background: {step_connector_3}; margin: 0 15px; border-radius: 2px;"></div>
        <!-- Step 4: Operator -->
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="background: {step_color_4}; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">4</span>
            <div>
                <div style="font-weight: 600; font-size: 0.9rem; color: {text_primary};">Human Operator</div>
                <div style="font-size: 0.75rem; color: {text_secondary}; font-weight: 500;">{status_text_4}</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Top Metrics Row
metrics_cols = st.columns(4)

total_queries = len(st.session_state.telemetry_history)
slow_queries = sum(1 for q in st.session_state.telemetry_history if q["status"] == "SLOW")
optimization_count = len(st.session_state.db_instance.executed_optimizations)

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
    hub_title_color = "#3b82f6" if st.session_state.theme == "Dark" else "#2563eb"
    st.markdown(f"<h3 style='color:{hub_title_color};'>Swarm Decision Hub</h3>", unsafe_allow_html=True)
    
    # Render Override Results if available
    if "override_results" in st.session_state and st.session_state.override_results:
        res = st.session_state.override_results
        st.markdown("### ⚡ Admin Override Query Execution Results")
        st.info(f"Executed SQL: `{res['query']}`")
        
        db_res = res["result"]
        if db_res.get("success"):
            if db_res.get("is_select"):
                cols = db_res.get("columns", [])
                rows = db_res.get("rows", [])
                if rows:
                    import pandas as pd
                    df = pd.DataFrame(rows, columns=cols)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.success("Query returned 0 rows.")
            else:
                st.success(db_res.get("message", "Query executed successfully."))
        else:
            st.error(f"Execution failed: {db_res.get('error')}")
            
        if st.button("Clear Results"):
            st.session_state.override_results = None
            st.rerun()
            
    proposal = st.session_state.pending_proposal
    
    if proposal:
        was_cancelled = proposal.get("was_cancelled", False)
        status_badge = "ACTIVE SWARM TASK: " + proposal['query_id']
        if was_cancelled:
            status_badge += " (BLOCKED & CANCELLED ON SERVER)"
            
        st.markdown(
            f"<div class='card' style='border-color: #d29922;'>"
            f"<span class='badge-alert'>{status_badge}</span>"
            f"<h4 style='margin-top: 15px; color:{text_primary};'>Intercepted SQL Query:</h4>"
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
            f"<div class='agent-header'>SENTRY AGENT</div>"
            f"<p style='color:{text_secondary};'>Log monitor detected database latency breach ({proposal['execution_time_ms']}ms > 100ms threshold). "
            f"Flagged query and dispatched to performance optimizer.</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # 2. Architect Agent
        st.markdown(
            f"<div class='card'>"
            f"<div class='agent-header'>ARCHITECT AGENT</div>"
            f"<p><b>Bottleneck Detected:</b> {proposal['bottleneck']}</p>"
            f"<p><b>Proposed Indexing SQL:</b></p>"
            f"<code>{proposal['proposed_sql']}</code>"
            f"<p style='margin-top: 10px; color:{text_secondary};'><b>Technical Reason:</b> {proposal['reasoning']}</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # 3. Security Guard Agent
        # Validate safety on-the-fly
        safety_report = st.session_state.swarm_security.validate_proposal(proposal)
        
        if st.session_state.theme == "Dark":
            guard_status_color = "#58a6ff" if safety_report["approved"] else "#da3633"
        else:
            guard_status_color = "#2563eb" if safety_report["approved"] else "#dc2626"
            
        guard_status_text = "APPROVED" if safety_report["approved"] else "REJECTED"
        
        st.markdown(
            f"<div class='card' style='border-color: {guard_status_color};'>"
            f"<div class='agent-header'>SECURITY GUARD AGENT</div>"
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
                if st.button("Approve & Deploy Index", type="primary", use_container_width=True):
                    # Execute the optimization index
                    result = st.session_state.db_instance.execute_ddl(proposal["proposed_sql"])
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
                if st.button("Reject Optimization", use_container_width=True):
                    st.session_state.pending_proposal = None
                    st.toast("Optimization proposal discarded.")
                    time.sleep(0.5)
                    st.rerun()
            
            # Admin Bypass Override
            st.markdown("---")
            st.markdown("#### Admin Bypass Override")
            if was_cancelled:
                st.warning("This active query was terminated on the server to prevent database lag. You can force-execute it using the override button below.")
            if st.button("Admin Override: Force Execute Original Query", use_container_width=True):
                with st.spinner("Executing query on live database..."):
                    result = st.session_state.db_instance.execute_query(proposal["original_query"])
                    st.session_state.override_results = {
                        "query": proposal["original_query"],
                        "result": result
                    }
                    st.session_state.pending_proposal = None
                    st.rerun()
        else:
            st.markdown("#### Safety Clearance Rejected")
            st.error("The Security Guard Agent has blocked this recommendation. Optimization cannot be authorized.")
            
            st.markdown("#### Admin Bypass Override")
            st.warning("You can override the Security Guard block and force-run this query on the database using the Admin Bypass.")
            if st.button("Admin Override: Force Execute Original Query", type="primary", use_container_width=True):
                with st.spinner("Executing query on live database..."):
                    result = st.session_state.db_instance.execute_query(proposal["original_query"])
                    st.session_state.override_results = {
                        "query": proposal["original_query"],
                        "result": result
                    }
                    st.session_state.pending_proposal = None
                    st.rerun()
            
            if st.button("Discard Blocked Task", use_container_width=True):
                st.session_state.pending_proposal = None
                st.rerun()
    else:
        st.info("System healthy. No slow queries currently queued for swarm analysis.")
        
        # ----------------- QUERY INTERCEPTOR & EXECUTION CONSOLE -----------------
        st.markdown("---")
        st.markdown(f"<h3 style='color:{title_color};'>Query Interceptor & Execution Console</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{text_secondary};'>Proactively intercept, monitor, optimize, and safely execute SQL queries on the active database.</p>", unsafe_allow_html=True)
        
        console_query = st.text_area(
            "Enter SQL Query to Execute",
            placeholder="SELECT * FROM users WHERE email = 'user_123@gmail.com';",
            height=120,
            key="console_query_input"
        )
        
        col_run1, col_run2 = st.columns([3, 1])
        with col_run1:
            run_clicked = st.button("Intercept & Run Query", type="primary", use_container_width=True)
        with col_run2:
            clear_clicked = st.button("Reset Console", use_container_width=True)
            
        if clear_clicked:
            st.session_state.console_status = None
            st.session_state.console_query = ""
            st.session_state.console_error = ""
            st.session_state.console_proposal = None
            st.session_state.console_result = None
            st.rerun()

        if run_clicked:
            if not console_query.strip():
                st.warning("Please enter a SQL query to execute.")
            else:
                # 1. Proactive Safety Audit
                is_safe, safety_err = st.session_state.swarm_security.check_query_safety(console_query)
                if not is_safe:
                    st.session_state.console_status = "BLOCKED"
                    st.session_state.console_query = console_query
                    st.session_state.console_error = safety_err
                    st.session_state.console_proposal = None
                    st.session_state.console_result = None
                    st.rerun()
                else:
                    # 2. Performance audit (EXPLAIN plan)
                    with st.spinner("Sentry and Architect agents analyzing query performance..."):
                        explain_res = st.session_state.db_instance.explain_query(console_query)
                        execution_time = explain_res.get("execution_time_ms", 0.0)
                        
                        if execution_time > 100.0:
                            # Propose optimization
                            alert_payload = {
                                "alert_id": "alert_console",
                                "query_id": f"q_console_{int(time.time())}",
                                "sql": console_query,
                                "execution_time_ms": execution_time,
                                "timestamp": time.time(),
                                "severity": "WARNING",
                                "status": "Awaiting Swarm Analysis"
                            }
                            proposal_payload = st.session_state.swarm_architect.analyze_slow_query(
                                alert_payload,
                                db_instance_override=st.session_state.db_instance
                            )
                            st.session_state.console_status = "SLOW"
                            st.session_state.console_query = console_query
                            st.session_state.console_proposal = proposal_payload
                            st.session_state.console_error = ""
                            st.session_state.console_result = None
                            st.rerun()
                        else:
                            # Execute immediately
                            with st.spinner("Executing query..."):
                                result = st.session_state.db_instance.execute_query(console_query)
                                st.session_state.console_status = "EXECUTED"
                                st.session_state.console_query = console_query
                                st.session_state.console_result = result
                                st.session_state.console_proposal = None
                                st.session_state.console_error = ""
                                st.rerun()

        # Display Console State/Results
        if st.session_state.console_status == "BLOCKED":
            st.markdown(
                f"<div class='card' style='border-color: #ef4444;'>"
                f"<span class='badge-slow'>PROACTIVELY BLOCKED BY SECURITY GUARD</span>"
                f"<h4 style='margin-top: 15px; color:{text_primary};'>SQL Threat Intercepted:</h4>"
                f"<code>{st.session_state.console_query}</code>"
                f"<p style='margin-top: 10px; color:#ef4444;'><b>Security Policy Violation:</b> {st.session_state.console_error}</p>"
                f"</div>",
                unsafe_allow_html=True
            )
            
            st.markdown("#### System Admin Options")
            st.warning("This query has been blocked to prevent destructive behavior. Do you want to authorize and execute it anyway?")
            col_ad1, col_ad2 = st.columns(2)
            with col_ad1:
                if st.button("Admin Bypass: Force Execute Query", type="primary", use_container_width=True):
                    with st.spinner("Admin bypassing guard. Executing query..."):
                        result = st.session_state.db_instance.execute_query(st.session_state.console_query)
                        st.session_state.console_status = "EXECUTED"
                        st.session_state.console_result = result
                        st.rerun()
            with col_ad2:
                if st.button("Discard Unsafe Request", use_container_width=True):
                    st.session_state.console_status = None
                    st.session_state.console_query = ""
                    st.session_state.console_error = ""
                    st.rerun()
                    
        elif st.session_state.console_status == "SLOW":
            prop = st.session_state.console_proposal
            st.markdown(
                f"<div class='card' style='border-color: #f59e0b;'>"
                f"<span class='badge-alert'>PERFORMANCE BREACH INTERCEPTED</span>"
                f"<h4 style='margin-top: 15px; color:{text_primary};'>Proposed Index Optimization:</h4>"
                f"<code>{prop['proposed_sql']}</code>"
                f"<p style='margin-top: 10px;'><b>Bottleneck:</b> {prop['bottleneck']}</p>"
                f"<p style='color:{text_secondary};'><b>Reasoning:</b> {prop['reasoning']}</p>"
                f"</div>",
                unsafe_allow_html=True
            )
            
            st.markdown("#### Execution Choices")
            col_ch1, col_ch2, col_ch3 = st.columns(3)
            with col_ch1:
                if st.button("Apply Optimization & Execute", type="primary", use_container_width=True):
                    with st.spinner("Applying index..."):
                        idx_res = st.session_state.db_instance.execute_ddl(prop["proposed_sql"])
                        if idx_res.get("success"):
                            st.success(idx_res.get("message"))
                            with st.spinner("Executing original query (now optimized!)..."):
                                result = st.session_state.db_instance.execute_query(st.session_state.console_query)
                                st.session_state.console_status = "EXECUTED"
                                st.session_state.console_result = result
                                st.rerun()
                        else:
                            st.error(idx_res.get("error"))
            with col_ch2:
                if st.button("Execute Anyway (Slow)", use_container_width=True):
                    with st.spinner("Executing slow query..."):
                        result = st.session_state.db_instance.execute_query(st.session_state.console_query)
                        st.session_state.console_status = "EXECUTED"
                        st.session_state.console_result = result
                        st.rerun()
            with col_ch3:
                if st.button("Cancel & Discard", use_container_width=True):
                    st.session_state.console_status = None
                    st.session_state.console_query = ""
                    st.session_state.console_proposal = None
                    st.rerun()
                    
        elif st.session_state.console_status == "EXECUTED":
            res = st.session_state.console_result
            st.markdown(f"#### ⚡ Query Execution Results")
            st.info(f"Query: `{st.session_state.console_query}`")
            
            if res.get("success"):
                if res.get("is_select"):
                    cols = res.get("columns", [])
                    rows = res.get("rows", [])
                    if rows:
                        df = pd.DataFrame(rows, columns=cols)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.success("Query completed successfully, returned 0 rows.")
                else:
                    st.success(res.get("message", "Query completed successfully."))
            else:
                st.error(f"Execution Error: {res.get('error')}")

        
    # --- CHAOS ENGINEERING SANDBOX (Security Demonstration) ---
    st.markdown("---")
    st.markdown(f"<h3 style='color:{title_color};'>Chaos Engineering Sandbox</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{text_secondary};'>Simulate custom operations to test the Security Guard Agent's safety validation skill directly.</p>", unsafe_allow_html=True)
    
    # Initialize sandbox preset value in session state if not present
    if "sandbox_sql_val" not in st.session_state:
        st.session_state.sandbox_sql_val = "CREATE INDEX CONCURRENTLY idx_users_email ON users (email);"
        
    st.markdown("**1-Click Test Presets (Dumb User Friendly):**")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        if st.button("Test Safe Index", help="Propose a safe, concurrent index creation", use_container_width=True):
            st.session_state.sandbox_sql_val = "CREATE INDEX CONCURRENTLY idx_users_email ON users (email);"
            st.rerun()
    with col_p2:
        if st.button("Test SQL Injection", help="Attempt to inject a destructive DROP TABLE command", use_container_width=True):
            st.session_state.sandbox_sql_val = "CREATE INDEX CONCURRENTLY idx_users_email ON users (email); DROP TABLE transactions;"
            st.rerun()
    with col_p3:
        if st.button("Test Table Lock", help="Attempt to create an index without the CONCURRENTLY keyword, which locks the database for writes", use_container_width=True):
            st.session_state.sandbox_sql_val = "CREATE INDEX idx_users_email ON users (email);"
            st.rerun()
            
    sandbox_sql = st.text_area("Type or edit SQL statement to evaluate:", value=st.session_state.sandbox_sql_val)
    
    if st.button("Run Security Guard Audit", use_container_width=True):
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
            st.success(f"**Security Guard Approved**  \n{sandbox_report['reason']}")
        else:
            st.error(f"**Security Guard Blocked**  \n**Reason:** {sandbox_report['reason']}  \n**Violation:** {sandbox_report['violation_details']}")
 
# ----------------- RIGHT PANEL: REAL-TIME TELEMETRY STREAM -----------------
with col_right:
    st.markdown(f"<h3 style='color:{title_color};'>Telemetry Live Feed</h3>", unsafe_allow_html=True)
    
    # Telemetry Feed Display
    if st.session_state.telemetry_history:
        # Display last 8 queries in a clean log format
        for q in reversed(st.session_state.telemetry_history[-8:]):
            badge = "<span class='badge-slow'>SLOW</span>" if q["status"] == "SLOW" else "<span class='badge-ok'>OK</span>"
            st.markdown(
                f"<div style='border: 1px solid {pipeline_border}; border-radius: 6px; padding: 10px; margin-bottom: 8px; background-color: {pipeline_bg};'>"
                f"<div style='display:flex; justify-content:space-between;'>"
                f"<span style='color:{text_secondary}; font-size:0.8rem;'>ID: {q['query_id']} | {datetime.fromtimestamp(q['timestamp']).strftime('%H:%M:%S')}</span>"
                f"{badge}"
                f"</div>"
                f"<div style='margin-top:5px; font-family: monospace; font-size:0.9rem; color:{text_primary}; overflow-x:auto;'>{q['sql']}</div>"
                f"<div style='margin-top:5px; color:#3b82f6; font-size:0.8rem;'>Latency: {q['execution_time_ms']} ms</div>"
                f"</div>",
                unsafe_allow_html=True
            )
    else:
        st.info("Start the Telemetry Stream in the sidebar to begin receiving database query logs.")
 
# ----------------- DYNAMIC CHARTING & PERFORMANCE TRACKING -----------------
st.markdown("---")
st.markdown(f"<h3 style='color:{title_color};'>Performance Optimization Analysis</h3>", unsafe_allow_html=True)
 
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
    
    chart_template = "plotly_dark" if st.session_state.theme == "Dark" else "plotly_white"
    chart_bg = "#161b22" if st.session_state.theme == "Dark" else "#ffffff"
    paper_bg = "#0b0e14" if st.session_state.theme == "Dark" else "#f8fafc"
    line_color = "#3b82f6" if st.session_state.theme == "Dark" else "#2563eb"
    
    fig = px.line(
        df_grouped,
        x='Time',
        y='execution_time_ms',
        title="Average Database Latency Trend (ms)",
        labels={'execution_time_ms': 'Average Execution Latency (ms)'},
        template=chart_template
    )
    fig.update_traces(line_color=line_color, line_width=3)
    fig.update_layout(
        plot_bgcolor=chart_bg,
        paper_bgcolor=paper_bg,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Additional query history needed to display performance analysis graphs.")
 
# ----------------- TELEMETRY STREAMING EXECUTION LOOP -----------------
if st.session_state.streaming_active:
    if isinstance(st.session_state.db_instance, RealPostgreSQLDatabase):
        # Poll for actual running queries on the database
        active_queries = st.session_state.db_instance.get_active_queries()
        
        for q in active_queries:
            sql = q["query"]
            pid = q["pid"]
            duration = q["duration_ms"]
            
            # Check safety first
            is_safe, safety_err = st.session_state.swarm_security.check_query_safety(sql)
            
            if not is_safe:
                # Proactively cancel / block the query immediately
                cancel_success = st.session_state.db_instance.cancel_query(pid)
                
                log_entry = {
                    "query_id": f"q_live_{pid}_{int(time.time())}",
                    "timestamp": time.time(),
                    "sql": sql,
                    "execution_time_ms": duration,
                    "plan": {},
                    "bottleneck": "Security policy violation.",
                    "potential_fix": "",
                    "pid": pid,
                    "status": "BLOCKED"
                }
                st.session_state.telemetry_history.append(log_entry)
                
                if not st.session_state.pending_proposal:
                    proposal_payload = {
                        "query_id": log_entry["query_id"],
                        "original_query": sql,
                        "execution_time_ms": duration,
                        "proposed_sql": "",
                        "bottleneck": "Unsafe query executing on database.",
                        "reasoning": f"Security Guard intercepted and terminated query: {safety_err}",
                        "status": "Blocked by Security Guard",
                        "pid": pid,
                        "was_cancelled": cancel_success,
                        "is_security_violation": True
                    }
                    st.session_state.pending_proposal = proposal_payload
                    st.session_state.streaming_active = False
                    st.toast(f"Security Alert: Unsafe query intercepted and cancelled (PID: {pid})!")
                break
            else:
                # Analyze query via EXPLAIN to get plans
                analysis = st.session_state.db_instance.explain_query(sql)
                
                log_entry = {
                    "query_id": f"q_live_{pid}_{int(time.time())}",
                    "timestamp": time.time(),
                    "sql": sql,
                    "execution_time_ms": duration if duration > 0 else analysis["execution_time_ms"],
                    "plan": analysis["plan_tree"],
                    "bottleneck": analysis["bottleneck_detected"],
                    "potential_fix": analysis["potential_fix"],
                    "pid": pid,
                    "status": "SLOW" if (duration > 100.0 or analysis["execution_time_ms"] > 100.0) else "OK"
                }
                
                # Add to history
                st.session_state.telemetry_history.append(log_entry)
                
                # Check with Sentry Agent
                sentry_alert = st.session_state.swarm_sentry.analyze_log_entry(log_entry)
                
                if sentry_alert and not st.session_state.pending_proposal:
                    # Swarm analyzes this slow query
                    proposal_payload = st.session_state.swarm_architect.analyze_slow_query(
                        sentry_alert,
                        db_instance_override=st.session_state.db_instance
                    )
                    
                    # Check security clearance on the fly
                    safety_report = st.session_state.swarm_security.validate_proposal(proposal_payload)
                    
                    # Cancel/block query immediately on the server backend
                    cancel_success = st.session_state.db_instance.cancel_query(pid)
                    
                    # Store the details
                    proposal_payload["pid"] = pid
                    proposal_payload["was_cancelled"] = cancel_success
                    
                    st.session_state.pending_proposal = proposal_payload
                    st.session_state.streaming_active = False
                    
                    if cancel_success:
                        st.toast(f"Active slow query intercepted and BLOCKED (PID: {pid}). Swarm analysis active.")
                    else:
                        st.toast(f"Active slow query intercepted (PID: {pid}). Swarm analysis active.")
                    break
        
        # Trigger Streamlit rerun to continue live monitoring
        time.sleep(0.5)
        st.rerun()
    else:
        # Pull one telemetry log from the generator
        log_entry = next(st.session_state.telemetry_generator.generate_query_stream(st.session_state.db_instance))
        
        # Check safety first
        is_safe, safety_err = st.session_state.swarm_security.check_query_safety(log_entry["sql"])
        
        if not is_safe:
            log_entry["status"] = "BLOCKED"
            # Record in history
            st.session_state.telemetry_history.append(log_entry)
            
            if not st.session_state.pending_proposal:
                proposal_payload = {
                    "query_id": log_entry["query_id"],
                    "original_query": log_entry["sql"],
                    "execution_time_ms": log_entry["execution_time_ms"],
                    "proposed_sql": "",
                    "bottleneck": "Security policy violation.",
                    "reasoning": f"Security Guard blocked the query: {safety_err}",
                    "status": "Blocked by Security Guard",
                    "is_security_violation": True
                }
                st.session_state.pending_proposal = proposal_payload
                st.session_state.streaming_active = False
                st.toast("Security Alert: Unsafe query intercepted and blocked!")
        else:
            # Record in history
            st.session_state.telemetry_history.append(log_entry)
            
            # Check with Sentry Agent
            sentry_alert = st.session_state.swarm_sentry.analyze_log_entry(log_entry)
            
            # If a slow query is intercepted, and we do not have an active proposal queued, trigger the swarm
            if sentry_alert and not st.session_state.pending_proposal:
                # Pass to Architect Agent
                proposal_payload = st.session_state.swarm_architect.analyze_slow_query(
                    sentry_alert,
                    db_instance_override=st.session_state.db_instance
                )
                # Store as pending in session
                st.session_state.pending_proposal = proposal_payload
                # Temporarily pause stream so user can inspect and act on proposal
                st.session_state.streaming_active = False
                st.toast("Slow query intercepted. Swarm optimization proposed.")
            
        # Trigger Streamlit rerun to continue live streaming
        time.sleep(0.5)
        st.rerun()

