import logging

from fastapi import FastAPI

from src.api.schemas import SentimentResponse, SummaryResponse, HealthResponse, SentimentSchema
from src.application.get_sentiment import GetSentiment
from src.application.build_summary import BuildSummary
from src.domain.interfaces.llm_client import LLMClient
from src.domain.services.sentiment_service import SentimentReport

logger = logging.getLogger("feedtrade.api")


def register_routes(app: FastAPI, deps: dict):
    """Register routes with pre-built dependencies (closure pattern)."""

    get_sentiment_uc: GetSentiment = deps["get_sentiment"]
    build_summary_uc: BuildSummary = deps["build_summary"]
    llm: LLMClient = deps["llm"]

    @app.get("/sentiment", response_model=SentimentResponse)
    async def sentiment_endpoint():
        result = await get_sentiment_uc.execute()
        report = SentimentReport(result)

        return SentimentResponse(
            results=[
                SentimentSchema(
                    article_id=s.article_id,
                    pair=s.pair,
                    sentiment=s.sentiment,
                    reason=s.reason,
                )
                for s in result.sentiments
            ],
            summary=report.summary(),
            total_fetched=result.total_fetched,
            total_analyzed=result.total_analyzed,
            time_seconds=result.time_seconds,
        )

    @app.get("/summary", response_model=SummaryResponse)
    async def summary_endpoint():
        return await build_summary_uc.execute()

    @app.get("/health", response_model=HealthResponse)
    async def health_endpoint():
        ollama_ok = await llm.health_check()
        feeds = deps["fetcher"].feeds if "fetcher" in deps else []
        return HealthResponse(
            status="healthy" if ollama_ok else "degraded",
            ollama=ollama_ok,
            feeds_count=len(feeds),
            cache_size=llm.cache_size,
        )
