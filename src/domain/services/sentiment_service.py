from collections import Counter
from typing import Optional

from src.domain.models.analysis import AnalysisResult
from src.domain.models.sentiment import Sentiment


class SentimentReport:
    """Domain service: aggregates and analyzes sentiment data."""

    def __init__(self, result: AnalysisResult):
        self.result = result

    def summary(self) -> dict[str, str]:
        by_pair: dict[str, list[str]] = {}
        for s in self.result.sentiments:
            if not s.is_valid:
                continue
            by_pair.setdefault(s.pair, []).append(s.sentiment)

        return {
            pair: f"{self._majority(sents)} ({len(sents)} article{'s' if len(sents) > 1 else ''})"
            for pair, sents in by_pair.items()
        }

    def detailed_breakdown(self) -> dict[str, dict]:
        pairs: dict[str, dict] = {}
        for s in self.result.sentiments:
            if not s.is_valid:
                continue
            if s.pair not in pairs:
                pairs[s.pair] = {"BULLISH": 0, "BEARISH": 0, "NEUTRAL": 0}
            pairs[s.pair][s.sentiment] = pairs[s.pair].get(s.sentiment, 0) + 1

        return {
            pair: {
                "sentiment": self._majority(list(counts.keys())),
                "counts": counts,
            }
            for pair, counts in pairs.items()
        }

    def pair_sentiment(self, pair: str) -> Optional[str]:
        summary = self.summary()
        return summary.get(pair)

    @staticmethod
    def _majority(sentiments: list[str]) -> str:
        if not sentiments:
            return "UNKNOWN"
        return Counter(sentiments).most_common(1)[0][0]
