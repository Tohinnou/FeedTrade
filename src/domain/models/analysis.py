from dataclasses import dataclass
from src.domain.models.sentiment import Sentiment


@dataclass(frozen=True)
class AnalysisResult:
    sentiments: list[Sentiment]
    total_fetched: int
    total_analyzed: int
    time_seconds: float