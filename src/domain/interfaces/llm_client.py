from abc import ABC, abstractmethod
from typing import Optional

from src.domain.models.article import Sentiment


class LLMClient(ABC):
    """Port: contract for any LLM provider."""

    @abstractmethod
    async def analyze_sentiment(self, article_id: int, text: str) -> Sentiment:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        pass

    @property
    @abstractmethod
    def cache_size(self) -> int:
        pass
