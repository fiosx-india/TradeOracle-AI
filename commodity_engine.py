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

def _initialize_commodity_engine(self) -> None:
    """
    Initialize the commodity engine and its dependencies.

    This method constructs the MCX data provider, wraps it in the
    CommodityDataSource, creates the CommodityEngine using dependency
    injection, and stores the resulting instance on this TradeOracle
    object.

    Raises:
        Exception:
            Re-raises any initialization error after logging.
    """
    self._logger.debug("Initializing CommodityEngine.")

    try:
        provider = MCXDataProvider(
            fetcher=self._fetch_mcx_market_data,
            logger_instance=self._logger,
        )

        data_source = CommodityDataSource(
            fetcher=provider.fetch,
            logger_instance=self._logger,
        )

        self._commodity_engine = CommodityEngine(
            data_source=data_source,
            logger_instance=self._logger,
        )

        self._logger.info("CommodityEngine initialized successfully.")

    except Exception:
        self._logger.exception(
            "Failed to initialize CommodityEngine."
        )
        raise

def _analyze_commodities(self) -> dict[str, Any]:
    """
    Analyze commodity market data using the initialized CommodityEngine.

    This method refreshes the commodity cache when required, retrieves the
    current commodity quotes, and returns a dictionary suitable for
    downstream AI processing and dashboard presentation.

    Returns:
        A dictionary containing commodity analysis results.

    Raises:
        RuntimeError:
            If the CommodityEngine has not been initialized.
    """
    if not hasattr(self, "_commodity_engine") or self._commodity_engine is None:
        raise RuntimeError("CommodityEngine has not been initialized.")

    self._logger.debug("Starting commodity analysis.")

    try:
        refreshed = self._commodity_engine.refresh_if_needed()
        commodities = self._commodity_engine.get_all_commodities()

        result: dict[str, Any] = {
            "commodities": commodities,
            "commodity_count": len(commodities),
            "cache_refreshed": refreshed,
            "statistics": self._commodity_engine.get_statistics(),
            "health": self._commodity_engine.health_check(),
        }

        self._logger.info(
            "Commodity analysis completed successfully.",
            extra={
                "commodity_count": result["commodity_count"],
                "cache_refreshed": refreshed,
            },
        )

        return result

    except Exception as exc:
        self._logger.exception("Commodity analysis failed.")

        return {
            "commodities": {},
            "commodity_count": 0,
            "cache_refreshed": False,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }


def _merge_commodity_results(
    self,
    results: Mapping[str, Any],
    commodity_results: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Merge commodity analysis results into the existing TradeOracle
    analysis results.

    Commodity data is added under a dedicated ``"commodities"`` key
    without modifying any existing analysis objects or keys.

    Args:
        results:
            Existing TradeOracle analysis results.

        commodity_results:
            Commodity analysis results returned by
            ``_analyze_commodities()``.

    Returns:
        A merged results dictionary containing the original analysis
        results and a dedicated ``"commodities"`` section.
    """
    merged: dict[str, Any] = dict(results)

    merged["commodities"] = dict(commodity_results)

    self._logger.debug(
        "Commodity analysis merged into TradeOracle results.",
        extra={
            "existing_result_keys": len(results),
            "commodity_result_keys": len(commodity_results),
            "merged_result_keys": len(merged),
        },
    )

    return merged


def analyze(self) -> dict[str, Any]:
    """
    Execute the complete TradeOracle analysis pipeline.

    The pipeline performs:
      1. Market analysis.
      2. News analysis.
      3. Signal analysis.
      4. Commodity analysis.
      5. Commodity result merging.

    Commodity analysis is isolated so that failures do not interrupt the
    primary market analysis workflow.

    Returns:
        A dictionary containing the complete TradeOracle analysis results.
    """
    self._logger.info("Starting TradeOracle analysis.")

    results: dict[str, Any] = self._run_analysis_pipeline()

    try:
        commodity_results = self._analyze_commodities()
        results = self._merge_commodity_results(
            results=results,
            commodity_results=commodity_results,
        )

        self._logger.debug(
            "Commodity analysis successfully integrated.",
            extra={
                "commodity_count": commodity_results.get(
                    "commodity_count",
                    0,
                ),
            },
        )

    except Exception:
        self._logger.exception(
            "Commodity analysis unavailable. Continuing with primary analysis."
        )

        results = self._merge_commodity_results(
            results=results,
            commodity_results={
                "commodities": {},
                "commodity_count": 0,
                "available": False,
            },
        )

    self._logger.info("TradeOracle analysis completed.")

    return results


def render_live_commodities(results: Mapping[str, Any]) -> None:
    """
    Render live commodity market data from the TradeOracle analysis results.

    Args:
        results:
            Dictionary returned by ``TradeOracle.analyze()``.
    """
    import streamlit as st

    st.subheader("🪙 Live Commodities")

    commodity_section = results.get("commodities")

    if not commodity_section:
        st.info("Commodity analysis is unavailable.")
        return

    commodities = commodity_section.get("commodities", {})

    if not commodities:
        st.info("No commodity market data is currently available.")
        return

    columns = st.columns(min(3, max(1, len(commodities))))

    for index, (_, quote) in enumerate(commodities.items()):
        column = columns[index % len(columns)]

        if isinstance(quote, Mapping):
            name = quote.get("name", "Unknown")
            last_price = quote.get("last_price", "—")
            change = quote.get("change", "—")
            change_percent = quote.get("change_percent", "—")
            exchange = quote.get("exchange", "—")
            timestamp = quote.get("timestamp", "—")
        else:
            name = getattr(quote, "name", "Unknown")
            last_price = getattr(quote, "last_price", "—")
            change = getattr(quote, "change", "—")
            change_percent = getattr(quote, "change_percent", "—")
            exchange = getattr(quote, "exchange", "—")
            timestamp = getattr(quote, "timestamp", "—")

        if hasattr(timestamp, "strftime"):
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        try:
            delta_text = f"{float(change):+.2f} ({float(change_percent):+.2f}%)"
        except (TypeError, ValueError):
            delta_text = f"{change} ({change_percent})"

        with column:
            st.markdown(
                f"""
                <div style="
                    border:1px solid rgba(128,128,128,0.25);
                    border-radius:10px;
                    padding:1rem;
                    margin-bottom:1rem;
                ">
                    <h4 style="margin-top:0;">{name}</h4>
                    <p><strong>Last Price:</strong> {last_price}</p>
                    <p><strong>Change:</strong> {delta_text}</p>
                    <p><strong>Exchange:</strong> {exchange}</p>
                    <p><strong>Timestamp:</strong> {timestamp}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_commodity_ai_summary(results: Mapping[str, Any]) -> None:
    """
    Render an AI summary for commodity markets.

    Args:
        results:
            Dictionary returned by ``TradeOracle.analyze()``.
    """
    import streamlit as st

    st.subheader("🧠 Commodity AI Summary")

    commodity_section = results.get("commodities")

    if not commodity_section:
        st.info("Commodity analysis is unavailable.")
        return

    commodities = commodity_section.get("commodities", {})

    if not commodities:
        st.info("No commodity market data is currently available.")
        return

    health = commodity_section.get("health", {})
    statistics = commodity_section.get("statistics", {})

    quotes: list[Any] = list(commodities.values())

    def _field(obj: Any, name: str, default: Any = None) -> Any:
        if isinstance(obj, Mapping):
            return obj.get(name, default)
        return getattr(obj, name, default)

    strongest = max(
        quotes,
        key=lambda q: float(_field(q, "change_percent", 0.0) or 0.0),
    )

    weakest = min(
        quotes,
        key=lambda q: float(_field(q, "change_percent", 0.0) or 0.0),
    )

    positive = sum(
        1
        for quote in quotes
        if float(_field(quote, "change_percent", 0.0) or 0.0) > 0.0
    )

    negative = sum(
        1
        for quote in quotes
        if float(_field(quote, "change_percent", 0.0) or 0.0) < 0.0
    )

    if positive > negative:
        market_mood = "Bullish"
    elif negative > positive:
        market_mood = "Bearish"
    else:
        market_mood = "Neutral"

    last_refresh = (
        statistics.get("last_refresh_at")
        or health.get("last_refresh_at")
        or "Unavailable"
    )

    engine_health = (
        "Healthy"
        if health.get("healthy", False)
        else "Unhealthy"
    )

    cache_status = health.get("cache_status", "Unknown")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Commodity Market Mood", market_mood)
        st.metric(
            "Strongest Commodity",
            _field(strongest, "name", "Unknown"),
            f"{float(_field(strongest, 'change_percent', 0.0)):+.2f}%",
        )
        st.metric(
            "Weakest Commodity",
            _field(weakest, "name", "Unknown"),
            f"{float(_field(weakest, 'change_percent', 0.0)):+.2f}%",
        )
        st.metric("Total Commodities", len(quotes))

    with col2:
        st.metric("Last Refresh Time", str(last_refresh))
        st.metric("Commodity Engine Health", engine_health)
        st.metric("Commodity Cache Status", str(cache_status))

def render_commodity_movement_prediction(results: Mapping[str, Any]) -> None:
    """
    Render AI movement prediction for each commodity.

    Args:
        results:
            Dictionary returned by ``TradeOracle.analyze()``.
    """
    import streamlit as st

    st.subheader("📈 Commodity Movement Prediction")

    commodity_section = results.get("commodities")

    if not commodity_section:
        st.info("Commodity analysis is unavailable.")
        return

    commodities = commodity_section.get("commodities", {})

    if not commodities:
        st.info("No commodity movement predictions are available.")
        return

    def _field(obj: Any, name: str, default: Any = "—") -> Any:
        if isinstance(obj, Mapping):
            return obj.get(name, default)
        return getattr(obj, name, default)

    for _, quote in commodities.items():
        movement = _field(quote, "movement_assessment")

        if movement is None:
            continue

        commodity_name = _field(quote, "name", _field(quote, "symbol", "Unknown"))

        with st.container(border=True):
            st.markdown(f"#### {commodity_name}")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "AI Movement Status",
                    str(_field(movement, "ai_movement_status")),
                )
                st.metric(
                    "Movement Strength",
                    f"{float(_field(movement, 'movement_strength', 0.0)):.2f}",
                )
                st.metric(
                    "Movement Confidence",
                    f"{float(_field(movement, 'movement_confidence_index', 0.0)):.2f}%",
                )
                st.metric(
                    "Trend Continuation",
                    f"{float(_field(movement, 'trend_continuation_chance', 0.0)):.2f}%",
                )
                st.metric(
                    "Trend Reversal",
                    f"{float(_field(movement, 'trend_reversal_chance', 0.0)):.2f}%",
                )
                st.metric(
                    "Buying Pressure",
                    f"{float(_field(movement, 'buying_pressure', 0.0)):.2f}%",
                )
                st.metric(
                    "Selling Pressure",
                    f"{float(_field(movement, 'selling_pressure', 0.0)):.2f}%",
                )

            with col2:
                st.metric(
                    "Breakout Chance",
                    f"{float(_field(movement, 'breakout_chance', 0.0)):.2f}%",
                )
                st.metric(
                    "Breakdown Chance",
                    f"{float(_field(movement, 'breakdown_chance', 0.0)):.2f}%",
                )
                st.metric(
                    "Entry Timing",
                    str(_field(movement, "entry_timing")),
                )
                st.metric(
                    "Exit Timing",
                    str(_field(movement, "exit_timing")),
                )
                st.metric(
                    "Signal Stability",
                    f"{float(_field(movement, 'signal_stability', 0.0)):.2f}%",
                )
                st.metric(
                    "False Signal Risk",
                    f"{float(_field(movement, 'false_signal_risk', 0.0)):.2f}%",
                )

            st.info(f"**AI Observation:** {_field(movement, 'ai_observation', 'No observation available.')}")


def render_commodity_dashboard(results: Mapping[str, Any]) -> None:
    """
    Render the complete commodity dashboard section.

    This function combines the live commodity view, AI commodity summary,
    and movement prediction into a single dashboard section while leaving
    the existing dashboard layout unchanged.

    Args:
        results:
            Dictionary returned by ``TradeOracle.analyze()``.
    """
    import streamlit as st

    st.markdown("---")
    st.header("🪙 Commodity Intelligence")

    commodity_section = results.get("commodities")

    if not commodity_section:
        st.info("Commodity analysis is currently unavailable.")
        return

    render_commodity_ai_summary(results)

    st.markdown("")

    render_live_commodities(results)

    st.markdown("")

    render_commodity_movement_prediction(results)

def attach_movement_assessments(
    self,
    commodities: Mapping[str, CommodityQuote],
) -> dict[str, CommodityQuote]:
    """
    Attach a ``MovementAssessment`` to each commodity quote.

    This method augments the commodity quotes immediately prior to
    dashboard rendering without modifying the existing analysis pipeline.
    A new mapping is returned, leaving the supplied mapping unchanged.

    Args:
        commodities:
            Mapping of commodity symbols to ``CommodityQuote`` instances.

    Returns:
        A new mapping whose values expose a ``movement_assessment``
        attribute containing the generated ``MovementAssessment``.
    """
    from dataclasses import replace

    updated: dict[str, CommodityQuote] = {}

    for symbol, quote in commodities.items():
        assessment = self.analyze(quote)

        try:
            # If CommodityQuote already defines movement_assessment.
            updated[symbol] = replace(
                quote,
                movement_assessment=assessment,
            )
        except TypeError:
            # Preserve the existing CommodityQuote implementation by
            # creating a shallow copy and attaching the assessment.
            clone = copy.copy(quote)
            setattr(clone, "movement_assessment", assessment)
            updated[symbol] = clone

    return updated

def _attach_commodity_movement_assessments(
    self,
    commodity_results: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Attach a ``MovementAssessment`` to every commodity quote contained in
    the commodity analysis results.

    The existing result structure is preserved. Only the value associated
    with the ``"commodities"`` key is replaced with an updated mapping
    whose quotes include a ``movement_assessment``.

    Args:
        commodity_results:
            Commodity analysis result dictionary produced by
            ``_analyze_commodities()``.

    Returns:
        A new commodity result dictionary with movement assessments
        attached to each commodity quote.

    Raises:
        RuntimeError:
            If the movement prediction engine has not been initialized.
    """
    if not hasattr(self, "_commodity_movement_ai"):
        raise RuntimeError(
            "CommodityMovementPredictionAI has not been initialized."
        )

    updated_results: dict[str, Any] = dict(commodity_results)

    commodities = commodity_results.get("commodities", {})

    if not isinstance(commodities, Mapping):
        self._logger.warning(
            "Commodity results do not contain a valid 'commodities' mapping."
        )
        updated_results["commodities"] = {}
        return updated_results

    updated_results["commodities"] = (
        self._commodity_movement_ai.attach_movement_assessments(
            commodities=commodities,
        )
    )

    self._logger.debug(
        "Commodity movement assessments attached.",
        extra={
            "commodity_count": len(updated_results["commodities"]),
        },
    )

    return updated_results


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

def _initialize_commodity_movement_ai(self) -> None:
    """
    Initialize the CommodityMovementPredictionAI instance.

    This method constructs the movement prediction companion using
    dependency injection and stores it on the TradeOracle instance for
    later use by the commodity analysis pipeline.

    Raises:
        Exception:
            Re-raises any initialization error after logging.
    """
    self._logger.debug("Initializing CommodityMovementPredictionAI.")

    try:
        self._commodity_movement_ai = CommodityMovementPredictionAI(
            logger_instance=self._logger,
        )

        self._logger.info(
            "CommodityMovementPredictionAI initialized successfully."
        )

    except Exception:
        self._logger.exception(
            "Failed to initialize CommodityMovementPredictionAI."
        )
        raise

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
