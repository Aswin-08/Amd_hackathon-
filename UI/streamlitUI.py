"""
Streamlit UI for Logs/Events Root Cause Analysis.

Run:
    streamlit run ui/streamlitUI.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import streamlit as st

# Allow importing agents package when running from RCA/ui.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.workflow import run_rca


st.set_page_config(
    page_title="Logs & Events RCA Agents",
    page_icon="🛠️",
    layout="wide",
)

st.title("🛠️ Logs & Events RCA Multi-Agent Copilot")
st.caption("Upload txt, csv, json, or jsonl logs. Qwen LLM is served locally through vLLM.")

with st.sidebar:
    st.header("LLM / vLLM Settings")
    st.text_input("vLLM Base URL", value=os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"), key="base_url")
    st.text_input("Model", value=os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct"), key="model_name")
    st.text_input("API Key", value=os.getenv("VLLM_API_KEY", "dummy-key"), key="api_key", type="password")
    st.slider("Temperature", min_value=0.0, max_value=1.0, value=float(os.getenv("LLM_TEMPERATURE", "0.1")), step=0.05, key="temperature")
    st.number_input("Max Tokens", min_value=128, max_value=4096, value=int(os.getenv("LLM_MAX_TOKENS", "800")), step=64, key="max_tokens")

    st.divider()
    st.markdown("### Agent Flow")
    st.markdown("1. **Agent1**: Parse and normalize logs")
    st.markdown("2. **Agent2**: RCA and category")
    st.markdown("3. **Agent3**: SOP and remediation")

uploaded_file = st.file_uploader(
    "Upload log/event file",
    type=["txt", "log", "csv", "json", "jsonl"],
    accept_multiple_files=False,
)

if uploaded_file:
    st.subheader("Uploaded File")
    st.write({"name": uploaded_file.name, "type": uploaded_file.type, "size_bytes": uploaded_file.size})

    preview = uploaded_file.getvalue()[:4000]
    try:
        st.code(preview.decode("utf-8", errors="ignore"), language="text")
    except Exception:
        st.info("Binary preview not available.")

    if st.button("Run RCA Analysis", type="primary"):
        os.environ["VLLM_BASE_URL"] = st.session_state.base_url
        os.environ["VLLM_MODEL"] = st.session_state.model_name
        os.environ["VLLM_API_KEY"] = st.session_state.api_key
        os.environ["LLM_TEMPERATURE"] = str(st.session_state.temperature)
        os.environ["LLM_MAX_TOKENS"] = str(st.session_state.max_tokens)

        suffix = Path(uploaded_file.name).suffix or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        with st.spinner("Agents are analyzing the logs/events..."):
            try:
                result = run_rca(tmp_path)
                st.session_state["last_result"] = result
                st.success("RCA analysis completed")
            except Exception as exc:
                st.error(f"RCA failed: {exc}")
                st.stop()

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    rca = result.get("root_cause_analysis", {})
    sop = result.get("sop_recommendation", {})
    parsed = result.get("parsed_context", {})

    st.divider()
    st.header("RCA Result")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Category", rca.get("category", "Unknown"))
    c2.metric("Severity", rca.get("severity", "Unknown"))
    c3.metric("Confidence", rca.get("confidence", "Unknown"))
    c4.metric("Records", result.get("summary", {}).get("records_analyzed", 0))

    st.subheader("Most Likely Root Cause")
    st.write(rca.get("root_cause", "Not available"))

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Evidence")
        for item in rca.get("evidence", []):
            st.markdown(f"- {item}")

        st.subheader("Impacted Services")
        services = rca.get("impacted_services") or parsed.get("suspected_services") or []
        for service in services:
            st.markdown(f"- `{service}`")

    with col_b:
        st.subheader("Recommended Next Steps")
        for item in rca.get("recommended_next_steps", []):
            st.markdown(f"- {item}")

    st.divider()
    st.header("SOP / Remediation Recommendation")
    st.write(f"**{sop.get('sop_id', 'SOP-N/A')} — {sop.get('sop_title', 'SOP recommendation')}**")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Triage Steps")
        for step in sop.get("triage_steps", []):
            st.markdown(f"- {step}")

        st.subheader("Validation Checks")
        for check in sop.get("validation_checks", []):
            st.markdown(f"- {check}")

    with col2:
        st.subheader("Remediation Steps")
        for step in sop.get("remediation_steps", []):
            st.markdown(f"- {step}")

        st.subheader("Governance")
        st.write({
            "rollback_required": sop.get("rollback_required"),
            "human_approval_required": sop.get("human_approval_required"),
            "escalation_team": sop.get("escalation_team"),
        })

    st.subheader("Prevention Recommendations")
    for rec in sop.get("prevention_recommendations", []):
        st.markdown(f"- {rec}")

    with st.expander("Parsed Context"):
        st.json(parsed)

    with st.expander("Full JSON Result"):
        st.json(result)

    st.download_button(
        "Download RCA JSON",
        data=json.dumps(result, indent=2),
        file_name="rca_result.json",
        mime="application/json",
    )
else:
    st.info("Upload a log/event file and click **Run RCA Analysis**.")
