"""
Page 4 — Dashboard: KPI cards, auto-generated charts, AI insights
"""
import json
import os
import requests
import streamlit as st
import pandas as pd

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Analytics Dashboard")

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

dataset_id = st.session_state.get("dataset_id")
if not dataset_id:
    st.warning("No dataset selected. Upload one on the Home page.")
    st.stop()

# ── Load profile ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_profile(did: int):
    resp = requests.get(f"{API_BASE}/api/profile/{did}", timeout=60)
    return resp.json() if resp.ok else {}

@st.cache_data(ttl=300)
def load_insights(did: int):
    resp = requests.post(
        f"{API_BASE}/api/query/",
        json={"dataset_id": did, "question": "Give me the top 5 business insights from this dataset"},
        timeout=120,
    )
    return resp.json() if resp.ok else {}

with st.spinner("Loading dashboard..."):
    profile = load_profile(dataset_id)

# ── KPI cards ─────────────────────────────────────────────────────────────────
if profile:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Rows",    f"{profile.get('row_count', 0):,}")
    col2.metric("Total Columns", profile.get("column_count", 0))

    num_cols = [c for c in profile.get("columns", []) if c.get("mean") is not None]
    null_pct_avg = (
        sum(c["null_pct"] for c in profile.get("columns", [])) / max(len(profile.get("columns", [])), 1)
    )
    col3.metric("Avg Null %",   f"{null_pct_avg:.1f}%")
    col4.metric("Numeric cols", len(num_cols))

    st.markdown("---")

# ── Distribution charts ────────────────────────────────────────────────────────
if PLOTLY_AVAILABLE:
    dist_charts = profile.get("distribution_charts", [])
    if dist_charts:
        st.subheader("📈 Distributions")
        cols = st.columns(2)
        for i, chart_json in enumerate(dist_charts[:4]):
            fig = go.Figure(json.loads(chart_json))
            cols[i % 2].plotly_chart(fig, use_container_width=True)

    if profile.get("correlation_chart"):
        st.subheader("🔗 Correlation Matrix")
        fig = go.Figure(json.loads(profile["correlation_chart"]))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── AI Insights ────────────────────────────────────────────────────────────────
st.subheader("💡 AI-Generated Insights")

if st.button("🔄 Generate Insights", type="primary"):
    with st.spinner("Analysing dataset for insights..."):
        insight_data = load_insights(dataset_id)
        if insight_data.get("insights"):
            for ins in insight_data["insights"]:
                st.success(f"💡 {ins}")
        elif insight_data.get("answer"):
            st.info(insight_data["answer"])
        else:
            st.warning("No insights generated — try asking a specific question in AI Chat.")
else:
    st.info("Click the button above to generate AI insights from your dataset.")

# ── Quick chart ────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("⚡ Quick Chart")

user_q = st.text_input(
    "Describe a chart you want",
    placeholder="e.g. Show monthly revenue as a line chart",
)
if user_q:
    with st.spinner("Building chart..."):
        try:
            resp = requests.post(
                f"{API_BASE}/api/visualize/",
                json={"dataset_id": dataset_id, "question": user_q},
                timeout=120,
            )
            resp.raise_for_status()
            result = resp.json()
            if PLOTLY_AVAILABLE and result.get("chart_json"):
                fig = go.Figure(json.loads(result["chart_json"]))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(result.get("answer", "Could not build chart."))
        except Exception as exc:
            st.error(f"Error: {exc}")
