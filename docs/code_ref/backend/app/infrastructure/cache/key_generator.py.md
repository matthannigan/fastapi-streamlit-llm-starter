---
sidebar_label: key_generator
---

# [REFACTORED] Cache key generation utilities for consistent and collision-free caching.

  file_path: `backend/app/infrastructure/cache/key_generator.py`

This module provides a standalone cache key generator that efficiently handles
large texts by using streaming SHA-256 hashing strategies while preserving
backward compatibility with existing key formats.

## Classes

CacheKeyGenerator: Optimized cache key generator that efficiently handles large texts
by using hashing strategies and metadata inclusion for uniqueness.

## Key Features

- **Streaming Hash Generation**: Uses streaming SHA-256 hashing for large texts
to minimize memory usage and maximize performance.

- **Backward Compatible Format**: Preserves existing cache key format to ensure
compatibility with existing cached data and implementations.

- **Performance Monitoring**: Optional integration with performance monitoring
for tracking key generation metrics and timing.

- **Intelligent Text Handling**: Efficiently processes texts of any size with
configurable thresholds for when to use hashing vs. direct inclusion.

- **Redis-Free Design**: Completely independent of Redis dependencies, accepting
only optional performance monitor for tracking.

- **Secure Hashing**: Uses SHA-256 for cryptographically secure hashing with
metadata inclusion for enhanced uniqueness.

## Configuration

The key generator supports extensive configuration:

- text_hash_threshold: Size threshold for text hashing (default: 1000 chars)
- hash_algorithm: Hash algorithm to use (default: hashlib.sha256)
- performance_monitor: Optional performance monitor for metrics tracking

## Usage Examples

### Basic Usage

```python
generator = CacheKeyGenerator()
key = generator.generate_cache_key(
    text="Document to summarize...",
    operation="summarize",
    options={"max_length": 100}
)
# Result: "ai_cache:op:summarize|txt:Document to summarize...|opts:abc12345"
```

### With Performance Monitoring

```python
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
monitor = CachePerformanceMonitor()
generator = CacheKeyGenerator(performance_monitor=monitor)
key = generator.generate_cache_key("text", "sentiment", {})
stats = generator.get_key_generation_stats()
print(f"Keys generated: {stats['total_keys_generated']}")
```

### Large Text Handling

```python
large_text = "A" * 10000  # 10KB text
key = generator.generate_cache_key(large_text, "summarize", {})
# Result: "ai_cache:op:summarize|txt:hash:a1b2c3d4e5f6"
```

### Custom Configuration

```python
generator = CacheKeyGenerator(
    text_hash_threshold=500,  # Hash texts over 500 chars
    hash_algorithm=hashlib.sha256
)
```

## Thread Safety

This module is designed to be thread-safe and stateless for concurrent usage.
Performance monitoring data is collected safely across multiple threads.

## Performance Considerations

- Streaming hashing minimizes memory usage for large texts
- Configurable thresholds allow optimization for specific use cases
- Performance monitoring adds minimal overhead (< 1ms per operation)
- Key generation scales linearly with text size for hashed content
