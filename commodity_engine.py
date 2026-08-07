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
    movement_assessment: "MovementAssessment | None" = None

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
        data_source: CommodityDataSource,
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

        self._data_source = data_source
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

@dataclass(frozen=True, slots=True)
class MovementEvidence:
    """
    Intermediate evidence collected while evaluating commodity movement.
    """

    trend_strength: float
    buying_pressure: float
    selling_pressure: float
    breakout_probability: float
    target_confidence: float


@dataclass(frozen=True, slots=True)
class MovementAssessment:
    """
    Final AI movement assessment produced for a commodity.
    """

    ai_movement_status: str

    movement_strength: float
    movement_confidence_index: float

    trend_continuation_chance: float
    trend_reversal_chance: float

    buying_pressure: float
    selling_pressure: float

    breakout_chance: float
    breakdown_chance: float

    entry_timing: str
    exit_timing: str

    signal_stability: float
    false_signal_risk: float

    ai_observation: str

    evidence: MovementEvidence | None = None

class CommodityMovementPredictionAI:
    
    def __init__(
        self,
        *,
        configuration: Mapping[str, Any] | None = None,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the CommodityMovementPredictionAI.

        Args:
            configuration:
                Optional runtime configuration. Any supplied keys override the
                built-in defaults while preserving unspecified values.

            logger_instance:
                Optional logger instance. When omitted, a module-level logger
                for this class is used.
        """
        self._logger: logging.Logger = (
            logger_instance
            if logger_instance is not None
            else logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        )

        defaults: dict[str, Any] = {
            "minimum_score": 0.0,
            "maximum_score": 100.0,
            "rounding_precision": 2,
            "high_confidence_threshold": 80.0,
            "medium_confidence_threshold": 60.0,
            "low_confidence_threshold": 40.0,
            "trend_weight": 0.20,
            "momentum_weight": 0.15,
            "pressure_weight": 0.15,
            "breakout_weight": 0.10,
            "target_weight": 0.15,
            "stability_weight": 0.15,
            "volatility_weight": 0.10,
            "clamp_scores": True,
        }

        self._config: dict[str, Any] = defaults

        if configuration:
            for key, value in configuration.items():
                if key in self._config:
                    self._config[key] = value

        self._initialized_at: datetime = datetime.utcnow()
        self._analysis_count: int = 0
        self._last_analysis_at: datetime | None = None
        self._last_error: Exception | None = None

        self._assessment_cache: dict[str, MovementAssessment] = {}
        self._evidence_cache: dict[str, MovementEvidence] = {}

        self._logger.info(
            "CommodityMovementPredictionAI initialized.",
            extra={
                "configuration_keys": tuple(sorted(self._config.keys())),
                "initialized_at": self._initialized_at.isoformat(),
            },
        )

    def _calculate_trend_strength(
        self,
        quote: CommodityQuote,
    ) -> float:
        """
        Calculate a normalized trend-strength score for a commodity.

        The calculation uses only public fields available on
        ``CommodityQuote`` and produces a deterministic score in the range
        [0.0, 100.0].

        Args:
            quote:
                Commodity market quote.

        Returns:
            A normalized trend-strength score.
        """
        last_price = max(float(quote.last_price), 0.0)
        open_price = max(float(quote.open_price), 0.0)
        high_price = max(float(quote.high_price), last_price)
        low_price = max(min(float(quote.low_price), high_price), 0.0)

        intraday_range = max(high_price - low_price, 1e-9)
        change_percent = abs(float(quote.change_percent))

        if open_price > 0.0:
            open_move = abs(last_price - open_price) / open_price * 100.0
        else:
            open_move = 0.0

        range_position = (last_price - low_price) / intraday_range

        direction_bias = (
            range_position
            if quote.change >= 0.0
            else (1.0 - range_position)
        )

        raw_score = (
            change_percent * 0.45
            + open_move * 0.35
            + direction_bias * 20.0
        )

        minimum = float(self._config.get("minimum_score", 0.0))
        maximum = float(self._config.get("maximum_score", 100.0))
        precision = int(self._config.get("rounding_precision", 2))

        score = max(minimum, min(maximum, raw_score))

        self._logger.debug(
            "Calculated commodity trend strength.",
            extra={
                "symbol": quote.symbol,
                "trend_strength": score,
            },
        )

        return round(score, precision)

    def _calculate_buying_selling_pressure(
        self,
        quote: CommodityQuote,
    ) -> tuple[float, float]:
        """
        Calculate normalized buying and selling pressure for a commodity.

        The calculation uses only fields already available on
        ``CommodityQuote`` and returns percentage values in the range
        [0.0, 100.0].

        Args:
            quote:
                Commodity market quote.

        Returns:
            Tuple containing:
                (buying_pressure, selling_pressure)
        """
        high_price = max(float(quote.high_price), 0.0)
        low_price = max(float(quote.low_price), 0.0)
        last_price = max(float(quote.last_price), 0.0)
        volume = max(float(quote.volume), 0.0)

        price_range = max(high_price - low_price, 1e-9)

        price_position = (last_price - low_price) / price_range
        price_position = max(0.0, min(1.0, price_position))

        volume_factor = min(volume / 100000.0, 1.0)

        buying_pressure = (
            price_position * 70.0
            + volume_factor * 30.0
        )

        buying_pressure = max(
            float(self._config["minimum_score"]),
            min(
                float(self._config["maximum_score"]),
                buying_pressure,
            ),
        )

        selling_pressure = 100.0 - buying_pressure

        precision = int(self._config["rounding_precision"])

        buying_pressure = round(buying_pressure, precision)
        selling_pressure = round(selling_pressure, precision)

        self._logger.debug(
            "Calculated buying/selling pressure.",
            extra={
                "symbol": quote.symbol,
                "buying_pressure": buying_pressure,
                "selling_pressure": selling_pressure,
            },
        )

        return buying_pressure, selling_pressure

    def _calculate_breakout_probability(
        self,
        quote: CommodityQuote,
        trend_strength: float,
        buying_pressure: float,
        selling_pressure: float,
    ) -> float:
        """
        Calculate the probability of a breakout.

        Args:
            quote:
                Commodity market quote.

            trend_strength:
                Trend strength score.

            buying_pressure:
                Buying pressure score.

            selling_pressure:
                Selling pressure score.

        Returns:
            Breakout probability in the range [0.0, 100.0].
        """
        high_price = max(float(quote.high_price), 0.0)
        low_price = max(float(quote.low_price), 0.0)
        last_price = max(float(quote.last_price), 0.0)

        trading_range = max(high_price - low_price, 1e-9)

        range_position = (
            (last_price - low_price) / trading_range
        )

        range_position = max(0.0, min(1.0, range_position))

        pressure_advantage = max(
            buying_pressure - selling_pressure,
            0.0,
        )

        raw_probability = (
            trend_strength * 0.45
            + pressure_advantage * 0.35
            + range_position * 20.0
        )

        minimum = float(self._config["minimum_score"])
        maximum = float(self._config["maximum_score"])

        probability = max(
            minimum,
            min(maximum, raw_probability),
        )

        probability = round(
            probability,
            int(self._config["rounding_precision"]),
        )

        self._logger.debug(
            "Calculated breakout probability.",
            extra={
                "symbol": quote.symbol,
                "breakout_probability": probability,
            },
        )

        return probability

    def _calculate_target_confidence(
        self,
        quote: CommodityQuote,
        trend_strength: float,
        breakout_probability: float,
    ) -> float:
        """
        Calculate the confidence that the current movement can achieve its
        expected target.

        Args:
            quote:
                Commodity market quote.

            trend_strength:
                Previously calculated trend-strength score.

            breakout_probability:
                Previously calculated breakout probability.

        Returns:
            Target confidence score in the range [0.0, 100.0].
        """
        high_price = max(float(quote.high_price), 0.0)
        low_price = max(float(quote.low_price), 0.0)
        last_price = max(float(quote.last_price), 0.0)

        trading_range = max(high_price - low_price, 1e-9)

        range_progress = (
            (last_price - low_price) / trading_range
        )

        range_progress = max(
            0.0,
            min(1.0, range_progress),
        )

        raw_confidence = (
            trend_strength * 0.55
            + breakout_probability * 0.30
            + range_progress * 15.0
        )

        minimum = float(self._config["minimum_score"])
        maximum = float(self._config["maximum_score"])

        confidence = max(
            minimum,
            min(maximum, raw_confidence),
        )

        confidence = round(
            confidence,
            int(self._config["rounding_precision"]),
        )

        self._logger.debug(
            "Calculated target confidence.",
            extra={
                "symbol": quote.symbol,
                "target_confidence": confidence,
            },
        )

        return confidence

    def _build_movement_assessment(
        self,
        quote: CommodityQuote,
        evidence: MovementEvidence,
    ) -> MovementAssessment:
        """
        Build the final AI movement assessment for a commodity.

        Args:
            quote:
                Commodity market quote.

            evidence:
                Previously calculated movement evidence.

        Returns:
            A complete MovementAssessment instance.
        """
        confidence = evidence.target_confidence

        if confidence >= self._config["high_confidence_threshold"]:
            status = "STRONG BUY" if quote.change >= 0 else "STRONG SELL"
        elif confidence >= self._config["medium_confidence_threshold"]:
            status = "BUY" if quote.change >= 0 else "SELL"
        elif confidence >= self._config["low_confidence_threshold"]:
            status = "WATCH"
        else:
            status = "NEUTRAL"

        trend_continuation = min(
            100.0,
            evidence.trend_strength * 0.70 + evidence.breakout_probability * 0.30,
        )

        trend_reversal = max(
            0.0,
            100.0 - trend_continuation,
        )

        signal_stability = (
            confidence * 0.60 +
            evidence.trend_strength * 0.40
        )

        false_signal_risk = max(
            0.0,
            100.0 - signal_stability,
        )

        breakout_chance = evidence.breakout_probability
        breakdown_chance = max(
            0.0,
            100.0 - breakout_chance,
        )

        entry_timing = (
            "Immediate"
            if confidence >= 80
            else "Wait for Confirmation"
            if confidence >= 50
            else "Avoid Entry"
        )

        exit_timing = (
            "Hold Trend"
            if trend_continuation >= 70
            else "Book Partial Profit"
            if trend_continuation >= 50
            else "Exit / Avoid"
        )

        observation = (
            f"{quote.name} currently shows "
            f"{status.lower()} characteristics with "
            f"{confidence:.2f}% confidence."
        )

        precision = int(self._config["rounding_precision"])

        return MovementAssessment(
            ai_movement_status=status,
            movement_strength=round(evidence.trend_strength, precision),
            movement_confidence_index=round(confidence, precision),
            trend_continuation_chance=round(trend_continuation, precision),
            trend_reversal_chance=round(trend_reversal, precision),
            buying_pressure=round(evidence.buying_pressure, precision),
            selling_pressure=round(evidence.selling_pressure, precision),
            breakout_chance=round(breakout_chance, precision),
            breakdown_chance=round(breakdown_chance, precision),
            entry_timing=entry_timing,
            exit_timing=exit_timing,
            signal_stability=round(signal_stability, precision),
            false_signal_risk=round(false_signal_risk, precision),
            ai_observation=observation,
            evidence=evidence,
        )

    def analyze(
        self,
        quote: CommodityQuote,
    ) -> MovementAssessment:
        """
        Analyze a commodity quote and generate a complete movement
        assessment.

        Args:
            quote:
                Commodity market quote.

        Returns:
            MovementAssessment for the supplied commodity.
        """
        self._analysis_count += 1
        self._last_analysis_at = datetime.utcnow()

        try:
            trend_strength = self._calculate_trend_strength(quote)

            buying_pressure, selling_pressure = (
                self._calculate_buying_selling_pressure(
                    quote,
                )
            )

            breakout_probability = (
                self._calculate_breakout_probability(
                    quote,
                    trend_strength,
                    buying_pressure,
                    selling_pressure,
                )
            )

            target_confidence = (
                self._calculate_target_confidence(
                    quote,
                    trend_strength,
                    breakout_probability,
                )
            )

            evidence = MovementEvidence(
                trend_strength=trend_strength,
                buying_pressure=buying_pressure,
                selling_pressure=selling_pressure,
                breakout_probability=breakout_probability,
                target_confidence=target_confidence,
            )

            assessment = self._build_movement_assessment(
                quote,
                evidence,
            )

            self._assessment_cache[quote.symbol] = assessment
            self._evidence_cache[quote.symbol] = evidence

            self._logger.debug(
                "Commodity movement analysis completed.",
                extra={
                    "symbol": quote.symbol,
                    "confidence": assessment.movement_confidence_index,
                },
            )

            return assessment

        except Exception as exc:
            self._last_error = exc

            self._logger.exception(
                "Commodity movement analysis failed.",
                extra={
                    "symbol": quote.symbol,
                },
            )

            raise

    def attach_movement_assessments(
        self,
        commodities: Mapping[str, CommodityQuote],
    ) -> dict[str, CommodityQuote]:
        """
        Attach a ``MovementAssessment`` to every commodity quote.

        Args:
            commodities:
                Mapping of commodity symbols to CommodityQuote objects.

        Returns:
            A new mapping containing commodity quotes with attached
            movement assessments.
        """
        from dataclasses import replace

        updated: dict[str, CommodityQuote] = {}

        for symbol, quote in commodities.items():
            assessment = self.analyze(quote)

            updated[symbol] = replace(
                quote,
                movement_assessment=assessment,
            )

        self._logger.debug(
            "Commodity movement assessments attached.",
            extra={
                "commodity_count": len(updated),
            },
        )

        return updated
