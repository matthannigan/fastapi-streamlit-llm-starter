---
sidebar_label: redis_generic
---

# Generic Redis cache implementation providing flexible caching capabilities.

  file_path: `backend/app/infrastructure/cache/redis_generic.py`

This module implements a generic Redis-backed cache that can handle various data
types and caching patterns. It extends the base cache interface with Redis-specific
functionality while maintaining compatibility with the standard cache contract.

## Classes

GenericRedisCache: A flexible Redis cache implementation that supports
multiple data types, custom serialization, and advanced
Redis features like expiration, atomic operations, and
pipeline operations.

## Key Features

- Generic data type support with automatic serialization/deserialization
- TTL (Time To Live) management with Redis native expiration
- Pipeline operations for batch processing
- Atomic operations using Redis transactions
- Connection pooling and failover support
- Metrics and monitoring integration

## Example

```python
```python
cache = GenericRedisCache(redis_url="redis://localhost:6379")
await cache.set("user:123", {"name": "John", "age": 30}, ttl=3600)
user_data = await cache.get("user:123")
await cache.delete("user:123")
```

## Note

This is a Phase-1 scaffolding stub. Implementation will be added in
subsequent phases of the cache refactoring project.
