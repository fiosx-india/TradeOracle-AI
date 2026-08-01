"""
TradeOracle AI
oracle_core.py

Purpose:
Connect all TradeOracle AI modules.
"""

from .indices_engine import IndicesEngine
from .market_analyzer import MarketAnalyzer
from .news_analyzer import NewsAnalyzer
from .signal_engine import SignalEngine


class TradeOracle:

    def __init__(self):

        self.indices = IndicesEngine()
        self.market = MarketAnalyzer()
        self.news = NewsAnalyzer()
        self.signal = SignalEngine()

    def analyze(self):

        results = {}

        market_data = self.indices.get_all_indices()

        if not market_data:
            return {}

        market_reports = self.market.analyze_all(market_data)

        news_report = self.news.analyze()

        for symbol in market_data:

            signal = self.signal.generate(
                market_reports[symbol],
                news_report
            )

            results[symbol] = {
                "index": market_data[symbol],
                "market": market_reports[symbol],
                "news": news_report,
                "signal": signal
            }

        return results


if __name__ == "__main__":

    oracle = TradeOracle()

    output = oracle.analyze()

    for symbol, result in output.items():

        print("=" * 40)

        print(symbol)

        print("Signal :", result["signal"].signal)

        print("Confidence :", result["signal"].confidence)

        print("Probability :", result["signal"].probability)

        print("Reason :", result["signal"].reason)
