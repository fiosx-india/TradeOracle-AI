
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
    interval=60 * 1000,
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

        # ================= AI Market Report =================

        st.subheader("🤖 AI Market Report")

        # ---------------- BUY / SELL ----------------

        buy_df = (
            df[df["Signal"] == "BUY"]
            .sort_values(
                ["Confidence", "Probability"],
                ascending=False,
            )
        )

        sell_df = (
            df[df["Signal"] == "SELL"]
            .sort_values(
                ["Confidence", "Probability"],
                ascending=False,
            )
        )

        # ================= AI Market Report =================

        st.subheader("🤖 AI Market Report")

        # ---------------- BUY / SELL ----------------

        buy_df = (
            df[df["Signal"] == "BUY"]
            .sort_values(
                ["Confidence", "Probability"],
                ascending=False,
            )
        )

        sell_df = (
            df[df["Signal"] == "SELL"]
            .sort_values(
                ["Confidence", "Probability"],
                ascending=False,
            )
        )

        news_report = next(iter(results.values()))["news"]

        buy_count = len(buy_df)
        sell_count = len(sell_df)

        if buy_count > sell_count:
            market_mood = "🟢 Bullish"
        elif sell_count > buy_count:
            market_mood = "🔴 Bearish"
        else:
            market_mood = "🟡 Sideways"

        best_buy = buy_df.iloc[0]["Index"] if not buy_df.empty else "-"
        best_sell = sell_df.iloc[0]["Index"] if not sell_df.empty else "-"

        best_confidence = (
            buy_df.iloc[0]["Confidence"]
            if not buy_df.empty
            else 0
        )

        # ================= REPORT =================

        with st.container(border=True):

            left, right = st.columns([2.4, 1.2])

            # ---------- LEFT ----------
            with left:

                st.markdown("### 🧠 AI Market Summary")

                if market_mood.startswith("🟢"):

                    st.success(
                        f"""
        ### Market Overview

        **Market Mood :** {market_mood}

        **Best BUY :** {best_buy}

        **BUY Signals :** {buy_count}

        **News :** {news_report.overall_sentiment}

        **AI Confidence :** {best_confidence}%

        ---

        The market is showing bullish momentum.

        AI recommends focusing on high-confidence BUY opportunities.

        Current strongest candidate is **{best_buy}**.
        """
                    )

                elif market_mood.startswith("🔴"):

                    st.error(
                        f"""
        ### Market Overview

        **Market Mood :** {market_mood}

        **Best SELL :** {best_sell}

        **SELL Signals :** {sell_count}

        **News :** {news_report.overall_sentiment}

        ---

        Market remains under selling pressure.

        AI recommends defensive positioning.

        Current strongest SELL candidate is **{best_sell}**.
        """
                    )

                else:

                    st.warning(
                        """
        ### Market Overview

        Market is moving sideways.

        No strong trend detected.

        Wait for confirmation before taking positions.
        """
                    )

            # ---------- RIGHT ----------
            with right:

                st.metric("Market Mood", market_mood)
                st.metric("AI Confidence", f"{best_confidence}%")

                st.metric("BUY Signals", buy_count)
                st.metric("SELL Signals", sell_count)

                st.metric("Best BUY", best_buy)
                st.metric("Best SELL", best_sell)

                st.metric("News", news_report.overall_sentiment)

                st.metric(
                    "F&O Companies",
                    len(oracle.indices.fno_symbols)
                )

        st.divider()

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
