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
