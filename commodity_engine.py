import logging
import copy

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping

@dataclass(frozen=True, slots=True)
class CommodityQuote:
    """
    Immutable representation of a single commodity market quote.

    Instances of this class are intended to be shared throughout the
    TradeOracle CommodityEngine for caching, AI analysis, monitoring,
    and dashboard presentation.
    """

    symbol: str
    name: str

    last_price: float
    change: float
    change_percent: float

    open_price: float
    high_price: float
    low_price: float

    volume: int

    timestamp: datetime

    exchange: str = "MCX"
    currency: str = "INR"

class CommodityDataSource:
    """
    Production-ready commodity market data source.

    This class encapsulates retrieval of commodity market data for
    ``CommodityEngine``. The actual retrieval mechanism is injected via a
    callable to preserve separation of concerns and allow different
    implementations without changing the engine.
    """

    def __init__(
        self,
        fetcher: Callable[[], Mapping[str, Any]],
        *,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the commodity data source.

        Args:
            fetcher:
                Callable responsible for retrieving commodity market data.

            logger_instance:
                Optional logger instance.
        """
        if not callable(fetcher):
            raise TypeError("fetcher must be callable.")

        self._fetcher: Callable[[], Mapping[str, Any]] = fetcher
        self._logger: logging.Logger = (
            logger_instance
            if logger_instance is not None
            else logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        )

    def fetch(self) -> dict[str, Any]:
        """
        Retrieve the latest commodity market data.

        Returns:
            Dictionary keyed by commodity symbol or identifier containing
            commodity market data compatible with ``CommodityEngine``.

        Raises:
            TypeError:
                If the configured fetcher returns an invalid object.

            Exception:
                Re-raises any exception from the underlying fetcher after
                logging the failure.
        """
        self._logger.debug("Fetching commodity market data.")

        try:
            result = self._fetcher()

            if not isinstance(result, Mapping):
                raise TypeError(
                    "Commodity data fetcher must return a mapping."
                )

            data = dict(result)

            self._logger.info(
                "Commodity market data retrieved successfully.",
                extra={"commodity_count": len(data)},
            )

            return data

        except Exception:
            self._logger.exception("Commodity data retrieval failed.")
            raise

class MCXDataProvider:
    """
    MCX commodity market data provider.

    This provider delegates retrieval of commodity market data to an
    injected callable so that the retrieval mechanism (HTTP client,
    exchange SDK, broker API, etc.) remains external to this class.

    The returned mapping is compatible with ``CommodityDataSource`` and
    suitable for dependency injection.
    """

    def __init__(
        self,
        fetcher: Callable[[], Mapping[str, Any]],
        *,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the MCX data provider.

        Args:
            fetcher:
                Callable responsible for retrieving MCX commodity data.

            logger_instance:
                Optional logger instance.
        """
        if not callable(fetcher):
            raise TypeError("fetcher must be callable.")

        self._fetcher: Callable[[], Mapping[str, Any]] = fetcher
        self._logger: logging.Logger = (
            logger_instance
            if logger_instance is not None
            else logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        )

    def fetch(self) -> Mapping[str, Any]:
        """
        Retrieve the latest MCX commodity market data.

        Returns:
            A mapping keyed by commodity symbol.

        Raises:
            ConnectionError:
                If the underlying data source is unavailable.

            RuntimeError:
                If the returned payload is invalid.

            Exception:
                Re-raises unexpected exceptions after logging.
        """
        self._logger.debug("Fetching MCX commodity market data.")

        try:
            payload = self._fetcher()

            if not isinstance(payload, Mapping):
                raise RuntimeError(
                    "MCX data provider returned an invalid payload."
                )

            data = dict(payload)

            self._logger.info(
                "MCX commodity market data retrieved successfully.",
                extra={
                    "commodity_count": len(data),
                },
            )

            return data

        except ConnectionError:
            self._logger.exception(
                "Unable to connect to the configured MCX data source."
            )
            raise

        except TimeoutError as exc:
            self._logger.exception(
                "Timed out while retrieving MCX commodity market data."
            )
            raise ConnectionError(
                "Timed out while connecting to the MCX data source."
            ) from exc

        except Exception:
            self._logger.exception(
                "Unexpected error while retrieving MCX commodity market data."
            )
            raise

class CommodityEngine:
    """
    Commodity market cache and retrieval engine.
    """

    def __init__(
        self,
        *,
        cache_ttl: float = 300.0,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the CommodityEngine.

        Args:
            cache_ttl:
                Default cache time-to-live, in seconds.

            logger_instance:
                Optional logger instance. When omitted, a module-level logger
                named after this module is used.
        """
        self._logger: logging.Logger = (
            logger_instance
            if logger_instance is not None
            else logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        )

        self._cache_ttl: float = float(cache_ttl)
        self._cache: dict[str, Any] = {}
        self._cache_timestamp: dict[str, datetime] = {}

        self._initialized_at: datetime = datetime.utcnow()
        self._last_refresh_at: datetime | None = None

        self._request_count: int = 0
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._last_error: Exception | None = None

        self._healthy: bool = True

        self._logger.info(
            "CommodityEngine initialized.",
            extra={
                "cache_ttl": self._cache_ttl,
                "initialized_at": self._initialized_at.isoformat(),
            },
        )

    def refresh(self) -> None:
        """
        Refresh commodity market data from the configured data source.

        This method refreshes the engine cache, updates runtime statistics,
        maintains engine health state, and records refresh timestamps.

        Raises:
            Exception:
                Propagates any exception raised by the configured data source
                after updating the engine state and logging the failure.
        """
        self._logger.info("Refreshing commodity market data.")

        self._request_count += 1

        try:
            data = self._data_source.fetch()

            if not isinstance(data, dict):
                raise TypeError(
                    "Configured commodity data source must return a dictionary."
                )

            self._cache.clear()
            self._cache.update(data)

            timestamp = datetime.utcnow()

            self._cache_timestamp.clear()
            self._cache_timestamp.update(
                {key: timestamp for key in self._cache}
            )

            self._last_refresh_at = timestamp
            self._last_error = None
            self._healthy = True

            self._logger.info(
                "Commodity market data refreshed successfully.",
                extra={
                    "commodity_count": len(self._cache),
                    "refreshed_at": timestamp.isoformat(),
                },
            )

        except Exception as exc:
            self._last_error = exc
            self._healthy = False

            self._logger.exception(
                "Commodity market data refresh failed.",
                extra={
                    "request_count": self._request_count,
                },
            )

            raise

    def get_all_commodities(self) -> dict[str, Any]:
        """
        Return all cached commodity market data.

        Returns:
            A defensive copy of the internal commodity cache.

        Raises:
            RuntimeError:
                If no commodity data is currently available in the cache.
        """
        if not self._cache:
            self._logger.warning(
                "Commodity cache is empty. No commodity market data available."
            )
            raise RuntimeError(
                "Commodity cache is empty. Call refresh() before requesting commodity data."
            )

        self._logger.debug(
            "Returning cached commodity market data.",
            extra={
                "commodity_count": len(self._cache),
                "cache_age_seconds": (
                    (datetime.utcnow() - self._last_refresh_at).total_seconds()
                    if self._last_refresh_at is not None
                    else None
                ),
            },
        )

        return dict(self._cache)

    def get_commodity(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Return the cached market data for a single commodity.

        Args:
            symbol:
                Commodity symbol.

        Returns:
            A defensive copy of the cached commodity market data.

        Raises:
            TypeError:
                If ``symbol`` is not a string.

            ValueError:
                If ``symbol`` is empty or contains only whitespace.

            KeyError:
                If the requested commodity is not present in the cache.
        """
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string.")

        key = symbol.strip().upper()

        if not key:
            raise ValueError("symbol must be a non-empty string.")

        commodity = self._cache.get(key)

        if commodity is None:
            self._logger.warning(
                "Commodity not found in cache.",
                extra={"symbol": key},
            )
            raise KeyError(f"Commodity '{key}' is not available in the cache.")

        self._logger.debug(
            "Returning cached commodity data.",
            extra={"symbol": key},
        )

        if isinstance(commodity, Mapping):
            return dict(commodity)

        if hasattr(commodity, "__dict__"):
            return dict(vars(commodity))

        return {"value": commodity}

    def is_cache_valid(self) -> bool:
        """
        Determine whether the current commodity cache is still valid.

        The cache is considered valid only when:
        - Cached commodity data exists.
        - A successful refresh timestamp is available.
        - The elapsed time since the last refresh does not exceed the
          configured cache TTL.

        Returns:
            True if the cache is valid; otherwise False.
        """
        if not self._cache:
            self._logger.debug(
                "Commodity cache validation failed: cache is empty."
            )
            return False

        if self._last_refresh_at is None:
            self._logger.debug(
                "Commodity cache validation failed: no refresh timestamp available."
            )
            return False

        age_seconds = (
            datetime.utcnow() - self._last_refresh_at
        ).total_seconds()

        is_valid = age_seconds <= self._cache_ttl

        self._logger.debug(
            "Commodity cache validation completed.",
            extra={
                "cache_valid": is_valid,
                "cache_age_seconds": round(age_seconds, 3),
                "cache_ttl_seconds": self._cache_ttl,
            },
        )

        return is_valid

    def refresh_if_needed(self) -> bool:
        """
        Refresh the commodity cache only if the current cache is invalid or
        expired.

        Returns:
            True if a refresh was performed; otherwise False.

        Raises:
            Exception:
                Propagates any exception raised by ``refresh()`` after logging.
        """
        if self.is_cache_valid():
            self._logger.debug(
                "Commodity cache is valid; refresh not required.",
                extra={
                    "last_refresh_at": (
                        self._last_refresh_at.isoformat()
                        if self._last_refresh_at is not None
                        else None
                    ),
                },
            )
            return False

        self._logger.info(
            "Commodity cache is invalid or expired. Refreshing commodity data."
        )

        try:
            self.refresh()

            self._logger.info(
                "Commodity cache refreshed successfully.",
                extra={
                    "last_refresh_at": (
                        self._last_refresh_at.isoformat()
                        if self._last_refresh_at is not None
                        else None
                    ),
                },
            )

            return True

        except Exception:
            self._logger.exception(
                "Commodity cache refresh failed."
            )
            raise

    def clear_cache(self) -> None:
        """
        Safely clear all cached commodity market data and reset cache metadata.

        This method removes all cached commodity data, clears cache timestamp
        metadata, and resets the last successful refresh timestamp. Engine
        configuration, runtime statistics, and health state are preserved.

        Returns:
            None
        """
        commodity_count = len(self._cache)

        self._logger.info(
            "Clearing commodity cache.",
            extra={
                "cached_commodities": commodity_count,
            },
        )

        self._cache.clear()
        self._cache_timestamp.clear()
        self._last_refresh_at = None

        self._logger.debug(
            "Commodity cache cleared successfully.",
            extra={
                "cached_commodities": len(self._cache),
                "last_refresh_at": self._last_refresh_at,
            },
        )

    def health_check(self) -> dict[str, Any]:
        """
        Return the current operational health status of the CommodityEngine.

        The returned dictionary is intended for monitoring, diagnostics, and
        dashboard display. Calling this method does not modify engine state.

        Returns:
            A dictionary containing engine health information.
        """
        cache_valid = self.is_cache_valid()

        status: dict[str, Any] = {
            "healthy": self._healthy,
            "cache_status": "POPULATED" if self._cache else "EMPTY",
            "cache_valid": cache_valid,
            "cached_commodities": len(self._cache),
            "last_refresh_at": (
                self._last_refresh_at.isoformat()
                if self._last_refresh_at is not None
                else None
            ),
            "last_error": (
                None
                if self._last_error is None
                else {
                    "type": type(self._last_error).__name__,
                    "message": str(self._last_error),
                }
            ),
            "request_count": self._request_count,
            "cache_hit_count": self._cache_hits,
            "cache_miss_count": self._cache_misses,
            "cache_ttl_seconds": self._cache_ttl,
            "initialized_at": self._initialized_at.isoformat(),
        }

        self._logger.debug(
            "CommodityEngine health check completed.",
            extra={
                "healthy": status["healthy"],
                "cache_valid": status["cache_valid"],
                "cached_commodities": status["cached_commodities"],
            },
        )

        return status

    def get_statistics(self) -> dict[str, Any]:
        """
        Return runtime statistics for the CommodityEngine.

        The returned statistics are intended for monitoring and dashboard
        presentation. Calling this method does not modify engine state.

        Returns:
            A dictionary containing runtime statistics.
        """
        total_requests = self._cache_hits + self._cache_misses

        cache_hit_ratio = (
            self._cache_hits / total_requests
            if total_requests > 0
            else 0.0
        )

        uptime_seconds = (
            datetime.utcnow() - self._initialized_at
        ).total_seconds()

        statistics: dict[str, Any] = {
            "request_count": self._request_count,
            "cache_hit_count": self._cache_hits,
            "cache_miss_count": self._cache_misses,
            "cached_commodities": len(self._cache),
            "cache_hit_ratio": round(cache_hit_ratio, 4),
            "last_refresh_at": (
                self._last_refresh_at.isoformat()
                if self._last_refresh_at is not None
                else None
            ),
            "cache_ttl_seconds": self._cache_ttl,
            "engine_uptime_seconds": round(uptime_seconds, 3),
        }

        self._logger.debug(
            "CommodityEngine runtime statistics collected.",
            extra={
                "request_count": statistics["request_count"],
                "cache_hit_count": statistics["cache_hit_count"],
                "cache_miss_count": statistics["cache_miss_count"],
                "cache_hit_ratio": statistics["cache_hit_ratio"],
            },
        )

        return statistics

