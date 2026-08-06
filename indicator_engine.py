"""
TradeOracle AI
indicator_engine.py

Purpose:
Calculate technical indicators for TradeOracle AI.
"""

from dataclasses import dataclass

@dataclass
class IndicatorResult:
    
    ema20: float = 0.0
    ema50: float = 0.0

    sma20: float = 0.0
    sma50: float = 0.0

    rsi: float = 0.0

    macd: float = 0.0
    signal_line: float = 0.0

    vwap: float = 0.0

    atr: float = 0.0

    adx: float = 0.0

    obv: float = 0.0

class IndicatorEngine:

    def __init__(self):
        pass

    def calculate_ema(self, prices, period=20):
        """
        Calculate Exponential Moving Average (EMA)
        """

        if prices is None:
            return 0.0

        if len(prices) < period:
            return 0.0

        multiplier = 2 / (period + 1)

        ema = sum(prices[:period]) / period

        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema

        return round(ema, 2)

    def calculate_sma(self, prices, period=20):
        """
        Calculate Simple Moving Average (SMA)
        """

        if prices is None:
            return 0.0

        if len(prices) < period:
            return 0.0

        sma = sum(prices[-period:]) / period

        return round(sma, 2)

    def calculate_vwap(self, prices, volumes):
        """
        Calculate VWAP
        """

        if not prices or not volumes:
            return 0.0

        if len(prices) != len(volumes):
            return 0.0

        total_price_volume = sum(
            p * v for p, v in zip(prices, volumes)
        )

        total_volume = sum(volumes)

        if total_volume == 0:
            return 0.0

        return round(total_price_volume / total_volume, 2)

    def calculate_rsi(self, prices, period=14):
        """
        Calculate Relative Strength Index (RSI)
        """

        if prices is None or len(prices) <= period:
            return 0.0

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]

            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def calculate_macd(self, prices):
        """
        Calculate MACD and Signal Line
        """

        if prices is None or len(prices) < 26:
            return 0.0, 0.0

        ema12 = self.calculate_ema(prices, 12)
        ema26 = self.calculate_ema(prices, 26)

        macd = ema12 - ema26

        # Simple Signal Line (temporary implementation)
        signal_line = macd * 0.9

        return round(macd, 2), round(signal_line, 2)

    def calculate_atr(self, highs, lows, closes, period=14):
        """
        Calculate Average True Range (ATR)
        """

        if highs is None or lows is None or closes is None:
            return 0.0

        if len(highs) < period or len(lows) < period or len(closes) < period:
            return 0.0

        true_ranges = []

        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            true_ranges.append(tr)

        atr = sum(true_ranges[-period:]) / period

        return round(atr, 2)

    def calculate_adx(self, highs, lows, closes, period=14):
        """
        Calculate Average Directional Index (Simple Version)
        """

        if highs is None or len(highs) < period:
            return 0.0

        price_range = max(highs[-period:]) - min(lows[-period:])

        if price_range == 0:
            return 0.0

        adx = (price_range / max(highs[-period:])) * 100

        return round(adx, 2)

    def calculate_obv(self, closes, volumes):
        """
        Calculate On Balance Volume (OBV)
        """

        if closes is None or volumes is None:
            return 0.0

        if len(closes) != len(volumes):
            return 0.0

        obv = 0

        for i in range(1, len(closes)):

            if closes[i] > closes[i - 1]:
                obv += volumes[i]

            elif closes[i] < closes[i - 1]:
                obv -= volumes[i]

        return obv

    def analyze_indicators(self, market_data):
        """
        Analyze all technical indicators.
        """

        result = IndicatorResult()

        # Historical data not available yet.
        # Use current market snapshot as placeholder values.

        result.ema20 = self.calculate_ema(market_data.close_prices, 20)
        result.ema50 = self.calculate_ema(market_data.close_prices, 50)

        result.sma20 = self.calculate_sma(market_data.close_prices, 20)
        result.sma50 = self.calculate_sma(market_data.close_prices, 50)

        result.rsi = self.calculate_rsi(market_data.close_prices)

        result.macd, result.signal_line = self.calculate_macd(
            market_data.close_prices
        )

        result.vwap = self.calculate_vwap(
            market_data.close_prices,
            market_data.volumes
        )

        result.atr = self.calculate_atr(
            market_data.high_prices,
            market_data.low_prices,
            market_data.close_prices
        )

        result.adx = self.calculate_adx(
            market_data.high_prices,
            market_data.low_prices,
            market_data.close_prices
        )

        result.obv = self.calculate_obv(
            market_data.close_prices,
            market_data.volumes
        )

        return result
