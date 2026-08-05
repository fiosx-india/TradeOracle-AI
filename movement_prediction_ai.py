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
