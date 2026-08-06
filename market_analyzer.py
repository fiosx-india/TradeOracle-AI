"""
TradeOracle AI
market_analyzer.py

Purpose:
Analyze Indian market trend, momentum, volume and strength.
"""

from dataclasses import dataclass
from typing import Dict
from indicator_engine import IndicatorEngine


@dataclass
class MarketAnalysis:

    # Market Direction
    trend: str = "NEUTRAL"
    momentum: str = "NORMAL"
    strength: float = 0.0
    confidence: float = 0.0

    # Price Action
    breakout: bool = False
    breakdown: bool = False
    
    last_price: float = 0.0
    support: float = 0.0
    resistance: float = 0.0

    # Technical Analysis
    ema20: float = 0.0
    ema50: float = 0.0
    rsi: float = 0.0
    macd: float = 0.0
    signal_line: float = 0.0
    vwap: float = 0.0
    atr: float = 0.0
    adx: float = 0.0

    # Market Behaviour
    volume_status: str = "NORMAL"
    oi_status: str = "UNKNOWN"
    vix_status: str = "NORMAL"

    # Score
    bullish_score: float = 0.0
    bearish_score: float = 0.0
    market_score: float = 0.0

    # Forecast
    prediction_5m: str = "NEUTRAL"
    prediction_15m: str = "NEUTRAL"
    prediction_30m: str = "NEUTRAL"
    prediction_1h: str = "NEUTRAL"


class MarketAnalyzer:
    def __init__(self):
        self.indicators = IndicatorEngine()

    def analyze(self, index_data) -> MarketAnalysis:

        result = MarketAnalysis()
        indicator = self.indicators.analyze_indicators(index_data)

        result.ema20 = indicator.ema20
        result.ema50 = indicator.ema50
        result.rsi = indicator.rsi
        result.macd = indicator.macd
        result.signal_line = indicator.signal_line
        result.vwap = indicator.vwap
        result.atr = indicator.atr
        result.adx = indicator.adx
        result.last_price = index_data.last_price
        
        # ---------- Indicator Score ----------

        # RSI
        if result.rsi >= 70:
            result.bullish_score += 15

        elif result.rsi >= 60:
            result.bullish_score += 10

        elif result.rsi <= 30:
            result.bearish_score += 15

        elif result.rsi <= 40:
            result.bearish_score += 10

        # EMA
        ema_gap = abs(result.ema20 - result.ema50)

        if result.ema20 > result.ema50:
            result.bullish_score += min(15, max(5, ema_gap))

        elif result.ema20 < result.ema50:
            result.bearish_score += min(15, max(5, ema_gap))

        # MACD
        macd_gap = abs(result.macd - result.signal_line)

        if result.macd > result.signal_line:
            result.bullish_score += min(15, max(5, macd_gap * 10))

        elif result.macd < result.signal_line:
            result.bearish_score += min(15, max(5, macd_gap * 10))

        # ADX
        if result.adx >= 40:
            result.strength += 30

        elif result.adx >= 25:
            result.strength += 20

        elif result.adx >= 15:
            result.strength += 10
            
        # ---------- Trend ----------

        price_change = index_data.last_price - index_data.open_price

        if price_change > 0:

            result.trend = "BULLISH"

            if index_data.change_percent >= 1.5:
                result.bullish_score += 30

            elif index_data.change_percent >= 0.75:
                result.bullish_score += 20

            else:
                result.bullish_score += 10

        elif price_change < 0:

            result.trend = "BEARISH"

            if index_data.change_percent <= -1.5:
                result.bearish_score += 30

            elif index_data.change_percent <= -0.75:
                result.bearish_score += 20

            else:
                result.bearish_score += 10

        else:
            result.trend = "SIDEWAYS"
            
        # ---------- Momentum ----------
        cp = index_data.change_percent

        if abs(cp) >= 1.50:
            result.momentum = "VERY_STRONG"
            result.strength += 30

            if cp > 0:
                result.bullish_score += 30
            else:
                result.bearish_score += 30

        elif abs(cp) >= 1.00:
            result.momentum = "STRONG"
            result.strength += 20

            if cp > 0:
                result.bullish_score += 20
            else:
                result.bearish_score += 20

        elif abs(cp) >= 0.50:
            result.momentum = "MODERATE"
            result.strength += 10

            if cp > 0:
                result.bullish_score += 10
            else:
                result.bearish_score += 10

        else:
            result.momentum = "WEAK"

        # ---------- Support / Resistance ----------
        result.support = index_data.low_price
        result.resistance = index_data.high_price

        # ---------- Breakout ----------
        if index_data.last_price >= index_data.high_price:
            result.breakout = True
            result.bullish_score += 20

        # ---------- Breakdown ----------
        if index_data.last_price <= index_data.low_price:
            result.breakdown = True
            result.bearish_score += 20

        # ---------- Volume ----------
        if index_data.volume > 0:
            result.volume_status = "AVAILABLE"
        else:
            result.volume_status = "UNAVAILABLE"

        # ---------- Confidence ----------
        
        score_gap = abs(result.bullish_score - result.bearish_score)

        result.confidence = round(
            min(
                95,
                max(
                    40,
                    max(result.bullish_score, result.bearish_score) + (score_gap * 0.3)
                )
            ),
            2,
        )

        # ---------- Market Score ----------
        result.market_score = result.bullish_score - result.bearish_score

        # ---------- Forecast ----------
        if result.market_score >= 20:
            result.prediction_5m = "UP"
            result.prediction_15m = "UP"
            result.prediction_30m = "UP"
            result.prediction_1h = "UP"

        elif result.market_score <= -20:
            result.prediction_5m = "DOWN"
            result.prediction_15m = "DOWN"
            result.prediction_30m = "DOWN"
            result.prediction_1h = "DOWN"

        else:
            result.prediction_5m = "SIDEWAYS"
            result.prediction_15m = "SIDEWAYS"
            result.prediction_30m = "SIDEWAYS"
            result.prediction_1h = "SIDEWAYS"

        return result

    def analyze_all(self, indices: Dict) -> Dict[str, MarketAnalysis]:

        reports = {}

        for symbol, data in indices.items():
            reports[symbol] = self.analyze(data)

        return reports
