
import streamlit as st
import pandas as pd

from oracle_core import TradeOracle
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="TradeOracle AI",
    page_icon="📈",
    layout="wide"
)

st_autorefresh(
    interval=60000,   # 60 seconds
    key="tradeoracle_refresh"
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

companies = sorted(oracle.indices.fno_symbols)

st.sidebar.metric("F&O Companies", len(companies))

search = st.sidebar.text_input(
    "",
    placeholder="🔍 Search Company",
    label_visibility="collapsed"
)

filtered_companies = [
    c for c in companies
    if search.upper() in c.upper()
]

selected_company = st.sidebar.selectbox(
    "",
    filtered_companies,
    label_visibility="collapsed"
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
# ---------------- Pages ----------------

if page == "📈 Market Overview":

    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🟢 Top BUY")

        buy_df = (
            df[df["Signal"] == "BUY"]
            .sort_values("Confidence", ascending=False)
            .head(10)
        )

        st.dataframe(
            buy_df[
                [
                    "Index",
                    "Last Price",
                    "Confidence",
                    "Probability",
                    "Reason"
                ]
            ],
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
            sell_df[
                [
                    "Index",
                    "Last Price",
                    "Confidence",
                    "Probability",
                    "Reason"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )


        # ===================================================
        # SAFE AI VALUES
        # ===================================================

        selected = buy_df.iloc[0] if not buy_df.empty else (
            sell_df.iloc[0] if not sell_df.empty else None
        )

        if selected is not None:

            trend = selected.get("Trend", "-")
            momentum = selected.get("Momentum", "-")
            signal = selected.get("Signal", "HOLD")

            confidence = float(selected.get("Confidence", 0))
            probability = float(selected.get("Probability", 0))

            entry_price = float(selected.get("Last Price", 0))

            stop_loss = float(selected.get("Stop Loss", 0))
            target1 = float(selected.get("Target 1", 0))

            risk_reward = float(selected.get("Risk Reward", 0))

            reason = selected.get("Reason", "-")

        else:

            trend = "-"
            momentum = "-"
            signal = "HOLD"

            confidence = 0.0
            probability = 0.0

            entry_price = 0.0
            stop_loss = 0.0
            target1 = 0.0

            risk_reward = 0.0

            reason = "No Signal"

            # ===================================================
            # SIGNAL VALIDATION
            # ===================================================

            final_signal = signal

            if confidence < 60 or probability < 60:
                final_signal = "HOLD"

            signal_icon = {
                "BUY": "🟢",
                "SELL": "🔴",
                "HOLD": "🟡",
            }.get(final_signal, "⚪")


    st.subheader("📊 Market Summary")

    for symbol, result in results.items():

        market = result["market"]
        signal = result["signal"]

        with st.expander(symbol):

            st.write(f"**Trend :** {market.trend}")
            st.write(f"**Momentum :** {market.momentum}")

            st.write(f"**Signal :** {signal.signal}")
            st.write(f"**Confidence :** {signal.confidence}%")
            st.write(f"**Probability :** {signal.probability}%")

            st.write(f"**Entry Price :** {signal.entry_price:.2f}")

            st.write(f"**Target 1 :** {signal.target1:.2f}")
            st.write(f"**Target 2 :** {signal.target2:.2f}")
            st.write(f"**Target 3 :** {signal.target3:.2f}")

            st.write(f"**Stop Loss :** {signal.stoploss:.2f}")

            st.write(f"**Risk / Reward :** {signal.risk_reward}")

            st.write(f"**Reason :** {signal.reason}")

            st.write(f"**Risk Level :** {signal.risk_level}")

elif page == "🏢 F&O Companies":

    st.header("🏢 F&O Companies")

    st.header(selected_company)

    st.success(f"Selected Company : {selected_company}")

    if oracle.indices.is_fno_symbol(selected_company):
        
        st.success("✅ F&O Eligible Company")
    else:
        st.error("❌ Not an F&O Company")
        
    st.divider()
    
    company_result = results.get(selected_company)
    if company_result:
            
            idx = company_result["index"]
            market = company_result["market"]
            signal = company_result["signal"]

            st.subheader(f"📈 {selected_company}")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Last Price", f"{idx.last_price:,.2f}")
                st.metric("Change %", f"{idx.change_percent:.2f}%")
                st.metric("Trend", market.trend)
                st.metric("Momentum", market.momentum)

            with col2:
                st.metric("Signal", signal.signal)
                st.metric("Confidence", f"{signal.confidence}%")
                st.metric("Probability", f"{signal.probability}%")
                st.metric("Risk", signal.risk_level)
                st.metric("Market Score", f"{signal.market_score:.2f}")

            st.divider()

            c1, c2 = st.columns(2)

            with c1:
                st.metric("Entry", f"{signal.entry_price:.2f}")
                st.metric("Target 1", f"{signal.target1:.2f}")
                st.metric("Target 2", f"{signal.target2:.2f}")
                st.metric("Expected Time", signal.expected_time)

            with c2:
                st.metric("Stop Loss", f"{signal.stoploss:.2f}")
                st.metric("Target 3", f"{signal.target3:.2f}")
                st.metric("Risk / Reward", f"{signal.risk_reward:.2f}")

            st.divider()

            st.subheader("🤖 AI Reason")
            st.info(signal.reason)

    else:
        st.warning("No analysis available for this company.")
            
elif page == "🟢 Buy Signals":

    st.header("🟢 Buy Signals")

    buy_df = (
        df[df["Signal"] == "BUY"]
        .sort_values("Confidence", ascending=False)
    )

    st.dataframe(
        buy_df,
        use_container_width=True,
        hide_index=True
    )

elif page == "🔴 Sell Signals":

    st.header("🔴 Sell Signals")

    sell_df = (
        df[df["Signal"] == "SELL"]
        .sort_values("Confidence", ascending=False)
    )

    st.dataframe(
        sell_df,
        use_container_width=True,
        hide_index=True
        )
