"""Abstract cache interface defining the contract for cache implementations.

This module provides the base abstract class that defines the standard interface
for all cache implementations in the application. It ensures consistent behavior
across different caching backends through a common contract.

Classes:
    CacheInterface: Abstract base class defining core cache operations that must
                    be implemented by all concrete cache classes.

Implementations:
    This interface is implemented by:
    - InMemoryCache (memory.py): Fast in-memory caching for development/testing
    - AIResponseCache (redis.py): Redis-backed persistent caching for production

Example:
    ```python
    # All cache implementations follow the same interface
    >>> cache: CacheInterface = InMemoryCache()  # or AIResponseCache()
    >>> await cache.set("key", {"data": "value"}, ttl=3600)
    >>> result = await cache.get("key")
    >>> await cache.delete("key")
    ```
"""
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
