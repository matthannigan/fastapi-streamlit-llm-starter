from abc import ABC, abstractmethod
from typing import Any, Optional

class CacheInterface(ABC):
    @abstractmethod
    async def get(self, key: str):
        pass
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        pass
    @abstractmethod
    async def delete(self, key: str):
        pass
