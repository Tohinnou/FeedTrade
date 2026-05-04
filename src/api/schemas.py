from typing import Dict, List
from pydantic import BaseModel


class SentimentSchema(BaseModel):
    article_id: int
    pair: str
    sentiment: str
    reason: str


class SentimentResponse(BaseModel):
    results: List[SentimentSchema]
    summary: Dict[str, str]
    total_fetched: int
    total_analyzed: int
    time_seconds: float


class SummaryResponse(BaseModel):
    summary: Dict[str, str]
    total_articles: int
    total_analyzed: int
    time_seconds: float


class HealthResponse(BaseModel):
    status: str
    ollama: bool
    feeds_count: int
    cache_size: int


class AskRequest(BaseModel):
    question: str
    top_k: int = 3
    
class AskResponse(BaseModel):
    answer: str
    sources: list[str] #les document utilisé
    question: str