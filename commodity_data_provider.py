"""
TradeOracle AI
commodity_data_provider.py

Purpose:
    Retrieve and normalize MCX commodity market data into
    CommodityQuote objects used by CommodityEngine and
    CommodityMovementPredictionAI.

Design:
    - No AI calculations
    - No trading signals
    - No dashboard logic
    - No fake/default market prices
    - Data acquisition and normalization only
"""

from __future__ import annotations

import logging
import os

from datetime import datetime, timezone
from typing import Any, Mapping

import requests

from commodity_engine import CommodityQuote


LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT_SECONDS = 15

MCX_COMMODITY_API_URL = os.getenv(
    "MCX_COMMODITY_API_URL",
    "",
)

MCX_COMMODITY_API_KEY = os.getenv(
    "MCX_COMMODITY_API_KEY",
    "",
)


# ---------------------------------------------------------------------------
# Commodity name mapping
# ---------------------------------------------------------------------------

COMMODITY_NAMES: dict[str, str] = {
    "GOLD": "Gold",
    "GOLDM": "Gold Mini",
    "GOLDGUINEA": "Gold Guinea",
    "GOLDPETAL": "Gold Petal",
    "GOLDTEN": "Gold Ten",
    "SILVER": "Silver",
    "SILVERM": "Silver Mini",
    "SILVERMIC": "Silver Micro",
    "SILVER100": "Silver 100",
    "CRUDEOIL": "Crude Oil",
    "CRUDEOILM": "Crude Oil Mini",
    "NATURALGAS": "Natural Gas",
    "NATGASMINI": "Natural Gas Mini",
    "COPPER": "Copper",
    "ZINC": "Zinc",
    "ZINCMINI": "Zinc Mini",
    "LEAD": "Lead",
    "LEADMINI": "Lead Mini",
    "NICKEL": "Nickel",
    "ALUMINIUM": "Aluminium",
    "ALUMINI": "Aluminium Mini",
    "MENTHAOIL": "Mentha Oil",
    "CARDAMOM": "Cardamom",
    "KAPAS": "Kapas",
    "STEELREBAR": "Steel Rebar",
}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _normalize_key(value: Any) -> str:
    """
    Normalize a dictionary field name so that different API naming
    conventions can be handled consistently.
    """
    return (
        str(value)
        .strip()
        .lower()
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
        .replace(".", "")
        .replace("%", "percent")
        .replace("(", "")
        .replace(")", "")
    )


def _build_normalized_mapping(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Create a normalized-key representation of an API record.
    """
    return {
        _normalize_key(key): value
        for key, value in record.items()
    }


def _first_value(
    record: Mapping[str, Any],
    *aliases: str,
) -> Any:
    """
    Return the first available value matching one of the supplied aliases.
    """
    normalized = _build_normalized_mapping(record)

    for alias in aliases:
        value = normalized.get(_normalize_key(alias))

        if value is not None:
            return value

    return None


def _to_float(
    value: Any,
    *,
    field_name: str,
) -> float:
    """
    Convert an API value into float safely.
    """
    if value is None:
        raise ValueError(
            f"Missing required numeric field: {field_name}"
        )

    if isinstance(value, bool):
        raise ValueError(
            f"Invalid boolean value for numeric field: {field_name}"
        )

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text:
        raise ValueError(
            f"Empty numeric field: {field_name}"
        )

    # Remove common display characters.
    text = (
        text
        .replace(",", "")
        .replace("%", "")
        .strip()
    )

    return float(text)


def _to_int(
    value: Any,
    *,
    field_name: str,
) -> int:
    """
    Convert an API value into integer safely.

    MCX volume is commonly represented as lots.
    """
    if value is None:
        raise ValueError(
            f"Missing required integer field: {field_name}"
        )

    if isinstance(value, bool):
        raise ValueError(
            f"Invalid boolean value for integer field: {field_name}"
        )

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    text = (
        str(value)
        .strip()
        .replace(",", "")
    )

    if not text:
        raise ValueError(
            f"Empty integer field: {field_name}"
        )

    return int(float(text))


def _parse_timestamp(value: Any) -> datetime:
    """
    Convert an API timestamp into a timezone-aware datetime.

    If the source does not provide a timestamp, current UTC time is used.
    """
    if value is None:
        return datetime.now(timezone.utc)

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value

    text = str(value).strip()

    if not text:
        return datetime.now(timezone.utc)

    # ISO-8601 support.
    try:
        parsed = datetime.fromisoformat(
            text.replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed

    except ValueError:
        pass

    # Common MCX-style date/time formats.
    formats = (
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
    )

    for fmt in formats:
        try:
            return datetime.strptime(
                text,
                fmt,
            ).replace(tzinfo=timezone.utc)

        except ValueError:
            continue

    LOGGER.warning(
        "Unable to parse commodity timestamp '%s'. "
        "Using current UTC time.",
        text,
    )

    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Payload extraction
# ---------------------------------------------------------------------------

def _extract_records(
    payload: Any,
) -> list[Mapping[str, Any]]:
    """
    Extract commodity records from common API response structures.

    Supported structures include:

        [
            {...},
            {...}
        ]

    {
        "data": [
            {...}
        ]
    }

    {
        "results": [
            {...}
        ]
    }

    {
        "records": [
            {...}
        ]
    }

    {
        "rows": [
            {...}
        ]
    }

    {
        "GOLD": {...},
        "SILVER": {...}
    }
    """

    if isinstance(payload, list):
        return [
            item
            for item in payload
            if isinstance(item, Mapping)
        ]

    if not isinstance(payload, Mapping):
        raise RuntimeError(
            "MCX API returned an unsupported payload type."
        )

    # Common container fields.
    for key in (
        "data",
        "results",
        "records",
        "rows",
        "items",
        "commodities",
        "marketData",
        "market_data",
    ):
        value = _first_value(
            payload,
            key,
        )

        if isinstance(value, list):
            return [
                item
                for item in value
                if isinstance(item, Mapping)
            ]

    # Direct symbol -> record mapping.
    records: list[Mapping[str, Any]] = []

    for symbol, value in payload.items():
        if isinstance(value, Mapping):
            record = dict(value)

            if _first_value(
                record,
                "symbol",
                "Symbol",
                "commodity",
                "Commodity",
            ) is None:
                record["symbol"] = symbol

            records.append(record)

    if records:
        return records

    raise RuntimeError(
        "MCX API response does not contain commodity records."
    )


# ---------------------------------------------------------------------------
# Contract filtering
# ---------------------------------------------------------------------------

def _is_supported_commodity(
    record: Mapping[str, Any],
) -> bool:
    """
    Determine whether the record represents an MCX commodity contract.

    Option contracts and index contracts are excluded from the commodity
    movement pipeline.
    """
    instrument = _first_value(
        record,
        "InstrumentName",
        "Instrument",
        "instrument_name",
        "instrument",
    )

    if instrument is not None:
        normalized = str(instrument).strip().upper()

        if normalized not in {
            "FUTCOM",
            "FUTCOM ",
        }:
            return False

    symbol = _first_value(
        record,
        "Symbol",
        "symbol",
        "Commodity",
        "commodity",
    )

    if symbol is None:
        return False

    symbol = str(symbol).strip().upper()

    return symbol in COMMODITY_NAMES


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def _normalize_commodity_record(
    record: Mapping[str, Any],
) -> CommodityQuote:
    """
    Convert one MCX market-data record into CommodityQuote.
    """

    symbol_value = _first_value(
        record,
        "Symbol",
        "symbol",
        "Commodity",
        "commodity",
    )

    if symbol_value is None:
        raise ValueError(
            "Commodity record does not contain a symbol."
        )

    symbol = str(symbol_value).strip().upper()

    name_value = _first_value(
        record,
        "Name",
        "name",
        "CommodityName",
        "commodity_name",
    )

    name = (
        str(name_value).strip()
        if name_value is not None
        else COMMODITY_NAMES.get(
            symbol,
            symbol,
        )
    )

    last_price = _to_float(
        _first_value(
            record,
            "LTP",
            "LastPrice",
            "last_price",
            "Last Traded Price",
        ),
        field_name="last_price",
    )

    open_price = _to_float(
        _first_value(
            record,
            "Open",
            "OpenPrice",
            "open_price",
        ),
        field_name="open_price",
    )

    high_price = _to_float(
        _first_value(
            record,
            "High",
            "HighPrice",
            "high_price",
        ),
        field_name="high_price",
    )

    low_price = _to_float(
        _first_value(
            record,
            "Low",
            "LowPrice",
            "low_price",
        ),
        field_name="low_price",
    )

    change = _to_float(
        _first_value(
            record,
            "Abs. Chng",
            "Abs Chng",
            "AbsoluteChange",
            "Change",
            "change",
        ),
        field_name="change",
    )

    change_percent = _to_float(
        _first_value(
            record,
            "% Change",
            "PercentChange",
            "ChangePercent",
            "change_percent",
        ),
        field_name="change_percent",
    )

    volume = _to_int(
        _first_value(
            record,
            "Vol (Lots)",
            "Vol Lots",
            "Volume",
            "volume",
            "VolumeLots",
        ),
        field_name="volume",
    )

    timestamp = _parse_timestamp(
        _first_value(
            record,
            "Timestamp",
            "timestamp",
            "Time",
            "time",
            "UpdatedAt",
            "updated_at",
            "LastUpdated",
        )
    )

    return CommodityQuote(
        symbol=symbol,
        name=name,
        last_price=last_price,
        change=change,
        change_percent=change_percent,
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        volume=volume,
        timestamp=timestamp,
        exchange="MCX",
        currency="INR",
    )


# ---------------------------------------------------------------------------
# HTTP acquisition
# ---------------------------------------------------------------------------

def _fetch_json_from_mcx() -> Any:
    """
    Retrieve the configured MCX-compatible market-data payload.

    The actual endpoint is intentionally supplied through environment
    configuration rather than hard-coded into the application.

    Environment variables:

        MCX_COMMODITY_API_URL
        MCX_COMMODITY_API_KEY   (optional)
    """

    if not MCX_COMMODITY_API_URL:
        raise RuntimeError(
            "MCX_COMMODITY_API_URL is not configured. "
            "Configure an authorized MCX market-data endpoint before "
            "starting live commodity analysis."
        )

    headers = {
        "Accept": "application/json",
        "User-Agent": "TradeOracle-AI/1.0",
    }

    if MCX_COMMODITY_API_KEY:
        headers["Authorization"] = (
            f"Bearer {MCX_COMMODITY_API_KEY}"
        )

    LOGGER.info(
        "Requesting MCX commodity market data."
    )

    try:
        response = requests.get(
            MCX_COMMODITY_API_URL,
            headers=headers,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )

        response.raise_for_status()

    except requests.Timeout as exc:
        LOGGER.exception(
            "MCX commodity data request timed out."
        )
        raise TimeoutError(
            "MCX commodity data request timed out."
        ) from exc

    except requests.RequestException as exc:
        LOGGER.exception(
            "MCX commodity data request failed."
        )
        raise ConnectionError(
            "Unable to retrieve MCX commodity market data."
        ) from exc

    try:
        return response.json()

    except ValueError as exc:
        LOGGER.exception(
            "MCX commodity endpoint returned invalid JSON."
        )
        raise RuntimeError(
            "MCX commodity endpoint returned invalid JSON."
        ) from exc


# ---------------------------------------------------------------------------
# Public fetcher
# ---------------------------------------------------------------------------

def fetch_mcx_commodities() -> dict[str, CommodityQuote]:
    """
    Fetch and normalize the latest MCX commodity market data.

    Returns:
        Dictionary keyed by commodity symbol containing CommodityQuote
        objects.

    Raises:
        ConnectionError:
            If the configured market-data endpoint cannot be reached.

        RuntimeError:
            If configuration or payload validation fails.

        ValueError:
            If individual commodity records contain invalid market data.
    """

    payload = _fetch_json_from_mcx()

    records = _extract_records(payload)

    commodities: dict[str, CommodityQuote] = {}

    for record in records:

        if not _is_supported_commodity(record):
            continue

        try:
            quote = _normalize_commodity_record(
                record
            )

        except (TypeError, ValueError) as exc:
            LOGGER.warning(
                "Skipping invalid commodity record: %s",
                exc,
            )
            continue

        commodities[quote.symbol] = quote

    if not commodities:
        raise RuntimeError(
            "No valid MCX commodity market records were found "
            "in the returned payload."
        )

    LOGGER.info(
        "MCX commodity data normalized successfully.",
        extra={
            "commodity_count": len(commodities),
            "symbols": tuple(sorted(commodities)),
        },
    )

    return commodities


# ---------------------------------------------------------------------------
# Public compatibility function
# ---------------------------------------------------------------------------

def get_commodity_data() -> dict[str, CommodityQuote]:
    """
    Compatibility wrapper used by TradeOracle.

    Returns:
        Normalized MCX commodity quotes.
    """
    return fetch_mcx_commodities()


__all__ = [
    "fetch_mcx_commodities",
    "get_commodity_data",
  ]
