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
        "🪙 Commodities",
        "🟢 Buy Signals",
        "🔴 Sell Signals",
    ]
)

oracle = TradeOracle()
results = oracle.analyze()


# ==========================================================
# COMMODITY AI RESULTS
# ==========================================================

commodity_results = {}

try:

    if hasattr(oracle, "commodity_engine") and hasattr(oracle, "commodity_ai"):

        commodity_engine = oracle.commodity_engine
        commodity_ai = oracle.commodity_ai

        commodity_engine.refresh_if_needed()

        commodities = commodity_engine.get_all_commodities()

        commodity_results = (
            commodity_ai.attach_movement_assessments(
                commodities
            )
        )

except Exception as exc:

    commodity_results = {}

    print(f"[Commodity AI] {exc}")

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

if not results and page != "🪙 Commodities":
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

        report_text = summary_text + "\n\n"

        for symbol, result in results.items():

            signal = result["signal"]
            market = result["market"]

            report_text += (
                f"{symbol} | "
                f"{signal.signal} | "
                f"{signal.confidence:.0f}% | "
                f"{signal.probability:.0f}% | "
                f"{market.trend} | "
                f"Entry:{signal.entry_price:.2f} | "
                f"Target:{signal.target1:.2f} | "
                f"SL:{signal.stoploss:.2f}\n"
            )

        title_col, action_col = st.columns([8, 1])

        with title_col:
            st.markdown("### 📈 Live Index Signals")

        with action_col:
            st.download_button(
                "📄",
                data=report_text,
                file_name="TradeOracle_AI_Report.txt",
                mime="text/plain",
                use_container_width=True,
                key="download_ai_report"
            )

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
# ==========================================================
# COMMODITY DASHBOARD
# ==========================================================

elif page == "🪙 Commodities":

    st.header("🪙 Commodity AI Dashboard")

    # ------------------------------------------------------
    # NO DATA
    # ------------------------------------------------------

    if not commodity_results:
        st.warning("No commodity data available.")
        st.stop()

    # ======================================================
    # 🔧 COMMODITY AI DIAGNOSTICS
    # ======================================================

    with st.expander(
        "🔧 Commodity AI Diagnostics",
        expanded=True,
    ):

        st.caption(
            "Raw market data → CommodityQuote → Engine → AI calculation "
            "→ Final assessment"
        )

        diagnostic_rows = []

        for symbol, quote in commodity_results.items():

            movement = quote.movement_assessment

            diagnostic_rows.append({
                # ------------------------------------------
                # IDENTIFICATION
                # ------------------------------------------
                "Symbol": quote.symbol,
                "Name": quote.name,

                # ------------------------------------------
                # RAW MARKET DATA
                # ------------------------------------------
                "Last Price": quote.last_price,
                "Change": quote.change,
                "Change %": quote.change_percent,
                "Open": quote.open_price,
                "High": quote.high_price,
                "Low": quote.low_price,
                "Volume": quote.volume,

                # ------------------------------------------
                # DATA METADATA
                # ------------------------------------------
                "Exchange": quote.exchange,
                "Currency": quote.currency,
                "Timestamp": (
                    quote.timestamp.isoformat()
                    if quote.timestamp is not None
                    else None
                ),

                # ------------------------------------------
                # AI EVIDENCE
                # ------------------------------------------
                "Trend Strength": (
                    movement.evidence.trend_strength
                    if movement and movement.evidence
                    else None
                ),

                "Buying Pressure": (
                    movement.evidence.buying_pressure
                    if movement and movement.evidence
                    else None
                ),

                "Selling Pressure": (
                    movement.evidence.selling_pressure
                    if movement and movement.evidence
                    else None
                ),

                "Breakout Probability": (
                    movement.evidence.breakout_probability
                    if movement and movement.evidence
                    else None
                ),

                "Target Confidence": (
                    movement.evidence.target_confidence
                    if movement and movement.evidence
                    else None
                ),

                # ------------------------------------------
                # FINAL AI OUTPUT
                # ------------------------------------------
                "AI Status": (
                    movement.ai_movement_status
                    if movement
                    else None
                ),

                "Movement Strength": (
                    movement.movement_strength
                    if movement
                    else None
                ),

                "Confidence": (
                    movement.movement_confidence_index
                    if movement
                    else None
                ),

                "Trend Continuation": (
                    movement.trend_continuation_chance
                    if movement
                    else None
                ),

                "Trend Reversal": (
                    movement.trend_reversal_chance
                    if movement
                    else None
                ),

                "Breakout": (
                    movement.breakout_chance
                    if movement
                    else None
                ),

                "Breakdown": (
                    movement.breakdown_chance
                    if movement
                    else None
                ),

                "Target 1": (
                    movement.target1_reach_confidence
                    if movement
                    else None
                ),

                "Target 2": (
                    movement.target2_reach_confidence
                    if movement
                    else None
                ),

                "Target 3": (
                    movement.target3_reach_confidence
                    if movement
                    else None
                ),

                "Market Energy": (
                    movement.market_energy
                    if movement
                    else None
                ),

                "Volatility": (
                    movement.volatility_state
                    if movement
                    else None
                ),

                "Signal Stability": (
                    movement.signal_stability
                    if movement
                    else None
                ),

                "False Signal Risk": (
                    movement.false_signal_risk
                    if movement
                    else None
                ),

                "Entry Timing": (
                    movement.entry_timing
                    if movement
                    else None
                ),

                "Exit Timing": (
                    movement.exit_timing
                    if movement
                    else None
                ),
            })

        diagnostic_df = pd.DataFrame(diagnostic_rows)

        # --------------------------------------------------
        # ENGINE / DATA SUMMARY
        # --------------------------------------------------

        d1, d2, d3, d4 = st.columns(4)

        with d1:
            st.metric(
                "Commodities Received",
                len(commodity_results),
            )

        with d2:
            st.metric(
                "AI Assessments",
                sum(
                    1
                    for quote in commodity_results.values()
                    if quote.movement_assessment is not None
                ),
            )

        with d3:
            st.metric(
                "Engine Cache",
                "Available"
                if hasattr(oracle, "commodity_engine")
                else "Unavailable",
            )

        with d4:

            if hasattr(oracle, "commodity_engine"):

                try:
                    cache_valid = (
                        oracle.commodity_engine.is_cache_valid()
                    )

                    st.metric(
                        "Cache Valid",
                        "YES" if cache_valid else "NO",
                    )

                except Exception:
                    st.metric(
                        "Cache Valid",
                        "ERROR",
                    )

            else:
                st.metric(
                    "Cache Valid",
                    "N/A",
                )

        st.divider()

        # --------------------------------------------------
        # FULL DIAGNOSTIC TABLE
        # --------------------------------------------------

        st.markdown("### 🔍 Complete Commodity Diagnostic Data")

        st.dataframe(
            diagnostic_df,
            use_container_width=True,
            hide_index=True,
        )

        # --------------------------------------------------
        # INDIVIDUAL COMMODITY DIAGNOSTIC
        # --------------------------------------------------

        st.markdown("### 🧪 Individual Commodity Analysis")

        diagnostic_symbol = st.selectbox(
            "Select commodity to inspect",
            sorted(commodity_results.keys()),
            key="commodity_diagnostic_symbol",
        )

        diagnostic_quote = commodity_results[
            diagnostic_symbol
        ]

        diagnostic_movement = (
            diagnostic_quote.movement_assessment
        )

        if diagnostic_movement:

            st.markdown(
                f"#### {diagnostic_quote.name} "
                f"({diagnostic_quote.symbol})"
            )

            # ----------------------------------------------
            # RAW DATA
            # ----------------------------------------------

            st.markdown("##### 1️⃣ Raw Market Data")

            r1, r2, r3, r4 = st.columns(4)

            with r1:
                st.metric(
                    "Last Price",
                    f"{diagnostic_quote.last_price:,.2f}",
                )

                st.metric(
                    "Change",
                    f"{diagnostic_quote.change:,.2f}",
                )

            with r2:
                st.metric(
                    "Change %",
                    f"{diagnostic_quote.change_percent:.2f}%",
                )

                st.metric(
                    "Volume",
                    f"{diagnostic_quote.volume:,}",
                )

            with r3:
                st.metric(
                    "Open",
                    f"{diagnostic_quote.open_price:,.2f}",
                )

                st.metric(
                    "High",
                    f"{diagnostic_quote.high_price:,.2f}",
                )

            with r4:
                st.metric(
                    "Low",
                    f"{diagnostic_quote.low_price:,.2f}",
                )

                st.metric(
                    "Exchange",
                    diagnostic_quote.exchange,
                )

            st.divider()

            # ----------------------------------------------
            # AI EVIDENCE
            # ----------------------------------------------

            st.markdown("##### 2️⃣ AI Evidence")

            evidence = diagnostic_movement.evidence

            if evidence:

                e1, e2, e3, e4, e5 = st.columns(5)

                with e1:
                    st.metric(
                        "Trend Strength",
                        f"{evidence.trend_strength:.2f}%",
                    )

                with e2:
                    st.metric(
                        "Buying Pressure",
                        f"{evidence.buying_pressure:.2f}%",
                    )

                with e3:
                    st.metric(
                        "Selling Pressure",
                        f"{evidence.selling_pressure:.2f}%",
                    )

                with e4:
                    st.metric(
                        "Breakout Probability",
                        f"{evidence.breakout_probability:.2f}%",
                    )

                with e5:
                    st.metric(
                        "Target Confidence",
                        f"{evidence.target_confidence:.2f}%",
                    )

            else:

                st.warning(
                    "No AI evidence object is attached."
                )

            st.divider()

            # ----------------------------------------------
            # FINAL AI OUTPUT
            # ----------------------------------------------

            st.markdown("##### 3️⃣ Final AI Assessment")

            a1, a2, a3, a4 = st.columns(4)

            with a1:
                st.metric(
                    "AI Status",
                    diagnostic_movement.ai_movement_status,
                )

            with a2:
                st.metric(
                    "Movement Strength",
                    f"{diagnostic_movement.movement_strength:.2f}%",
                )

            with a3:
                st.metric(
                    "Confidence",
                    f"{diagnostic_movement.movement_confidence_index:.2f}%",
                )

            with a4:
                st.metric(
                    "Market Energy",
                    f"{diagnostic_movement.market_energy:.2f}%",
                )

            a5, a6, a7, a8 = st.columns(4)

            with a5:
                st.metric(
                    "Trend Continuation",
                    f"{diagnostic_movement.trend_continuation_chance:.2f}%",
                )

            with a6:
                st.metric(
                    "Trend Reversal",
                    f"{diagnostic_movement.trend_reversal_chance:.2f}%",
                )

            with a7:
                st.metric(
                    "Breakout",
                    f"{diagnostic_movement.breakout_chance:.2f}%",
                )

            with a8:
                st.metric(
                    "Breakdown",
                    f"{diagnostic_movement.breakdown_chance:.2f}%",
                )

            st.divider()

            # ----------------------------------------------
            # TARGET / RISK OUTPUT
            # ----------------------------------------------

            st.markdown("##### 4️⃣ Target & Signal Quality")

            t1, t2, t3, t4 = st.columns(4)

            with t1:
                st.metric(
                    "Target 1 Confidence",
                    f"{diagnostic_movement.target1_reach_confidence:.2f}%",
                )

            with t2:
                st.metric(
                    "Target 2 Confidence",
                    f"{diagnostic_movement.target2_reach_confidence:.2f}%",
                )

            with t3:
                st.metric(
                    "Target 3 Confidence",
                    f"{diagnostic_movement.target3_reach_confidence:.2f}%",
                )

            with t4:
                st.metric(
                    "False Signal Risk",
                    f"{diagnostic_movement.false_signal_risk:.2f}%",
                )

            q1, q2, q3, q4 = st.columns(4)

            with q1:
                st.metric(
                    "Signal Stability",
                    f"{diagnostic_movement.signal_stability:.2f}%",
                )

            with q2:
                st.metric(
                    "Volatility",
                    diagnostic_movement.volatility_state,
                )

            with q3:
                st.metric(
                    "Entry Timing",
                    diagnostic_movement.entry_timing,
                )

            with q4:
                st.metric(
                    "Exit Timing",
                    diagnostic_movement.exit_timing,
                )

            st.divider()

            # ----------------------------------------------
            # AI OBSERVATION
            # ----------------------------------------------

            st.markdown("##### 5️⃣ AI Observation")

            st.info(
                diagnostic_movement.ai_observation
            )

            # ----------------------------------------------
            # TIMESTAMP
            # ----------------------------------------------

            st.caption(
                f"Quote Timestamp: "
                f"{diagnostic_quote.timestamp.isoformat()}"
            )

    # ======================================================
    # NORMAL COMMODITY TABLE
    # ======================================================

    st.markdown("### 📊 Commodity Overview")

    rows = []

    for symbol, quote in commodity_results.items():

        movement = quote.movement_assessment

        rows.append({
            "Commodity": quote.name,
            "Symbol": quote.symbol,
            "Price": quote.last_price,
            "Change %": quote.change_percent,
            "AI Status": (
                movement.ai_movement_status
                if movement
                else "--"
            ),
            "Movement": (
                movement.movement_strength
                if movement
                else None
            ),
            "Confidence": (
                movement.movement_confidence_index
                if movement
                else None
            ),
            "Buying": (
                movement.buying_pressure
                if movement
                else None
            ),
            "Selling": (
                movement.selling_pressure
                if movement
                else None
            ),
            "Breakout": (
                movement.breakout_chance
                if movement
                else None
            ),
        })

    commodity_df = pd.DataFrame(rows)

    st.dataframe(
        commodity_df,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # ======================================================
    # COMMODITY DETAILS
    # ======================================================

    for symbol, quote in commodity_results.items():

        movement = quote.movement_assessment

        with st.expander(
            f"{quote.name} ({symbol})"
        ):

            if movement is None:
                st.warning(
                    "No movement assessment available."
                )
                continue

            c1, c2 = st.columns(2)

            with c1:

                st.metric(
                    "Last Price",
                    f"{quote.last_price:.2f}",
                )

                st.metric(
                    "Change %",
                    f"{quote.change_percent:.2f}%",
                )

                st.metric(
                    "AI Status",
                    movement.ai_movement_status,
                )

                st.metric(
                    "Confidence",
                    f"{movement.movement_confidence_index:.2f}%",
                )

                st.metric(
                    "Movement",
                    f"{movement.movement_strength:.2f}%",
                )

            with c2:

                st.metric(
                    "Buying",
                    f"{movement.buying_pressure:.2f}%",
                )

                st.metric(
                    "Selling",
                    f"{movement.selling_pressure:.2f}%",
                )

                st.metric(
                    "Breakout",
                    f"{movement.breakout_chance:.2f}%",
                )

                st.metric(
                    "Breakdown",
                    f"{movement.breakdown_chance:.2f}%",
                )

                st.metric(
                    "False Signal",
                    f"{movement.false_signal_risk:.2f}%",
                )

            st.divider()

            st.write(
                f"**Entry Timing:** "
                f"{movement.entry_timing}"
            )

            st.write(
                f"**Exit Timing:** "
                f"{movement.exit_timing}"
            )

            st.write(
                f"**Trend Continuation:** "
                f"{movement.trend_continuation_chance:.2f}%"
            )

            st.write(
                f"**Trend Reversal:** "
                f"{movement.trend_reversal_chance:.2f}%"
            )

            st.info(
                movement.ai_observation
            )

            
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
