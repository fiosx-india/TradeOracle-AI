"""
TradeOracle AI
ai_market_oracle.py

Master AI Intelligence Layer

This module provides the highest-level AI orchestration layer for
TradeOracle AI. It coordinates the existing public modules without
changing their responsibilities.

Architecture

    AIMarketOracle
            │
            ▼
      TradeOracle
            │
            ├── IndicesEngine
            ├── MarketAnalyzer
            ├── NewsAnalyzer
            └── SignalEngine

Responsibilities

* AI orchestration
* Market context construction
* Explainable AI reasoning
* Confidence calibration
* Technical confirmation
* News weighting
* Multi-timeframe intelligence
* Risk evaluation
* Decision normalization
* Extension hook execution

This module intentionally communicates with the existing project only
through public interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from statistics import mean
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Protocol,
    Sequence,
    Tuple,
)

import logging
import math

from oracle_core import TradeOracle
from signal_engine import SignalResult
from market_analyzer import MarketAnalysis
from news_analyzer import NewsAnalysis


LOGGER_NAME = "TradeOracle.AIMarketOracle"

logger = logging.getLogger(LOGGER_NAME)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.setLevel(logging.INFO)
logger.propagate = False


class Decision(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class MarketRegime(Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"


class TrendStrength(Enum):
    VERY_WEAK = "VERY_WEAK"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"


class RiskCategory(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


@dataclass(frozen=True)
class ConfidenceBreakdown:
    technical: float
    news: float
    market_structure: float
    momentum: float
    trend: float
    volatility: float
    confirmation: float

    @property
    def total(self) -> float:
        score = (
            self.technical
            + self.news
            + self.market_structure
            + self.momentum
            + self.trend
            + self.volatility
            + self.confirmation
        )
        return round(max(0.0, min(100.0, score)), 2)


@dataclass(frozen=True)
class MarketContext:
    symbol: str
    timestamp: datetime
    regime: MarketRegime
    trend: str
    momentum: str
    strength: float
    market_score: float
    bullish_score: float
    bearish_score: float
    news_score: float
    confidence: float
    last_price: float
    support: float
    resistance: float
    volume_status: str
    risk_level: str


@dataclass(frozen=True)
class TechnicalConfirmation:
    ema_confirmed: bool
    macd_confirmed: bool
    rsi_confirmed: bool
    adx_confirmed: bool
    breakout_confirmed: bool
    breakdown_confirmed: bool

    @property
    def confirmations(self) -> int:
        return sum(
            (
                self.ema_confirmed,
                self.macd_confirmed,
                self.rsi_confirmed,
                self.adx_confirmed,
                self.breakout_confirmed,
                self.breakdown_confirmed,
            )
        )


@dataclass(frozen=True)
class NewsWeight:
    sentiment: str
    raw_score: float
    bullish_weight: float
    bearish_weight: float
    normalized_score: float


@dataclass(frozen=True)
class TimeframeAssessment:
    timeframe: str
    direction: Decision
    confidence: float
    probability: float


@dataclass(frozen=True)
class RiskProfile:
    category: RiskCategory
    reward_ratio: float
    stop_loss: float
    target_1: float
    target_2: float
    target_3: float


@dataclass
class ExplainableReasoning:
    headline: str
    summary: str
    evidence: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_evidence(self, text: str) -> None:
        if text:
            self.evidence.append(text)

    def add_warning(self, text: str) -> None:
        if text:
            self.warnings.append(text)


@dataclass
class AIInsight:
    symbol: str
    decision: Decision
    confidence: float
    probability: float
    context: MarketContext
    technical: TechnicalConfirmation
    news: NewsWeight
    risk: RiskProfile
    reasoning: ExplainableReasoning
    timeframes: List[TimeframeAssessment]


class AIMarketOracleExtension(Protocol):
    def before_analysis(
        self,
        symbol: str,
        payload: Mapping[str, Any],
    ) -> None:
        ...

    def after_analysis(
        self,
        insight: AIInsight,
    ) -> None:
        ...


class ConfidenceStrategy(Protocol):
    def __call__(
        self,
        market: MarketAnalysis,
        signal: SignalResult,
        news: NewsAnalysis,
    ) -> ConfidenceBreakdown:
        ...


class ExplanationStrategy(Protocol):
    def __call__(
        self,
        market: MarketAnalysis,
        signal: SignalResult,
        news: NewsAnalysis,
    ) -> ExplainableReasoning:
        ...


ExtensionFactory = Callable[[], AIMarketOracleExtension]
StrategyFactory = Callable[..., Any]

DEFAULT_SIGNAL_WEIGHTS: Mapping[str, float] = {
    "technical": 0.35,
    "news": 0.15,
    "trend": 0.15,
    "momentum": 0.10,
    "market_structure": 0.15,
    "volatility": 0.05,
    "confirmation": 0.05,
}

DEFAULT_TIMEFRAMES: Tuple[str, ...] = (
    "5m",
    "15m",
    "30m",
    "1h",
)

SUPPORTED_DECISIONS: Tuple[Decision, ...] = (
    Decision.BUY,
    Decision.SELL,
    Decision.HOLD,
)

class PluginRegistry:
    """
    Central registry for TradeOracle AI plugins.

    The registry stores plugin instances by unique name and provides a
    deterministic execution order. Plugins may optionally implement the
    following lifecycle methods:

        initialize() -> None
        before_analysis(context) -> None
        after_analysis(result) -> None
        shutdown() -> None

    The registry is thread-safe and may be safely shared across multiple
    analysis threads.
    """

    def __init__(self) -> None:
        from threading import RLock

        self._plugins: dict[str, object] = {}
        self._lock = RLock()

    def register(self, name: str, plugin: object) -> None:
        """
        Register a plugin.

        Args:
            name:
                Unique plugin name.
            plugin:
                Plugin instance.

        Raises:
            TypeError:
                If name or plugin is invalid.
            ValueError:
                If the name already exists.
        """
        if not isinstance(name, str) or not name.strip():
            raise TypeError("Plugin name must be a non-empty string.")

        if plugin is None:
            raise TypeError("Plugin instance cannot be None.")

        key = name.strip()

        with self._lock:
            if key in self._plugins:
                raise ValueError(f"Plugin '{key}' is already registered.")

            self._plugins[key] = plugin

    def unregister(self, name: str) -> object:
        """
        Remove a registered plugin.

        Args:
            name:
                Registered plugin name.

        Returns:
            Removed plugin instance.

        Raises:
            KeyError:
                If the plugin is not registered.
        """
        with self._lock:
            return self._plugins.pop(name)

    def get(self, name: str) -> object:
        """
        Retrieve a registered plugin.

        Args:
            name:
                Plugin name.

        Returns:
            Registered plugin instance.

        Raises:
            KeyError:
                If the plugin is not registered.
        """
        with self._lock:
            return self._plugins[name]

    def exists(self, name: str) -> bool:
        """
        Check whether a plugin exists.
        """
        with self._lock:
            return name in self._plugins

    def names(self) -> tuple[str, ...]:
        """
        Return registered plugin names in registration order.
        """
        with self._lock:
            return tuple(self._plugins.keys())

    def plugins(self) -> tuple[object, ...]:
        """
        Return registered plugin instances in registration order.
        """
        with self._lock:
            return tuple(self._plugins.values())

    def initialize_all(self) -> None:
        """
        Invoke initialize() on every registered plugin that implements it.
        """
        with self._lock:
            plugins = tuple(self._plugins.values())

        for plugin in plugins:
            method = getattr(plugin, "initialize", None)
            if callable(method):
                method()

    def before_analysis(self, context: object) -> None:
        """
        Invoke before_analysis() on every compatible plugin.
        """
        with self._lock:
            plugins = tuple(self._plugins.values())

        for plugin in plugins:
            method = getattr(plugin, "before_analysis", None)
            if callable(method):
                method(context)

    def after_analysis(self, result: object) -> None:
        """
        Invoke after_analysis() on every compatible plugin.
        """
        with self._lock:
            plugins = tuple(self._plugins.values())

        for plugin in plugins:
            method = getattr(plugin, "after_analysis", None)
            if callable(method):
                method(result)

    def shutdown_all(self) -> None:
        """
        Invoke shutdown() on every registered plugin that implements it.

        Plugins are invoked in reverse registration order to mirror the
        initialization sequence.
        """
        with self._lock:
            plugins = tuple(reversed(tuple(self._plugins.values())))

        for plugin in plugins:
            method = getattr(plugin, "shutdown", None)
            if callable(method):
                method()

    def clear(self) -> None:
        """
        Remove all registered plugins.
        """
        with self._lock:
            self._plugins.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._plugins)

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return False

        with self._lock:
            return name in self._plugins

    def __iter__(self):
        with self._lock:
            return iter(tuple(self._plugins.items()))

class AIMarketOracle:
    def __init__(
        self,
        oracle: TradeOracle | None = None,
        *,
        configuration: Mapping[str, Any] | None = None,
        logger_instance: logging.Logger | None = None,
        extensions: Iterable[AIMarketOracleExtension] | None = None,
    ) -> None:
        """
        Initialize the master AI intelligence layer.

        Args:
            oracle:
                Existing TradeOracle instance. When omitted, a new instance is
                created using the project's public API.

            configuration:
                Optional runtime configuration. User-supplied values override the
                built-in defaults.

            logger_instance:
                Optional logger. When omitted, the module logger is used.

            extensions:
                Optional collection of AI extensions implementing the
                AIMarketOracleExtension protocol.
        """
        self._logger: logging.Logger = logger_instance or logger

        self._logger.debug("Initializing AIMarketOracle.")

        # ------------------------------------------------------------------
        # Core TradeOracle integration
        # ------------------------------------------------------------------
        self._oracle: TradeOracle = oracle if oracle is not None else TradeOracle()

        # Public engine references (obtained only through TradeOracle)
        self._indices = self._oracle.indices
        self._market = self._oracle.market
        self._news = self._oracle.news
        self._signal = self._oracle.signal

        # ------------------------------------------------------------------
        # Configuration
        # ------------------------------------------------------------------
        defaults: dict[str, Any] = {
            "confidence_floor": 50.0,
            "confidence_ceiling": 100.0,
            "enable_news_weighting": True,
            "enable_multi_timeframe": True,
            "enable_risk_analysis": True,
            "enable_explainability": True,
            "default_timeframes": DEFAULT_TIMEFRAMES,
            "signal_weights": dict(DEFAULT_SIGNAL_WEIGHTS),
        }

        self._config: dict[str, Any] = defaults

        if configuration:
            self._config.update(dict(configuration))

        # ------------------------------------------------------------------
        # Extension management
        # ------------------------------------------------------------------
        self._extensions: list[AIMarketOracleExtension] = (
            list(extensions) if extensions is not None else []
        )

        # ------------------------------------------------------------------
        # Internal state
        # ------------------------------------------------------------------
        self._initialized_at: datetime = datetime.utcnow()
        self._analysis_count: int = 0
        self._last_analysis_at: datetime | None = None

        self._market_contexts: dict[str, MarketContext] = {}
        self._latest_insights: dict[str, AIInsight] = {}

        # ------------------------------------------------------------------
        # Helper objects
        # ------------------------------------------------------------------
        self._confidence_strategy: ConfidenceStrategy | None = None
        self._explanation_strategy: ExplanationStrategy | None = None

        self._logger.info(
            "AIMarketOracle initialized.",
            extra={
                "extensions": len(self._extensions),
                "configuration_keys": tuple(sorted(self._config.keys())),
            },
        )
        

    
