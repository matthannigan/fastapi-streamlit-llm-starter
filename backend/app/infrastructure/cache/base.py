from abc import ABC, abstractmethod

class CacheInterface(ABC):
    @abstractmethod
    async def get(self, key: str):
        pass
    @abstractmethod
    async def set(self, key: str, value: any, ttl: int = None):
        pass
    @abstractmethod
    async def delete(self, key: str):
        pass
