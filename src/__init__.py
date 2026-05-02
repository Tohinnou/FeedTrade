from src.domain.models.article import FeedConfig
from src.domain.interfaces.cache import Cache
from src.domain.interfaces.llm_client import LLMClient
from src.domain.interfaces.rss_fetcher import RSSFetcher

from src.infrastructure.cache.lru_cache import LRUCache
from src.infrastructure.llm.ollama_client import OllamaClient, OllamaConfig
from src.infrastructure.rss.feed_fetcher import FeedParserFetcher, DEFAULT_FEEDS

from src.application.get_sentiment import GetSentiment
from src.application.build_summary import BuildSummary


class Container:
    """Dependency injection container. Wires all layers together."""

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434/api/generate",
        ollama_model: str = "qwen2.5:1.5b",
        feeds: list[FeedConfig] = None,
        articles_per_feed: int = 5,
        cache_max_size: int = 100,
        cache_ttl: int = 120,
        llm_timeout: float = 30,
        llm_max_concurrent: int = 3,
    ):
        # Infrastructure
        self._cache: Cache = LRUCache(max_size=cache_max_size, default_ttl=cache_ttl)
        self._llm_config = OllamaConfig(
            url=ollama_url,
            model=ollama_model,
            timeout=llm_timeout,
            max_concurrent=llm_max_concurrent,
        )
        self._llm: LLMClient = OllamaClient(config=self._llm_config, cache=self._cache)
        self._fetcher: RSSFetcher = FeedParserFetcher(
            feeds=feeds or DEFAULT_FEEDS,
            articles_per_feed=articles_per_feed,
        )

        # Application
        self._get_sentiment = GetSentiment(fetcher=self._fetcher, llm=self._llm)
        self._build_summary = BuildSummary(get_sentiment=self._get_sentiment)

        # Expose
        self.deps = {
            "get_sentiment": self._get_sentiment,
            "build_summary": self._build_summary,
            "llm": self._llm,
            "fetcher": self._fetcher,
            "cache": self._cache,
        }
