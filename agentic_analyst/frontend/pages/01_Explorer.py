"""
Page 2 — Dataset Explorer: preview, profiling, data types
"""
import json
import os
import requests
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Dataset Explorer", page_icon="🔍", layout="wide")
st.title("🔍 Dataset Explorer")

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

dataset_id = st.session_state.get("dataset_id")
if not dataset_id:
    st.warning("No dataset selected. Upload one on the Home page.")
    st.stop()

st.caption(f"Dataset ID: `{dataset_id}` — {st.session_state.get('dataset_name', '')}")

tab_profile, tab_clean = st.tabs(["📊 Profile", "🧹 Data Quality"])

# ── Profile tab ────────────────────────────────────────────────────────────────
with tab_profile:
    with st.spinner("Running data profiler..."):
        try:
            resp = requests.get(f"{API_BASE}/api/profile/{dataset_id}", timeout=60)
            resp.raise_for_status()
            profile = resp.json()
        except Exception as exc:
            st.error(f"Profiling failed: {exc}")
            st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Rows",    f"{profile['row_count']:,}")
    col2.metric("Columns", profile["column_count"])

    null_cols = sum(1 for c in profile["columns"] if c["null_pct"] > 0)
    col3.metric("Columns with nulls", null_cols)

    st.markdown("---")
    st.subheader("Column details")

    import pandas as pd
    rows = []
    for c in profile["columns"]:
        rows.append({
            "Column":  c["name"],
            "Type":    c["dtype"],
            "Nulls":   c["null_count"],
            "Null %":  f"{c['null_pct']}%",
            "Unique":  c["unique_count"],
            "Mean":    c.get("mean", "—"),
            "Std":     c.get("std",  "—"),
            "Min":     c.get("min",  "—"),
            "Max":     c.get("max",  "—"),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # Distribution charts
    if profile.get("distribution_charts"):
        st.markdown("---")
        st.subheader("Distributions")
        cols = st.columns(2)
        for i, chart_json in enumerate(profile["distribution_charts"]):
            fig = go.Figure(json.loads(chart_json))
            cols[i % 2].plotly_chart(fig, use_container_width=True)

    # Correlation heatmap
    if profile.get("correlation_chart"):
        st.markdown("---")
        st.subheader("Correlation Matrix")
        fig = go.Figure(json.loads(profile["correlation_chart"]))
        st.plotly_chart(fig, use_container_width=True)

# ── Data Quality tab ───────────────────────────────────────────────────────────
with tab_clean:
    st.subheader("Data Cleaning Report")
    if st.button("🧹 Run Cleaner Now", type="primary"):
        with st.spinner("Cleaning data..."):
            try:
                resp = requests.post(f"{API_BASE}/api/clean/{dataset_id}", timeout=60)
                resp.raise_for_status()
                report = resp.json()

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Missing fixed",       report["missing_fixed"])
                col2.metric("Duplicates removed",  report["duplicates_removed"])
                col3.metric("Columns converted",   report["columns_converted"])
                col4.metric("Outliers flagged",    report["outliers_flagged"])

                st.success("Cleaning complete!")
                for item in report["summary"]:
                    st.markdown(f"• {item}")
            except Exception as exc:
                st.error(f"Cleaning failed: {exc}")
    else:
        st.info("Click the button above to run the automatic data cleaning pipeline.")
