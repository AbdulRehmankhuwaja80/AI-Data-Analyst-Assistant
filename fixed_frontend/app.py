"""
Agentic AI Data Analyst — Streamlit Frontend
"""
import os
import streamlit as st

st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global state ──────────────────────────────────────────────────────────────
if "dataset_id" not in st.session_state:
    st.session_state.dataset_id = None
if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 AI Data Analyst")
    st.markdown("---")

    if st.session_state.dataset_id:
        st.success(f"✅ Active dataset:\n**{st.session_state.dataset_name}**")
    else:
        st.info("Upload a dataset to get started.")

    st.markdown("---")
    st.markdown("### Navigation")
    st.page_link("app.py",                  label="🏠 Home")
    st.page_link("pages/01_Explorer.py",    label="🔍 Dataset Explorer")
    st.page_link("pages/02_AI_Chat.py",     label="💬 AI Chat")
    st.page_link("pages/03_Dashboard.py",   label="📊 Dashboard")
    st.page_link("pages/04_Reports.py",     label="📄 Reports")
    st.markdown("---")
    st.caption("Powered by Ollama + LangChain")

# ── Home page ─────────────────────────────────────────────────────────────────
st.title("🤖 Agentic AI Data Analyst")
st.markdown("""
Upload your CSV or Excel dataset and let the multi-agent AI system:

| Agent | Capability |
|-------|------------|
| 🔀 Router | Classifies your query and dispatches to the right agent |
| 🗄️ SQL | Converts natural language to SQL and runs it |
| 📈 Visualization | Picks the best chart type and builds an interactive plot |
| 💡 Insight | Detects trends, anomalies, and KPIs |
| 🧹 Cleaning | Fixes missing values, duplicates, and type errors |
| 🔬 Profiling | Generates a full statistical overview |
| 📄 Report | Exports a PDF report with all analysis sections |

---
""")

# ── Upload section ────────────────────────────────────────────────────────────
st.subheader("📤 Upload Dataset")

uploaded = st.file_uploader(
    "Choose a CSV or Excel file",
    type=["csv", "xlsx", "xls"],
    help="Max file size: 200 MB",
)

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

if uploaded:
    col1, col2 = st.columns([3, 1])
    with col2:
        upload_btn = st.button("🚀 Upload & Analyse", type="primary", use_container_width=True)

    if upload_btn:
        import requests
        with st.spinner("Uploading and auto-cleaning dataset..."):
            try:
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                resp  = requests.post(f"{API_BASE}/api/upload/", files=files, timeout=120)
                resp.raise_for_status()
                data = resp.json()

                st.session_state.dataset_id   = data["dataset_id"]
                st.session_state.dataset_name = data["filename"]
                st.session_state.chat_messages = []

                st.success(
                    f"✅ Upload successful! "
                    f"**{data['rows']:,} rows × {data['columns']} columns** "
                    f"— Dataset ID: `{data['dataset_id']}`"
                )
                st.info("Navigate to **Dataset Explorer** or **AI Chat** from the sidebar.")

            except requests.RequestException as exc:
                st.error(f"Upload failed: {exc}")

# ── Recent datasets ───────────────────────────────────────────────────────────
st.subheader("📂 Recent Datasets")

import requests
try:
    resp = requests.get(f"{API_BASE}/api/upload/list", timeout=10)
    datasets = resp.json() if resp.ok else []
except Exception:
    datasets = []

if datasets:
    for ds in datasets[:5]:
        c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
        c1.write(f"**{ds['name']}**")
        c2.write(f"{ds['rows']:,} rows")
        c3.write(f"{ds['columns']} cols")
        if c4.button("Use this", key=f"use_{ds['id']}"):
            st.session_state.dataset_id   = ds["id"]
            st.session_state.dataset_name = ds["name"]
            st.session_state.chat_messages = []
            st.rerun()
else:
    st.caption("No datasets yet — upload one above.")
