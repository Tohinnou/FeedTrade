from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Article:
    id: int
    title: str
    summary: str
    source: str
    published: Optional[datetime] = None
    url: Optional[str] = None

    @property
    def brief(self) -> str:
        return f"{self.title} {self.summary[:200]}".strip()


@dataclass(frozen=True)
class Sentiment:
    article_id: int
    pair: str
    sentiment: str
    reason: str
    raw_response: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.pair not in _INVALID_PAIRS and self.sentiment in _VALID_SENTIMENTS


@dataclass(frozen=True)
class FeedConfig:
    url: str
    name: str


@dataclass(frozen=True)
class AnalysisResult:
    sentiments: list[Sentiment]
    total_fetched: int
    total_analyzed: int
    time_seconds: float


_INVALID_PAIRS = {"UNKNOWN", "PARSE_ERR", "ERROR", "TIMEOUT", "HORS_SCOPE", "CIRCUIT_OPEN"}
_VALID_SENTIMENTS = {"BULLISH", "BEARISH", "NEUTRAL"}
