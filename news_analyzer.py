"""
TradeOracle AI
news_analyzer.py

Purpose:
Analyze market news and calculate news impact.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class NewsItem:
    title: str
    source: str
    category: str
    sentiment: str
    impact_score: float


@dataclass
class NewsAnalysis:
    overall_sentiment: str = "NEUTRAL"
    total_score: float = 0.0
    news_count: int = 0
    high_impact: bool = False
    positive_count: int = 0
    negative_count: int = 0

    bullish_score: float = 0.0
    bearish_score: float = 0.0

    recommendation: str = "HOLD"


class NewsAnalyzer:
    def __init__(self):
        self.news: List[NewsItem] = []

    def add_news(self, title, source, category, sentiment, impact_score):
        self.news.append(NewsItem(title, source, category, sentiment, impact_score))

    def analyze(self):

        result = NewsAnalysis()

        if not self.news:
            return result

        score = 0
        positive = 0
        negative = 0

        for item in self.news:

            score += item.impact_score

            if item.sentiment.upper() == "POSITIVE":
                positive += 1
                result.bullish_score += item.impact_score

            elif item.sentiment.upper() == "NEGATIVE":
                negative += 1
                result.bearish_score += item.impact_score

        result.news_count = len(self.news)
        result.total_score = score
        result.positive_count = positive
        result.negative_count = negative

        average = score / len(self.news)

        if average >= 70:
            result.overall_sentiment = "POSITIVE"

        elif average <= 30:
            result.overall_sentiment = "NEGATIVE"

        else:
            result.overall_sentiment = "NEUTRAL"

        if average >= 80:
            result.high_impact = True
        if result.bullish_score > result.bearish_score:
            result.recommendation = "BUY"

        elif result.bearish_score > result.bullish_score:
            result.recommendation = "SELL"

        else:
            result.recommendation = "HOLD"
        return result

    def clear(self):
        self.news.clear()
