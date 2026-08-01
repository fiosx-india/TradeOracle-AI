"""
TradeOracle AI
market_analyzer.py

Purpose:
Analyze Indian market trend, momentum, volume and strength.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class MarketAnalysis:
    trend: str = "NEUTRAL"
    momentum: str = "NORMAL"
    strength: float = 0.0
    breakout: bool = False

    support: float = 0.0
    resistance: float = 0.0

    volume_status: str = "NORMAL"
    oi_status: str = "UNKNOWN"

    bullish_score: float = 0.0
    bearish_score: float = 0.0


class MarketAnalyzer:

    def __init__(self):
        pass

    def analyze(self, index_data) -> MarketAnalysis:

        result = MarketAnalysis()

        # ---------- Trend ----------
        if index_data.last_price > index_data.open_price:
            result.trend = "BULLISH"
            result.bullish_score += 20
        elif index_data.last_price < index_data.open_price:
            result.trend = "BEARISH"
            result.bearish_score += 20

        # ---------- Momentum ----------
        if abs(index_data.change_percent) >= 1:
            result.momentum = "STRONG"
        elif abs(index_data.change_percent) >= 0.5:
            result.momentum = "MODERATE"
        else:
            result.momentum = "WEAK"

        # ---------- Support ----------
        result.support = index_data.low_price

        # ---------- Resistance ----------
        result.resistance = index_data.high_price

        # ---------- Breakout ----------
        if index_data.last_price >= index_data.high_price:
            result.breakout = True
            result.bullish_score += 15

        # ---------- Volume ----------
        if index_data.volume > 0:
            result.volume_status = "AVAILABLE"

        # ---------- Strength ----------
        result.strength = max(
            result.bullish_score,
            result.bearish_score
        )

        return result

    def analyze_all(self, indices: Dict):

        reports = {}

        for symbol, data in indices.items():
            reports[symbol] = self.analyze(data)

        return reports
