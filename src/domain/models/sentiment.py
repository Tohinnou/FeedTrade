from dataclasses import dataclass
from typing import Optional

_INVALID_PAIRS = {"UNKNOWN", "PARSE_ERR", "ERROR", "TIMEOUT", "HORS_SCOPE", "CIRCUIT_OPEN"}
_VALID_SENTIMENTS = {"BULLISH", "BEARISH", "NEUTRAL"}

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