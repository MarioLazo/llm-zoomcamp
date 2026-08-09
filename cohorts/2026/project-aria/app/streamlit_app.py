"""ARIA — Automated Regulatory Intelligence Agent. Streamlit UI.

Three modes over the same RAG pipeline: chat, evidence, briefing.
Each answer can be rated 👍/👎; ratings + interactions feed the dashboard.
"""
import streamlit as st

from app import monitoring
from app.rag import RAG

st.set_page_config(page_title="ARIA", page_icon="🛡️", layout="wide")


@st.cache_resource
def get_rag():
    return RAG()


st.title("🛡️ ARIA")
st.caption("Automated Regulatory Intelligence Agent — grounded Q&A, evidence, and briefings over your transcripts")

mode = st.radio(
    "Mode",
    ["chat", "evidence", "briefing"],
    horizontal=True,
    format_func=lambda m: {"chat": "💬 Chat", "evidence": "📌 Evidence", "briefing": "📋 Briefing"}[m],
)

placeholder = {
    "chat": "What controls did we describe for vendor AI risk?",
    "evidence": "Theme: fear of losing control to an AI black box",
    "briefing": "Topic: how regulated industries govern AI agent adoption",
}[mode]

query = st.text_input("Your request", placeholder=placeholder)

if st.button("Run", type="primary") and query:
    with st.spinner("Searching the corpus…"):
        result = get_rag().answer(query, mode=mode)
        result["interaction_id"] = monitoring.log_interaction(result)
        st.session_state["last"] = result

if "last" in st.session_state:
    result = st.session_state["last"]

    st.markdown("### Answer")
    st.markdown(result["answer"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Model", result["model"].split("-")[0])
    col2.metric("Latency", f"{result['latency_ms']:.0f} ms")
    col3.metric("Tokens (out)", result["tokens_out"])
    col4.metric("Top score", f"{result['top_score']:.2f}")

    with st.expander("🔎 Retrieved sources (after rerank)"):
        st.caption(f"Rewritten query: _{result['rewritten']}_")
        for s in result["sources"]:
            st.markdown(
                f"**{s['source']}** · rerank={s['rerank_score']:.2f} · "
                f"hybrid={s['score']:.2f}\n\n{s['text'][:400]}…"
            )

    st.markdown("#### Was this helpful?")
    c1, c2, _ = st.columns([1, 1, 6])
    if c1.button("👍"):
        monitoring.log_feedback(result["interaction_id"], "up")
        st.success("Thanks!")
    if c2.button("👎"):
        monitoring.log_feedback(result["interaction_id"], "down")
        st.info("Noted — logged for improvement.")
