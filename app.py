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

# ==========================================================
# AI SIGNAL DEBUG
# ==========================================================

print("\n================= AI SIGNAL DEBUG =================\n")

print(f"Total Results : {len(results)}")
print(f"Total F&O     : {len(oracle.indices.fno_symbols)}")

for symbol, result in results.items():

    market = result["market"]
    signal = result["signal"]
    movement = result.get("movement")

    print(f"\n{'='*70}")
    print(f"Symbol       : {symbol}")
    print(f"Trend        : {market.trend}")
    print(f"Momentum     : {market.momentum}")
    print(f"Signal       : {signal.signal}")
    print(f"Confidence   : {signal.confidence:.2f}%")
    print(f"Probability  : {signal.probability:.2f}%")

    if movement:
        print(f"AI Status    : {movement.ai_movement_status}")
        print(f"Movement     : {movement.movement_strength:.2f}%")
        print(f"Buying       : {movement.buying_pressure:.2f}%")
        print(f"Selling      : {movement.selling_pressure:.2f}%")
        print(f"Continuation : {movement.trend_continuation_chance:.2f}%")

print("\n================= END DEBUG =================\n")

st.sidebar.divider()

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

        # ==========================================================
        # AI SUMMARY VALUES
        # ==========================================================

        buy_count = len(buy_df)
        sell_count = len(sell_df)

        best_confidence = 0

        if not buy_df.empty:
            best_confidence = max(best_confidence, float(buy_df["Confidence"].max()))

        if not sell_df.empty:
            best_confidence = max(best_confidence, float(sell_df["Confidence"].max()))

        if buy_count > sell_count:
            market_mood = "🟢 Bullish"
        elif sell_count > buy_count:
            market_mood = "🔴 Bearish"
        else:
            market_mood = "🟡 Neutral"

        summary_text = (
            f"BUY Signals : {buy_count} | "
            f"SELL Signals : {sell_count} | "
            f"Best Confidence : {best_confidence:.0f}%"
        )

        # ==========================================================
        # 🤖 AI COMMAND CENTER
        # ==========================================================

        st.markdown("---")

        title_col, action_col = st.columns([8, 1])

        with title_col:
            st.subheader("🤖 AI Command Center")

        with action_col:
            st.download_button(
                "📄",
                data=summary_text,
                file_name="TradeOracle_AI_Summary.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # ==========================================================
        # MARKET HEALTH
        # ==========================================================

        m1, m2, m3, m4, m5, m6 = st.columns(6)

        with m1:
            st.metric("Market Mood", market_mood)

        with m2:
            st.metric("AI Confidence", f"{best_confidence:.0f}%")

        with m3:
            st.metric("BUY", buy_count)

        with m4:
            st.metric("SELL", sell_count)

        with m5:
            st.metric("News", "N/A")

        with m6:
            st.metric("F&O", len(oracle.indices.fno_symbols))

        st.divider()

        # ==========================================================
        # MARKET OVERVIEW
        # ==========================================================

        st.markdown("### 🧠 AI Market Overview")

        if market_mood.startswith("🟢"):
            st.success(summary_text)

        elif market_mood.startswith("🔴"):
            st.error(summary_text)

        else:
            st.warning(summary_text)

        st.divider()

        # ==========================================================
        # LIVE INDEX SIGNALS
        # ==========================================================

        st.markdown("### 📈 Live Index Signals")

        symbols = list(results.items())

        for row in range(0, len(symbols), 3):

            cols = st.columns(3)

            for col, (symbol, result) in zip(cols, symbols[row:row + 3]):

                signal = result["signal"]
                market = result["market"]
                movement = result.get("movement")

                icon = {
                    "BUY": "🟢",
                    "SELL": "🔴",
                    "HOLD": "🟡"
                }.get(signal.signal, "⚪")

                trend_icon = {
                    "BULLISH": "⬆",
                    "BEARISH": "⬇",
                    "SIDEWAYS": "➡"
                }.get(market.trend, "➡")

                if movement:
                    status = movement.ai_movement_status
                    move = f"{movement.movement_strength:.0f}%"
                    cont = f"{movement.trend_continuation_chance:.0f}%"
                    timing = movement.entry_timing
                else:
                    status = "--"
                    move = "--"
                    cont = "--"
                    timing = "--"

                with col:

                    with st.container(border=True):

                        st.markdown(
                            f"""
        **{icon} {symbol}**

        **{signal.signal}** • {signal.confidence:.0f}%

        {trend_icon} {move}

        ⚡ {timing}
        """
                        )

                        if st.button(
                            "Details",
                            key=f"details_{symbol}",
                            use_container_width=True,
                        ):

                            st.write(f"**Trend :** {market.trend}")
                            st.write(f"**Momentum :** {market.momentum}")

                            st.write(f"**Confidence :** {signal.confidence:.0f}%")
                            st.write(f"**Probability :** {signal.probability:.0f}%")

                            st.divider()

                            st.write(f"**Entry :** ₹{signal.entry_price:,.2f}")
                            st.write(f"**Target :** ₹{signal.target1:,.2f}")
                            st.write(f"**Stop Loss :** ₹{signal.stoploss:,.2f}")

                            if movement:

                                st.divider()

                                st.write(f"**AI Status :** {status}")
                                st.write(f"**Movement :** {move}")
                                st.write(f"**Buying :** {movement.buying_pressure:.0f}%")
                                st.write(f"**Selling :** {movement.selling_pressure:.0f}%")
                                st.write(f"**Continuation :** {cont}")

                                st.write(f"**Breakout :** {movement.breakout_chance:.0f}%")
                                st.write(f"**Breakdown :** {movement.breakdown_chance:.0f}%")

                                st.write(f"**Target-1 :** {movement.target1_reach_confidence:.0f}%")
                                st.write(f"**Target-2 :** {movement.target2_reach_confidence:.0f}%")
                                st.write(f"**Target-3 :** {movement.target3_reach_confidence:.0f}%")

                                st.write(f"**False Signal :** {movement.false_signal_risk:.0f}%")

                                st.divider()

                                st.write(f"**Entry Timing :** {movement.entry_timing}")
                                st.write(f"**Exit Timing :** {movement.exit_timing}")

                                st.write(f"**Market Energy :** {movement.market_energy:.0f}%")
                                st.write(f"**Volatility :** {movement.volatility_state}")

                                st.info(movement.ai_observation)


        # ==========================================================
        # TOP AI PICKS
        # ==========================================================

        left, right = st.columns(2)

        with left:

            st.markdown("### 🟢 Strong BUY")

            if not buy_df.empty:

                st.dataframe(
                    buy_df[
                        [
                            "Index",
                            "Confidence",
                            "Probability"
                        ]
                    ].head(5),
                    hide_index=True,
                    use_container_width=True,
                )

        with right:

            st.markdown("### 🔴 Strong SELL")

            if not sell_df.empty:

                st.dataframe(
                    sell_df[
                        [
                            "Index",
                            "Confidence",
                            "Probability"
                        ]
                    ].head(5),
                    hide_index=True,
                    use_container_width=True,
                )

        st.divider()

        # ==========================================================
        # AI STATUS
        # ==========================================================

        if best_confidence >= 80:

            st.success("✅ AI Engine Status : Excellent")

        elif best_confidence >= 60:

            st.info("🟢 AI Engine Status : Good")

        elif best_confidence >= 40:

            st.warning("🟡 AI Engine Status : Moderate")

        else:

            st.error("🔴 AI Engine Status : Weak")
            
    st.subheader("📊 Market Summary")

    for symbol, result in results.items():

        market = result["market"]
        signal = result["signal"]
        movement = result.get("movement")

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
