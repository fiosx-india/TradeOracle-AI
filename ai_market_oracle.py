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
        

    def register_extension(
        self,
        extension: AIMarketOracleExtension,
    ) -> None:
        """
        Register an AI extension.

        The extension is appended to the execution pipeline and will
        participate in subsequent analysis runs through the existing
        lifecycle hooks.

        Args:
            extension:
                Extension implementing the AIMarketOracleExtension protocol.

        Raises:
            TypeError:
                If the supplied object is None.
            ValueError:
                If the extension is already registered.
        """
        if extension is None:
            raise TypeError("extension cannot be None.")

        if extension in self._extensions:
            raise ValueError("Extension is already registered.")

        self._extensions.append(extension)

        self._logger.info(
            "AI extension registered.",
            extra={
                "extension": type(extension).__name__,
                "extension_count": len(self._extensions),
            },
        )


    def unregister_extension(
        self,
        extension: AIMarketOracleExtension,
    ) -> None:
        """
        Unregister a previously registered AI extension.

        Args:
            extension:
                Registered extension instance.

        Raises:
            ValueError:
                If the extension is not currently registered.
        """
        self._extensions.remove(extension)

        self._logger.info(
            "AI extension unregistered.",
            extra={
                "extension": type(extension).__name__,
                "extension_count": len(self._extensions),
            },
        )


    def get_extensions(
        self,
    ) -> Tuple[AIMarketOracleExtension, ...]:
        """
        Return the currently registered AI extensions.

        Returns:
            An immutable tuple containing the registered extensions in
            execution order.
        """
        return tuple(self._extensions)

    def _build_market_context(
        self,
        symbol: str,
        market: MarketAnalysis,
        news: NewsAnalysis,
        signal: SignalResult,
    ) -> MarketContext:
        """
        Construct a MarketContext instance from the existing TradeOracle public
        analysis objects.

        Args:
            symbol:
                Market symbol.

            market:
                Technical market analysis produced by ``MarketAnalyzer``.

            news:
                News analysis produced by ``NewsAnalyzer``.

            signal:
                Trading signal produced by ``SignalEngine``.

        Returns:
            A populated ``MarketContext`` describing the current market state.
        """
        if market.market_score >= 20:
            regime = MarketRegime.BULL
        elif market.market_score <= -20:
            regime = MarketRegime.BEAR
        elif market.strength >= 30:
            regime = MarketRegime.VOLATILE
        else:
            regime = MarketRegime.SIDEWAYS

        return MarketContext(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            regime=regime,
            trend=market.trend,
            momentum=market.momentum,
            strength=market.strength,
            market_score=market.market_score,
            bullish_score=market.bullish_score,
            bearish_score=market.bearish_score,
            news_score=news.total_score,
            confidence=signal.confidence,
            last_price=market.last_price,
            support=market.support,
            resistance=market.resistance,
            volume_status=market.volume_status,
            risk_level=signal.risk_level,
        )

    def _build_technical_confirmation(
        self,
        market: MarketAnalysis,
    ) -> TechnicalConfirmation:
        """
        Build a technical confirmation summary from the current market analysis.

        The confirmation flags are derived exclusively from the existing
        ``MarketAnalysis`` public interface without introducing any additional
        project-specific APIs.

        Args:
            market:
                Market analysis generated by ``MarketAnalyzer``.

        Returns:
            A populated ``TechnicalConfirmation`` instance.
        """
        return TechnicalConfirmation(
            ema_confirmed=market.ema20 > market.ema50,
            macd_confirmed=market.macd > market.signal_line,
            rsi_confirmed=market.rsi >= 60.0,
            adx_confirmed=market.adx >= 25.0,
            breakout_confirmed=market.breakout,
            breakdown_confirmed=market.breakdown,
        )

    def _build_news_weight(
        self,
        news: NewsAnalysis,
    ) -> NewsWeight:
        """
        Build a normalized news weighting model from the current news analysis.

        The weighting is derived exclusively from the public ``NewsAnalysis``
        interface and does not depend on any additional project APIs.

        Args:
            news:
                News analysis generated by ``NewsAnalyzer``.

        Returns:
            A populated ``NewsWeight`` instance.
        """
        total_weight = news.bullish_score + news.bearish_score

        if total_weight > 0.0:
            bullish_weight = round(news.bullish_score / total_weight, 4)
            bearish_weight = round(news.bearish_score / total_weight, 4)
        else:
            bullish_weight = 0.0
            bearish_weight = 0.0

        if news.news_count > 0:
            normalized_score = round(
                news.total_score / float(news.news_count),
                2,
            )
        else:
            normalized_score = 0.0

        return NewsWeight(
            sentiment=news.overall_sentiment,
            raw_score=news.total_score,
            bullish_weight=bullish_weight,
            bearish_weight=bearish_weight,
            normalized_score=normalized_score,
        )

    def _invoke_extensions_before(
        self,
        context: Mapping[str, Any],
    ) -> None:
        """
        Invoke the ``before_analysis`` lifecycle hook on all registered
        extensions.

        Extensions that do not implement ``before_analysis`` are ignored.
        Exceptions raised by an individual extension are isolated so that
        remaining extensions continue to execute.

        Args:
            context:
                Immutable analysis context passed to each extension.
        """
        if not self._extensions:
            return

        self._logger.debug(
            "Invoking before_analysis extensions.",
            extra={"extension_count": len(self._extensions)},
        )

        for extension in self._extensions:
            method = getattr(extension, "before_analysis", None)

            if not callable(method):
                continue

            extension_name = type(extension).__name__

            try:
                self._logger.debug(
                    "Executing before_analysis extension.",
                    extra={"extension": extension_name},
                )

                method(context)

                self._logger.debug(
                    "before_analysis extension completed.",
                    extra={"extension": extension_name},
                )

            except Exception:
                self._logger.exception(
                    "before_analysis extension failed.",
                    extra={"extension": extension_name},
                )

    def _invoke_extensions_after(
        self,
        insight: AIInsight,
    ) -> None:
        """
        Invoke the ``after_analysis`` lifecycle hook on all registered
        extensions.

        Extensions that do not implement ``after_analysis`` are ignored.
        Exceptions raised by an individual extension are isolated so that
        remaining extensions continue to execute.

        Args:
            insight:
                The completed AI insight passed to each extension.
        """
        if not self._extensions:
            return

        self._logger.debug(
            "Invoking after_analysis extensions.",
            extra={"extension_count": len(self._extensions)},
        )

        for extension in self._extensions:
            method = getattr(extension, "after_analysis", None)

            if not callable(method):
                continue

            extension_name = type(extension).__name__

            try:
                self._logger.debug(
                    "Executing after_analysis extension.",
                    extra={"extension": extension_name},
                )

                method(insight)

                self._logger.debug(
                    "after_analysis extension completed.",
                    extra={"extension": extension_name},
                )

            except Exception:
                self._logger.exception(
                    "after_analysis extension failed.",
                    extra={"extension": extension_name},
                )

    def _build_risk_profile(
        self,
        signal: SignalResult,
        market: MarketAnalysis,
    ) -> RiskProfile:
        """
        Build a normalized risk profile from the existing TradeOracle analysis
        objects.

        This method relies exclusively on the public interfaces exposed by
        ``SignalResult`` and ``MarketAnalysis`` and performs no market-specific
        inference beyond normalizing the available values.

        Args:
            signal:
                Trading signal generated by ``SignalEngine``.

            market:
                Market analysis generated by ``MarketAnalyzer``.

        Returns:
            A populated ``RiskProfile`` instance.
        """
        signal_risk = signal.risk_level.upper()

        if signal_risk == "LOW":
            category = RiskCategory.LOW
        elif signal_risk == "MEDIUM":
            category = RiskCategory.MEDIUM
        elif signal_risk == "HIGH":
            category = RiskCategory.HIGH
        else:
            category = RiskCategory.EXTREME

        reward_ratio = signal.risk_reward

        if reward_ratio <= 0.0:
            entry = signal.entry_price

            if signal.signal == "BUY":
                risk = max(0.0, entry - signal.stoploss)
                reward = max(0.0, signal.target1 - entry)
            elif signal.signal == "SELL":
                risk = max(0.0, signal.stoploss - entry)
                reward = max(0.0, entry - signal.target1)
            else:
                risk = 0.0
                reward = 0.0

            if risk > 0.0:
                reward_ratio = round(reward / risk, 2)
            else:
                reward_ratio = 0.0

        stop_loss = signal.stoploss if signal.stoploss > 0.0 else market.support

        target_1 = signal.target1
        if target_1 <= 0.0:
            target_1 = signal.target if signal.target > 0.0 else market.resistance

        target_2 = signal.target2 if signal.target2 > 0.0 else target_1
        target_3 = signal.target3 if signal.target3 > 0.0 else target_2

        return RiskProfile(
            category=category,
            reward_ratio=reward_ratio,
            stop_loss=stop_loss,
            target_1=target_1,
            target_2=target_2,
            target_3=target_3,
        )

    def _build_explainable_reasoning(
        self,
        market: MarketAnalysis,
        news: NewsAnalysis,
        signal: SignalResult,
    ) -> ExplainableReasoning:
        """
        Build an explainable reasoning summary using the existing TradeOracle
        public analysis models.

        Args:
            market:
                Market analysis generated by ``MarketAnalyzer``.

            news:
                News analysis generated by ``NewsAnalyzer``.

            signal:
                Trading signal generated by ``SignalEngine``.

        Returns:
            A populated ``ExplainableReasoning`` instance.
        """
        reasoning = ExplainableReasoning(
            headline=f"{signal.signal} Recommendation",
            summary=signal.reason or "No additional reasoning available.",
        )

        # ------------------------------------------------------------------
        # Technical Evidence
        # ------------------------------------------------------------------
        reasoning.add_evidence(f"Market trend: {market.trend}.")
        reasoning.add_evidence(f"Momentum: {market.momentum}.")
        reasoning.add_evidence(
            f"Market score: {market.market_score:.2f} "
            f"(Bullish {market.bullish_score:.2f} / "
            f"Bearish {market.bearish_score:.2f})."
        )

        if market.breakout:
            reasoning.add_evidence(
                "Price is trading at or above the recorded breakout level."
            )

        if market.breakdown:
            reasoning.add_evidence(
                "Price is trading at or below the recorded breakdown level."
            )

        if market.ema20 > market.ema50:
            reasoning.add_evidence(
                "EMA20 is above EMA50, confirming bullish trend alignment."
            )
        elif market.ema20 < market.ema50:
            reasoning.add_evidence(
                "EMA20 is below EMA50, confirming bearish trend alignment."
            )

        if market.macd > market.signal_line:
            reasoning.add_evidence(
                "MACD is above the signal line."
            )
        elif market.macd < market.signal_line:
            reasoning.add_evidence(
                "MACD is below the signal line."
            )

        if market.rsi >= 60:
            reasoning.add_evidence(
                f"RSI ({market.rsi:.2f}) supports bullish momentum."
            )
        elif market.rsi <= 40:
            reasoning.add_evidence(
                f"RSI ({market.rsi:.2f}) supports bearish momentum."
            )

        if market.adx >= 25:
            reasoning.add_evidence(
                f"ADX ({market.adx:.2f}) indicates a relatively strong trend."
            )

        # ------------------------------------------------------------------
        # News Evidence
        # ------------------------------------------------------------------
        reasoning.add_evidence(
            f"News sentiment: {news.overall_sentiment} "
            f"(Score: {news.total_score:.2f})."
        )

        if news.news_count > 0:
            reasoning.add_evidence(
                f"News items analysed: {news.news_count} "
                f"(Positive: {news.positive_count}, "
                f"Negative: {news.negative_count})."
            )

        if news.high_impact:
            reasoning.add_warning(
                "High-impact news may increase short-term volatility."
            )

        # ------------------------------------------------------------------
        # Signal Evidence
        # ------------------------------------------------------------------
        reasoning.add_evidence(
            f"AI signal: {signal.signal} "
            f"with confidence {signal.confidence:.2f}% "
            f"and probability {signal.probability:.2f}%."
        )

        reasoning.add_evidence(
            f"Expected holding period: {signal.expected_time}."
        )

        if signal.risk_reward > 0:
            reasoning.add_evidence(
                f"Risk/Reward ratio: {signal.risk_reward:.2f}."
            )

        # ------------------------------------------------------------------
        # Warnings
        # ------------------------------------------------------------------
        if signal.signal == "HOLD":
            reasoning.add_warning(
                "No clear directional edge was identified."
            )

        if signal.risk_level.upper() == "HIGH":
            reasoning.add_warning(
                "Current setup is classified as high risk."
            )

        if (
            market.prediction_5m
            != market.prediction_15m
            or market.prediction_15m
            != market.prediction_30m
            or market.prediction_30m
            != market.prediction_1h
        ):
            reasoning.add_warning(
                "Forecasts across available timeframes are not fully aligned."
            )

        if (
            news.overall_sentiment == "POSITIVE"
            and market.market_score < 0
        ) or (
            news.overall_sentiment == "NEGATIVE"
            and market.market_score > 0
        ):
            reasoning.add_warning(
                "Technical analysis and news sentiment are not aligned."
            )

        return reasoning

    def _build_timeframe_assessments(
        self,
        market: MarketAnalysis,
        signal: SignalResult,
    ) -> List[TimeframeAssessment]:
        """
        Build timeframe assessments from the existing market predictions.

        This method uses only the public ``MarketAnalysis`` and
        ``SignalResult`` interfaces.

        Args:
            market:
                Market analysis generated by ``MarketAnalyzer``.

            signal:
                Trading signal generated by ``SignalEngine``.

        Returns:
            A list of ``TimeframeAssessment`` instances ordered from the
            shortest to the longest timeframe.
        """

        def _to_decision(prediction: str) -> Decision:
            value = prediction.upper()

            if value == "UP":
                return Decision.BUY

            if value == "DOWN":
                return Decision.SELL

            return Decision.HOLD

        timeframe_predictions = (
            ("5m", market.prediction_5m),
            ("15m", market.prediction_15m),
            ("30m", market.prediction_30m),
            ("1h", market.prediction_1h),
        )

        assessments: List[TimeframeAssessment] = []

        for timeframe, prediction in timeframe_predictions:
            decision = _to_decision(prediction)

            if decision == Decision.HOLD:
                confidence = min(signal.confidence, 50.0)
                probability = min(signal.probability, 50.0)
            else:
                confidence = signal.confidence
                probability = signal.probability

            assessments.append(
                TimeframeAssessment(
                    timeframe=timeframe,
                    direction=decision,
                    confidence=round(confidence, 2),
                    probability=round(probability, 2),
                )
            )

        return assessments

    def _build_decision(
        self,
        signal: SignalResult,
    ) -> Decision:
        """
        Convert a ``SignalResult`` into a normalized ``Decision``.

        The conversion is performed exclusively from the public
        ``SignalResult.signal`` field. The comparison is case-insensitive,
        ignores surrounding whitespace, and safely defaults to
        ``Decision.HOLD`` for unknown or missing values.

        Args:
            signal:
                Trading signal generated by ``SignalEngine``.

        Returns:
            The corresponding normalized ``Decision``.
        """
        value = signal.signal.strip().upper()

        if value == Decision.BUY.value:
            return Decision.BUY

        if value == Decision.SELL.value:
            return Decision.SELL

        return Decision.HOLD

    def _build_ai_insight(
        self,
        symbol: str,
        market: MarketAnalysis,
        news: NewsAnalysis,
        signal: SignalResult,
    ) -> AIInsight:
        """
        Build a complete AIInsight from the existing TradeOracle analysis
        objects.

        This method is intentionally side-effect free. It performs no cache
        updates, does not invoke extensions, and does not modify any internal
        AIMarketOracle state.

        Args:
            symbol:
                Trading symbol.

            market:
                Market analysis generated by ``MarketAnalyzer``.

            news:
                News analysis generated by ``NewsAnalyzer``.

            signal:
                Trading signal generated by ``SignalEngine``.

        Returns:
            A fully populated ``AIInsight`` instance.
        """
        decision = self._build_decision(signal)

        context = self._build_market_context(
            symbol=symbol,
            market=market,
            news=news,
            signal=signal,
        )

        technical = self._build_technical_confirmation(
            market=market,
        )

        news_weight = self._build_news_weight(
            news=news,
        )

        risk = self._build_risk_profile(
            signal=signal,
            market=market,
        )

        reasoning = self._build_explainable_reasoning(
            market=market,
            news=news,
            signal=signal,
        )

        timeframe_assessments = self._build_timeframe_assessments(
            market=market,
            signal=signal,
        )

        return AIInsight(
            symbol=symbol,
            decision=decision,
            confidence=signal.confidence,
            probability=signal.probability,
            context=context,
            technical=technical,
            news=news_weight,
            risk=risk,
            reasoning=reasoning,
            timeframes=timeframe_assessments,
        )

    def _collect_analysis_inputs(
        self,
    ) -> tuple[
        dict[str, Any],
        dict[str, MarketAnalysis],
        NewsAnalysis,
    ]:
        """
        Collect the current TradeOracle analysis inputs.

        This method gathers the existing public objects produced by the
        TradeOracle pipeline without performing any AI processing.

        Returns:
            A tuple containing:

            - market_data:
                Mapping of symbol to index data returned by
                ``TradeOracle.indices.get_all_indices()``.

            - market_reports:
                Mapping of symbol to ``MarketAnalysis`` produced by
                ``MarketAnalyzer.analyze_all()``.

            - news_report:
                The current ``NewsAnalysis`` produced by
                ``NewsAnalyzer.analyze()``.

        Raises:
            RuntimeError:
                If market data cannot be collected.
        """
        self._logger.debug("Collecting TradeOracle analysis inputs.")

        market_data = self._indices.get_all_indices()

        if not market_data:
            self._logger.warning("No market data available from IndicesEngine.")
            raise RuntimeError("No market data available.")

        market_reports = self._market.analyze_all(market_data)

        news_report = self._news.analyze()

        self._logger.debug(
            "TradeOracle analysis inputs collected.",
            extra={
                "symbols": len(market_data),
                "news_items": news_report.news_count,
            },
        )

        return market_data, market_reports, news_report


    def _update_internal_state(
        self,
        symbol: str,
        insight: AIInsight,
    ) -> None:
        """
        Update the internal AIMarketOracle state with the latest analysis result.

        This method performs only internal cache and state updates. It does not
        invoke extensions, perform additional analysis, or modify any external
        TradeOracle components.

        Args:
            symbol:
                Trading symbol associated with the analysis.

            insight:
                The completed AI insight to cache.
        """
        self._latest_insights[symbol] = insight
        self._market_contexts[symbol] = insight.context
        self._analysis_count += 1
        self._last_analysis_at = datetime.utcnow()

