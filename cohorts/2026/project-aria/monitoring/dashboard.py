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
# pd.cut() bins have a pandas IntervalIndex, which Vega-Lite (via st.bar_chart)
# can't serialize — raises SchemaValidationError ("invalid value for `0`").
# Found by actually opening the dashboard; cast the bin labels to str first.
st.subheader("2 · Latency distribution (ms)")
latency_dist = pd.cut(interactions["latency_ms"], bins=10).value_counts().sort_index()
latency_dist.index = latency_dist.index.astype(str)
st.bar_chart(latency_dist)

# --- Chart 3: tokens (cost proxy) by model ----------------------------------
st.subheader("3 · Avg output tokens by model (cost proxy)")
st.caption(
    "Token counts, not $ — convert using your provider's current per-token "
    "pricing page rather than a hardcoded rate baked into this dashboard."
)
st.bar_chart(interactions.groupby("model")["tokens_out"].mean())

# --- Chart 4: usage by mode -------------------------------------------------
st.subheader("4 · Queries by mode")
st.bar_chart(interactions["mode"].value_counts())

# --- Chart 5: retrieval quality (top rerank score) --------------------------
# Same IntervalIndex serialization issue as Chart 2 — see note there.
st.subheader("5 · Top retrieval score distribution")
score_dist = pd.cut(interactions["top_score"], bins=10).value_counts().sort_index()
score_dist.index = score_dist.index.astype(str)
st.bar_chart(score_dist)

# --- Chart 6: feedback breakdown --------------------------------------------
st.subheader("6 · User feedback")
if feedback.empty:
    st.caption("No feedback yet.")
else:
    st.bar_chart(feedback["rating"].value_counts())
