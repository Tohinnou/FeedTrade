import time
from collections import OrderedDict
from typing import Any

from src.domain.interfaces.cache import Cache


class LRUCache(Cache):
    """Thread-safe LRU cache with TTL."""

    def __init__(self, max_size: int = 100, default_ttl: int = 120):
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._data: OrderedDict = OrderedDict()
        self._times: OrderedDict = OrderedDict()
        self._ttls: dict[str, int] = {}

    def get(self, key: str) -> Any | None:
        if key not in self._times:
            return None
        ttl = self._ttls.get(key, self._default_ttl)
        if time.monotonic() - self._times[key] > ttl:
            self._evict(key)
            return None
        self._data.move_to_end(key)
        self._times.move_to_end(key)
        return self._data[key]

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if key in self._data:
            self._data.move_to_end(key)
            self._times.move_to_end(key)
        else:
            while len(self._data) >= self._max_size:
                self._evict(next(iter(self._data)))
        self._data[key] = value
        self._times[key] = time.monotonic()
        if ttl is not None:
            self._ttls[key] = ttl

    def clear(self) -> None:
        self._data.clear()
        self._times.clear()
        self._ttls.clear()

    @property
    def size(self) -> int:
        return len(self._data)

    def _evict(self, key: str) -> None:
        self._data.pop(key, None)
        self._times.pop(key, None)
        self._ttls.pop(key, None)
