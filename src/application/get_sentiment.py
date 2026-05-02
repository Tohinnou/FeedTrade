import asyncio
import logging
import time

from src.domain.interfaces.llm_client import LLMClient
from src.domain.interfaces.rss_fetcher import RSSFetcher
from src.domain.models.article import Article, AnalysisResult

logger = logging.getLogger("feedtrade.application")


class GetSentiment:
    """Use case: fetch articles and analyze their sentiment."""

    def __init__(self, fetcher: RSSFetcher, llm: LLMClient):
        self.fetcher = fetcher
        self.llm = llm

    async def execute(self) -> AnalysisResult:
        t0 = time.monotonic()

        articles = self.fetcher.fetch_all()
        if not articles:
            return AnalysisResult([], 0, 0, time.monotonic() - t0)

        sentiments = await self._analyze_all(articles)
        valid = [s for s in sentiments if s.is_valid]

        return AnalysisResult(
            sentiments=sentiments,
            total_fetched=len(articles),
            total_analyzed=len(valid),
            time_seconds=round(time.monotonic() - t0, 2),
        )

    async def _analyze_all(self, articles: list[Article]) -> list:
        tasks = [
            self.llm.analyze_sentiment(article.id, article.brief)
            for article in articles
        ]
        results = await asyncio.gather(*tasks)
        logger.info("Analyzed %d articles", len(results))
        return list(results)
