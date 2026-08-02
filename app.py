import streamlit as st
import pandas as pd

from oracle_core import TradeOracle

st.set_page_config(
    page_title="TradeOracle AI",
    page_icon="📈",
    layout="wide"
)

st.title("📈 TradeOracle AI Dashboard")
st.caption("Indian Market Intelligence")

oracle = TradeOracle()
results = oracle.analyze()

if not results:
    st.error("No market data available.")
    st.stop()

rows = []

for symbol, result in results.items():
    idx = result["index"]
    market = result["market"]
    signal = result["signal"]

    rows.append({
        "Index": symbol,
        "Last Price": idx.last_price,
        "Change %": idx.change_percent,
        "Trend": market.trend,
        "Momentum": market.momentum,
        "Signal": signal.signal,
        "Confidence": signal.confidence,
        "Probability": signal.probability,
        "Reason": signal.reason,
    })

df = pd.DataFrame(rows)

st.dataframe(df, use_container_width=True)

st.subheader("Market Summary")

for symbol, result in results.items():
    with st.expander(symbol):
        st.write(result["market"])
        st.write(result["signal"])
