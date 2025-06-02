from functools import lru_cache
from fastapi import Depends
from .config import Settings, settings
from .services.cache import AIResponseCache
from .services.text_processor import TextProcessorService


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


def get_cache_service(settings: Settings = Depends(get_settings)) -> AIResponseCache:
    """
    Dependency provider for AI response cache service.
    
    Creates and returns a configured AIResponseCache instance using
    settings from the application configuration. Note: Does not use
    lru_cache since Settings objects are not hashable.
    
    Args:
        settings: Application settings dependency
        
    Returns:
        AIResponseCache: Configured cache service instance
    """
    return AIResponseCache(
        redis_url=settings.redis_url,
        default_ttl=3600  # 1 hour default, could be made configurable
    )


def get_text_processor_service(cache_service: AIResponseCache = Depends(get_cache_service)) -> TextProcessorService:
    """
    Dependency provider for text processor service.
    
    Creates and returns a configured TextProcessorService instance that uses
    the injected cache service. Note: Does not use lru_cache since AIResponseCache
    objects are not hashable.
    
    Args:
        cache_service: Injected cache service dependency
        
    Returns:
        TextProcessorService: Configured text processor service instance
    """
    return TextProcessorService(cache_service=cache_service) 