"""
TradeOracle AI
oracle_core.py

Purpose:
Connect all TradeOracle AI modules.
"""

from indices_engine import IndicesEngine
from market_analyzer import MarketAnalyzer
from news_analyzer import NewsAnalyzer
from signal_engine import SignalEngine
from movement_prediction_ai import MovementPredictionAI
from commodity_engine import (
    CommodityEngine,
    CommodityDataSource,
    CommodityMovementPredictionAI,
)
from commodity_data_provider import fetch_mcx_commodities

class TradeOracle:
    def __init__(self):

        self.indices = IndicesEngine()
        self.market = MarketAnalyzer()
        self.news = NewsAnalyzer()
        self.signal = SignalEngine()
        self.movement = MovementPredictionAI()
        
        commodity_source = CommodityDataSource(
            fetch_mcx_commodities
        )

        self.commodity_engine = CommodityEngine(
            data_source=commodity_source,
            cache_ttl=300.0,
        )

        self.commodity_ai = CommodityMovementPredictionAI()

    def analyze(self):

        results = {}

        market_data = self.indices.get_all_indices()

        if not market_data:
            return {}

        market_reports = self.market.analyze_all(market_data)

        self.news.clear()

        self.news.add_news(
            title="Market opens strong",
            source="NSE",
            category="Market",
            sentiment="POSITIVE",
            impact_score=75,
        )

        news_report = self.news.analyze()

        for symbol in market_data:
            
            report = market_reports[symbol]

            print(f"\n{symbol}")
            print("Bullish :", report.bullish_score)
            print("Bearish :", report.bearish_score)
            print("Market Score :", report.market_score)
            print("News :", news_report.overall_sentiment)
            print("Last Price :", market_data[symbol].last_price)
            print("Open Price :", market_data[symbol].open_price)
            print("High Price :", market_data[symbol].high_price)
            print("Low Price :", market_data[symbol].low_price)
            print("Change % :", market_data[symbol].change_percent)
            
            signal = self.signal.generate(report, news_report)
            
            movement = self.movement.analyze(report, news_report, signal)

            results[symbol] = {
                "index": market_data[symbol],
                "market": market_reports[symbol],
                "news": news_report,
                "signal": signal,
                "movement": movement,
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
