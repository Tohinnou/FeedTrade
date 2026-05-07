import asyncio
import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

import aiohttp

from src.domain.interfaces.cache import Cache
from src.domain.interfaces.llm_client import LLMClient
from src.domain.models.sentiment import Sentiment

logger = logging.getLogger("feedtrade.infrastructure.llm")


@dataclass
class OllamaConfig:
    url: str = "http://localhost:11434/api/generate"
    model: str = "qwen2.5:1.5b"
    timeout: float = 30
    max_concurrent: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_recovery: float = 60


_PROMPT = """Analyse cette news forex. Retourne UNIQUEMENT un JSON:
{{"pair": "EUR/USD", "sentiment": "BULLISH", "reason": "court"}}

NEWS:
{title}
{summary}"""


class OllamaClient(LLMClient):
    """Adapter: implements LLMClient using Ollama."""

    def __init__(self, config: OllamaConfig, cache: Cache):
        self.config = config
        self.cache = cache
        self._failures = 0
        self._recovery_at: Optional[float] = None
        self._semaphore = asyncio.Semaphore(config.max_concurrent)

    async def analyze_sentiment(self, article_id: int, text: str) -> Sentiment:
        if self._circuit_open:
            return Sentiment(article_id, "CIRCUIT_OPEN", "NEUTRAL", "Circuit breaker open")

        async with self._semaphore:
            return await self._call_ollama(article_id, text)

    async def _call_ollama(self, article_id: int, text: str) -> Sentiment:
        cache_key = f"ollama:{article_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        title, summary = (text.split("\n", 1) + [""])[:2]
        prompt = _PROMPT.format(title=title, summary=summary[:200])

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.url,
                    json={"model": self.config.model, "prompt": prompt, "stream": False},
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                ) as resp:
                    raw = await resp.text()
                    if resp.status != 200:
                        self._record_failure()
                        return Sentiment(article_id, "ERROR", "NEUTRAL", f"HTTP {resp.status}")

                    data = json.loads(raw)
                    response = data.get("response", "")
                    result = self._parse(response, article_id)

                    if result.is_valid:
                        self.cache.set(cache_key, result)
                    self._record_success()
                    return result

        except asyncio.TimeoutError:
            self._record_failure()
            return Sentiment(article_id, "TIMEOUT", "NEUTRAL", "Ollama timeout")
        except Exception as e:
            self._record_failure()
            return Sentiment(article_id, "ERROR", "NEUTRAL", str(e))

    async def health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.url,
                    json={"model": self.config.model, "prompt": "ok", "stream": False},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def clear_cache(self) -> None:
        self.cache.clear()

    @property
    def cache_size(self) -> int:
        return self.cache.size

    @property
    def _circuit_open(self) -> bool:
        if self._recovery_at and asyncio.get_event_loop().time() < self._recovery_at:
            return True
        if self._recovery_at:
            self._failures = 0
            self._recovery_at = None
        return False

    def _record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.config.circuit_breaker_threshold:
            self._recovery_at = asyncio.get_event_loop().time() + self.config.circuit_breaker_recovery
            logger.warning("Circuit breaker opened after %d failures", self._failures)

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
                    raw_response=raw[:200],
                )
        except json.JSONDecodeError:
            pass

        return Sentiment(article_id, "PARSE_ERR", "NEUTRAL", "Parse failed")
