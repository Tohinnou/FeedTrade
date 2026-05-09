import logging
from datetime import datetime

import feedparser

from src.domain.interfaces.rss_fetcher import RSSFetcher
from src.domain.models.article import Article
from src.domain.models.feed import FeedConfig

logger = logging.getLogger("feedtrade.infrastructure.rss")

DEFAULT_FEEDS = [
    FeedConfig(url="https://www.forexlive.com/feed", name="forexlive"),
    FeedConfig(url="https://www.fxstreet.com/rss/news", name="fxstreet"),
    FeedConfig(url="https://www.investing.com/rss/news_1.rss", name="investing"),
]


class FeedParserFetcher(RSSFetcher):
    """Adapter: implements RSSFetcher using feedparser."""

    def __init__(self, feeds: list[FeedConfig], articles_per_feed: int = 5):
        self.feeds = feeds
        self.articles_per_feed = articles_per_feed
        self._id_counter = 0

    def fetch_all(self) -> list[Article]:
        articles: list[Article] = []
        for cfg in self.feeds:
            batch = self._fetch_one(cfg)
            articles.extend(batch)
            logger.info("Fetched %d articles from %s", len(batch), cfg.name)
        return articles

    def _fetch_one(self, cfg: FeedConfig) -> list[Article]:
        try:
            feed = feedparser.parse(cfg.url)
            articles = []
            for entry in feed.entries[: self.articles_per_feed]:
                self._id_counter += 1
                articles.append(
                    Article(
                        id=self._id_counter,
                        title=entry.title,
                        summary=entry.get("summary", ""),
                        source=cfg.name,
                        published=self._parse_date(entry.get("published")),
                        url=entry.get("link"),
                    )
                )
            return articles
        except Exception as e:
            logger.warning("Error fetching %s: %s", cfg.url, e)
            return []

    @staticmethod
    def _parse_date(raw: str | None) -> datetime | None:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
