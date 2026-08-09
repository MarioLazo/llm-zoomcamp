"""ARIA — Monitoring dashboard (Streamlit) — 6 charts + user-feedback summary.

Run as a second Streamlit page/service; reads directly from Postgres.
"""
import pandas as pd
import streamlit as st

from app import monitoring

st.set_page_config(page_title="ARIA Monitoring", page_icon="📊", layout="wide")
st.title("📊 ARIA — Monitoring")

interactions = pd.DataFrame(monitoring.fetch_interactions())
feedback = pd.DataFrame(monitoring.fetch_feedback())

if interactions.empty:
    st.info("No interactions logged yet. Use the app, then refresh.")
    st.stop()

interactions["ts"] = pd.to_datetime(interactions["ts"])

# --- KPI row -----------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total queries", len(interactions))
k2.metric("Avg latency", f"{interactions['latency_ms'].mean():.0f} ms")
k3.metric("Avg out tokens", f"{interactions['tokens_out'].mean():.0f}")
if not feedback.empty:
    up_rate = (feedback["rating"] == "up").mean()
    k4.metric("👍 rate", f"{up_rate:.0%}")

# --- Chart 1: query volume over time ----------------------------------------
st.subheader("1 · Query volume over time")
vol = interactions.set_index("ts").resample("1H").size()
st.line_chart(vol)

# --- Chart 2: latency distribution ------------------------------------------
st.subheader("2 · Latency distribution (ms)")
st.bar_chart(pd.cut(interactions["latency_ms"], bins=10).value_counts().sort_index())

# --- Chart 3: tokens (cost proxy) by model ----------------------------------
st.subheader("3 · Avg output tokens by model")
st.bar_chart(interactions.groupby("model")["tokens_out"].mean())

# --- Chart 4: usage by mode -------------------------------------------------
st.subheader("4 · Queries by mode")
st.bar_chart(interactions["mode"].value_counts())

# --- Chart 5: retrieval quality (top rerank score) --------------------------
st.subheader("5 · Top retrieval score distribution")
st.bar_chart(pd.cut(interactions["top_score"], bins=10).value_counts().sort_index())

# --- Chart 6: feedback breakdown --------------------------------------------
st.subheader("6 · User feedback")
if feedback.empty:
    st.caption("No feedback yet.")
else:
    st.bar_chart(feedback["rating"].value_counts())
