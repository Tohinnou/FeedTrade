from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

from src.domain.models.article import Article, Sentiment


class ArticleRepository(ABC):
    @abstractmethod
    async def save_article(self, article: Article) -> Article:
        """Save an article and return the persisted instance (with DB ID)."""

    @abstractmethod
    async def save_sentiment(self, sentiment: Sentiment) -> Sentiment:
        """Save a sentiment analysis result."""

    @abstractmethod
    async def get_article_by_url(self, url: str) -> Optional[Article]:
        """Check if an article already exists to avoid duplicates."""

    @abstractmethod
    async def get_sentiments_since(self, since: datetime) -> list[Sentiment]:
        """Retrieve all sentiment analyses since a given time."""
