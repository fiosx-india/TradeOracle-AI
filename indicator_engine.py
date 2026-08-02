"""
TradeOracle AI
indicator_engine.py

Purpose:
Calculate technical indicators for TradeOracle AI.
"""

from dataclasses import dataclass
from typing import List

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
