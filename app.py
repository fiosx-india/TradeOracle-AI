
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
        # AI MARKET REPORT
        # ===================================================

        st.subheader("🤖 AI Market Report")

        # ---------------------------------------------------
        # SIGNAL VALIDATION
        # ---------------------------------------------------

        final_signal = signal

        if confidence < 60 or probability < 60:
            final_signal = "HOLD"

        signal_icon = {
            "BUY": "🟢",
            "SELL": "🔴",
            "HOLD": "🟡"
        }.get(final_signal, "⚪")

        with st.container(border=True):

            # ==================================================
            # AI SUMMARY
            # ==================================================

            st.markdown("## 🧠 AI Market Summary")

            if market_mood.startswith("🟢"):
                st.success(summary_text)

            elif market_mood.startswith("🔴"):
                st.error(summary_text)

            else:
                st.warning(summary_text)

            st.divider()

            # ==================================================
            # MARKET SNAPSHOT
            # ==================================================

            st.markdown("### 📊 Market Snapshot")

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric("Market Mood", market_mood)
                st.metric("BUY Signals", buy_count)

            with c2:
                st.metric("AI Confidence", f"{best_confidence:.1f}%")
                st.metric("SELL Signals", sell_count)

            with c3:
                st.metric("Best BUY", best_buy)
                st.metric("Best SELL", best_sell)

            with c4:
                st.metric("News", news_report.overall_sentiment)
                st.metric("F&O Symbols", len(oracle.indices.fno_symbols))

            st.divider()

            # ==================================================
            # AI DECISION
            # ==================================================

            st.markdown("### 🔍 AI Decision")

            left, right = st.columns(2)

            with left:

                st.write(f"**Trend :** {trend}")
                st.write(f"**Momentum :** {momentum}")
                st.write(f"**AI Signal :** {signal_icon} {final_signal}")
                st.write(f"**Confidence :** {confidence:.1f}%")
                st.write(f"**Probability :** {probability:.1f}%")

            with right:

                st.write(f"**Entry :** ₹{entry_price:,.2f}")
                st.write(f"**Stop Loss :** ₹{stop_loss:,.2f}")
                st.write(f"**Target 1 :** ₹{target1:,.2f}")
                st.write(f"**Risk / Reward :** {risk_reward:.2f}")
                st.write(f"**Reason :** {reason}")

            st.divider()

            # ==================================================
            # AI HEALTH CHECK
            # ==================================================

            st.markdown("### 🩺 AI Health Check")

            if final_signal == "HOLD":

                st.warning(f"""
        ### ⚠ Weak Signal

        AI has reduced this signal to **HOLD**.

        • Confidence : **{confidence:.1f}%**
        • Probability : **{probability:.1f}%**

        Recommendation:

        • Wait for trend confirmation.

        • Avoid aggressive BUY / SELL entries.

        • Monitor price action before entering.
        """)

            else:

                st.success(f"""
        ### ✅ Strong Signal

        AI recommends **{final_signal}**

        • Confidence : **{confidence:.1f}%**

        • Probability : **{probability:.1f}%**

        Current signal has acceptable confirmation.
        """)

            st.divider()

            # ==================================================
            # RESERVED EXPANSION AREA
            # ==================================================

            st.markdown("### 🚀 Future AI Modules")

            row1 = st.columns(3)

            with row1[0]:
                st.info("📊 Sector Analysis\n\nReserved")

            with row1[1]:
                st.info("🔥 AI Watchlist\n\nReserved")

            with row1[2]:
                st.info("📈 Strategy Recommendation\n\nReserved")

            row2 = st.columns(3)

            with row2[0]:
                st.info("🚨 Live Alerts\n\nReserved")

            with row2[1]:
                st.info("🗺 Market Heat Map\n\nReserved")

            with row2[2]:
                st.info("📉 Market Breadth\n\nReserved")

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
