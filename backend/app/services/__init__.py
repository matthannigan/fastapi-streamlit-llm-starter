"""
Domain Services Layer

Re-exports the primary domain services of the application.
During refactoring, this points to the original location.
"""

# Bridge the example domain service from its old location.
from .text_processor import TextProcessorService

from .monitoring import CachePerformanceMonitor, PerformanceMetric, CompressionMetric, MemoryUsageMetric, InvalidationMetric

__all__ = [
    "CachePerformanceMonitor",
    "PerformanceMetric", 
    "CompressionMetric",
    "MemoryUsageMetric",
    "InvalidationMetric",
    "TextProcessorService"
]
