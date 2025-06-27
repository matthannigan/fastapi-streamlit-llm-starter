"""FastAPI Dependency Providers Module.

This module provides dependency injection functions for FastAPI endpoints,
offering centralized access to core application services and configuration.

Dependencies Provided:
    get_settings(): Cached application settings provider that returns a singleton
        Settings instance for consistent configuration access across the application.
        
    get_fresh_settings(): Uncached settings provider that creates fresh Settings
        instances on each call. Primarily used for testing scenarios where
        configuration overrides or isolated instances are needed.
        
    get_cache_service(): Async AI response cache service provider that creates
        and configures an AIResponseCache instance with Redis connectivity.
        Includes graceful degradation to in-memory-only operation when Redis
        is unavailable.

Usage:
    These dependency providers are designed to be used with FastAPI's dependency
    injection system through the Depends() function:
    
    ```python
    @app.get("/endpoint")
    async def endpoint(
        settings: Settings = Depends(get_settings),
        cache: AIResponseCache = Depends(get_cache_service)
    ):
        # Use injected dependencies
        pass
    ```

Notes:
    - get_settings() uses functools.lru_cache for performance optimization
    - get_cache_service() handles Redis connection failures gracefully
    - All providers follow FastAPI's dependency injection patterns
"""

from functools import lru_cache
import logging
from fastapi import Depends

from app.config import Settings, settings
from app.infrastructure.cache import AIResponseCache

logger = logging.getLogger(__name__)


@lru_cache()
def get_settings() -> Settings:
    """
    Dependency provider for application settings.
    
    Uses lru_cache to ensure the same Settings instance is returned
    across all dependency injections, improving performance and
    ensuring consistent configuration throughout the application.
    
    Returns:
        Settings: The application settings instance
    """
    return settings


# Alternative dependency provider that creates a fresh instance each time
# (useful for testing scenarios where you might want to override settings)
def get_fresh_settings() -> Settings:
    """
    Dependency provider that creates a fresh Settings instance.
    
    This is useful for testing scenarios where you might want to
    override environment variables or provide different configurations.
    
    Returns:
        Settings: A fresh Settings instance
    """
    return Settings()


async def get_cache_service(settings: Settings = Depends(get_settings)) -> AIResponseCache:
    """
    Dependency provider for AI response cache service.
    
    Creates and returns a configured AIResponseCache instance using
    settings from the application configuration. Initializes the
    cache connection asynchronously with graceful degradation when
    Redis is unavailable.
    
    Args:
        settings: Application settings dependency
        
    Returns:
        AIResponseCache: Configured cache service instance (with or without Redis connection)
    """
    cache = AIResponseCache(
        redis_url=settings.redis_url,
        default_ttl=settings.cache_default_ttl,
        text_hash_threshold=settings.cache_text_hash_threshold,
        compression_threshold=settings.cache_compression_threshold,
        compression_level=settings.cache_compression_level,
        text_size_tiers=settings.cache_text_size_tiers,
        memory_cache_size=settings.cache_memory_cache_size
    )
    
    try:
        await cache.connect()
    except Exception as e:
        # Log the error but continue gracefully - cache will operate without Redis
        logger.warning(f"Failed to connect to Redis: {e}. Cache will operate without persistence.")
    
    return cache
