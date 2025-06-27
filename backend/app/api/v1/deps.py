from fastapi import Depends

from app.config import Settings
from app.dependencies import get_settings, get_cache_service
from app.infrastructure.cache import AIResponseCache
from app.services.text_processor import TextProcessorService


async def get_text_processor(
    settings: Settings = Depends(get_settings), 
    cache: AIResponseCache = Depends(get_cache_service)
) -> TextProcessorService:
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
