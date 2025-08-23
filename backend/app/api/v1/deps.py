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
    Asynchronous domain service dependency provider for comprehensive AI text processing capabilities.
    
    This async dependency provider creates fully configured TextProcessorService instances by composing
    infrastructure services (settings and cache) into domain-specific functionality. It demonstrates
    advanced dependency injection patterns for multi-service composition and async service instantiation
    optimized for high-performance AI text processing operations.
    
    Args:
        settings: Application configuration dependency containing AI model settings, API keys,
                 processing parameters, and environment-specific configuration for text processing
        cache: AI response cache service dependency providing Redis-backed caching with memory
              fallback for optimized response times and reduced AI service load
    
    Returns:
        TextProcessorService: Fully configured domain service instance providing:
                             - Comprehensive AI text processing operations (summarization, sentiment, etc.)
                             - Integrated caching for improved performance and cost optimization
                             - Async-optimized processing with concurrent operation support
                             - Infrastructure service composition for production reliability
    
    Behavior:
        **Service Composition:**
        - Instantiates TextProcessorService with fully configured infrastructure dependencies
        - Composes settings and cache services into unified domain service interface
        - Provides async-compatible service initialization for optimal FastAPI integration
        - Enables dependency injection chains for complex service hierarchies
        
        **Infrastructure Integration:**
        - Automatically inherits all configuration from injected settings dependency
        - Leverages cache service for response optimization and performance enhancement
        - Integrates with monitoring and health checking through infrastructure services
        - Provides seamless fallback mechanisms when infrastructure services degrade
        
        **Performance Optimization:**
        - Uses async dependency resolution for non-blocking service creation
        - Enables concurrent processing through async service patterns
        - Optimizes memory usage through efficient service composition
        - Minimizes initialization overhead with direct service instantiation
        
        **Error Handling:**
        - Inherits robust error handling from composed infrastructure services
        - Provides graceful degradation when cache service is unavailable
        - Maintains service functionality even with partial infrastructure failures
        - Supports comprehensive logging and monitoring for troubleshooting
    
    Examples:
        >>> # Basic FastAPI endpoint integration
        >>> from fastapi import APIRouter, Depends
        >>> from app.api.v1.deps import get_text_processor
        >>> 
        >>> router = APIRouter()
        >>> 
        >>> @router.post("/process-text")
        >>> async def process_text(
        ...     text: str,
        ...     processor: TextProcessorService = Depends(get_text_processor)
        ... ):
        ...     result = await processor.process_text(text, "summarize")
        ...     return {"result": result, "cached": result.from_cache}
        
        >>> # Advanced endpoint with error handling
        >>> @router.post("/advanced-processing")
        >>> async def advanced_processing(
        ...     request: TextProcessingRequest,
        ...     processor: TextProcessorService = Depends(get_text_processor)
        ... ):
        ...     try:
        ...         result = await processor.process_operation(
        ...             text=request.text,
        ...             operation=request.operation,
        ...             options=request.options
        ...         )
        ...         return {"success": True, "data": result}
        ...     except Exception as e:
        ...         return {"success": False, "error": str(e)}
        
        >>> # Service verification and health checking
        >>> processor = await get_text_processor()
        >>> assert processor.settings is not None
        >>> assert processor.cache is not None
        >>> health_status = await processor.health_check()
        >>> assert health_status["ai_service"] is True
        
        >>> # Batch processing integration
        >>> @router.post("/batch-process")
        >>> async def batch_process(
        ...     requests: List[TextProcessingRequest],
        ...     processor: TextProcessorService = Depends(get_text_processor)
        ... ):
        ...     results = []
        ...     for request in requests:
        ...         result = await processor.process_text(
        ...             request.text, request.operation
        ...         )
        ...         results.append(result)
        ...     return {"results": results, "count": len(results)}
    
    Note:
        This async dependency provider is optimized for FastAPI async endpoints and provides
        optimal performance for AI text processing operations. Use this version for async
        endpoints to maintain proper async context and enable concurrent processing capabilities.
        The service maintains full infrastructure integration while providing domain-specific
        functionality tailored for AI text processing use cases.
    """
    return TextProcessorService(settings=settings, cache=cache)


def get_text_processor_service(
    settings: Settings = Depends(get_settings),
    cache_service: AIResponseCache = Depends(get_cache_service)
) -> TextProcessorService:
    """
    Synchronous domain service dependency provider for AI text processing with infrastructure composition.
    
    This synchronous dependency provider creates TextProcessorService instances through infrastructure
    service composition, optimized for synchronous FastAPI endpoints and testing scenarios. It provides
    the same domain functionality as the async variant but with synchronous dependency resolution patterns
    suitable for compatibility requirements and specific integration use cases.
    
    Args:
        settings: Application configuration dependency providing AI model configuration, API keys,
                 processing parameters, and environment-specific settings for text processing operations
        cache_service: AI response cache service dependency offering Redis-backed caching with graceful
                      fallback to memory-only operation for performance optimization and cost reduction
    
    Returns:
        TextProcessorService: Fully configured domain service instance providing:
                             - Complete AI text processing capabilities across multiple operations
                             - Integrated caching for response optimization and reduced AI service costs
                             - Infrastructure service composition with robust error handling
                             - Synchronous operation compatibility for legacy integration requirements
    
    Behavior:
        **Synchronous Service Composition:**
        - Instantiates TextProcessorService with synchronous dependency resolution patterns
        - Composes infrastructure services into unified domain service interface
        - Provides compatibility with synchronous FastAPI endpoints and testing frameworks
        - Avoids LRU caching due to AIResponseCache non-hashable object constraints
        
        **Infrastructure Integration:**
        - Integrates with application settings for comprehensive configuration management
        - Leverages cache service for performance optimization and response caching
        - Maintains compatibility with all infrastructure monitoring and health checking
        - Provides seamless integration with logging and error handling systems
        
        **Performance Considerations:**
        - Creates fresh service instances for each dependency resolution (no caching)
        - Optimizes for memory efficiency through direct service instantiation
        - Maintains fast dependency resolution suitable for high-traffic scenarios
        - Balances performance with object lifecycle management requirements
        
        **Error Handling:**
        - Inherits comprehensive error handling from infrastructure service dependencies
        - Maintains service functionality with graceful degradation patterns
        - Provides robust operation continuation even with partial infrastructure failures
        - Supports detailed logging and monitoring for operational troubleshooting
    
    Examples:
        >>> # Basic synchronous FastAPI endpoint integration
        >>> from fastapi import APIRouter, Depends
        >>> from app.api.v1.deps import get_text_processor_service
        >>> 
        >>> router = APIRouter()
        >>> 
        >>> @router.post("/sync-process")
        >>> def sync_process_text(
        ...     text: str,
        ...     processor: TextProcessorService = Depends(get_text_processor_service)
        ... ):
        ...     # Note: Even with sync dependency, service operations may still be async
        ...     result = await processor.process_text(text, "summarize")
        ...     return {"result": result}
        
        >>> # Testing integration with synchronous dependency
        >>> def test_text_processor_creation():
        ...     from app.dependencies import get_settings, get_cache_service
        ...     settings = get_settings()
        ...     cache = await get_cache_service()
        ...     
        ...     processor = get_text_processor_service(settings, cache)
        ...     assert isinstance(processor, TextProcessorService)
        ...     assert processor.settings == settings
        ...     assert processor.cache == cache
        
        >>> # Dependency override for testing scenarios
        >>> from fastapi.testclient import TestClient
        >>> from unittest.mock import Mock
        >>> 
        >>> def get_mock_processor():
        ...     mock_settings = Mock()
        ...     mock_cache = Mock()
        ...     return get_text_processor_service(mock_settings, mock_cache)
        >>> 
        >>> app.dependency_overrides[get_text_processor_service] = get_mock_processor
        >>> client = TestClient(app)
        
        >>> # Service configuration verification
        >>> processor = get_text_processor_service()
        >>> assert hasattr(processor, 'settings')
        >>> assert hasattr(processor, 'cache')
        >>> assert callable(processor.process_text)
        
        >>> # Multiple instance creation behavior (no caching)
        >>> processor1 = get_text_processor_service()
        >>> processor2 = get_text_processor_service()
        >>> assert processor1 is not processor2  # Different instances due to no caching
    
    Note:
        This synchronous dependency provider does not use LRU caching because AIResponseCache
        objects are not hashable. Each call creates a fresh TextProcessorService instance with
        the injected dependencies. Use the async variant `get_text_processor()` for async
        endpoints to maintain proper async context and optimal performance characteristics.
    """
    return TextProcessorService(settings=settings, cache=cache_service)
