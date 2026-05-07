from dataclasses import dataclass

@dataclass(frozen=True)
class FeedConfig:
    url: str
    name: str
