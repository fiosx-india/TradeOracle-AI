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

# ---------------- Sidebar ----------------

st.sidebar.title("📊 TradeOracle AI")

page = st.sidebar.radio(
    "Navigation",
    [
        "📈 Market Overview",
        "🏢 F&O Companies",
        "🟢 Buy Signals",
        "🔴 Sell Signals",
    ]
)

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
# ---------------- Pages ----------------

if page == "📈 Market Overview":

    st.dataframe(df, use_container_width=True)

elif page == "🏢 F&O Companies":

    st.header("🏢 F&O Companies")

    company = st.sidebar.selectbox(
        "Select Company",
        sorted(oracle.indices.fno_symbols)
    )

    st.success(company)
    st.info("Company Analysis coming next.")

elif page == "🟢 Buy Signals":

    st.header("🟢 Buy Signals")

    buy_df = df[df["Signal"] == "BUY"]

    st.dataframe(buy_df, use_container_width=True)

elif page == "🔴 Sell Signals":

    st.header("🔴 Sell Signals")

    sell_df = df[df["Signal"] == "SELL"]

    st.dataframe(sell_df, use_container_width=True)

if page == "📈 Market Overview":

    st.subheader("Market Summary")

    for symbol, result in results.items():
        with st.expander(symbol):
            st.write(result["market"])
            st.write(result["signal"])
