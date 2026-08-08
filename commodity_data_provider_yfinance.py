"""
TradeOracle AI
commodity_data_provider.py

Purpose:
    API-key-free commodity market-data connectivity provider for the
    existing TradeOracle CommodityEngine / CommodityMovementPredictionAI
    pipeline.

IMPORTANT:
    This implementation uses Yahoo Finance futures data through yfinance.

    It is intended for connectivity/testing and does NOT claim to be an
    official MCX live-data feed. Yahoo futures symbols such as GC=F, SI=F,
    CL=F, NG=F and HG=F are used only to get real market data without an
    MCX API key.

Design:
    - No AI calculations
    - No trading signals
    - No dashboard logic
    - No fake/default market prices
    - Real returned market data only
    - Normalizes data into the existing CommodityQuote object
    - Preserves the existing public fetch_mcx_commodities() name for
      backward compatibility with TradeOracle / CommodityEngine
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from commodity_engine import CommodityQuote


LOGGER = logging.getLogger(__name__)


# ============================================================================
# API-KEY-FREE TEST MARKET MAPPING
# ============================================================================
#
# IMPORTANT:
# These are Yahoo Finance futures symbols.
# They are NOT official MCX contract symbols.
#
# This mapping is intentionally kept separate from the AI layer. Once an
# authorized MCX data source is available, only this provider needs to be
# replaced; CommodityEngine and CommodityMovementPredictionAI can remain
# unchanged.
# ============================================================================

TEST_COMMODITIES: dict[str, dict[str, str]] = {
    "GC=F": {
        "name": "Gold",
        "sector": "Precious Metals",
    },
    "SI=F": {
        "name": "Silver",
        "sector": "Precious Metals",
    },
    "CL=F": {
        "name": "Crude Oil",
        "sector": "Energy",
    },
    "NG=F": {
        "name": "Natural Gas",
        "sector": "Energy",
    },
    "HG=F": {
        "name": "Copper",
        "sector": "Base Metals",
    },
    "PL=F": {
        "name": "Platinum",
        "sector": "Precious Metals",
    },
}


# ============================================================================
# SAFE CONVERSION HELPERS
# ============================================================================

def _safe_float(value: Any, field_name: str) -> float:
    """
    Convert a real market-data value to float.

    No fallback market price is created.
    """
    if value is None:
        raise ValueError(f"Missing market value: {field_name}")

    if isinstance(value, bool):
        raise ValueError(f"Invalid boolean market value: {field_name}")

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid numeric market value for {field_name}: {value!r}"
        ) from exc

    if result != result:
        raise ValueError(f"Market value is NaN: {field_name}")

    return result


def _safe_int(value: Any) -> int:
    """
    Convert volume into integer.

    Yahoo may return missing/zero volume for some futures instruments.
    Missing volume is therefore represented as 0 rather than inventing a
    volume value.
    """
    if value is None:
        return 0

    if isinstance(value, bool):
        return 0

    try:
        result = float(value)

        if result != result:
            return 0

        return int(result)

    except (TypeError, ValueError):
        return 0


def _normalize_timestamp(value: Any) -> datetime:
    """
    Normalize a pandas/yfinance timestamp to timezone-aware UTC.
    """
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    if hasattr(value, "to_pydatetime"):
        parsed = value.to_pydatetime()

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    # This is only metadata normalization when the source index is unusual.
    # No market price is fabricated.
    return datetime.now(timezone.utc)


# ============================================================================
# YAHOO FINANCE DATA ACQUISITION
# ============================================================================

def _get_intraday_history(symbol: str):
    """
    Retrieve recent intraday futures data.

    The latest real bar returned by Yahoo is used.

    If the market is closed, the latest available real bar may be older.
    No synthetic/live-looking price is generated.
    """
    ticker = yf.Ticker(symbol)

    return ticker.history(
        period="1d",
        interval="1m",
        auto_adjust=False,
        prepost=True,
    )


def _get_daily_history(symbol: str):
    """
    Retrieve recent daily candles.

    Used only to determine the previous real daily close for change
    calculation.
    """
    ticker = yf.Ticker(symbol)

    return ticker.history(
        period="5d",
        interval="1d",
        auto_adjust=False,
        prepost=False,
    )


# ============================================================================
# CHANGE CALCULATION
# ============================================================================

def _calculate_change(
    symbol: str,
    last_price: float,
    session_open: float,
) -> tuple[float, float]:
    """
    Calculate absolute and percentage change.

    Preferred reference:
        Previous daily close.

    Fallback:
        Current/returned session open, only if it is a real positive value.

    No synthetic/default price is created.
    """
    try:
        daily = _get_daily_history(symbol)

        if daily is not None and not daily.empty:
            daily = daily.dropna(subset=["Close"])

            if len(daily) >= 2:
                previous_close = _safe_float(
                    daily["Close"].iloc[-2],
                    "previous_close",
                )

                if previous_close > 0:
                    change = last_price - previous_close
                    change_percent = (
                        change / previous_close
                    ) * 100.0

                    return change, change_percent

    except Exception:
        LOGGER.warning(
            "Unable to calculate previous-close change for %s; "
            "trying session-open reference.",
            symbol,
            exc_info=True,
        )

    if session_open > 0:
        change = last_price - session_open
        change_percent = (change / session_open) * 100.0

        return change, change_percent

    # No valid reference was available. Return zero for the change fields,
    # while keeping the real last price untouched.
    return 0.0, 0.0


# ============================================================================
# SINGLE COMMODITY NORMALIZATION
# ============================================================================

def _fetch_single_commodity(
    symbol: str,
) -> CommodityQuote | None:
    """
    Fetch and normalize one Yahoo Finance futures contract.
    """
    metadata = TEST_COMMODITIES[symbol]

    try:
        history = _get_intraday_history(symbol)

        if history is None or history.empty:
            LOGGER.warning(
                "No market data returned for %s.",
                symbol,
            )
            return None

        # Close is the minimum required real market value.
        history = history.dropna(subset=["Close"])

        if history.empty:
            LOGGER.warning(
                "No valid closing prices returned for %s.",
                symbol,
            )
            return None

        latest = history.iloc[-1]

        last_price = _safe_float(
            latest.get("Close"),
            "last_price",
        )

        open_price = _safe_float(
            latest.get("Open"),
            "open_price",
        )

        high_price = _safe_float(
            latest.get("High"),
            "high_price",
        )

        low_price = _safe_float(
            latest.get("Low"),
            "low_price",
        )

        volume = _safe_int(
            latest.get("Volume")
        )

        if last_price <= 0:
            LOGGER.warning(
                "Skipping %s because last price is invalid: %s",
                symbol,
                last_price,
            )
            return None

        change, change_percent = _calculate_change(
            symbol,
            last_price,
            open_price,
        )

        timestamp = _normalize_timestamp(
            history.index[-1]
        )

        quote = CommodityQuote(
            symbol=symbol,
            name=metadata["name"],
            last_price=last_price,
            change=change,
            change_percent=change_percent,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            volume=volume,
            timestamp=timestamp,

            # Explicitly identify the real source.
            # Do not label Yahoo data as MCX.
            exchange="Yahoo Finance Futures",
            currency="USD",
        )

        LOGGER.info(
            "Commodity quote normalized.",
            extra={
                "symbol": symbol,
                "name": metadata["name"],
                "last_price": last_price,
                "change_percent": change_percent,
                "timestamp": timestamp.isoformat(),
            },
        )

        return quote

    except Exception:
        LOGGER.exception(
            "Failed to retrieve commodity data for %s.",
            symbol,
        )
        return None


# ============================================================================
# PUBLIC FETCHER
# ============================================================================

def fetch_mcx_commodities() -> dict[str, CommodityQuote]:
    """
    Fetch the latest/last-available commodity futures data.

    Compatibility:
        The public function name is intentionally kept as
        fetch_mcx_commodities() because the existing TradeOracle pipeline
        expects this name.

    Data source:
        Yahoo Finance through yfinance.

    Important:
        This is NOT an official MCX feed.
    """
    commodities: dict[str, CommodityQuote] = {}

    for symbol in TEST_COMMODITIES:
        quote = _fetch_single_commodity(symbol)

        if quote is not None:
            commodities[symbol] = quote

    if not commodities:
        raise RuntimeError(
            "No commodity market data could be retrieved from Yahoo Finance. "
            "Check network access, yfinance installation, and Yahoo Finance "
            "availability."
        )

    LOGGER.info(
        "Commodity test market data normalized successfully.",
        extra={
            "commodity_count": len(commodities),
            "symbols": tuple(sorted(commodities)),
        },
    )

    return commodities


# ============================================================================
# BACKWARD-COMPATIBILITY WRAPPER
# ============================================================================

def get_commodity_data() -> dict[str, CommodityQuote]:
    """
    Compatibility wrapper used by TradeOracle.
    """
    return fetch_mcx_commodities()


# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    "fetch_mcx_commodities",
    "get_commodity_data",
]
