"""
Intelligent cache management with secure Redis → Memory fallback.

This module provides the CacheManager class that implements intelligent cache
management with automatic fallback from secure Redis to memory cache when Redis
is unavailable. It follows the security-first architecture where all cache
operations are secure by default.

## Key Features

- **Secure Redis First**: Always attempts secure Redis connection first
- **Graceful Fallback**: Automatic fallback to memory cache when Redis unavailable
- **Transparent API**: Unified interface regardless of backend cache type
- **Performance Monitoring**: Comprehensive metrics for both cache backends
- **Cache Type Indicator**: Monitoring endpoints report active cache type
- **Security Built-in**: All Redis operations use mandatory security features

## Usage

```python
from app.infrastructure.cache.manager import CacheManager

# Create manager with automatic backend selection
manager = CacheManager()

# Use unified cache interface
await manager.set("key", {"data": "value"}, ttl=3600)
value = await manager.get("key")
await manager.delete("key")

# Check active cache backend
cache_type = manager.cache_type  # "redis_secure" or "memory"
```
"""

import logging
from typing import Any, Dict
from app.core.exceptions import ConfigurationError


class CacheManager:
    """
    Intelligent cache management with secure Redis → Memory fallback.
    
    This class provides a unified interface for cache operations that automatically
    selects the best available cache backend. It always attempts to use secure
    Redis first, with graceful fallback to memory cache when Redis is unavailable.
    
    The security-first architecture ensures that all Redis connections are secure
    and all cached data is encrypted at rest.
    """

    def __init__(self, redis_url: str | None = None):
        """
        Initialize cache manager with automatic backend selection.
        
        Args:
            redis_url: Optional Redis connection URL. If None, uses environment defaults.
        
        Examples:
            # Automatic configuration
            manager = CacheManager()
        
            # Custom Redis URL
            manager = CacheManager("rediss://production:6380")
        
        Note:
            The manager attempts secure Redis connection first, then falls back
            to memory cache if Redis is unavailable. This ensures the application
            continues functioning even without Redis.
        """
        ...

    async def get(self, key: str) -> Any:
        """
        Get value from cache with transparent backend selection.
        
        Args:
            key: Cache key to retrieve
        
        Returns:
            Cached value or None if not found
        
        Examples:
            # Get user data
            user_data = await manager.get("user:123")
        
            # Check if key exists
            if await manager.get("session:abc") is not None:
                print("Session is active")
        
        Note:
            Security is handled transparently - Redis data is automatically
            decrypted, memory cache data is returned as-is.
        """
        ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Set value in cache with transparent backend selection.
        
        Args:
            key: Cache key to store
            value: Value to cache (must be serializable)
            ttl: Time-to-live in seconds (optional)
        
        Examples:
            # Store user data
            await manager.set("user:123", {"name": "Alice", "role": "admin"}, ttl=3600)
        
            # Store AI response
            await manager.set("ai:query:hash", {
                "response": "Generated content",
                "model": "gpt-4",
                "timestamp": time.time()
            })
        
        Note:
            Security is handled transparently - Redis data is automatically
            encrypted before storage, memory cache stores data as-is.
        """
        ...

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache with transparent backend selection.
        
        Args:
            key: Cache key to delete
        
        Returns:
            True if key was deleted, False if not found
        
        Examples:
            # Delete user session
            deleted = await manager.delete("session:abc")
        
            # Clear AI cache
            await manager.delete("ai:query:hash")
        """
        ...

    async def clear(self) -> None:
        """
        Clear all cached data.
        
        Examples:
            # Clear all cache data
            await manager.clear()
        
        Warning:
            This operation clears ALL cached data. Use with caution.
        """
        ...

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
        
        Returns:
            True if key exists, False otherwise
        
        Examples:
            # Check if user session exists
            if await manager.exists("session:abc"):
                print("User is logged in")
        """
        ...

    async def connect(self) -> bool:
        """
        Establish connection to cache backend.
        
        Returns:
            True if connection successful, False otherwise
        
        Examples:
            # Ensure cache connection
            if await manager.connect():
                print("Cache is ready")
            else:
                print("Cache connection failed")
        
        Note:
            For Redis cache, this establishes secure TLS connection.
            For memory cache, this always returns True.
        """
        ...

    async def disconnect(self) -> None:
        """
        Disconnect from cache backend.
        
        Examples:
            # Cleanup on application shutdown
            await manager.disconnect()
        
        Note:
            Properly closes Redis connections to prevent resource leaks.
            Memory cache cleanup is automatic.
        """
        ...

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about active cache backend.
        
        Returns:
            Dictionary with cache backend information
        
        Examples:
            # Get cache status
            info = manager.get_cache_info()
            print(f"Using {info['cache_type']} cache")
            print(f"Security enabled: {info['security_enabled']}")
        
        Returns:
            Dictionary containing:
            - cache_type: "redis_secure" or "memory"
            - security_enabled: Boolean indicating encryption status
            - backend_info: Backend-specific information
        """
        ...

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on cache backend.
        
        Returns:
            Dictionary with health check results
        
        Examples:
            # Check cache health
            health = await manager.health_check()
            if health["healthy"]:
                print("Cache is operational")
            else:
                print(f"Cache issues: {health['errors']}")
        """
        ...

    def __str__(self) -> str:
        """
        String representation of cache manager.
        """
        ...

    def __repr__(self) -> str:
        """
        Detailed string representation of cache manager.
        """
        ...
