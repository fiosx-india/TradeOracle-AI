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

    # ======================================================
    # 🔧 COMMODITY DATA PIPELINE DIAGNOSTICS
    # ======================================================

    with st.expander(
        "🔧 Commodity Data Pipeline Diagnostics",
        expanded=True,
    ):

        st.caption(
            "Market Data Source → Commodity Provider → "
            "CommodityEngine → Commodity Results → AI Assessment"
        )

        # ==================================================
        # 1️⃣ COMMODITY RESULTS STATUS
        # ==================================================

        st.markdown("### 1️⃣ Commodity Results")

        d1, d2, d3, d4 = st.columns(4)

        # --------------------------------------------------
        # Object Type
        # --------------------------------------------------

        with d1:

            st.metric(
                "Object Type",
                type(commodity_results).__name__,
            )

        # --------------------------------------------------
        # Commodity Count
        # --------------------------------------------------

        with d2:

            if isinstance(commodity_results, dict):

                st.metric(
                    "Commodity Count",
                    len(commodity_results),
                )

            else:

                st.metric(
                    "Commodity Count",
                    "INVALID",
                )

        # --------------------------------------------------
        # Mapping
        # --------------------------------------------------

        with d3:

            st.metric(
                "Is Mapping",
                "YES"
                if isinstance(commodity_results, dict)
                else "NO",
            )

        # --------------------------------------------------
        # Status
        # --------------------------------------------------

        with d4:

            if commodity_results:

                st.metric(
                    "Status",
                    "DATA RECEIVED",
                )

            else:

                st.metric(
                    "Status",
                    "EMPTY",
                )

        # ==================================================
        # 2️⃣ COMMODITY ENGINE STATUS
        # ==================================================

        st.markdown("### 2️⃣ Commodity Engine")

        engine = getattr(
            oracle,
            "commodity_engine",
            None,
        )

        if engine is None:

            st.error(
                "❌ oracle.commodity_engine is not available."
            )

        else:

            # ------------------------------------------------
            # Read health ONCE
            # ------------------------------------------------

            try:

                health = engine.health_check()

            except Exception as exc:

                health = {
                    "healthy": False,
                    "cache_status": "ERROR",
                    "cache_valid": False,
                    "cached_commodities": 0,
                    "last_refresh_at": None,
                    "last_error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                }

            # ------------------------------------------------
            # Engine metrics
            # ------------------------------------------------

            e1, e2, e3, e4 = st.columns(4)

            with e1:

                st.metric(
                    "Engine",
                    "AVAILABLE",
                )

            with e2:

                st.metric(
                    "Cache Valid",
                    "YES"
                    if health.get("cache_valid")
                    else "NO",
                )

            with e3:

                st.metric(
                    "Engine Cache",
                    health.get(
                        "cached_commodities",
                        0,
                    ),
                )

            with e4:

                st.metric(
                    "Engine Healthy",
                    "YES"
                    if health.get("healthy")
                    else "NO",
                )

            # ------------------------------------------------
            # Engine health details
            # ------------------------------------------------

            with st.expander(
                "Engine Health Details",
                expanded=False,
            ):

                st.json(health)

        # ==================================================
        # 3️⃣ ACTUAL MARKET DATA SOURCE
        # ==================================================

        st.markdown("### 3️⃣ Market Data Source")

        s1, s2, s3, s4 = st.columns(4)

        with s1:

            st.metric(
                "Provider",
                "Yahoo Finance",
            )

        with s2:

            st.metric(
                "Library",
                "yfinance",
            )

        with s3:

            st.metric(
                "API Key",
                "NOT REQUIRED",
            )

        with s4:

            st.metric(
                "Official MCX Feed",
                "NO",
            )

        st.info(
            "Current API-key-free test source is Yahoo Finance futures "
            "data through yfinance. It provides real returned market "
            "data, but it is NOT an official MCX market-data feed."
        )

        st.caption(
            "The existing fetch_mcx_commodities() function name is "
            "retained only for backward compatibility with the "
            "CommodityEngine pipeline."
        )

        # ==================================================
        # 4️⃣ SOURCE SYMBOL MAPPING
        # ==================================================

        st.markdown("### 4️⃣ Commodity Source Mapping")

        source_mapping = [
            {
                "Name": "Gold",
                "Source Symbol": "GC=F",
                "Source": "Yahoo Finance Futures",
                "Exchange Label": "Yahoo Finance Futures",
                "Currency": "USD",
            },
            {
                "Name": "Silver",
                "Source Symbol": "SI=F",
                "Source": "Yahoo Finance Futures",
                "Exchange Label": "Yahoo Finance Futures",
                "Currency": "USD",
            },
            {
                "Name": "Crude Oil",
                "Source Symbol": "CL=F",
                "Source": "Yahoo Finance Futures",
                "Exchange Label": "Yahoo Finance Futures",
                "Currency": "USD",
            },
            {
                "Name": "Natural Gas",
                "Source Symbol": "NG=F",
                "Source": "Yahoo Finance Futures",
                "Exchange Label": "Yahoo Finance Futures",
                "Currency": "USD",
            },
            {
                "Name": "Copper",
                "Source Symbol": "HG=F",
                "Source": "Yahoo Finance Futures",
                "Exchange Label": "Yahoo Finance Futures",
                "Currency": "USD",
            },
            {
                "Name": "Platinum",
                "Source Symbol": "PL=F",
                "Source": "Yahoo Finance Futures",
                "Exchange Label": "Yahoo Finance Futures",
                "Currency": "USD",
            },
        ]

        st.dataframe(
            pd.DataFrame(source_mapping),
            use_container_width=True,
            hide_index=True,
        )

        # ==================================================
        # 5️⃣ COMMODITY RESULTS CONTENT
        # ==================================================

        st.markdown("### 5️⃣ Commodity Results Content")

        if commodity_results:

            diagnostic_rows = []

            for symbol, quote in commodity_results.items():

                movement = getattr(
                    quote,
                    "movement_assessment",
                    None,
                )

                timestamp = getattr(
                    quote,
                    "timestamp",
                    None,
                )

                diagnostic_rows.append({

                    # --------------------------------------
                    # IDENTITY
                    # --------------------------------------

                    "Symbol": getattr(
                        quote,
                        "symbol",
                        symbol,
                    ),

                    "Name": getattr(
                        quote,
                        "name",
                        None,
                    ),

                    # --------------------------------------
                    # SOURCE
                    # --------------------------------------

                    "Exchange / Source": getattr(
                        quote,
                        "exchange",
                        None,
                    ),

                    "Currency": getattr(
                        quote,
                        "currency",
                        None,
                    ),

                    # --------------------------------------
                    # MARKET DATA
                    # --------------------------------------

                    "Last Price": getattr(
                        quote,
                        "last_price",
                        None,
                    ),

                    "Change": getattr(
                        quote,
                        "change",
                        None,
                    ),

                    "Change %": getattr(
                        quote,
                        "change_percent",
                        None,
                    ),

                    "Open": getattr(
                        quote,
                        "open_price",
                        None,
                    ),

                    "High": getattr(
                        quote,
                        "high_price",
                        None,
                    ),

                    "Low": getattr(
                        quote,
                        "low_price",
                        None,
                    ),

                    "Volume": getattr(
                        quote,
                        "volume",
                        None,
                    ),

                    # --------------------------------------
                    # TIMESTAMP
                    # --------------------------------------

                    "Timestamp": (
                        timestamp.isoformat()
                        if timestamp is not None
                        else None
                    ),

                    # --------------------------------------
                    # AI PIPELINE
                    # --------------------------------------

                    "AI Assessment": (
                        "AVAILABLE"
                        if movement is not None
                        else "MISSING"
                    ),

                    "AI Status": (
                        getattr(
                            movement,
                            "ai_movement_status",
                            None,
                        )
                        if movement
                        else None
                    ),

                    "Movement Strength": (
                        getattr(
                            movement,
                            "movement_strength",
                            None,
                        )
                        if movement
                        else None
                    ),

                    "Confidence": (
                        getattr(
                            movement,
                            "movement_confidence_index",
                            None,
                        )
                        if movement
                        else None
                    ),

                    "Buying Pressure": (
                        getattr(
                            movement,
                            "buying_pressure",
                            None,
                        )
                        if movement
                        else None
                    ),

                    "Selling Pressure": (
                        getattr(
                            movement,
                            "selling_pressure",
                            None,
                        )
                        if movement
                        else None
                    ),

                    "Breakout": (
                        getattr(
                            movement,
                            "breakout_chance",
                            None,
                        )
                        if movement
                        else None
                    ),

                    "Breakdown": (
                        getattr(
                            movement,
                            "breakdown_chance",
                            None,
                        )
                        if movement
                        else None
                    ),

                    "Trend Continuation": (
                        getattr(
                            movement,
                            "trend_continuation_chance",
                            None,
                        )
                        if movement
                        else None
                    ),

                    "Trend Reversal": (
                        getattr(
                            movement,
                            "trend_reversal_chance",
                            None,
                        )
                        if movement
                        else None
                    ),

                    "False Signal Risk": (
                        getattr(
                            movement,
                            "false_signal_risk",
                            None,
                        )
                        if movement
                        else None
                    ),
                })

            diagnostic_df = pd.DataFrame(
                diagnostic_rows
            )

            st.dataframe(
                diagnostic_df,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.warning(
                "⚠️ commodity_results is EMPTY."
            )

            # ----------------------------------------------
            # Show engine error when available
            # ----------------------------------------------

            if engine is not None:

                try:

                    engine_health = engine.health_check()

                    last_error = engine_health.get(
                        "last_error"
                    )

                    if last_error:

                        st.error(
                            f"Provider / Engine Error: "
                            f"{last_error.get('type', 'Unknown')}: "
                            f"{last_error.get('message', 'Unknown error')}"
                        )

                except Exception:
                    pass

            st.info(
                "No normalized commodity records reached the "
                "dashboard. Check the provider and CommodityEngine."
            )

        # ==================================================
        # 6️⃣ SELECTED COMMODITY DEEP DIAGNOSTICS
        # ==================================================

        if commodity_results:

            st.markdown(
                "### 6️⃣ Individual Commodity Diagnostics"
            )

            selected_symbol = st.selectbox(
                "Select commodity",
                sorted(
                    commodity_results.keys()
                ),
                key="commodity_diagnostic_symbol",
            )

            selected_quote = commodity_results[
                selected_symbol
            ]

            selected_movement = getattr(
                selected_quote,
                "movement_assessment",
                None,
            )

            st.markdown(
                f"#### {getattr(selected_quote, 'name', selected_symbol)} "
                f"({getattr(selected_quote, 'symbol', selected_symbol)})"
            )

            # ==================================================
            # RAW MARKET DATA
            # ==================================================

            st.markdown(
                "##### 6.1️⃣ Raw Market Data"
            )

            r1, r2, r3, r4 = st.columns(4)

            with r1:

                st.metric(
                    "Last Price",
                    f"{getattr(selected_quote, 'last_price', 0):,.4f}",
                )

                st.metric(
                    "Change",
                    f"{getattr(selected_quote, 'change', 0):,.4f}",
                )

            with r2:

                st.metric(
                    "Change %",
                    f"{getattr(selected_quote, 'change_percent', 0):.4f}%",
                )

                st.metric(
                    "Volume",
                    f"{getattr(selected_quote, 'volume', 0):,}",
                )

            with r3:

                st.metric(
                    "Open",
                    f"{getattr(selected_quote, 'open_price', 0):,.4f}",
                )

                st.metric(
                    "High",
                    f"{getattr(selected_quote, 'high_price', 0):,.4f}",
                )

            with r4:

                st.metric(
                    "Low",
                    f"{getattr(selected_quote, 'low_price', 0):,.4f}",
                )

                st.metric(
                    "Currency",
                    getattr(
                        selected_quote,
                        "currency",
                        "--",
                    ),
                )

            timestamp = getattr(
                selected_quote,
                "timestamp",
                None,
            )

            if timestamp:

                st.caption(
                    f"Market Data Timestamp: "
                    f"{timestamp.isoformat()}"
                )

            st.divider()

            # ==================================================
            # AI EVIDENCE
            # ==================================================

            st.markdown(
                "##### 6.2️⃣ AI Evidence"
            )

            if selected_movement is not None:

                evidence = getattr(
                    selected_movement,
                    "evidence",
                    None,
                )

                if evidence:

                    e1, e2, e3, e4, e5 = st.columns(5)

                    with e1:

                        st.metric(
                            "Trend Strength",
                            f"{getattr(evidence, 'trend_strength', 0):.2f}%",
                        )

                    with e2:

                        st.metric(
                            "Buying Pressure",
                            f"{getattr(evidence, 'buying_pressure', 0):.2f}%",
                        )

                    with e3:

                        st.metric(
                            "Selling Pressure",
                            f"{getattr(evidence, 'selling_pressure', 0):.2f}%",
                        )

                    with e4:

                        st.metric(
                            "Breakout Probability",
                            f"{getattr(evidence, 'breakout_probability', 0):.2f}%",
                        )

                    with e5:

                        st.metric(
                            "Target Confidence",
                            f"{getattr(evidence, 'target_confidence', 0):.2f}%",
                        )

                else:

                    st.warning(
                        "AI movement assessment exists, "
                        "but no evidence object is attached."
                    )

            else:

                st.warning(
                    "No AI movement assessment is attached."
                )

            st.divider()

            # ==================================================
            # FINAL AI ASSESSMENT
            # ==================================================

            st.markdown(
                "##### 6.3️⃣ Final AI Assessment"
            )

            if selected_movement is not None:

                a1, a2, a3, a4 = st.columns(4)

                with a1:

                    st.metric(
                        "AI Status",
                        getattr(
                            selected_movement,
                            "ai_movement_status",
                            "--",
                        ),
                    )

                with a2:

                    st.metric(
                        "Movement Strength",
                        f"{getattr(selected_movement, 'movement_strength', 0):.2f}%",
                    )

                with a3:

                    st.metric(
                        "Confidence",
                        f"{getattr(selected_movement, 'movement_confidence_index', 0):.2f}%",
                    )

                with a4:

                    st.metric(
                        "Market Energy",
                        f"{getattr(selected_movement, 'market_energy', 0):.2f}%",
                    )

                a5, a6, a7, a8 = st.columns(4)

                with a5:

                    st.metric(
                        "Trend Continuation",
                        f"{getattr(selected_movement, 'trend_continuation_chance', 0):.2f}%",
                    )

                with a6:

                    st.metric(
                        "Trend Reversal",
                        f"{getattr(selected_movement, 'trend_reversal_chance', 0):.2f}%",
                    )

                with a7:

                    st.metric(
                        "Breakout",
                        f"{getattr(selected_movement, 'breakout_chance', 0):.2f}%",
                    )

                with a8:

                    st.metric(
                        "Breakdown",
                        f"{getattr(selected_movement, 'breakdown_chance', 0):.2f}%",
                    )

                st.divider()

                # ==================================================
                # TARGET / QUALITY
                # ==================================================

                st.markdown(
                    "##### 6.4️⃣ Target & Signal Quality"
                )

                q1, q2, q3, q4 = st.columns(4)

                with q1:

                    st.metric(
                        "Target 1",
                        f"{getattr(selected_movement, 'target1_reach_confidence', 0):.2f}%",
                    )

                with q2:

                    st.metric(
                        "Target 2",
                        f"{getattr(selected_movement, 'target2_reach_confidence', 0):.2f}%",
                    )

                with q3:

                    st.metric(
                        "Target 3",
                        f"{getattr(selected_movement, 'target3_reach_confidence', 0):.2f}%",
                    )

                with q4:

                    st.metric(
                        "False Signal Risk",
                        f"{getattr(selected_movement, 'false_signal_risk', 0):.2f}%",
                    )

                q5, q6, q7, q8 = st.columns(4)

                with q5:

                    st.metric(
                        "Signal Stability",
                        f"{getattr(selected_movement, 'signal_stability', 0):.2f}%",
                    )

                with q6:

                    st.metric(
                        "Volatility",
                        getattr(
                            selected_movement,
                            "volatility_state",
                            "--",
                        ),
                    )

                with q7:

                    st.metric(
                        "Entry Timing",
                        getattr(
                            selected_movement,
                            "entry_timing",
                            "--",
                        ),
                    )

                with q8:

                    st.metric(
                        "Exit Timing",
                        getattr(
                            selected_movement,
                            "exit_timing",
                            "--",
                        ),
                    )

                st.divider()

                # ==================================================
                # AI OBSERVATION
                # ==================================================

                st.markdown(
                    "##### 6.5️⃣ AI Observation"
                )

                st.info(
                    getattr(
                        selected_movement,
                        "ai_observation",
                        "No AI observation available.",
                    )
                )

        # ==================================================
        # 7️⃣ FINAL PIPELINE STATUS
        # ==================================================

        st.markdown(
            "### 7️⃣ Pipeline Status"
        )

        if not commodity_results:

            st.error(
                "❌ Commodity pipeline produced ZERO records."
            )

            st.write(
                """
                Current expected flow:

                Yahoo Finance Futures
                    ↓
                yfinance
                    ↓
                commodity_data_provider.py
                    ↓
                fetch_mcx_commodities()
                    ↓
                CommodityDataSource
                    ↓
                CommodityEngine
                    ↓
                get_all_commodities()
                    ↓
                CommodityMovementPredictionAI
                    ↓
                commodity_results
                    ↓
                Dashboard
                """
            )

        else:

            st.success(
                f"✅ Commodity pipeline produced "
                f"{len(commodity_results)} commodity records."
            )

            if engine is not None:

                try:

                    final_health = engine.health_check()

                    if final_health.get("healthy"):

                        st.success(
                            "✅ CommodityEngine is healthy."
                        )

                    else:

                        st.warning(
                            "⚠️ CommodityEngine has reported an "
                            "unhealthy state. See Engine Health Details."
                        )

                except Exception as exc:

                    st.warning(
                        f"Unable to verify final engine health: "
                        f"{type(exc).__name__}: {exc}"
                    )

    # ======================================================
    # NORMAL DASHBOARD
    # ======================================================

    if not commodity_results:

        st.warning(
            "No commodity data available."
        )

        st.stop()
            
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
