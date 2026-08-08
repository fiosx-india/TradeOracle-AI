"""
TradeOracle AI
commodity_data_provider.py

Purpose:
    API-key-free commodity market-data test provider.

Current source:
    Yahoo Finance via yfinance.

IMPORTANT:
    This provider is intentionally a TEST / CONNECTIVITY implementation.
    It does NOT claim to provide official MCX live market data.

    The existing public function name ``fetch_mcx_commodities`` is retained
    for backward compatibility with TradeOracle / CommodityEngine.

Design:
    - No AI calculations
    - No trading signals
    - No dashboard logic
    - No fake/default prices
    - Retrieves market data and normalizes it into CommodityQuote objects
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from commodity_engine import CommodityQuote


LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Test commodity mapping
# ---------------------------------------------------------------------------
#
# These are Yahoo Finance futures symbols.
# They are NOT MCX contract symbols.
#
# We intentionally keep this mapping small for the first connectivity test.
# Once the pipeline is confirmed, an official/authorized MCX provider can
# replace this module without changing CommodityEngine or the AI layer.
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(value: Any) -> float:
    """Convert a value to float without inventing a market price."""
    if value is None:
        raise ValueError("Missing numeric market value.")

    if isinstance(value, bool):
        raise ValueError("Boolean is not a valid market value.")

    result = float(value)

    if result != result:  # NaN
        raise ValueError("Market value is NaN.")

    return result


def _safe_int(value: Any) -> int:
    """Convert a volume value to integer."""
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

    # pandas Timestamp has to_pydatetime().
    if hasattr(value, "to_pydatetime"):
        parsed = value.to_pydatetime()

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    return datetime.now(timezone.utc)


def _get_intraday_history(symbol: str):
    """
    Retrieve recent 1-minute market data.

    If the market is closed, the last available bar is returned by Yahoo
    Finance. No synthetic price is created.
    """
    ticker = yf.Ticker(symbol)

    return ticker.history(
        period="1d",
        interval="1m",
        auto_adjust=False,
        prepost=True,
    )


def _get_daily_history(symbol: str):
    """Retrieve recent daily candles for previous-close calculation."""
    ticker = yf.Ticker(symbol)

    return ticker.history(
        period="5d",
        interval="1d",
        auto_adjust=False,
    )


def _calculate_change(
    symbol: str,
    last_price: float,
    open_price: float,
) -> tuple[float, float]:
    """
    Calculate absolute and percentage change.

    Preferred reference:
        Previous daily close.

    Fallback:
        Current session open.

    No fallback/default price is fabricated.
    """
    try:
        daily = _get_daily_history(symbol)

        if daily is not None and not daily.empty:
            daily = daily.dropna(subset=["Close"])

            if len(daily) >= 2:
                previous_close = _safe_float(
                    daily["Close"].iloc[-2]
                )

                if previous_close > 0:
                    change = last_price - previous_close
                    change_percent = (
                        change / previous_close
                    ) * 100.0

                    return change, change_percent

    except Exception:
        LOGGER.warning(
            "Unable to calculate previous-close change for %s.",
            symbol,
            exc_info=True,
        )

    # Intraday-open fallback only when a real open price exists.
    if open_price > 0:
        change = last_price - open_price
        change_percent = (change / open_price) * 100.0

        return change, change_percent

    return 0.0, 0.0


# ---------------------------------------------------------------------------
# Single commodity
# ---------------------------------------------------------------------------

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

        history = history.dropna(subset=["Close"])

        if history.empty:
            LOGGER.warning(
                "No valid closing prices returned for %s.",
                symbol,
            )
            return None

        latest = history.iloc[-1]

        last_price = _safe_float(latest.get("Close"))
        open_price = _safe_float(latest.get("Open"))
        high_price = _safe_float(latest.get("High"))
        low_price = _safe_float(latest.get("Low"))
        volume = _safe_int(latest.get("Volume"))

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

        timestamp = _normalize_timestamp(history.index[-1])

        return CommodityQuote(
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

            # Explicitly identify the test source.
            # Do NOT label Yahoo data as MCX.
            exchange="Yahoo Finance",
            currency="USD",
        )

    except Exception:
        LOGGER.exception(
            "Failed to retrieve commodity test data for %s.",
            symbol,
        )
        return None


# ---------------------------------------------------------------------------
# Public fetcher
# ---------------------------------------------------------------------------

def fetch_mcx_commodities() -> dict[str, CommodityQuote]:
    """
    Fetch the current/last-available commodity futures data.

    Compatibility note:
        The function name is retained because the existing TradeOracle
        architecture imports ``fetch_mcx_commodities``.

    Data source:
        Yahoo Finance through yfinance.

    This is NOT an official MCX feed.
    """
    commodities: dict[str, CommodityQuote] = {}

    for symbol in TEST_COMMODITIES:
        quote = _fetch_single_commodity(symbol)

        if quote is not None:
            commodities[symbol] = quote

    if not commodities:
        raise RuntimeError(
            "No commodity market data could be retrieved from "
            "Yahoo Finance. Check network access and yfinance."
        )

    LOGGER.info(
        "Commodity test data normalized successfully.",
        extra={
            "commodity_count": len(commodities),
            "symbols": tuple(sorted(commodities)),
        },
    )

    return commodities


def get_commodity_data() -> dict[str, CommodityQuote]:
    """
    Compatibility wrapper used by TradeOracle.
    """
    return fetch_mcx_commodities()


__all__ = [
    "fetch_mcx_commodities",
    "get_commodity_data",
]
