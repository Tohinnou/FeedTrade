import asyncio
import os
import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

from groq import AsyncGroq

from src.domain.interfaces.cache import Cache
from src.domain.interfaces.llm_client import LLMClient
from src.domain.models.article import Sentiment

logger = logging.getLogger("feedtrade.infrastructure.llm.groq")


@dataclass
class GroqConfig:
    model: str = "llama-3.1-8b-instant"
    api_key: Optional[str] = None
    timeout: float = 30
    max_concurrent: int = 5
    circuit_breaker_threshold: int = 5
    circuit_breaker_recovery: float = 60


_PROMPT = """Analyse cette news forex. Retourne UNIQUEMENT un JSON valide:
{{"pair": "EUR/USD", "sentiment": "BULLISH", "reason": "court"}}

NEWS:
{title}
{summary}"""


class GroqClient(LLMClient):
    """Adapter: implements LLMClient using Groq Cloud API."""

    def __init__(self, config: GroqConfig, cache: Cache):
        self.config = config
        self.cache = cache
        api_key = config.api_key or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is required.")
        self.client = AsyncGroq(api_key=api_key)
        self._failures = 0
        self._recovery_at: Optional[float] = None
        self._semaphore = asyncio.Semaphore(config.max_concurrent)

    async def analyze_sentiment(self, article_id: int, text: str) -> Sentiment:
        if self._circuit_open:
            return Sentiment(article_id, "CIRCUIT_OPEN", "NEUTRAL", "Circuit breaker open")

        async with self._semaphore:
            return await self._call_groq(article_id, text)

    async def _call_groq(self, article_id: int, text: str) -> Sentiment:
        cache_key = f"groq:{article_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        title, summary = (text.split("\n", 1) + [""])[:2]
        prompt = _PROMPT.format(title=title, summary=summary[:200])

        try:
            completion = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200,
            )
            response = completion.choices[0].message.content
            result = self._parse(response, article_id)

            if result.is_valid:
                self.cache.set(cache_key, result)
            self._record_success()
            return result

        except Exception as e:
            self._record_failure()
            logger.error("Groq API error: %s", e)
            return Sentiment(article_id, "ERROR", "NEUTRAL", str(e))

    async def health_check(self) -> bool:
        try:
            await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False

    def clear_cache(self) -> None:
        self.cache.clear()

    @property
    def cache_size(self) -> int:
        return self.cache.size

    @property
    def _circuit_open(self) -> bool:
        import asyncio
        if self._recovery_at and asyncio.get_event_loop().time() < self._recovery_at:
            return True
        if self._recovery_at:
            self._failures = 0
            self._recovery_at = None
        return False

    def _record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.config.circuit_breaker_threshold:
            import asyncio
            self._recovery_at = asyncio.get_event_loop().time() + self.config.circuit_breaker_recovery
            logger.warning("Groq Circuit breaker opened after %d failures", self._failures)

    def _record_success(self) -> None:
        self._failures = 0
        self._recovery_at = None

    @staticmethod
    def _parse(raw: str, article_id: int) -> Sentiment:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return Sentiment(article_id, "PARSE_ERR", "NEUTRAL", "Parse failed")

        try:
            cleaned = re.sub(r",\s*([}\]])", r"\1", match.group(0))
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "sentiment" in parsed:
                return Sentiment(
                    article_id=article_id,
                    pair=parsed.get("pair", "UNKNOWN"),
                    sentiment=parsed["sentiment"],
                    reason=parsed.get("reason", ""),
                    raw_response=match.group(0),
                )
        except json.JSONDecodeError:
            pass

        return Sentiment(article_id, "PARSE_ERR", "NEUTRAL", "Parse failed")
