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
    market_score: float = 0.0
    news_score: float = 0.0

    risk_level: str = "MEDIUM"

    target: float = 0.0
    stoploss: float = 0.0


class SignalEngine:
    def __init__(self):
        pass

    def generate(self, market, news):

        result = SignalResult()

        bullish = market.bullish_score
        bearish = market.bearish_score

        result.market_score = market.market_score
        result.news_score = news.total_score

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
            result.risk_level = "LOW"

        elif bearish >= bullish + 15:

            result.signal = "SELL"
            result.confidence = min(95, bearish)
            result.probability = min(95, bearish)
            result.expected_time = "30m"
            result.reason = "Bearish market with negative news"
            result.risk_level = "LOW"

        else:

            result.signal = "HOLD"
            result.confidence = 50
            result.probability = 50
            result.expected_time = "15m"
            result.reason = "No clear market direction"
            result.risk_level = "HIGH"

        return result
