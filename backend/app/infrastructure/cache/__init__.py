"""
Caching Infrastructure Service

Re-exports the main caching service class and related components.
This provides a single entry point for all caching-related imports.
"""

from app.refactor import USE_REFACTORED_STRUCTURE

if USE_REFACTORED_STRUCTURE:
    from .base import CacheInterface
    from .redis import AIResponseCache, CacheKeyGenerator
    from .memory import InMemoryCache
    from ...services.monitoring import CachePerformanceMonitor

    __all__ = ["CacheInterface", "AIResponseCache", "CacheKeyGenerator", "InMemoryCache", "CachePerformanceMonitor"]

else:
    # Bridge from the old 'services' directory.
    from ...services.cache import AIResponseCache, CacheKeyGenerator

    # Re-exporting the monitoring component from its old location.
    from ...services.monitoring import CachePerformanceMonitor

    __all__ = ["AIResponseCache", "CacheKeyGenerator", "CachePerformanceMonitor"]
