"""
[REFACTORED] Abstract cache interface defining the contract for cache implementations.

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
    """
    Abstract base class defining the standard cache interface contract for all cache implementations.
    
    Establishes the fundamental cache operations that must be implemented by all concrete
    cache classes, ensuring consistent behavior across different caching backends while
    enabling polymorphic usage patterns throughout the application.
    
    Public Methods:
        get(): Retrieve cached value by key with type preservation
        set(): Store value with optional TTL for automatic expiration
        delete(): Remove cached entry immediately
        
    State Management:
        - Abstract class provides no state management (implementation-specific)
        - Defines async interface contract requiring coroutine implementations
        - Ensures consistent error handling patterns across implementations
        - Enables polymorphic cache usage without backend-specific code
        
    Usage:
        # All cache implementations follow the same interface
        cache: CacheInterface = InMemoryCache()  # or AIResponseCache()
        
        # Basic cache operations
        await cache.set("user:123", {"name": "John", "active": True}, ttl=3600)
        user_data = await cache.get("user:123")
        await cache.delete("user:123")
        
        # Polymorphic usage in services
        class UserService:
            def __init__(self, cache: CacheInterface):
                self.cache = cache  # Works with any cache implementation
    """

    @abstractmethod
    async def get(self, key: str):
        """
        Retrieve cached value by key with implementation-specific type handling.
        
        Args:
            key: Cache key string for value lookup. Implementation may apply
                key normalization or validation patterns.
                
        Returns:
            Cached value if found, preserving original data types and structure.
            None if key not found or expired in most implementations.
            
        Behavior:
            - Returns None for missing or expired keys (implementation-specific)
            - Preserves original data types stored during set() operation
            - May apply key normalization or validation before lookup
            - Handles concurrent access according to implementation design
            - Thread/async-safe operation for production environments
        """
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Store value in cache with optional time-to-live expiration.
        
        Args:
            key: Cache key string for value storage. Implementation may apply
                key validation, normalization, or length restrictions.
            value: Data to cache, supporting JSON-serializable types in most implementations.
                  Complex objects may require implementation-specific handling.
            ttl: Optional time-to-live in seconds for automatic expiration.
                If None, uses implementation default or no expiration.
                
        Behavior:
            - Stores value with type preservation where possible
            - Applies TTL for automatic expiration if supported
            - Overwrites existing values for the same key
            - May perform serialization for storage optimization
            - Handles storage failures gracefully without raising exceptions
            - Thread/async-safe operation for concurrent access
        """
        ...

    @abstractmethod
    async def delete(self, key: str):
        """
        Remove cached entry immediately from storage.
        
        Args:
            key: Cache key string for entry removal. Implementation may apply
                key normalization before deletion.
                
        Behavior:
            - Removes cache entry immediately if present
            - No-op for non-existent keys (graceful handling)
            - May perform cleanup of related metadata or indexes
            - Thread/async-safe operation for concurrent access
            - Success regardless of key existence for idempotent behavior
        """
        ...
