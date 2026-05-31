"""
Page 3 — AI Chat: conversational interface with dataset context
"""
import json
import os
import requests
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="AI Chat", page_icon="💬", layout="wide")
st.title("💬 AI Chat with your Data")

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

dataset_id = st.session_state.get("dataset_id")
if not dataset_id:
    st.warning("No dataset selected. Upload one on the Home page.")
    st.stop()

st.caption(f"Chatting with: **{st.session_state.get('dataset_name', '')}**")

# ── Example prompts ────────────────────────────────────────────────────────────
with st.expander("💡 Try these prompts"):
    examples = [
        "Show me the top 10 rows by the first numeric column",
        "What is the monthly trend of sales?",
        "Are there any anomalies in the data?",
        "Which category has the highest average value?",
        "Generate a bar chart comparing categories",
        "Give me business insights from this dataset",
    ]
    cols = st.columns(3)
    for i, ex in enumerate(examples):
        if cols[i % 3].button(ex, key=f"ex_{i}"):
            st.session_state.chat_messages.append({"role": "user", "content": ex})
            st.rerun()

# ── Chat history display ───────────────────────────────────────────────────────
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sql"):
            with st.expander("🗄️ Generated SQL"):
                st.code(msg["sql"], language="sql")
        if msg.get("chart_json"):
            fig = go.Figure(json.loads(msg["chart_json"]))
            st.plotly_chart(fig, use_container_width=True)
        if msg.get("result_data") and len(msg["result_data"]) > 0:
            import pandas as pd
            with st.expander("📋 Query results"):
                st.dataframe(pd.DataFrame(msg["result_data"]), use_container_width=True)

# ── Input ──────────────────────────────────────────────────────────────────────
prompt = st.chat_input("Ask anything about your dataset...")

if prompt:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Use query route (router agent) for structured responses
                resp = requests.post(
                    f"{API_BASE}/api/query/",
                    json={"dataset_id": dataset_id, "question": prompt},
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()

                agent_badge = {
                    "sql":           "🗄️ SQL Agent",
                    "visualization": "📈 Visualization Agent",
                    "insight":       "💡 Insight Agent",
                    "cleaning":      "🧹 Cleaning Agent",
                    "profiling":     "🔬 Profiling Agent",
                    "report":        "📄 Report Agent",
                    "general":       "🤖 General Agent",
                }.get(data.get("agent_used", ""), "🤖 Agent")

                st.caption(f"Handled by: **{agent_badge}**")
                st.markdown(data["answer"])

                if data.get("sql"):
                    with st.expander("🗄️ Generated SQL"):
                        st.code(data["sql"], language="sql")

                if data.get("chart_json"):
                    fig = go.Figure(json.loads(data["chart_json"]))
                    st.plotly_chart(fig, use_container_width=True)

                if data.get("result_data") and len(data["result_data"]) > 0:
                    import pandas as pd
                    with st.expander(f"📋 Results ({len(data['result_data'])} rows)"):
                        st.dataframe(pd.DataFrame(data["result_data"]), use_container_width=True)

                if data.get("insights"):
                    with st.expander("💡 Insights"):
                        for ins in data["insights"]:
                            st.markdown(f"• {ins}")

                # Append to history
                st.session_state.chat_messages.append({
                    "role":       "assistant",
                    "content":    data["answer"],
                    "sql":        data.get("sql"),
                    "chart_json": data.get("chart_json"),
                    "result_data": data.get("result_data"),
                })

            except Exception as exc:
                st.error(f"Error: {exc}")

# ── Clear chat ─────────────────────────────────────────────────────────────────
if st.sidebar.button("🗑️ Clear chat"):
    st.session_state.chat_messages = []
    st.rerun()
