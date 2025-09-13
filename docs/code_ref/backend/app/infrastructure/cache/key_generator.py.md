---
sidebar_label: key_generator
---

# Optimized cache key generation with streaming hash support for large texts.

  file_path: `backend/app/infrastructure/cache/key_generator.py`

This module provides efficient cache key generation that handles texts of any size
using streaming SHA-256 hashing strategies while maintaining backward compatibility
with existing key formats.

## Classes

**CacheKeyGenerator**: Optimized cache key generator with intelligent text handling
and streaming hash generation for memory-efficient processing of large texts.

## Key Features

- **Streaming Hashing**: Memory-efficient SHA-256 hashing for large texts
- **Performance Optimized**: Configurable thresholds for hash vs. direct inclusion
- **Backward Compatible**: Preserves existing cache key formats
- **Monitoring Integration**: Optional performance monitoring and metrics tracking
- **Redis-Free Design**: Independent operation without Redis dependencies
      only optional performance monitor for tracking.

    - **Secure Hashing**: Uses SHA-256 for cryptographically secure hashing with
      metadata inclusion for enhanced uniqueness.

Configuration:
    The key generator supports extensive configuration:

    - text_hash_threshold: Size threshold for text hashing (default: 1000 chars)
    - hash_algorithm: Hash algorithm to use (default: hashlib.sha256)
    - performance_monitor: Optional performance monitor for metrics tracking

Usage Examples:
    Basic Usage:
        >>> generator = CacheKeyGenerator()
        >>> key = generator.generate_cache_key(
        ...     text="Document to summarize...",
        ...     operation="summarize",
        ...     options={"max_length": 100}
        ... )
        >>> # Result: "ai_cache:op:summarize|txt:Document to summarize...|opts:abc12345"

    Q&A Usage with Question in Options:
        >>> key = generator.generate_cache_key(
        ...     text="Document content",
        ...     operation="qa",
        ...     options={"question": "What is the main point?", "max_tokens": 150}
        ... )
        >>> # Result: "ai_cache:op:qa|txt:Document content|opts:def12345|q:ghi67890"

    With Performance Monitoring:
        >>> from app.infrastructure.cache.monitoring import CachePerformanceMonitor
        >>> monitor = CachePerformanceMonitor()
        >>> generator = CacheKeyGenerator(performance_monitor=monitor)
        >>> key = generator.generate_cache_key("text", "sentiment", {})
        >>> stats = generator.get_key_generation_stats()
        >>> print(f"Keys generated: {stats['total_keys_generated']}")

    Large Text Handling:
        >>> large_text = "A" * 10000  # 10KB text
        >>> key = generator.generate_cache_key(large_text, "summarize", {})
        >>> # Result: "ai_cache:op:summarize|txt:hash:a1b2c3d4e5f6"

    Custom Configuration:
        >>> generator = CacheKeyGenerator(
        ...     text_hash_threshold=500,  # Hash texts over 500 chars
        ...     hash_algorithm=hashlib.sha256
        ... )

Thread Safety:
    This module is designed to be thread-safe and stateless for concurrent usage.
    Performance monitoring data is collected safely across multiple threads.

Performance Considerations:
    - Streaming hashing minimizes memory usage for large texts
    - Configurable thresholds allow optimization for specific use cases
    - Performance monitoring adds minimal overhead (< 1ms per operation)
    - Key generation scales linearly with text size for hashed content

## CacheKeyGenerator

High-performance cache key generator with streaming hash algorithms and intelligent text processing.

Provides efficient cache key generation optimized for AI text processing workloads with
configurable hashing thresholds, backward compatibility, and performance monitoring.
Designed as a standalone component free of external cache dependencies.

Attributes:
    text_hash_threshold: int character count threshold (100-100000) for hash vs direct inclusion
    hash_algorithm: Callable hash algorithm function (default: hashlib.sha256)
    performance_monitor: Optional[CachePerformanceMonitor] metrics tracking instance

Public Methods:
    generate_cache_key(): Primary key generation method with intelligent text handling
    _hash_large_text(): Internal streaming hash method for memory efficiency

State Management:
    - Thread-safe key generation for concurrent cache operations
    - Consistent key format maintaining backward compatibility
    - Streaming hash processing for memory-efficient large text handling
    - Optional performance metrics collection without impacting generation speed

Usage:
    # Basic key generation
    generator = CacheKeyGenerator()
    key = generator.generate_cache_key("User input text", "summarize", {"max_length": 100})

    # Large text optimization with custom threshold
    generator = CacheKeyGenerator(text_hash_threshold=2000)
    key = generator.generate_cache_key(large_document, "analyze", {})

    # Production usage with monitoring
    monitor = CachePerformanceMonitor()
    generator = CacheKeyGenerator(
        text_hash_threshold=1000,
        performance_monitor=monitor
    )

Example:
    >>> generator = CacheKeyGenerator()
    >>> key = generator.generate_cache_key(
    ...     text="Document text...",
    ...     operation="summarize",
    ...     options={"max_length": 100}
    ... )
    >>> stats = generator.get_key_generation_stats()
    >>> print(f"Total keys: {stats.get('total_keys_generated', 0)}")

### __init__()

```python
def __init__(self, text_hash_threshold: int = 1000, hash_algorithm = hashlib.sha256, performance_monitor: Optional['CachePerformanceMonitor'] = None):
```

Initialize CacheKeyGenerator with configurable parameters.

Args:
    text_hash_threshold: Character count threshold above which text is hashed
    hash_algorithm: Hash algorithm to use (default: SHA256)
    performance_monitor: Optional performance monitor for tracking key generation timing

### generate_cache_key()

```python
def generate_cache_key(self, text: str, operation: str, options: Dict[str, Any]) -> str:
```

Generate optimized cache key with efficient text handling.

Creates a cache key using the format:
"ai_cache:op:{operation}|txt:{text_or_hash}|opts:{options_hash}|q:{question_hash}"

The method maintains backward compatibility with existing key formats
while providing efficient handling of large texts through streaming hashing.
Questions are now extracted from the options dictionary to maintain
architectural separation and eliminate domain-specific parameters.

Args:
    text: Input text content
    operation: Operation type (summarize, sentiment, etc.)
    options: Operation options dictionary containing all parameters
            including embedded question for Q&A operations

Returns:
    Optimized cache key string compatible with existing cache systems.

Example:
    >>> generator = CacheKeyGenerator()
    >>> key = generator.generate_cache_key(
    ...     text="Sample document",
    ...     operation="summarize",
    ...     options={"max_length": 100}
    ... )
    >>> print(key)
    'ai_cache:op:summarize|txt:Sample document|opts:abc12345'

    >>> # Q&A operation with question in options
    >>> key = generator.generate_cache_key(
    ...     text="Document content",
    ...     operation="qa",
    ...     options={"question": "What is the main point?", "max_tokens": 150}
    ... )
    >>> print(key)
    'ai_cache:op:qa|txt:Document content|opts:def67890|q:hij12345'

### get_key_generation_stats()

```python
def get_key_generation_stats(self) -> Dict[str, Any]:
```

Get key generation statistics from the performance monitor.

Returns comprehensive statistics about key generation performance
including timing, text size distribution, and operation patterns.

Returns:
    Dict[str, Any]: Statistics dictionary containing:
        - total_keys_generated: Total number of keys generated
        - average_generation_time: Average time to generate a key
        - text_size_distribution: Distribution of text sizes processed
        - operation_distribution: Distribution of operations processed
        - recent_performance: Recent performance metrics

Example:
    >>> generator = CacheKeyGenerator(performance_monitor=monitor)
    >>> # ... generate some keys ...
    >>> stats = generator.get_key_generation_stats()
    >>> print(f"Generated {stats['total_keys_generated']} keys")
    >>> print(f"Average time: {stats['average_generation_time']:.3f}s")
