from src.domain.models.article import FeedConfig
from src.domain.interfaces.cache import Cache
from src.domain.interfaces.llm_client import LLMClient
from src.domain.interfaces.rss_fetcher import RSSFetcher
from src.domain.interfaces.article_repository import ArticleRepository

from src.infrastructure.cache.lru_cache import LRUCache
from src.infrastructure.llm.groq_client import GroqClient, GroqConfig
from src.infrastructure.rss.feed_fetcher import FeedParserFetcher, DEFAULT_FEEDS
from src.infrastructure.repositories.article_repository import SQLAlchemyArticleRepository

from src.application.get_sentiment import GetSentiment
from src.application.build_summary import BuildSummary


class Container:
    """Dependency injection container. Wires all layers together."""

    def __init__(
        self,
        groq_api_key: str = None,
        groq_model: str = "llama-3.1-8b-instant",
        feeds: list[FeedConfig] = None,
        articles_per_feed: int = 1,
        cache_max_size: int = 100,
        cache_ttl: int = 120,
        llm_timeout: float = 30,
        llm_max_concurrent: int = 5,
        db_session=None,
    ):
        # Infrastructure
        self._cache: Cache = LRUCache(max_size=cache_max_size, default_ttl=cache_ttl)
        self._llm_config = GroqConfig(
            api_key=groq_api_key,
            model=groq_model,
            timeout=llm_timeout,
            max_concurrent=llm_max_concurrent,
        )
        self._llm: LLMClient = GroqClient(config=self._llm_config, cache=self._cache)
        self._fetcher: RSSFetcher = FeedParserFetcher(
            feeds=feeds or DEFAULT_FEEDS,
            articles_per_feed=articles_per_feed,
        )
        self._repo: ArticleRepository = (
            SQLAlchemyArticleRepository(session=db_session) if db_session else None
        )

        # Application
        self._get_sentiment = GetSentiment(
            fetcher=self._fetcher, llm=self._llm, repo=self._repo
        )
        self._build_summary = BuildSummary(get_sentiment=self._get_sentiment)

        # Expose
        self.deps = {
            "get_sentiment": self._get_sentiment,
            "build_summary": self._build_summary,
            "llm": self._llm,
            "fetcher": self._fetcher,
            "cache": self._cache,
            "repo": self._repo,
        }
