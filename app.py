"""
app.py  –  Data Quality Pipeline
A professional dark-themed Streamlit app with a 3-panel layout:
  Left sidebar  | Main workspace  | Right info panel
"""

import os, sys, json, time, traceback
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agentic Data Pipeline",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS  –  dark editorial theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;500;600;700&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background: #0d0f14;
    color: #e2e4ea;
}
code, pre, .stCode { font-family: 'DM Mono', monospace !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #13161d; }
::-webkit-scrollbar-thumb { background: #2a2f3e; border-radius: 2px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #10121a !important;
    border-right: 1px solid #1e2130 !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

/* ── Main content area ── */
[data-testid="stAppViewContainer"] > .main {
    background: #0d0f14;
    padding: 0 !important;
}
[data-testid="stMainBlockContainer"] {
    padding: 0 !important;
    max-width: 100% !important;
}
.block-container {
    padding: 1.5rem 1.5rem 3rem !important;
    max-width: 100% !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Outfit', sans-serif;
    font-weight: 500;
    font-size: 0.82rem;
    letter-spacing: 0.02em;
    border-radius: 6px;
    padding: 0.45rem 1.1rem;
    transition: all 0.2s;
}
.stButton > button[kind="primary"] {
    background: #4f6ef7;
    border: none;
    color: #fff;
}
.stButton > button[kind="primary"]:hover {
    background: #6b85fa;
    box-shadow: 0 0 16px rgba(79,110,247,0.35);
}
.stButton > button[kind="secondary"] {
    background: transparent;
    border: 1px solid #2a2f3e;
    color: #a0a6bc;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #4f6ef7;
    color: #e2e4ea;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #13161d;
    border: 1.5px dashed #2a2f3e;
    border-radius: 10px;
    padding: 1rem;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #4f6ef7; }

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #13161d;
    border-radius: 8px;
    padding: 3px;
    gap: 2px;
    border: 1px solid #1e2130;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: 'Outfit', sans-serif;
    font-size: 0.82rem;
    font-weight: 500;
    color: #6b7290;
    border-radius: 6px;
    padding: 0.35rem 1rem;
    background: transparent;
    border: none;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #1e2435 !important;
    color: #c5ccf0 !important;
}

/* ── Code blocks ── */
[data-testid="stCodeBlock"] {
    background: #13161d !important;
    border: 1px solid #1e2130;
    border-radius: 8px;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #13161d;
    border: 1px solid #1e2130 !important;
    border-radius: 8px;
}
[data-testid="stExpander"] summary {
    font-family: 'Outfit', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    color: #a0a6bc;
}

/* ── DataFrames ── */
[data-testid="stDataFrame"] {
    background: #13161d;
    border: 1px solid #1e2130;
    border-radius: 8px;
    overflow: hidden;
}

/* ── Inputs & selects ── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"],
[data-testid="stTextArea"] textarea {
    background: #13161d !important;
    border-color: #2a2f3e !important;
    color: #e2e4ea !important;
    font-family: 'Outfit', sans-serif;
    border-radius: 6px;
}

/* ── Divider ── */
hr { border-color: #1e2130 !important; margin: 1rem 0; }

/* ── Custom card ── */
.dq-card {
    background: #13161d;
    border: 1px solid #1e2130;
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.8rem;
}
.dq-card-header {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4f6ef7;
    margin-bottom: 0.4rem;
}
.dq-card-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #e2e4ea;
    line-height: 1;
}
.dq-card-sub {
    font-size: 0.75rem;
    color: #6b7290;
    margin-top: 0.25rem;
}

/* ── Status pills ── */
.pill {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 0.18rem 0.65rem;
    border-radius: 20px;
    margin: 0 0.2rem;
}
.pill-blue   { background: #1a2355; color: #6b8dff; border: 1px solid #2a3a7a; }
.pill-green  { background: #0f2a1a; color: #4ade80; border: 1px solid #1a4a2a; }
.pill-amber  { background: #2a1f08; color: #fbbf24; border: 1px solid #4a3510; }
.pill-red    { background: #2a0f0f; color: #f87171; border: 1px solid #4a1a1a; }
.pill-gray   { background: #1a1d27; color: #8891b0; border: 1px solid #2a2f3e; }

/* ── Sidebar nav items ── */
.nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.5rem 0.75rem;
    border-radius: 7px;
    cursor: pointer;
    font-size: 0.84rem;
    font-weight: 400;
    color: #8891b0;
    transition: all 0.15s;
    margin-bottom: 2px;
}
.nav-item:hover { background: #1a1e2c; color: #c5ccf0; }
.nav-item.active { background: #1a2045; color: #7b9fff; font-weight: 500; }
.nav-icon { font-size: 14px; width: 18px; text-align: center; }

/* ── Agent step cards ── */
.agent-step {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 0.9rem 1rem;
    background: #13161d;
    border: 1px solid #1e2130;
    border-radius: 9px;
    margin-bottom: 0.6rem;
}
.agent-num {
    min-width: 26px; height: 26px;
    background: #1a2045;
    color: #6b8dff;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; font-weight: 700;
}
.agent-info h4 { margin: 0 0 2px; font-size: 0.88rem; font-weight: 600; color: #c5ccf0; }
.agent-info p  { margin: 0; font-size: 0.78rem; color: #6b7290; }

/* ── Page header ── */
.page-header {
    padding: 1.2rem 0 0.8rem;
    border-bottom: 1px solid #1e2130;
    margin-bottom: 1.2rem;
}
.page-header h1 {
    font-size: 1.35rem; font-weight: 700;
    color: #e2e4ea; margin: 0 0 0.2rem;
}
.page-header p {
    font-size: 0.82rem; color: #6b7290; margin: 0;
}

/* ── Section label ── */
.section-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4a5070;
    margin: 1.2rem 0 0.5rem;
}

/* ── Suggestion chips ── */
.chip-row { display: flex; flex-wrap: wrap; gap: 6px; margin: 0.5rem 0 1rem; }
.chip {
    font-size: 0.78rem;
    padding: 0.3rem 0.75rem;
    background: #13161d;
    border: 1px solid #2a2f3e;
    border-radius: 20px;
    color: #8891b0;
    cursor: pointer;
    transition: all 0.15s;
}
.chip:hover { border-color: #4f6ef7; color: #a8b4ff; background: #1a1e2c; }

/* ── Rule table ── */
.rule-row {
    display: flex; align-items: center; gap: 10px;
    padding: 0.55rem 0.75rem;
    border-bottom: 1px solid #1a1e2c;
    font-size: 0.82rem;
}
.rule-row:last-child { border-bottom: none; }
.rule-col { color: #7b9fff; font-family: 'DM Mono', monospace; min-width: 130px; }
.rule-type { color: #8891b0; min-width: 100px; }
.rule-desc { color: #c5ccf0; flex: 1; }
.rule-sev-crit { color: #f87171; min-width: 70px; font-weight: 600; }
.rule-sev-warn { color: #fbbf24; min-width: 70px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
defaults = {
    "df": None, "table_name": None, "ddl_result": None,
    "dq_result": None, "sql_result": None,
    "db_created": False, "bronze_loaded": False,
    "silver_promoted": False, "active_page": "pipeline",
    "pipeline_log": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def log(msg: str, kind: str = "info"):
    st.session_state.pipeline_log.append({"msg": msg, "kind": kind, "ts": time.strftime("%H:%M:%S")})


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand
    st.markdown("""
    <div style="padding:1.2rem 0.75rem 0.8rem; border-bottom:1px solid #1e2130; margin-bottom:0.8rem;">
      <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.14em;
                  text-transform:uppercase;color:#4f6ef7;margin-bottom:2px;">
        ⬡ Agentic Data Pipeline
      </div>
      <div style="font-size:1.05rem;font-weight:700;color:#e2e4ea;line-height:1.1;">
        Data Pipeline
      </div>
      <div style="font-size:0.72rem;color:#4a5070;margin-top:2px;">
        Bronze · Silver · Validated
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Nav
    pages = [
        ("pipeline",  "⬡", "Pipeline Builder"),
        ("rules",     "◈", "DQ Rules"),
        ("sql",       "◉", "SQL Queries"),
        ("database",  "◌", "Database"),
        ("logs",      "≡", "Activity Log"),
    ]
    for page_id, icon, label in pages:
        active = "active" if st.session_state.active_page == page_id else ""
        if st.button(f"{icon}  {label}", key=f"nav_{page_id}", use_container_width=True):
            st.session_state.active_page = page_id
            st.rerun()

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Pipeline Status</div>', unsafe_allow_html=True)

    # Status indicators
    steps = [
        ("CSV Uploaded",   st.session_state.df is not None),
        ("DDL Generated",  st.session_state.ddl_result is not None),
        ("DQ Rules Ready", st.session_state.dq_result is not None),
        ("SQL Generated",  st.session_state.sql_result is not None),
        ("DB Tables Created", st.session_state.db_created),
        ("Bronze Loaded",  st.session_state.bronze_loaded),
        ("Silver Promoted",st.session_state.silver_promoted),
    ]
    for label, done in steps:
        icon  = "✓" if done else "○"
        color = "#4ade80" if done else "#2a2f3e"
        st.markdown(
            f'<div style="font-size:0.78rem;color:{color};padding:3px 0;'
            f'display:flex;align-items:center;gap:7px;">'
            f'<span style="font-weight:700">{icon}</span>{label}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # DB connection status
    from database.db import test_connection
    ok, msg = test_connection()
    dot   = "🟢" if ok else "🔴"
    label = "PostgreSQL connected" if ok else "PostgreSQL offline"
    st.markdown(
        f'<div style="font-size:0.75rem;color:#4a5070;margin-top:auto;'
        f'padding:0.5rem 0.75rem;border-top:1px solid #1e2130;">'
        f'{dot} {label}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def severity_pill(sev: str) -> str:
    s = str(sev).lower()
    if s == "critical":
        return '<span class="pill pill-red">critical</span>'
    return '<span class="pill pill-amber">warning</span>'


def status_pill(label: str, color: str = "blue") -> str:
    return f'<span class="pill pill-{color}">{label}</span>'


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: PIPELINE BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def page_pipeline():
    st.markdown("""
    <div class="page-header">
      <h1>Pipeline Builder</h1>
      <p>Upload a CSV dataset to generate DDL, Data Quality rules, and Bronze → Silver SQL automatically.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Agent overview ──
    st.markdown('<div class="section-label">Autonomous Agents</div>', unsafe_allow_html=True)
    agents = [
        ("1", "DDL Generator",    "Extracts schema metadata from CSV and generates PostgreSQL Bronze + Silver DDL"),
        ("2", "Data Quality",     "Analyses column distributions and generates Pydantic-validated DQ rules"),
        ("3", "SQL Query Builder","Converts DQ rules into Bronze → Silver INSERT + filter SQL queries"),
    ]
    cols = st.columns(3)
    for col, (num, name, desc) in zip(cols, agents):
        with col:
            st.markdown(f"""
            <div class="dq-card" style="min-height:90px">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <div class="agent-num">{num}</div>
                <div style="font-size:0.88rem;font-weight:600;color:#c5ccf0;">{name}</div>
              </div>
              <div style="font-size:0.78rem;color:#6b7290;line-height:1.45;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Upload Dataset</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        uploaded = st.file_uploader(
            "Drop your CSV file here",
            type=["csv"],
            label_visibility="collapsed",
        )
    with c2:
        table_input = st.text_input(
            "Table name",
            value=st.session_state.table_name or "",
            placeholder="e.g. sales_data",
        )

    if uploaded:
        df = pd.read_csv(uploaded)
        tname = table_input.strip() or uploaded.name.replace(".csv","").replace(" ","_").lower()
        st.session_state.df = df
        st.session_state.table_name = tname

        st.markdown(f"""
        <div class="dq-card" style="margin-bottom:1rem;">
          <div class="dq-card-header">Dataset Preview</div>
          <div style="display:flex;gap:1.5rem;margin-bottom:0.6rem;">
            <div><span style="font-size:1.1rem;font-weight:700;color:#e2e4ea;">{len(df):,}</span>
                 <span style="font-size:0.75rem;color:#6b7290;margin-left:4px;">rows</span></div>
            <div><span style="font-size:1.1rem;font-weight:700;color:#e2e4ea;">{len(df.columns)}</span>
                 <span style="font-size:0.75rem;color:#6b7290;margin-left:4px;">columns</span></div>
            <div><span style="font-size:1.1rem;font-weight:700;color:#7b9fff;">{tname}</span>
                 <span style="font-size:0.75rem;color:#6b7290;margin-left:4px;">table</span></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(df.head(8), use_container_width=True, height=200)

    # ── Run pipeline ──
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    if st.session_state.df is not None:
        if st.button("⬡  Run Full Pipeline", type="primary", use_container_width=False):
            _run_pipeline()

        if st.session_state.ddl_result or st.session_state.dq_result or st.session_state.sql_result:
            _show_pipeline_results()
    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0;color:#4a5070;">
          <div style="font-size:2rem;margin-bottom:0.5rem;">⬡</div>
          <div style="font-size:0.9rem;">Upload a CSV file to begin</div>
        </div>
        """, unsafe_allow_html=True)


def _run_pipeline():
    from agents import run_ddl_agent, run_dq_agent, run_sql_agent

    df    = st.session_state.df
    tname = st.session_state.table_name

    progress = st.progress(0, text="Starting pipeline...")
    status   = st.empty()

    try:
        # Step 1: DDL
        status.markdown('<span class="pill pill-blue">⬡ DDL Agent running...</span>', unsafe_allow_html=True)
        with st.spinner(""):
            ddl = run_ddl_agent(df, tname)
        st.session_state.ddl_result = ddl
        log(f"DDL generated for {tname} — {len(ddl['metadata'])} columns", "success")
        progress.progress(33, text="DDL generated")

        # Step 2: DQ Rules
        status.markdown('<span class="pill pill-blue">◈ DQ Agent running...</span>', unsafe_allow_html=True)
        with st.spinner(""):
            dq = run_dq_agent(df, tname)
        st.session_state.dq_result = dq
        log(f"DQ rules generated — {len(dq['rules'])} rules across {len(df.columns)} columns", "success")
        progress.progress(66, text="DQ rules generated")

        # Step 3: SQL
        status.markdown('<span class="pill pill-blue">◉ SQL Agent running...</span>', unsafe_allow_html=True)
        with st.spinner(""):
            sqr = run_sql_agent(tname, dq["rules"], ddl["metadata"])
        st.session_state.sql_result = sqr
        log(f"SQL queries generated — Bronze→Silver INSERT ready", "success")
        progress.progress(100, text="Pipeline complete")

        status.markdown('<span class="pill pill-green">✓ Pipeline complete</span>', unsafe_allow_html=True)
        time.sleep(0.5)
        st.rerun()

    except Exception as e:
        log(f"Pipeline error: {e}", "error")
        status.markdown(f'<span class="pill pill-red">Pipeline error: {e}</span>', unsafe_allow_html=True)
        st.error(traceback.format_exc())


def _show_pipeline_results():
    ddl = st.session_state.ddl_result
    dq  = st.session_state.dq_result
    sqr = st.session_state.sql_result

    st.markdown('<div class="section-label">Generated Outputs</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["⬡  DDL", "◈  DQ Rules", "◉  SQL Queries"])

    with tab1:
        if ddl:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="dq-card-header">Bronze Layer DDL</div>', unsafe_allow_html=True)
                st.code(ddl["bronze_ddl"], language="sql")
            with c2:
                st.markdown('<div class="dq-card-header">Silver Layer DDL</div>', unsafe_allow_html=True)
                st.code(ddl["silver_ddl"], language="sql")

            # Create tables button
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            if st.button("◌  Create Tables in PostgreSQL", type="primary"):
                from database.db import execute_ddl
                res = execute_ddl(ddl["bronze_ddl"], ddl["silver_ddl"])
                if res["success"]:
                    st.session_state.db_created = True
                    log("Bronze & Silver tables created in PostgreSQL", "success")
                    st.success(res["message"])
                else:
                    st.error(res["message"])

    with tab2:
        if dq:
            rules = dq.get("rules", [])
            critical = sum(1 for r in rules if str(r.get("severity","")).lower() == "critical")
            warning  = len(rules) - critical

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Rules",    len(rules))
            c2.metric("Critical",       critical)
            c3.metric("Warnings",       warning)

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            st.markdown('<div class="dq-card-header">Rule Details</div>', unsafe_allow_html=True)
            st.markdown('<div class="dq-card" style="padding:0;">', unsafe_allow_html=True)
            for rule in rules:
                sev   = str(rule.get("severity","warning")).lower()
                scls  = "rule-sev-crit" if sev == "critical" else "rule-sev-warn"
                st.markdown(f"""
                <div class="rule-row">
                  <div class="rule-col">{rule.get('column','')}</div>
                  <div class="rule-type">{rule.get('rule_type','')}</div>
                  <div class="rule-desc">{rule.get('description','')}</div>
                  <div class="{scls}">{sev}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if dq.get("pydantic_code"):
                with st.expander("View Pydantic DQ Model code"):
                    st.code(dq["pydantic_code"], language="python")

    with tab3:
        if sqr:
            st.markdown('<div class="dq-card-header">Bronze → Silver (Passing records)</div>', unsafe_allow_html=True)
            st.code(sqr["bronze_to_silver_sql"], language="sql")
            st.markdown('<div class="dq-card-header" style="margin-top:1rem;">Failed Records Query</div>', unsafe_allow_html=True)
            st.code(sqr["failed_records_sql"], language="sql")
            st.markdown('<div class="dq-card-header" style="margin-top:1rem;">Layer Stats Query</div>', unsafe_allow_html=True)
            st.code(sqr["stats_sql"], language="sql")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DQ RULES
# ─────────────────────────────────────────────────────────────────────────────
def page_rules():
    st.markdown("""
    <div class="page-header">
      <h1>Data Quality Rules</h1>
      <p>Auto-generated Pydantic validation rules for every column in your dataset.</p>
    </div>
    """, unsafe_allow_html=True)

    dq = st.session_state.dq_result
    if not dq:
        st.info("Run the pipeline first to generate DQ rules.")
        return

    rules = dq.get("rules", [])
    # Group by column
    by_col: dict = {}
    for r in rules:
        by_col.setdefault(r.get("column", "?"), []).append(r)

    cols = list(by_col.keys())
    search = st.text_input("Search columns…", placeholder="Filter by column name", label_visibility="collapsed")
    if search:
        cols = [c for c in cols if search.lower() in c.lower()]

    for col in cols:
        col_rules = by_col[col]
        with st.expander(f"**{col}**  —  {len(col_rules)} rule(s)", expanded=False):
            for r in col_rules:
                sev = str(r.get("severity","warning")).lower()
                pill = '<span class="pill pill-red">critical</span>' if sev=="critical" else '<span class="pill pill-amber">warning</span>'
                st.markdown(f"""
                <div class="dq-card" style="margin-bottom:6px;">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                    <span style="font-size:0.85rem;font-weight:600;color:#c5ccf0;">{r.get('rule_name','')}</span>
                    {pill}
                  </div>
                  <div style="font-size:0.8rem;color:#8891b0;">{r.get('description','')}</div>
                  <div style="font-size:0.75rem;color:#4a5070;margin-top:6px;">
                    Type: <span style="color:#7b9fff">{r.get('rule_type','')}</span> &nbsp;|&nbsp;
                    Threshold: <span style="color:#a8d5a2">{r.get('threshold','—')}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

    if dq.get("pydantic_code"):
        st.markdown('<div class="section-label">Pydantic Model</div>', unsafe_allow_html=True)
        st.code(dq["pydantic_code"], language="python")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: SQL QUERIES
# ─────────────────────────────────────────────────────────────────────────────
def page_sql():
    st.markdown("""
    <div class="page-header">
      <h1>SQL Queries</h1>
      <p>Generated SQL to load Bronze and promote clean data to Silver.</p>
    </div>
    """, unsafe_allow_html=True)

    sqr = st.session_state.sql_result
    if not sqr:
        st.info("Run the pipeline first to generate SQL queries.")
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "Bronze → Silver", "Failed Records", "Stats Query", "Custom SQL"
    ])

    with tab1:
        st.markdown('<div class="dq-card-header">INSERT passing records to Silver layer</div>', unsafe_allow_html=True)
        st.code(sqr["bronze_to_silver_sql"], language="sql")
        if st.button("▶  Execute Bronze → Silver", type="primary"):
            from database.db import promote_to_silver
            res = promote_to_silver(sqr["bronze_to_silver_sql"])
            if res["success"]:
                st.session_state.silver_promoted = True
                log(f"Silver promotion: {res['rows_promoted']} rows promoted", "success")
                st.success(res["message"])
            else:
                st.error(res["message"])

    with tab2:
        st.markdown('<div class="dq-card-header">Records that FAILED quality checks</div>', unsafe_allow_html=True)
        st.code(sqr["failed_records_sql"], language="sql")
        if st.button("▶  Run Failed Records Query"):
            from database.db import run_custom_sql
            rows, err = run_custom_sql(sqr["failed_records_sql"])
            if err:
                st.error(err)
            elif rows is not None:
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with tab3:
        st.markdown('<div class="dq-card-header">Layer comparison stats</div>', unsafe_allow_html=True)
        st.code(sqr["stats_sql"], language="sql")
        if st.button("▶  Run Stats"):
            from database.db import get_layer_stats
            stats = get_layer_stats(sqr["stats_sql"])
            if stats:
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Total Records",   stats.get("total_records","—"))
                c2.metric("Passed",          stats.get("passed_records","—"))
                c3.metric("Failed",          stats.get("failed_records","—"))
                c4.metric("Pass Rate",       f"{stats.get('pass_rate_pct','—')}%")
            else:
                st.warning("No data returned.")

    with tab4:
        st.markdown('<div class="dq-card-header">Run any SQL query</div>', unsafe_allow_html=True)
        custom = st.text_area("SQL", height=120, placeholder="SELECT * FROM bronze.your_table_bronze LIMIT 20;",
                              label_visibility="collapsed")
        if st.button("▶  Execute", type="primary") and custom.strip():
            from database.db import run_custom_sql
            rows, err = run_custom_sql(custom)
            if err:
                st.error(err)
            elif rows is not None:
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
                st.caption(f"{len(rows)} rows returned")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DATABASE
# ─────────────────────────────────────────────────────────────────────────────
def page_database():
    st.markdown("""
    <div class="page-header">
      <h1>Database Operations</h1>
      <p>Manage Bronze and Silver layer tables in PostgreSQL.</p>
    </div>
    """, unsafe_allow_html=True)

    ok, msg = test_connection()
    if ok:
        st.markdown(f'<span class="pill pill-green">✓ Connected</span> <span style="font-size:0.78rem;color:#4a5070;margin-left:6px;">{msg[:80]}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="pill pill-red">✗ Offline</span> <span style="font-size:0.78rem;color:#f87171;margin-left:6px;">{msg}</span>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Actions</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown('<div class="dq-card">', unsafe_allow_html=True)
        st.markdown('<div class="dq-card-header">Create Tables</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.78rem;color:#6b7290;margin-bottom:0.7rem;">Execute the generated DDL to create Bronze + Silver tables.</div>', unsafe_allow_html=True)
        if st.button("◌  Create Tables", type="primary", use_container_width=True):
            ddl = st.session_state.ddl_result
            if not ddl:
                st.warning("Run pipeline first.")
            else:
                from database.db import execute_ddl
                res = execute_ddl(ddl["bronze_ddl"], ddl["silver_ddl"])
                if res["success"]:
                    st.session_state.db_created = True
                    log("Tables created", "success")
                    st.success(res["message"])
                else:
                    st.error(res["message"])
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="dq-card">', unsafe_allow_html=True)
        st.markdown('<div class="dq-card-header">Load Bronze</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.78rem;color:#6b7290;margin-bottom:0.7rem;">Bulk-insert CSV data into the Bronze layer table.</div>', unsafe_allow_html=True)
        if st.button("⬡  Ingest to Bronze", use_container_width=True):
            df    = st.session_state.df
            tname = st.session_state.table_name
            if df is None:
                st.warning("Upload CSV first.")
            else:
                from database.db import ingest_to_bronze
                res = ingest_to_bronze(df, tname)
                if res["success"]:
                    st.session_state.bronze_loaded = True
                    log(f"Bronze: {res['rows_inserted']} rows loaded", "success")
                    st.success(res["message"])
                else:
                    st.error(res["message"])
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="dq-card">', unsafe_allow_html=True)
        st.markdown('<div class="dq-card-header">Promote to Silver</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.78rem;color:#6b7290;margin-bottom:0.7rem;">Run DQ filters and move clean records to Silver layer.</div>', unsafe_allow_html=True)
        if st.button("◉  Promote to Silver", use_container_width=True):
            sqr = st.session_state.sql_result
            if not sqr:
                st.warning("Generate SQL first.")
            else:
                from database.db import promote_to_silver
                res = promote_to_silver(sqr["bronze_to_silver_sql"])
                if res["success"]:
                    st.session_state.silver_promoted = True
                    log(f"Silver: {res['rows_promoted']} rows promoted", "success")
                    st.success(res["message"])
                else:
                    st.error(res["message"])
        st.markdown('</div>', unsafe_allow_html=True)

    # Architecture diagram
    st.markdown('<div class="section-label">Layer Architecture</div>', unsafe_allow_html=True)
    tname = st.session_state.table_name or "your_table"
    b_color = "#0f2a1a" if st.session_state.bronze_loaded  else "#1a1d27"
    s_color = "#0f1f3a" if st.session_state.silver_promoted else "#1a1d27"
    b_border= "#1a4a2a" if st.session_state.bronze_loaded  else "#2a2f3e"
    s_border= "#1a3a6a" if st.session_state.silver_promoted else "#2a2f3e"
    b_text  = "#4ade80" if st.session_state.bronze_loaded  else "#4a5070"
    s_text  = "#7b9fff" if st.session_state.silver_promoted else "#4a5070"

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:1rem;padding:1.2rem;">
      <div style="background:#13161d;border:1px solid #2a2f3e;border-radius:8px;
                  padding:1rem 1.4rem;text-align:center;min-width:140px;">
        <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.1em;color:#8891b0;margin-bottom:4px;">Source</div>
        <div style="font-size:0.9rem;font-weight:600;color:#c5ccf0;">CSV File</div>
      </div>
      <div style="color:#2a2f3e;font-size:1.2rem;flex:1;text-align:center;">──────→</div>
      <div style="background:{b_color};border:1px solid {b_border};border-radius:8px;
                  padding:1rem 1.4rem;text-align:center;min-width:160px;">
        <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.1em;color:#8b6914;margin-bottom:4px;">Bronze Layer</div>
        <div style="font-size:0.9rem;font-weight:600;color:{b_text};">bronze.{tname}_bronze</div>
        <div style="font-size:0.72rem;color:#4a5070;margin-top:3px;">Raw • All records</div>
      </div>
      <div style="color:#2a2f3e;font-size:1.2rem;flex:1;text-align:center;">── DQ filter ──→</div>
      <div style="background:{s_color};border:1px solid {s_border};border-radius:8px;
                  padding:1rem 1.4rem;text-align:center;min-width:160px;">
        <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.1em;color:#1e4a8a;margin-bottom:4px;">Silver Layer</div>
        <div style="font-size:0.9rem;font-weight:600;color:{s_text};">silver.{tname}_silver</div>
        <div style="font-size:0.72rem;color:#4a5070;margin-top:3px;">Clean • Validated</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.silver_promoted:
        st.markdown('<div class="section-label">Sorted Data (Silver Layer)</div>', unsafe_allow_html=True)
        if st.button("👁  View Sorted Data", type="secondary"):
            from database.db import run_custom_sql, SILVER_SCHEMA
            tname = st.session_state.table_name
            if tname:
                needs_quotes = any(c in tname for c in '-./() \t')
                silver_table_name = f'{tname}_silver'
                full_table_name = f'{SILVER_SCHEMA}."{silver_table_name}"' if needs_quotes else f'{SILVER_SCHEMA}.{silver_table_name}'
                query = f"SELECT * FROM {full_table_name} LIMIT 100;"
                with st.spinner("Fetching sorted data from database..."):
                    rows, err = run_custom_sql(query)
                if err:
                    st.error(f"Error fetching data: {err}")
                elif rows:
                    df_silver = pd.DataFrame(rows)
                    st.markdown(f'<div class="dq-card" style="padding:0;"><div class="dq-card-header" style="padding:1rem 1rem 0;">Preview ({len(rows)} rows)</div>', unsafe_allow_html=True)
                    st.dataframe(df_silver, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("The Silver table is currently empty.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: LOGS
# ─────────────────────────────────────────────────────────────────────────────
def page_logs():
    st.markdown("""
    <div class="page-header">
      <h1>Activity Log</h1>
      <p>Pipeline execution history and agent messages.</p>
    </div>
    """, unsafe_allow_html=True)

    logs = st.session_state.pipeline_log
    if not logs:
        st.markdown('<div style="text-align:center;color:#4a5070;padding:3rem;">No activity yet.</div>', unsafe_allow_html=True)
        return

    c1, c2 = st.columns([5, 1])
    with c2:
        if st.button("Clear log"):
            st.session_state.pipeline_log = []
            st.rerun()

    for entry in reversed(logs):
        kind  = entry.get("kind", "info")
        color = {"success": "#4ade80", "error": "#f87171", "warning": "#fbbf24"}.get(kind, "#8891b0")
        icon  = {"success": "✓", "error": "✗", "warning": "⚠"}.get(kind, "·")
        st.markdown(f"""
        <div class="dq-card" style="display:flex;align-items:center;gap:10px;padding:0.6rem 1rem;">
          <span style="color:{color};font-weight:700;min-width:16px;">{icon}</span>
          <span style="font-size:0.8rem;color:#c5ccf0;flex:1;">{entry['msg']}</span>
          <span style="font-size:0.72rem;color:#4a5070;font-family:'DM Mono',monospace;">{entry['ts']}</span>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
page = st.session_state.active_page
if   page == "pipeline": page_pipeline()
elif page == "rules":    page_rules()
elif page == "sql":      page_sql()
elif page == "database": page_database()
elif page == "logs":     page_logs()
