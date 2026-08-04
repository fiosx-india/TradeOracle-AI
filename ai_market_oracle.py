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

