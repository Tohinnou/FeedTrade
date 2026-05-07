from dataclasses import dataclass
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

