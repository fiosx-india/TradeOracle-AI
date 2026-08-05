from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True, slots=True)
class MovementAssessment:
    """
    Immutable companion assessment describing the quality and expected
    evolution of an existing trading signal.

    This assessment supplements the existing SignalEngine output and does
    not replace or modify BUY/SELL/HOLD decisions, confidence, probability,
    entry, targets, or stop-loss values.
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

    target1_reach_confidence: float
    target2_reach_confidence: float
    target3_reach_confidence: float

    entry_timing: str
    exit_timing: str

    acceleration_status: str
    deceleration_status: str

    market_energy: float
    volatility_state: str

    signal_stability: float
    false_signal_risk: float

    ai_observation: str
    ai_evidence_summary: Tuple[str, ...]
    ai_explanation: str

from enum import Enum


class MovementStatus(Enum):
    """Overall movement state of the existing signal."""

    STRENGTHENING = "STRENGTHENING"
    STABLE = "STABLE"
    WEAKENING = "WEAKENING"
    REVERSING = "REVERSING"
    CONSOLIDATING = "CONSOLIDATING"


class TimingQuality(Enum):
    """Quality assessment for entry or exit timing."""

    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    AVOID = "AVOID"


class AccelerationStatus(Enum):
    """Current momentum acceleration state."""

    ACCELERATING = "ACCELERATING"
    STABLE = "STABLE"
    DECELERATING = "DECELERATING"


class VolatilityState(Enum):
    """Current market volatility regime."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class MarketEnergy(Enum):
    """Overall market participation and directional energy."""

    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"

from typing import Final, Mapping

DEFAULT_MOVEMENT_CONFIGURATION: Final[Mapping[str, float | int | bool]] = {
    # Normalized score limits
    "minimum_score": 0.0,
    "maximum_score": 100.0,

    # Classification thresholds
    "high_confidence_threshold": 80.0,
    "medium_confidence_threshold": 60.0,
    "low_confidence_threshold": 40.0,

    # Trend assessment
    "trend_continuation_weight": 0.25,
    "trend_reversal_weight": 0.20,
    "momentum_weight": 0.15,
    "market_structure_weight": 0.15,
    "volume_weight": 0.10,
    "volatility_weight": 0.10,
    "news_weight": 0.05,

    # Breakout / Breakdown
    "breakout_confirmation_threshold": 70.0,
    "breakdown_confirmation_threshold": 70.0,

    # Signal quality
    "false_signal_warning_threshold": 65.0,
    "signal_stability_threshold": 75.0,

    # Target reach assessment
    "target1_weight": 1.00,
    "target2_weight": 0.80,
    "target3_weight": 0.60,

    # Timing assessment
    "entry_quality_threshold": 75.0,
    "exit_quality_threshold": 75.0,

    # Market energy
    "market_energy_threshold": 60.0,

    # Deterministic behaviour
    "rounding_precision": 2,
    "clamp_scores": True,
}

MOVEMENT_SCORE_RANGE: Final[tuple[float, float]] = (0.0, 100.0)

MOVEMENT_TIMEFRAMES: Final[tuple[str, ...]] = (
    "5m",
    "15m",
    "30m",
    "1h",
)

SUPPORTED_MOVEMENT_FIELDS: Final[tuple[str, ...]] = (
    "trend",
    "momentum",
    "rsi",
    "macd",
    "ema",
    "vwap",
    "adx",
    "atr",
    "support",
    "resistance",
    "breakout",
    "breakdown",
    "market_score",
    "confidence",
    "probability",
    "risk_level",
    "entry_price",
    "target1",
    "target2",
    "target3",
    "stoploss",
    "risk_reward",
    "expected_time",
    "overall_sentiment",
)

LOGGER_NAME: Final[str] = "TradeOracle.MovementPredictionAI"

from typing import Protocol


class MarketAnalysisProtocol(Protocol):
    """Minimum public MarketAnalysis interface required by MovementPredictionAI."""

    trend: str
    momentum: str

    strength: float
    market_score: float
    bullish_score: float
    bearish_score: float

    last_price: float
    support: float
    resistance: float

    ema20: float
    ema50: float

    rsi: float

    macd: float
    signal_line: float

    vwap: float
    atr: float
    adx: float

    volume_status: str

    breakout: bool
    breakdown: bool

    prediction_5m: str
    prediction_15m: str
    prediction_30m: str
    prediction_1h: str


class NewsAnalysisProtocol(Protocol):
    """Minimum public NewsAnalysis interface required by MovementPredictionAI."""

    overall_sentiment: str

    total_score: float

    news_count: int

    bullish_score: float
    bearish_score: float

    positive_count: int
    negative_count: int

    recommendation: str

    high_impact: bool


class SignalResultProtocol(Protocol):
    """Minimum public SignalResult interface required by MovementPredictionAI."""

    signal: str

    confidence: float
    probability: float

    expected_time: str

    reason: str

    market_score: float
    news_score: float

    risk_level: str

    entry_price: float

    target: float
    target1: float
    target2: float
    target3: float

    stoploss: float

    risk_reward: float

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True, slots=True)
class MovementEvidence:
    """
    Immutable evidence supporting the overall movement assessment.
    """

    trend_alignment: float
    momentum_alignment: float
    market_structure_score: float
    technical_confirmation_score: float
    news_alignment_score: float
    signal_alignment_score: float
    supporting_factors: Tuple[str, ...]
    warning_factors: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TimingEvidence:
    """
    Immutable evidence supporting entry and exit timing assessments.
    """

    entry_score: float
    exit_score: float
    entry_distance: float
    stoploss_distance: float
    target_distance: float
    risk_reward_ratio: float
    expected_time: str
    observations: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PressureEvidence:
    """
    Immutable evidence describing buying and selling pressure.
    """

    buying_pressure: float
    selling_pressure: float
    trend_strength: float
    momentum_strength: float
    volume_strength: float
    market_energy: float
    acceleration_score: float
    deceleration_score: float
    observations: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TargetEvidence:
    """
    Immutable evidence supporting target reach assessments.
    """

    target1_confidence: float
    target2_confidence: float
    target3_confidence: float
    breakout_probability: float
    breakdown_probability: float
    continuation_probability: float
    reversal_probability: float
    false_signal_probability: float
    observations: Tuple[str, ...]

