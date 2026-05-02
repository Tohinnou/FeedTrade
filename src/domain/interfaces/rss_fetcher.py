from abc import ABC, abstractmethod

from src.domain.models.article import Article


class RSSFetcher(ABC):
    """Port: contract for any RSS source."""

    @abstractmethod
    def fetch_all(self) -> list[Article]:
        pass
