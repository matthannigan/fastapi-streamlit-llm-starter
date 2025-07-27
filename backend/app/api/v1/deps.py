"""Domain Service: API Dependency Providers

📚 **EXAMPLE IMPLEMENTATION** - Replace in your project  
💡 **Demonstrates infrastructure usage patterns**  
🔄 **Expected to be modified/replaced**

This module provides FastAPI dependency providers for domain services, demonstrating
how to compose infrastructure services into domain-specific dependency injection
patterns. It serves as an example for building dependency hierarchies that combine
multiple infrastructure services.

## Core Components

### Dependency Providers
- `get_text_processor()`: Async text processor service provider
- `get_text_processor_service()`: Sync text processor service provider

### Service Composition
Both providers demonstrate how to:
- Inject multiple infrastructure dependencies (settings, cache)
- Compose them into domain service instances
- Handle async vs sync dependency patterns
- Avoid caching issues with non-hashable dependencies

## Dependencies & Integration

### Infrastructure Dependencies
- `get_settings()`: Application settings dependency from core infrastructure
- `get_cache_service()`: Cache service dependency from infrastructure layer
- `TextProcessorService`: Domain service that composes infrastructure services

### Composition Patterns
- **Multi-dependency injection**: Combines settings and cache services
- **Service instantiation**: Creates configured domain service instances
- **Async compatibility**: Provides both sync and async variants

## Usage Examples

### In API Endpoints
```python
@router.post("/process")
async def process_text(
    request: TextProcessingRequest,
    text_processor: TextProcessorService = Depends(get_text_processor)
):
    return await text_processor.process_text(request)
```

### Dependency Chain
```
API Endpoint → get_text_processor() → TextProcessorService(settings, cache)
                ↑                           ↑          ↑
        FastAPI DI              get_settings()  get_cache_service()
```

## Implementation Notes

This module demonstrates domain-level dependency patterns that:
- Compose infrastructure services into domain services
- Handle complex dependency hierarchies with proper injection
- Provide both sync and async variants for different use cases
- Avoid common pitfalls like caching non-hashable objects

**Replace in your project** - Customize the dependency providers and service
composition patterns based on your specific domain service requirements.
"""

from fastapi import Depends

from app.core.config import Settings
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
