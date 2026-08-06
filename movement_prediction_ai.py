from dataclasses import dataclass
from enum import Enum
import logging

from typing import (
    Any,
    Final,
    Mapping,
    Protocol,
    Tuple,
)

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

class MovementPredictionAI:
    """
    AI companion responsible for evaluating how an existing BUY/SELL/HOLD
    signal is likely to evolve.

    This class does not generate trading signals. Instead, it analyzes the
    strength, continuation, reversal, breakout potential, buying pressure,
    selling pressure, target confidence, and overall quality of an existing
    signal before it reaches the dashboard.
    """

    def __init__(
        self,
        *,
        configuration: Mapping[str, Any] | None = None,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        self._logger = (
            logger_instance
            if logger_instance is not None
            else logging.getLogger(LOGGER_NAME)
        )

        self._config = dict(DEFAULT_MOVEMENT_CONFIGURATION)

        if configuration:
            self._config.update(configuration)

        self._analysis_count = 0
        self._last_error = None

        self._assessment_cache: dict[str, MovementAssessment] = {}
        self._evidence_cache: dict[str, MovementEvidence] = {}

        self._logger.info(
            "MovementPredictionAI initialized.",
            extra={
                "configuration_keys": tuple(sorted(self._config.keys()))
            },
        )


    def analyze(
        self,
        market: MarketAnalysisProtocol,
        news: NewsAnalysisProtocol,
        signal: SignalResultProtocol,
    ) -> MovementAssessment:
        """
        Analyze an existing trading signal and produce a MovementAssessment.

        This method orchestrates the internal analysis pipeline without
        modifying the existing BUY/SELL/HOLD signal.
        """

        self._analysis_count += 1

        try:
            trend_strength = self._calculate_trend_strength(
                market,
                signal,
            )

            pressure = self._calculate_buying_selling_pressure(
                market,
                signal,
            )

            breakout_probability = self._calculate_breakout_probability(
                market,
                signal,
                trend_strength,
                pressure,
            )

            target_confidence = self._calculate_target_confidence(
                market,
                signal,
                trend_strength,
                pressure,
                breakout_probability,
            )

            assessment = self._build_movement_assessment(
                market=market,
                news=news,
                signal=signal,
                trend_strength=trend_strength,
                pressure=pressure,
                target_confidence=target_confidence,
            )

            return assessment

        except Exception as exc:
            self._last_error = exc
            self._logger.exception(
                "Movement prediction analysis failed."
            )
            raise
    def _calculate_trend_strength(
        self,
        market: MarketAnalysisProtocol,
        signal: SignalResultProtocol,
    ) -> float:
        """
        Calculate a normalized trend strength score using the
        existing market and signal objects.
        """

        score = 0.0

        # Trend
        if market.trend.upper() == "BULLISH":
            score += 20.0
        elif market.trend.upper() == "BEARISH":
            score += 20.0

        # Momentum
        momentum = market.momentum.upper()

        if momentum == "VERY_STRONG":
            score += 20.0
        elif momentum == "STRONG":
            score += 16.0
        elif momentum == "MODERATE":
            score += 12.0
        elif momentum == "WEAK":
            score += 6.0

        # ADX
        if market.adx >= 40:
            score += 20.0
        elif market.adx >= 25:
            score += 15.0
        elif market.adx >= 15:
            score += 8.0

        # Market Strength
        score += min(15.0, float(market.strength) * 0.25)

        # Confidence
        score += min(15.0, float(signal.confidence) * 0.15)

        # Probability
        score += min(10.0, float(signal.probability) * 0.10)

        minimum = float(self._config["minimum_score"])
        maximum = float(self._config["maximum_score"])
        precision = int(self._config["rounding_precision"])

        score = max(minimum, min(maximum, score))

        self._logger.debug(
            "Trend strength calculated.",
            extra={
                "trend_strength": score,
            },
        )

        return round(score, precision)

    def _calculate_buying_selling_pressure(
        self,
        market: MarketAnalysisProtocol,
        signal: SignalResultProtocol,
    ) -> PressureEvidence:
        """
        Calculate buying and selling pressure using market trend,
        momentum, technical indicators and signal confidence.
        """

        buying_pressure = 0.0
        selling_pressure = 0.0

        observations: list[str] = []

        # Trend
        if market.trend.upper() == "BULLISH":
            buying_pressure += 20.0
            observations.append("Bullish trend")
        elif market.trend.upper() == "BEARISH":
            selling_pressure += 20.0
            observations.append("Bearish trend")

        # Momentum
        momentum = market.momentum.upper()

        if momentum == "VERY_STRONG":
            if buying_pressure >= selling_pressure:
                buying_pressure += 20.0
            else:
                selling_pressure += 20.0

        elif momentum == "STRONG":
            if buying_pressure >= selling_pressure:
                buying_pressure += 15.0
            else:
                selling_pressure += 15.0

        elif momentum == "MODERATE":
            if buying_pressure >= selling_pressure:
                buying_pressure += 10.0
            else:
                selling_pressure += 10.0

        else:
            observations.append("Weak momentum")

        # RSI
        if market.rsi >= 70:
            buying_pressure += 15.0

        elif market.rsi >= 60:
            buying_pressure += 10.0

        elif market.rsi <= 30:
            selling_pressure += 15.0

        elif market.rsi <= 40:
            selling_pressure += 10.0

        # EMA
        ema_gap = abs(market.ema20 - market.ema50)

        if market.ema20 > market.ema50:
            buying_pressure += min(15.0, max(5.0, ema_gap))

        elif market.ema20 < market.ema50:
            selling_pressure += min(15.0, max(5.0, ema_gap))

        # MACD
        macd_gap = abs(market.macd - market.signal_line)

        if market.macd > market.signal_line:
            buying_pressure += min(15.0, max(5.0, macd_gap * 10))

        elif market.macd < market.signal_line:
            selling_pressure += min(15.0, max(5.0, macd_gap * 10))

        # ADX
        if market.adx >= 40:
            if buying_pressure >= selling_pressure:
                buying_pressure += 10.0
            else:
                selling_pressure += 10.0

        elif market.adx >= 25:
            if buying_pressure >= selling_pressure:
                buying_pressure += 5.0
            else:
                selling_pressure += 5.0

        # VWAP
        if market.last_price >= market.vwap:
            buying_pressure += 10.0
        else:
            selling_pressure += 10.0

        # Breakout / Breakdown
        if market.breakout:
            buying_pressure += 15.0
            observations.append("Breakout confirmed")

        if market.breakdown:
            selling_pressure += 15.0
            observations.append("Breakdown confirmed")

        # Signal confidence
        confidence_bonus = signal.confidence * 0.15

        if signal.signal.upper() == "BUY":
            buying_pressure += confidence_bonus

        elif signal.signal.upper() == "SELL":
            selling_pressure += confidence_bonus

        minimum = float(self._config["minimum_score"])
        maximum = float(self._config["maximum_score"])
        precision = int(self._config["rounding_precision"])

        buying_pressure = max(minimum, min(maximum, buying_pressure))
        selling_pressure = max(minimum, min(maximum, selling_pressure))

        market_energy = max(
            buying_pressure,
            selling_pressure,
            float(market.strength),
        )

        return PressureEvidence(
            buying_pressure=round(buying_pressure, precision),
            selling_pressure=round(selling_pressure, precision),

            trend_strength=round(
                abs(market.market_score),
                precision,
            ),

            momentum_strength=round(
                float(market.strength),
                precision,
            ),

            volume_strength=100.0 if market.volume_status == "AVAILABLE" else 30.0,

            market_energy=round(
                market_energy,
                precision,
            ),

            acceleration_score=round(
                buying_pressure,
                precision,
            ),

            deceleration_score=round(
                selling_pressure,
                precision,
            ),

            observations=tuple(observations),
            )

    def _calculate_breakout_probability(
        self,
        market: MarketAnalysisProtocol,
        signal: SignalResultProtocol,
        trend_strength: float,
        pressure: PressureEvidence,
    ) -> TargetEvidence:
        """
        Calculate breakout, breakdown and target reach probabilities.
        """

        breakout_probability = 0.0
        breakdown_probability = 0.0

        # Trend Strength
        breakout_probability += trend_strength * 0.25
        breakdown_probability += trend_strength * 0.25

        # Buying / Selling Pressure
        breakout_probability += pressure.buying_pressure * 0.30
        breakdown_probability += pressure.selling_pressure * 0.30

        # Market Score
        if market.market_score > 0:
            breakout_probability += min(15.0, market.market_score * 0.30)

        elif market.market_score < 0:
            breakdown_probability += min(
                15.0,
                abs(market.market_score) * 0.30,
            )

        # Breakout / Breakdown Confirmation
        if market.breakout:
            breakout_probability += 20.0

        if market.breakdown:
            breakdown_probability += 20.0

        # ADX Confirmation
        if market.adx >= 40:
            breakout_probability += 10.0
            breakdown_probability += 10.0

        elif market.adx >= 25:
            breakout_probability += 5.0
            breakdown_probability += 5.0

        # Signal Confidence
        if signal.signal.upper() == "BUY":
            breakout_probability += signal.confidence * 0.15

        elif signal.signal.upper() == "SELL":
            breakdown_probability += signal.confidence * 0.15

        minimum = float(self._config["minimum_score"])
        maximum = float(self._config["maximum_score"])
        precision = int(self._config["rounding_precision"])

        breakout_probability = max(
            minimum,
            min(maximum, breakout_probability),
        )

        breakdown_probability = max(
            minimum,
            min(maximum, breakdown_probability),
        )

        if signal.signal.upper() == "BUY":
            continuation_probability = breakout_probability
            reversal_probability = breakdown_probability

        elif signal.signal.upper() == "SELL":
            continuation_probability = breakdown_probability
            reversal_probability = breakout_probability

        else:
            continuation_probability = (
                breakout_probability + breakdown_probability
            ) / 2

            reversal_probability = continuation_probability

        target1 = continuation_probability
        target2 = continuation_probability * 0.85
        target3 = continuation_probability * 0.70

        false_signal_probability = max(
            minimum,
            100.0 - continuation_probability,
        )

        return TargetEvidence(
            target1_confidence=round(target1, precision),
            target2_confidence=round(target2, precision),
            target3_confidence=round(target3, precision),

            breakout_probability=round(
                breakout_probability,
                precision,
            ),

            breakdown_probability=round(
                breakdown_probability,
                precision,
            ),

            continuation_probability=round(
                continuation_probability,
                precision,
            ),

            reversal_probability=round(
                reversal_probability,
                precision,
            ),

            false_signal_probability=round(
                false_signal_probability,
                precision,
            ),

            observations=(
                "Trend strength evaluated.",
                "Buying/Selling pressure evaluated.",
                "Breakout probability calculated.",
                "Target confidence estimated.",
            ),
        )

    def _calculate_target_confidence(
        self,
        market: MarketAnalysisProtocol,
        signal: SignalResultProtocol,
        trend_strength: float,
        pressure: PressureEvidence,
        target_evidence: TargetEvidence,
    ) -> TargetEvidence:
        """
        Refine target reach confidence using trend strength,
        buying/selling pressure, breakout probability and
        overall market quality.
        """

        continuation = target_evidence.continuation_probability

        adjustment = (
            (trend_strength * 0.20)
            + (pressure.buying_pressure * 0.15)
            - (pressure.selling_pressure * 0.10)
            + (market.strength * 0.15)
            + (signal.confidence * 0.10)
            + (signal.probability * 0.10)
        )

        continuation += adjustment

        minimum = float(self._config["minimum_score"])
        maximum = float(self._config["maximum_score"])
        precision = int(self._config["rounding_precision"])

        continuation = max(
            minimum,
            min(
                maximum,
                continuation,
            ),
        )

        if signal.signal.upper() == "BUY":
            continuation = max(
                continuation,
                target_evidence.breakout_probability,
            )

        elif signal.signal.upper() == "SELL":
            continuation = max(
                continuation,
                target_evidence.breakdown_probability,
            )

        target1 = continuation

        target2 = max(
            minimum,
            continuation * 0.85,
        )

        target3 = max(
            minimum,
            continuation * 0.70,
        )

        reversal = max(
            minimum,
            min(
                maximum,
                100.0 - continuation,
            ),
        )

        false_signal = max(
            minimum,
            min(
                maximum,
                reversal * 0.80,
            ),
        )

        return TargetEvidence(
            target1_confidence=round(target1, precision),
            target2_confidence=round(target2, precision),
            target3_confidence=round(target3, precision),

            breakout_probability=round(
                target_evidence.breakout_probability,
                precision,
            ),

            breakdown_probability=round(
                target_evidence.breakdown_probability,
                precision,
            ),

            continuation_probability=round(
                continuation,
                precision,
            ),

            reversal_probability=round(
                reversal,
                precision,
            ),

            false_signal_probability=round(
                false_signal,
                precision,
            ),

            observations=(
                *target_evidence.observations,
                "Trend strength applied.",
                "Signal confidence applied.",
                "Target confidence refined.",
            ),
        )

    def _build_movement_assessment(
        self,
        market: MarketAnalysisProtocol,
        news: NewsAnalysisProtocol,
        signal: SignalResultProtocol,
        trend_strength: float,
        pressure: PressureEvidence,
        target_confidence: TargetEvidence,
    ) -> MovementAssessment:
        """
        Build the final immutable MovementAssessment.
        """

        continuation = target_confidence.continuation_probability
        reversal = target_confidence.reversal_probability

        if continuation >= 80:
            status = MovementStatus.STRENGTHENING.value
        elif continuation >= 60:
            status = MovementStatus.STABLE.value
        elif reversal >= 70:
            status = MovementStatus.REVERSING.value
        else:
            status = MovementStatus.WEAKENING.value

        if continuation >= 75:
            entry = TimingQuality.EXCELLENT.value
        elif continuation >= 60:
            entry = TimingQuality.GOOD.value
        elif continuation >= 40:
            entry = TimingQuality.FAIR.value
        else:
            entry = TimingQuality.AVOID.value

        if reversal >= 75:
            exit_time = TimingQuality.EXCELLENT.value
        elif reversal >= 60:
            exit_time = TimingQuality.GOOD.value
        else:
            exit_time = TimingQuality.FAIR.value

        volatility = (
            VolatilityState.HIGH.value
            if market.atr > 0
            else VolatilityState.NORMAL.value
        )

        acceleration = (
            AccelerationStatus.ACCELERATING.value
            if pressure.buying_pressure >= pressure.selling_pressure
            else AccelerationStatus.DECELERATING.value
        )

        observation = (
            f"{signal.signal} signal with "
            f"{continuation:.0f}% continuation probability."
        )

        explanation = (
            "Assessment combines trend, momentum, breakout, "
            "technical structure and signal confidence."
        )

        return MovementAssessment(
            ai_movement_status=status,
            movement_strength=trend_strength,
            movement_confidence_index=continuation,

            trend_continuation_chance=continuation,
            trend_reversal_chance=reversal,

            buying_pressure=pressure.buying_pressure,
            selling_pressure=pressure.selling_pressure,

            breakout_chance=target_confidence.breakout_probability,
            breakdown_chance=target_confidence.breakdown_probability,

            target1_reach_confidence=target_confidence.target1_confidence,
            target2_reach_confidence=target_confidence.target2_confidence,
            target3_reach_confidence=target_confidence.target3_confidence,

            entry_timing=entry,
            exit_timing=exit_time,

            acceleration_status=acceleration,
            deceleration_status=(
                AccelerationStatus.DECELERATING.value
                if acceleration == AccelerationStatus.ACCELERATING.value
                else AccelerationStatus.ACCELERATING.value
            ),

            market_energy=pressure.market_energy,
            volatility_state=volatility,

            signal_stability=continuation,
            false_signal_risk=target_confidence.false_signal_probability,

            ai_observation=observation,
            ai_evidence_summary=(
                *pressure.observations,
                *target_confidence.observations,
            ),
            ai_explanation=explanation,
        )

    def get_analysis_count(self) -> int:
            """
            Return the total number of completed movement analyses.
            """
            return self._analysis_count
