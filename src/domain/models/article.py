from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Article:
    id: int
    title: str
    summary: str
    source: str
    published: datetime | None = None
    url: str | None = None

    @property
    def brief(self) -> str:
        return f"{self.title} {self.summary[:200]}".strip()
