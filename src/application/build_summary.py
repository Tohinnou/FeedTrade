import logging

from src.application.get_sentiment import GetSentiment
from src.domain.services.sentiment_service import SentimentReport

logger = logging.getLogger("feedtrade.application")


class BuildSummary:
    """Use case: get aggregated sentiment summary."""

    def __init__(self, get_sentiment: GetSentiment):
        self.get_sentiment = get_sentiment

    async def execute(self) -> dict:
        result = await self.get_sentiment.execute()
        report = SentimentReport(result)
        return {
            "summary": report.summary(),
            "total_articles": result.total_fetched,
            "total_analyzed": result.total_analyzed,
            "time_seconds": result.time_seconds,
        }
