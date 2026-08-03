"""
TradeOracle AI
signal_engine.py

Purpose:
Generate AI trading signals.
"""

from dataclasses import dataclass
from market_analyzer import MarketAnalyzer


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
    
    entry_price: float = 0.0

    target1: float = 0.0
    target2: float = 0.0
    target3: float = 0.0

    risk_reward: float = 0.0


class SignalEngine:
    def __init__(self):
        self.market = MarketAnalyzer()
        
    def generate(self, market, news):

        result = SignalResult()
        reasons = []

        bullish = market.bullish_score
        bearish = market.bearish_score

        result.market_score = market.market_score
        result.news_score = news.total_score
        
        if news.overall_sentiment == "POSITIVE":
            bullish += 20
            reasons.append("Positive News")

        elif news.overall_sentiment == "NEGATIVE":
            bearish += 20
            reasons.append("Negative News")

        else:
            reasons.append("Neutral News")
        # ---------- Technical Indicator Confirmation ----------

        if market.rsi >= 60:
            bullish += 10
            reasons.append("RSI Bullish")

        elif market.rsi <= 40:
            bearish += 10
            reasons.append("RSI Bearish")

        if market.ema20 > market.ema50:
            bullish += 10
            reasons.append("EMA Bullish Cross")

        elif market.ema20 < market.ema50:
            bearish += 10
            reasons.append("EMA Bearish Cross")

        if market.macd > market.signal_line:
            bullish += 10
            reasons.append("MACD Bullish")

        elif market.macd < market.signal_line:
            bearish += 10
            reasons.append("MACD Bearish")

        if market.adx >= 25:
            bullish += 5
            bearish += 5
            reasons.append("Strong Trend (ADX)")

        if bullish >= bearish + 15:
            
            result.signal = "BUY"
            result.confidence = min(95, bullish)
            result.probability = min(95, (bullish + market.market_score) / 2)
            result.expected_time = "30m"
            result.reason = ", ".join(reasons)
            result.risk_level = "LOW"

        elif bearish >= bullish + 15:
            
            result.signal = "SELL"
            result.confidence = min(95, bearish)
            result.probability = min(95, (bearish + market.market_score) / 2)
            result.expected_time = "30m"
            result.reason = ", ".join(reasons)
            result.risk_level = "LOW"

        else:

            result.signal = "HOLD"
            result.confidence = 50
            result.probability = 50
            result.expected_time = "15m"

            if reasons:
                result.reason = ", ".join(reasons)
            else:
                result.reason = "No clear market direction"

            result.risk_level = "HIGH"

        if result.signal == "BUY":

            result.entry_price = market.last_price
            result.stoploss = market.support

            result.target1 = market.resistance
            result.target2 = market.resistance * 1.01
            result.target3 = market.resistance * 1.02

            result.target = result.target1

            risk = result.entry_price - result.stoploss
            reward = result.target1 - result.entry_price

            if risk > 0:
                result.risk_reward = round(reward / risk, 2)


        elif result.signal == "SELL":

            result.entry_price = market.last_price
            result.stoploss = market.resistance

            result.target1 = market.support
            result.target2 = market.support * 0.99
            result.target3 = market.support * 0.98

            result.target = result.target1

            risk = result.stoploss - result.entry_price
            reward = result.entry_price - result.target1

            if risk > 0:
                result.risk_reward = round(reward / risk, 2)
            
        return result

