import asyncio
import logging
import time

from src.domain.interfaces.llm_client import LLMClient
from src.domain.interfaces.rss_fetcher import RSSFetcher
from src.domain.models.article import Article
from src.domain.models.analysis import AnalysisResult

logger = logging.getLogger("feedtrade.application")


class GetSentiment:
    """Use case: fetch articles and analyze their sentiment."""

    def __init__(self, fetcher: RSSFetcher, llm: LLMClient, repo=None):
        self.fetcher = fetcher
        self.llm = llm
        self.repo = repo

    async def execute(self) -> AnalysisResult:
        t0 = time.monotonic()

        articles = self.fetcher.fetch_all()
        if not articles:
            return AnalysisResult([], 0, 0, time.monotonic() - t0)

        # Sync with DB (deduplicate by URL)
        if self.repo:
            articles = await self._sync_articles_to_db(articles)

        sentiments = await self._analyze_all(articles)
        valid = [s for s in sentiments if s.is_valid]

        # Persist sentiments
        if self.repo:
            await self._save_sentiments(valid)

        return AnalysisResult(
            sentiments=sentiments,
            total_fetched=len(articles),
            total_analyzed=len(valid),
            time_seconds=round(time.monotonic() - t0, 2),
        )

    async def _sync_articles_to_db(self, articles: list[Article]) -> list[Article]:
        synced = []
        for article in articles:
            
            if article.url:
                existing = await self.repo.get_article_by_url(article.url)
                if existing:
                    synced.append(existing)
                    continue
            
            if article.title:
                existing = await self.repo.get_article_by_title_source(
                    article.title, article.source
                )
                if existing:
                    synced.append(existing)
                    continue
                
            # Save new article to get ID
            synced.append(await self.repo.save_article(article))
        return synced

    async def _save_sentiments(self, sentiments: list):
        for s in sentiments:
            await self.repo.save_sentiment(s)

    async def _analyze_all(self, articles: list[Article]) -> list:
        tasks = [
            self.llm.analyze_sentiment(article.id, article.brief)
            for article in articles
        ]
        results = await asyncio.gather(*tasks)
        logger.info("Analyzed %d articles", len(results))
        return list(results)
