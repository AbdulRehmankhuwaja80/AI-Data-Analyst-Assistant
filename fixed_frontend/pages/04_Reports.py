"""
Page 5 — Reports: generate and download PDF analysis reports
"""
import os
import requests
import streamlit as st

st.set_page_config(page_title="Reports", page_icon="📄", layout="wide")
st.title("📄 Report Generator")

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

dataset_id = st.session_state.get("dataset_id")
if not dataset_id:
    st.warning("No dataset selected. Upload one on the Home page.")
    st.stop()

st.markdown("""
Generate a comprehensive PDF report including:
- Dataset overview and column statistics
- Data quality summary
- AI-generated business insights
- Visualizations embedded in the PDF
- Statistical summary tables
""")

# ── Generate report ────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])
with col1:
    focus_q = st.text_input(
        "Optional: focus question for insights",
        placeholder="e.g. What are the key revenue drivers?",
        value="",
    )

with col2:
    generate = st.button("🚀 Generate PDF Report", type="primary", use_container_width=True)

if generate:
    with st.spinner("Generating report — this may take 30–60 seconds..."):
        try:
            payload = {
                "dataset_id": dataset_id,
                "question": focus_q or "Generate a comprehensive analysis report",
            }
            resp = requests.post(
                f"{API_BASE}/api/report/generate",
                json=payload,
                timeout=180,
            )
            resp.raise_for_status()
            result = resp.json()

            st.success(f"✅ Report generated: **{result['report_name']}**")

            dl_url = f"{API_BASE}{result['download_url']}"
            pdf_resp = requests.get(dl_url, timeout=30)
            if pdf_resp.ok:
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_resp.content,
                    file_name=result["report_name"],
                    mime="application/pdf",
                    type="primary",
                )
        except Exception as exc:
            st.error(f"Report generation failed: {exc}")

# ── Past reports ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📁 Past Reports")

try:
    resp = requests.get(f"{API_BASE}/api/report/list", timeout=10)
    reports = resp.json() if resp.ok else []
except Exception:
    reports = []

if reports:
    for rpt in reports:
        c1, c2, c3 = st.columns([5, 3, 2])
        c1.write(f"📄 **{rpt['name']}**")
        c2.write(str(rpt.get("created_at", ""))[:19])
        dl_url = f"{API_BASE}{rpt['download_url']}"
        try:
            pdf_bytes = requests.get(dl_url, timeout=10).content
            c3.download_button(
                "⬇️ Download",
                data=pdf_bytes,
                file_name=rpt["name"],
                mime="application/pdf",
                key=f"dl_{rpt['id']}",
            )
        except Exception:
            c3.write("Unavailable")
else:
    st.caption("No reports yet — generate one above.")
