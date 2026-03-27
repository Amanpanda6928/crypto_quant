"""
Streamlit Dashboard - Fixed (Multi-Asset Compatible)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.api import fetch_current_data
from model.predict import Predictor
from features.pipeline import FeaturePipeline


# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Crypto Quant Research System",
    page_icon="📈",
    layout="wide"
)

# =========================
# STYLE
# =========================

st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
}
.metric-card {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
}
.signal-buy { color: green; font-weight: bold; }
.signal-sell { color: red; font-weight: bold; }
.signal-hold { color: orange; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# =========================
# CHARTS
# =========================

def create_candlestick_chart(df):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df["open_time"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"]
    ))

    if "ema_20" in df.columns:
        fig.add_trace(go.Scatter(x=df["open_time"], y=df["ema_20"], name="EMA20"))

    if "ema_50" in df.columns:
        fig.add_trace(go.Scatter(x=df["open_time"], y=df["ema_50"], name="EMA50"))

    fig.update_layout(height=500)
    return fig


def create_prediction_chart(preds):
    fig = make_subplots(rows=1, cols=len(preds),
                       specs=[[{"type": "indicator"}]*len(preds)])

    for i, (h, (p, s)) in enumerate(preds.items(), 1):
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=p*100,
            title={"text": h},
            gauge={"axis": {"range": [0, 100]}}
        ), row=1, col=i)

    return fig


# =========================
# MAIN
# =========================

def main():

    st.markdown('<div class="main-header">Crypto Quant Dashboard</div>', unsafe_allow_html=True)

    # Sidebar
    asset = st.sidebar.selectbox(
        "Select Asset",
        ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT"]
    )

    lookback = st.sidebar.slider("Lookback", 100, 1000, 500)

    refresh = st.sidebar.button("Refresh")

    auto = st.sidebar.checkbox("Auto Refresh (5s)")

    if refresh:
        st.cache_data.clear()
        st.rerun()

    if auto:
        time.sleep(5)
        st.rerun()

    # =========================
    # DATA
    # =========================

    df = fetch_current_data(asset, lookback=lookback)

    # 🔥 CRITICAL FIX
    df["symbol"] = asset

    pipeline = FeaturePipeline()
    df_features = pipeline.transform(df)

    # =========================
    # METRICS
    # =========================

    price = df["close"].iloc[-1]
    change = (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2] * 100

    col1, col2 = st.columns(2)

    col1.metric("Price", f"${price:.2f}", f"{change:.2f}%")

    if "rsi_14" in df_features.columns:
        rsi = df_features["rsi_14"].iloc[-1]
        col2.metric("RSI", f"{rsi:.2f}")

    # =========================
    # PREDICTIONS
    # =========================

    st.subheader("Predictions")

    predictor = Predictor()
    preds = predictor.predict_single(asset)

    cols = st.columns(len(preds))

    for i, (h, (p, s)) in enumerate(preds.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
            <h4>{h}</h4>
            <h2>{p:.2%}</h2>
            <p class="signal-{s.lower()}">{s}</p>
            </div>
            """, unsafe_allow_html=True)

    st.plotly_chart(create_prediction_chart(preds), use_container_width=True)

    # =========================
    # CHART
    # =========================

    st.subheader("Price Chart")
    st.plotly_chart(create_candlestick_chart(df_features), use_container_width=True)


if __name__ == "__main__":
    main()