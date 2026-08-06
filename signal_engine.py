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

        # RSI
        if market.rsi >= 70:
            bullish += 15
            reasons.append("Strong RSI Bullish")

        elif market.rsi >= 60:
            bullish += 10
            reasons.append("RSI Bullish")

        elif market.rsi <= 30:
            bearish += 15
            reasons.append("Strong RSI Bearish")

        elif market.rsi <= 40:
            bearish += 10
            reasons.append("RSI Bearish")


        # EMA
        ema_gap = abs(market.ema20 - market.ema50)

        if market.ema20 > market.ema50:
            bullish += min(15, max(5, ema_gap))
            reasons.append("EMA Bullish Cross")

        elif market.ema20 < market.ema50:
            bearish += min(15, max(5, ema_gap))
            reasons.append("EMA Bearish Cross")


        # MACD
        macd_gap = abs(market.macd - market.signal_line)

        if market.macd > market.signal_line:
            bullish += min(15, max(5, macd_gap * 10))
            reasons.append("MACD Bullish")

        elif market.macd < market.signal_line:
            bearish += min(15, max(5, macd_gap * 10))
            reasons.append("MACD Bearish")


        # ADX
        if market.adx >= 40:
            if bullish > bearish:
                bullish += 10
            elif bearish > bullish:
                bearish += 10

            reasons.append("Very Strong Trend")

        elif market.adx >= 25:
            if bullish > bearish:
                bullish += 5
            elif bearish > bullish:
                bearish += 5

            reasons.append("Strong Trend")


        # Decision Threshold
        if bullish >= bearish + 20:
            
            result.signal = "BUY"
            score = bullish - bearish

            result.confidence = round(
                min(
                    95,
                    max(
                        40,
                        market.confidence + (score * 0.5)
                    )
                ),
                2,
            )

            result.probability = round(
                min(
                    95,
                    max(
                        45,
                        result.confidence + (market.strength * 0.3)
                    )
                ),
                2,
            )
            result.expected_time = "30m"
            result.reason = ", ".join(reasons)
            result.risk_level = "LOW"

        elif bearish >= bullish + 15:
            
            result.signal = "SELL"
            score = bearish - bullish

            result.confidence = round(
                min(
                    95,
                    max(
                        40,
                        market.confidence + (score * 0.5)
                    )
                ),
                2,
            )

            result.probability = round(
                min(
                    95,
                    max(
                        45,
                        result.confidence + (market.strength * 0.3)
                    )
                ),
                2,
            )
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

