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

logger = logging.getLogger(__name__)


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
        self.logger = logging.getLogger(__name__)
        self.redis_url = redis_url
        self.cache = None
        self.cache_type = None

        self._initialize_cache()

    def _initialize_cache(self) -> None:
        """
        Initialize cache with secure Redis → memory fallback strategy.

        This method implements the intelligent fallback logic where secure Redis
        is attempted first, with graceful degradation to memory cache.
        """
        self.logger.info("🚀 Initializing intelligent cache manager")

        # Try secure Redis first
        try:
            from app.infrastructure.cache.redis_generic import \
                GenericRedisCache

            if self.redis_url:
                self.cache = GenericRedisCache.create_secure(self.redis_url)
            else:
                self.cache = GenericRedisCache.create_secure()

            self.cache_type = "redis_secure"
            self.logger.info("✅ Using secure Redis cache with automatic encryption")

        except (ConfigurationError, ImportError) as e:
            # Graceful fallback to memory cache
            self.logger.warning(
                f"Redis unavailable ({e}), falling back to memory cache"
            )
            self._initialize_memory_fallback()

        except Exception as e:
            # Unexpected errors also trigger fallback
            self.logger.error(
                f"Unexpected error initializing Redis ({e}), falling back to memory cache"
            )
            self._initialize_memory_fallback()

    def _initialize_memory_fallback(self) -> None:
        """Initialize memory cache as fallback when Redis is unavailable."""
        try:
            from app.infrastructure.cache.memory import MemoryCache

            self.cache = MemoryCache()
            self.cache_type = "memory"
            self.logger.info("✅ Using memory cache as fallback")

        except ImportError as e:
            raise ConfigurationError(
                "🔒 CACHE ERROR: Neither Redis nor Memory cache available.\n"
                "\n"
                f"Missing modules: {e}\n"
                "\n"
                "Ensure cache modules are properly installed:\n"
                "- app.infrastructure.cache.redis_generic\n"
                "- app.infrastructure.cache.memory\n",
                context={
                    "error_type": "no_cache_backend_available",
                    "original_error": str(e),
                },
            )

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
        if not self.cache:
            raise ConfigurationError("Cache manager not initialized")

        return await self.cache.get(key)

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
        if not self.cache:
            raise ConfigurationError("Cache manager not initialized")

        return await self.cache.set(key, value, ttl)

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
        if not self.cache:
            raise ConfigurationError("Cache manager not initialized")

        return await self.cache.delete(key)

    async def clear(self) -> None:
        """
        Clear all cached data.

        Examples:
            # Clear all cache data
            await manager.clear()

        Warning:
            This operation clears ALL cached data. Use with caution.
        """
        if not self.cache:
            raise ConfigurationError("Cache manager not initialized")

        if hasattr(self.cache, "clear"):
            await self.cache.clear()
        else:
            self.logger.warning(
                f"Clear operation not supported by {self.cache_type} cache"
            )

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
        if not self.cache:
            raise ConfigurationError("Cache manager not initialized")

        # Use get method as fallback if exists method not available
        if hasattr(self.cache, "exists"):
            return await self.cache.exists(key)
        return (await self.cache.get(key)) is not None

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
        if not self.cache:
            raise ConfigurationError("Cache manager not initialized")

        if hasattr(self.cache, "connect"):
            return await self.cache.connect()
        # Memory cache doesn't need explicit connection
        return True

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
        if not self.cache:
            return

        if hasattr(self.cache, "disconnect"):
            await self.cache.disconnect()

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
        info = {
            "cache_type": self.cache_type,
            "security_enabled": self.cache_type == "redis_secure",
            "initialized": self.cache is not None,
        }

        if self.cache and hasattr(self.cache, "get_performance_stats"):
            try:
                info["performance_stats"] = self.cache.get_performance_stats()
            except Exception:
                info["performance_stats"] = "unavailable"

        if self.cache_type == "redis_secure":
            info["encryption_active"] = True
            info["connection_secure"] = True
            if self.redis_url:
                info["connection_scheme"] = self.redis_url.split("://")[0]
        else:
            info["encryption_active"] = False
            info["connection_secure"] = False

        return info

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
        health = {
            "timestamp": __import__("time").time(),
            "cache_type": self.cache_type,
            "healthy": False,
            "errors": [],
        }

        try:
            if not self.cache:
                health["errors"].append("Cache manager not initialized")
                return health

            # Test basic cache operations
            test_key = "_health_check_test"
            test_value = {"test": True, "timestamp": health["timestamp"]}

            # Test write operation
            await self.set(test_key, test_value, ttl=10)

            # Test read operation
            retrieved = await self.get(test_key)
            if retrieved != test_value:
                health["errors"].append("Cache read/write test failed")

            # Test delete operation
            deleted = await self.delete(test_key)
            if not deleted:
                health["errors"].append("Cache delete test failed")

            # Additional Redis-specific health checks
            if self.cache_type == "redis_secure" and hasattr(
                self.cache, "test_security_configuration"
            ):
                try:
                    security_test = await self.cache.test_security_configuration()
                    if not security_test.get("overall_secure", False):
                        health["errors"].extend(
                            security_test.get("errors", ["Security test failed"])
                        )
                except Exception as e:
                    health["errors"].append(f"Security test failed: {e}")

            health["healthy"] = len(health["errors"]) == 0

        except Exception as e:
            health["errors"].append(f"Health check failed: {e!s}")

        return health

    def __str__(self) -> str:
        """String representation of cache manager."""
        return f"CacheManager(type={self.cache_type}, initialized={self.cache is not None})"

    def __repr__(self) -> str:
        """Detailed string representation of cache manager."""
        return f"CacheManager(cache_type='{self.cache_type}', redis_url='{self.redis_url}', initialized={self.cache is not None})"
