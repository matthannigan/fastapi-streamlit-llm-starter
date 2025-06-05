from functools import lru_cache
import logging
from fastapi import Depends
from .config import Settings, settings
from .services.cache import AIResponseCache
from .services.text_processor import TextProcessorService

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
        default_ttl=3600,  # 1 hour default, could be made configurable
        text_hash_threshold=settings.cache_text_hash_threshold,
        compression_threshold=settings.cache_compression_threshold,
        compression_level=settings.cache_compression_level
    )
    
    try:
        await cache.connect()
    except Exception as e:
        # Log the error but continue gracefully - cache will operate without Redis
        logger.warning(f"Failed to connect to Redis: {e}. Cache will operate without persistence.")
    
    return cache


async def get_text_processor(settings: Settings = Depends(get_settings), cache: AIResponseCache = Depends(get_cache_service)) -> TextProcessorService:
    """
    Asynchronous dependency provider for text processor service.
    
    Creates and returns a configured TextProcessorService instance that uses
    the injected settings and cache service. This is the async version of the
    text processor dependency provider.
    
    Args:
        settings: Injected application settings dependency
        cache: Injected cache service dependency
        
    Returns:
        TextProcessorService: Configured text processor service instance
    """
    return TextProcessorService(settings=settings, cache=cache)


def get_text_processor_service(
    settings: Settings = Depends(get_settings),
    cache_service: AIResponseCache = Depends(get_cache_service)
) -> TextProcessorService:
    """
    Dependency provider for text processor service.
    
    Creates and returns a configured TextProcessorService instance that uses
    the injected settings and cache service. Note: Does not use lru_cache since 
    AIResponseCache objects are not hashable.
    
    Args:
        settings: Injected application settings dependency
        cache_service: Injected cache service dependency
        
    Returns:
        TextProcessorService: Configured text processor service instance
    """
    return TextProcessorService(settings=settings, cache=cache_service) 