from abc import ABC, abstractmethod
from typing import Any, Optional


class Cache(ABC):
    """Port: contract for any cache implementation."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        pass
