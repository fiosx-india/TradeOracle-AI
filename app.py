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

st.sidebar.divider()

st.sidebar.subheader("🏢 F&O Companies")

company = st.sidebar.selectbox(
    "Select Company",
    sorted(oracle.indices.fno_symbols)
)

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

st.sidebar.divider()

st.sidebar.subheader("🏢 F&O Companies")

company = st.sidebar.selectbox(
    "Select Company",
    sorted(oracle.indices.fno_symbols)
)

# ---------------- Pages ----------------

if page == "📈 Market Overview":

    st.header("📈 Market Overview")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🟢 Top BUY")
        buy_df = (
            df[df["Signal"] == "BUY"]
            .sort_values("Confidence", ascending=False)
            .head(10)
        )
        st.dataframe(
            buy_df[["Index", "Last Price", "Confidence", "Probability", "Reason"]],
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.subheader("🔴 Top SELL")
        sell_df = (
            df[df["Signal"] == "SELL"]
            .sort_values("Confidence", ascending=False)
            .head(10)
        )
        st.dataframe(
            sell_df[["Index", "Last Price", "Confidence", "Probability", "Reason"]],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")
    st.subheader("📊 Market Summary")

    for symbol, result in results.items():
        with st.expander(f"🔹 {symbol}", expanded=False):
            st.write(result.get("market", "No market data"))
            st.write(result.get("signal", "No signal data"))

elif page == "🏢 F&O Companies":

    st.header("🏢 F&O Companies")

    # Company Selection
    company_list = sorted(df["Index"].unique().tolist()) if "Index" in df.columns else []
    company = st.selectbox(
        "Select Company",
        options=company_list,
        key="fno_company_select"
    )

    if company:
        st.markdown("---")
        st.subheader(f"📌 {company}")
        st.success(f"**Selected Company :** {company}")

        # F&O Status
        if oracle.indices.is_fno_symbol(company):
            st.success("✅ F&O Eligible Company")
        else:
            st.error("❌ Not an F&O Company")

        st.info("🤖 Company AI Analysis coming soon.")
    else:
        st.warning("Please select a company to view details.")

elif page == "🟢 Buy Signals":

    st.header("🟢 Buy Signals")
    st.markdown("High confidence BUY opportunities sorted by confidence score.")

    buy_df = (
        df[df["Signal"] == "BUY"]
        .sort_values("Confidence", ascending=False)
    )

    st.dataframe(
        buy_df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(f"Total Buy Signals: **{len(buy_df)}**")

elif page == "🔴 Sell Signals":

    st.header("🔴 Sell Signals")
    st.markdown("High confidence SELL opportunities sorted by confidence score.")

    sell_df = (
        df[df["Signal"] == "SELL"]
        .sort_values("Confidence", ascending=False)
    )

    st.dataframe(
        sell_df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(f"Total Sell Signals: **{len(sell_df)}**")
