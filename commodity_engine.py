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

