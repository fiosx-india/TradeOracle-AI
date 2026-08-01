"""
TradeOracle AI
signal_engine.py

Purpose:
Generate AI trading signals.
"""

from dataclasses import dataclass


@dataclass
class SignalResult:
    signal: str = "HOLD"
    confidence: float = 0.0
    probability: float = 0.0
    expected_time: str = "15m"
    reason: str = ""


class SignalEngine:

    def __init__(self):
        pass

    def generate(self, market, news):

        result = SignalResult()

        bullish = market.bullish_score
        bearish = market.bearish_score

        if news.overall_sentiment == "POSITIVE":
            bullish += 20

        elif news.overall_sentiment == "NEGATIVE":
            bearish += 20

        if bullish >= bearish + 15:

            result.signal = "BUY"
            result.confidence = min(95, bullish)
            result.probability = min(95, bullish)
            result.expected_time = "30m"
            result.reason = "Bullish market with positive news"

        elif bearish >= bullish + 15:

            result.signal = "SELL"
            result.confidence = min(95, bearish)
            result.probability = min(95, bearish)
            result.expected_time = "30m"
            result.reason = "Bearish market with negative news"

        else:

            result.signal = "HOLD"
            result.confidence = 50
            result.probability = 50
            result.expected_time = "15m"
            result.reason = "No clear market direction"

        return result
