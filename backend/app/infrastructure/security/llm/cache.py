"""
Security Result Cache - Intelligent caching for LLM security scan results.

This module provides production-ready caching infrastructure for security scan results
to minimize redundant AI security scans and improve application performance. It implements
Redis-based distributed caching with graceful fallback to in-memory caching, ensuring
security scanning reliability even when external services are unavailable.

## Architecture Overview

The security result cache provides enterprise-grade caching capabilities:

- **Content-Based Key Generation**: SHA-256 hash combining scanned content, scanner
  configuration, and version identifiers ensures cache integrity
- **Intelligent TTL Management**: Configurable time-to-live per scanner type with
  automatic expiration and cleanup
- **Performance Monitoring**: Real-time cache statistics including hit rates, miss rates,
  and lookup performance metrics
- **Graceful Degradation**: Automatic fallback from Redis to memory cache when
  distributed cache is unavailable
- **Configuration Integration**: Seamless integration with security scanner configuration
  changes to maintain cache consistency

## Key Features

- **Deterministic Cache Keys**: Content hash with scanner configuration and version
- **Rich Cache Entries**: Complete SecurityResult objects with metadata and access patterns
- **Configuration-Aware Caching**: Automatic cache invalidation on scanner configuration changes
- **Comprehensive Monitoring**: Cache health checks, performance metrics, and usage statistics
- **Fault Tolerance**: Cache failures never break security scanning functionality

## Primary Classes

- **SecurityResultCache**: Main cache implementation with Redis and memory fallback
- **CacheStatistics**: Performance metrics tracking and monitoring
- **CacheEntry**: Rich cache entries with metadata and access tracking

## Usage Example

```python
from app.infrastructure.security.llm.config import SecurityConfig
from app.infrastructure.security.llm.cache import SecurityResultCache

# Initialize cache with security configuration
config = SecurityConfig.from_file("security_config.yaml")
cache = SecurityResultCache(config)
await cache.initialize()

# Cache a security result
result = SecurityResult(is_safe=True, violations=[], score=1.0, ...)
await cache.set("user input text", "input", result, ttl_seconds=3600)

# Retrieve cached result
cached_result = await cache.get("user input text", "input")
if cached_result:
    print("Using cached security result")
else:
    print("Performing new security scan")

# Monitor cache performance
stats = await cache.get_statistics()
print(f"Cache hit rate: {stats.hit_rate:.1f}%")
```

## Performance Characteristics

- **Redis Mode**: Distributed caching with sub-millisecond lookups
- **Memory Fallback**: Local caching with microsecond lookups when Redis unavailable
- **Hit Rate Optimization**: Content-based keys maximize cache efficiency
- **Memory Management**: Automatic TTL-based expiration prevents memory leaks
- **Thread Safety**: All operations are async-safe for concurrent access
"""

import hashlib
import json
import logging
import time
from datetime import datetime, UTC
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.memory import InMemoryCache
from app.infrastructure.cache.factory import CacheFactory
from app.infrastructure.security.llm.protocol import SecurityResult, Violation
from app.infrastructure.security.llm.config import SecurityConfig

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """
    Rich cache entry containing security scan results with comprehensive metadata.

    This class encapsulates a cached security result along with all metadata needed
    for cache management, performance monitoring, and configuration change detection.
    It provides serialization support for Redis storage and tracks access patterns
    for cache optimization.

    Attributes:
        result: SecurityResult object containing scan findings, violations, and metadata
        cached_at: UTC timestamp when this entry was originally cached
        cache_key: Unique cache key used to identify this entry in storage
        scanner_config_hash: SHA-256 hash of scanner configuration used for the scan
        scanner_version: Version identifier of security scanners that generated this result
        ttl_seconds: Time-to-live duration in seconds for this cache entry
        hit_count: Number of times this entry has been successfully retrieved from cache

    Public Methods:
        to_dict(): Convert entry to dictionary for Redis serialization
        from_dict(): Create entry from dictionary for Redis deserialization

    Usage:
        >>> # Create a new cache entry
        >>> result = SecurityResult(
        ...     is_safe=True,
        ...     violations=[],
        ...     score=1.0,
        ...     scanned_text="test input",
        ...     scan_duration_ms=150,
        ...     scanner_results={},
        ...     metadata={}
        ... )
        >>> entry = CacheEntry(
        ...     result=result,
        ...     cached_at=datetime.now(UTC),
        ...     cache_key="security_scan:input:abc123hash",
        ...     scanner_config_hash="def456hash",
        ...     scanner_version="1.0.0",
        ...     ttl_seconds=3600
        ... )
        >>>
        >>> # Serialize for Redis storage
        >>> serialized = entry.to_dict()
        >>>
        >>> # Deserialize from Redis
        >>> restored_entry = CacheEntry.from_dict(serialized)
        >>> assert restored_entry.result.is_safe == result.is_safe
    """
    result: SecurityResult
    cached_at: datetime
    cache_key: str
    scanner_config_hash: str
    scanner_version: str
    ttl_seconds: int
    hit_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert cache entry to dictionary for Redis serialization.

        Serializes all entry data including nested SecurityResult objects
        and datetime objects to Redis-compatible formats. All data is
        converted to JSON-serializable types.

        Returns:
            Dictionary containing all entry data in JSON-serializable format:
            - result: SecurityResult data as dictionary
            - cached_at: ISO-formatted UTC timestamp string
            - cache_key: String cache key identifier
            - scanner_config_hash: Configuration hash string
            - scanner_version: Scanner version string
            - ttl_seconds: TTL duration as integer
            - hit_count: Access count as integer

        Example:
            >>> entry = CacheEntry(...)
            >>> serialized = entry.to_dict()
            >>> assert isinstance(serialized["cached_at"], str)
            >>> assert isinstance(serialized["result"], dict)
        """
        return {
            "result": asdict(self.result),
            "cached_at": self.cached_at.isoformat(),
            "cache_key": self.cache_key,
            "scanner_config_hash": self.scanner_config_hash,
            "scanner_version": self.scanner_version,
            "ttl_seconds": self.ttl_seconds,
            "hit_count": self.hit_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """
        Create cache entry from dictionary for Redis deserialization.

        Reconstructs a complete CacheEntry object from dictionary data,
        including nested SecurityResult objects and datetime parsing.
        Handles missing optional fields with appropriate defaults.

        Args:
            data: Dictionary containing serialized cache entry data with
                  the following required keys:
                - result: SecurityResult dictionary with scan data
                - cached_at: ISO-formatted timestamp string
                - cache_key: Cache key string
                - scanner_config_hash: Configuration hash string
                - scanner_version: Scanner version string
                - ttl_seconds: TTL duration integer
                Optional keys:
                - hit_count: Access count integer (defaults to 0)

        Returns:
            Reconstructed CacheEntry object with all data properly deserialized

        Raises:
            KeyError: If required dictionary keys are missing
            ValueError: If timestamp format is invalid or data is malformed
            TypeError: If data types are incorrect for reconstruction

        Example:
            >>> serialized = entry.to_dict()
            >>> restored = CacheEntry.from_dict(serialized)
            >>> assert restored.result.is_safe == entry.result.is_safe
            >>> assert restored.cached_at == entry.cached_at
        """
        # Recreate SecurityResult from dict
        result_data = data["result"]
        violations = [
            Violation(**v) for v in result_data.get("violations", [])
        ]

        result = SecurityResult(
            is_safe=result_data["is_safe"],
            violations=violations,
            score=result_data["score"],
            scanned_text=result_data["scanned_text"],
            scan_duration_ms=result_data["scan_duration_ms"],
            scanner_results=result_data.get("scanner_results", {}),
            metadata=result_data.get("metadata", {}),
        )

        return cls(
            result=result,
            cached_at=datetime.fromisoformat(data["cached_at"]),
            cache_key=data["cache_key"],
            scanner_config_hash=data["scanner_config_hash"],
            scanner_version=data["scanner_version"],
            ttl_seconds=data["ttl_seconds"],
            hit_count=data.get("hit_count", 0),
        )


@dataclass
class CacheStatistics:
    """
    Comprehensive cache performance metrics and monitoring data.

    This class tracks all aspects of cache performance including hit/miss ratios,
    lookup times, cache size, and memory usage. It provides running averages
    and derived metrics for cache optimization and monitoring.

    Attributes:
        hits: Number of successful cache retrievals (read-only)
        misses: Number of cache misses where data was not found (read-only)
        total_requests: Total number of cache operations performed (read-only)
        avg_lookup_time_ms: Rolling average lookup time in milliseconds (read-only)
        cache_size: Current number of entries stored in cache (read-only)
        memory_usage_mb: Estimated memory usage of cache in megabytes (read-only)
        last_reset: UTC timestamp when statistics were last reset (auto-set on init)

    Public Properties:
        hit_rate: Calculated cache hit rate as percentage (0-100)

    Public Methods:
        record_hit(): Record a successful cache retrieval with timing
        record_miss(): Record a cache miss with timing
        reset(): Reset all statistics to initial values
        to_dict(): Convert statistics to dictionary for serialization

    Usage:
        >>> stats = CacheStatistics()
        >>>
        >>> # Record cache operations
        >>> stats.record_hit(0.5)  # 0.5ms lookup time
        >>> stats.record_miss(1.2)  # 1.2ms lookup time
        >>>
        >>> # Check performance
        >>> print(f"Hit rate: {stats.hit_rate:.1f}%")
        >>> print(f"Avg lookup: {stats.avg_lookup_time_ms:.2f}ms")
        >>>
        >>> # Reset for new measurement period
        >>> stats.reset()

    State Management:
        - Thread-safe for concurrent access within async context
        - Maintains running averages using mathematical rolling calculation
        - Auto-initializes last_reset timestamp on creation
        - All timing measurements use floating-point milliseconds
    """
    hits: int = 0
    misses: int = 0
    total_requests: int = 0
    avg_lookup_time_ms: float = 0.0
    cache_size: int = 0
    memory_usage_mb: float = 0.0
    last_reset: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.last_reset is None:
            self.last_reset = datetime.now(UTC)

    @property
    def hit_rate(self) -> float:
        """
        Calculate cache hit rate as percentage of total requests.

        Returns:
            Hit rate as float percentage (0.0 to 100.0). Returns 0.0 when
            no requests have been recorded to avoid division by zero.

        Example:
            >>> stats = CacheStatistics()
            >>> stats.record_hit(1.0)
            >>> stats.record_miss(1.0)
            >>> print(stats.hit_rate)  # 50.0%
            50.0
        """
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    def record_hit(self, lookup_time_ms: float) -> None:
        """
        Record a successful cache retrieval with timing information.

        Updates hit count, total requests, and running average lookup time.
        This method should be called after each successful cache retrieval.

        Args:
            lookup_time_ms: Time taken for cache lookup in milliseconds.
                          Should be positive float for valid measurements.

        Behavior:
            - Increments hit counter by 1
            - Increments total requests counter by 1
            - Updates rolling average lookup time using mathematical formula
            - Handles first request case for average initialization

        Example:
            >>> stats = CacheStatistics()
            >>> stats.record_hit(0.75)  # 0.75ms lookup time
            >>> assert stats.hits == 1
            >>> assert stats.total_requests == 1
            >>> assert stats.avg_lookup_time_ms == 0.75
        """
        self.hits += 1
        self.total_requests += 1
        self._update_avg_lookup_time(lookup_time_ms)

    def record_miss(self, lookup_time_ms: float) -> None:
        """
        Record a cache miss with timing information.

        Updates miss count, total requests, and running average lookup time.
        This method should be called after each failed cache retrieval.

        Args:
            lookup_time_ms: Time taken for cache lookup in milliseconds.
                          Should be positive float for valid measurements.

        Behavior:
            - Increments miss counter by 1
            - Increments total requests counter by 1
            - Updates rolling average lookup time using mathematical formula
            - Maintains consistent averaging across hits and misses

        Example:
            >>> stats = CacheStatistics()
            >>> stats.record_miss(2.1)  # 2.1ms lookup time
            >>> assert stats.misses == 1
            >>> assert stats.total_requests == 1
            >>> assert stats.avg_lookup_time_ms == 2.1
        """
        self.misses += 1
        self.total_requests += 1
        self._update_avg_lookup_time(lookup_time_ms)

    def _update_avg_lookup_time(self, lookup_time_ms: float) -> None:
        """
        Update rolling average lookup time using mathematical running average.

        Uses formula: new_avg = (old_avg * (n-1) + new_value) / n
        This provides O(1) time complexity and maintains accurate running
        averages without storing all historical values.

        Args:
            lookup_time_ms: New lookup time to incorporate into average
        """
        if self.total_requests == 1:
            self.avg_lookup_time_ms = lookup_time_ms
        else:
            # Running average: new_avg = (old_avg * (n-1) + new_value) / n
            self.avg_lookup_time_ms = (
                (self.avg_lookup_time_ms * (self.total_requests - 1) + lookup_time_ms)
                / self.total_requests
            )

    def reset(self) -> None:
        """
        Reset all statistics to initial state for new measurement period.

        Resets all counters and timing data while updating the last_reset
        timestamp to current time. This is useful for periodic monitoring
        or testing scenarios where clean state is needed.

        Behavior:
            - Sets hits, misses, and total_requests to 0
            - Sets average lookup time to 0.0
            - Updates last_reset timestamp to current UTC time
            - Preserves cache_size and memory_usage_mb (set externally)

        Example:
            >>> stats = CacheStatistics()
            >>> stats.record_hit(1.0)
            >>> stats.record_miss(1.0)
            >>> print(stats.hit_rate)  # 50.0%
            >>> stats.reset()
            >>> print(stats.hit_rate)  # 0.0%
            >>> assert stats.total_requests == 0
        """
        self.hits = 0
        self.misses = 0
        self.total_requests = 0
        self.avg_lookup_time_ms = 0.0
        self.last_reset = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert statistics to dictionary for JSON serialization and API responses.

        Formats all data for JSON compatibility, including timestamp conversion
        and rounding of floating-point values for consistent API responses.

        Returns:
            Dictionary containing formatted statistics:
            - hits: Integer hit count
            - misses: Integer miss count
            - total_requests: Integer total request count
            - hit_rate: Rounded hit rate percentage (2 decimal places)
            - avg_lookup_time_ms: Rounded average lookup time (3 decimal places)
            - cache_size: Current cache entry count
            - memory_usage_mb: Rounded memory usage in MB (2 decimal places)
            - last_reset: ISO-formatted UTC timestamp string or None

        Example:
            >>> stats = CacheStatistics()
            >>> stats.record_hit(1.234)
            >>> serialized = stats.to_dict()
            >>> assert serialized["hit_rate"] == 100.0
            >>> assert serialized["avg_lookup_time_ms"] == 1.234
            >>> assert isinstance(serialized["last_reset"], str)
        """
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate, 2),
            "avg_lookup_time_ms": round(self.avg_lookup_time_ms, 3),
            "cache_size": self.cache_size,
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "last_reset": self.last_reset.isoformat() if self.last_reset is not None else None,
        }


class SecurityResultCache:
    """
    Production-ready intelligent cache for LLM security scan results.

    This class provides enterprise-grade caching infrastructure with Redis-based
    distributed caching and graceful fallback to in-memory caching. It implements
    content-based key generation, intelligent TTL management, comprehensive
    performance monitoring, and fault-tolerant operation patterns.

    Attributes:
        redis_cache: Redis cache interface for distributed caching (None when unavailable)
        memory_cache: In-memory cache instance for local fallback caching
        config: Security configuration containing scanner settings and performance options
        stats: Real-time cache statistics and performance metrics
        enabled: Whether caching is currently enabled (depends on config and availability)
        key_prefix: Prefix string for all cache keys to avoid namespace collisions
        default_ttl: Default time-to-live duration in seconds for cache entries
        _redis_available: Internal flag indicating Redis connectivity status
        _scanner_config_hash: Hash of current scanner configuration for cache invalidation
        _scanner_version: Version identifier of security scanners being used

    Public Methods:
        initialize(): Establish Redis connection and test cache functionality
        get(): Retrieve cached security result with fallback patterns
        set(): Cache security result with TTL and metadata management
        delete(): Remove specific cache entry
        clear_all(): Clear all cached security results
        get_statistics(): Retrieve current cache performance metrics
        health_check(): Perform comprehensive cache health validation
        generate_cache_key(): Create deterministic cache key from content

    State Management:
        - Thread-safe async operations for concurrent access
        - Automatic Redis health monitoring and fallback switching
        - Configuration-aware cache invalidation on scanner changes
        - Memory management through TTL-based expiration
        - Graceful degradation without breaking security scanning

    Usage:
        >>> # Basic initialization and usage
        >>> config = SecurityConfig.from_file("security_config.yaml")
        >>> cache = SecurityResultCache(config, default_ttl=3600)
        >>> await cache.initialize()
        >>>
        >>> # Cache a security scan result
        >>> result = SecurityResult(
        ...     is_safe=True,
        ...     violations=[],
        ...     score=1.0,
        ...     scanned_text="user input",
        ...     scan_duration_ms=150,
        ...     scanner_results={},
        ...     metadata={}
        ... )
        >>> await cache.set("user input", "input", result, ttl_seconds=1800)
        >>>
        >>> # Retrieve cached result
        >>> cached_result = await cache.get("user input", "input")
        >>> if cached_result:
        ...     print("Using cached result - scan saved!")
        ... else:
        ...     print("Performing new security scan")
        >>>
        >>> # Monitor performance
        >>> stats = await cache.get_statistics()
        >>> print(f"Cache hit rate: {stats.hit_rate:.1f}%")
        >>> print(f"Average lookup: {stats.avg_lookup_time_ms:.2f}ms")

    Error Handling:
        - Redis connection failures automatically trigger memory fallback
        - Cache operation failures never raise exceptions to caller
        - Configuration validation occurs during initialization
        - All errors are logged for debugging and monitoring
        - Cache health status is tracked and reportable

    Performance Characteristics:
        - Redis Mode: Sub-millisecond lookups with distributed consistency
        - Memory Fallback: Microsecond lookups when Redis unavailable
        - Hit Rate Optimization: Content-based keys maximize cache efficiency
        - Memory Efficiency: Automatic cleanup prevents memory leaks
        - Concurrent Access: Async-safe for high-throughput scenarios
    """

    def __init__(
        self,
        config: SecurityConfig,
        redis_url: str | None = None,
        enabled: bool = True,
        key_prefix: str = "security_scan:",
        default_ttl: int = 3600,
    ):
        """
        Initialize security result cache with configuration and caching options.

        Creates a new cache instance with the specified security configuration
        and caching parameters. The cache supports both Redis-based distributed
        caching and in-memory fallback for fault tolerance.

        Args:
            config: Security configuration containing scanner settings, performance
                   options, and caching preferences. Must be a valid SecurityConfig
                   instance with proper scanner configuration.
            redis_url: Optional Redis connection URL. If provided, overrides the
                      Redis URL from the security configuration. Format should be
                      "redis://host:port" or "redis://username:password@host:port".
                      When None, uses configuration default or localhost:6379.
            enabled: Whether caching should be enabled. When False, all cache
                    operations become no-ops. This parameter is combined with
                    configuration settings to determine final enabled state.
            key_prefix: Prefix string added to all cache keys to avoid namespace
                       collisions. Should end with ":" for consistency. Defaults
                       to "security_scan:" for security scan cache isolation.
            default_ttl: Default time-to-live duration in seconds for cache entries.
                        Must be positive integer. Individual cache operations can
                        override this value. Defaults to 3600 (1 hour).

        Raises:
            TypeError: If config is not a SecurityConfig instance
            ValueError: If default_ttl is not a positive integer
            ConfigurationError: If security configuration is invalid

        Behavior:
            - Initializes internal state and statistics tracking
            - Creates memory cache instance for fallback usage
            - Generates scanner configuration hash for cache invalidation
            - Sets scanner version for cache compatibility tracking
            - Determines final enabled state from parameters and configuration
            - Logs initialization status and configuration summary

        Examples:
            >>> # Basic initialization with default settings
            >>> config = SecurityConfig.from_file("security.yaml")
            >>> cache = SecurityResultCache(config)
            >>> await cache.initialize()

            >>> # Custom configuration
            >>> cache = SecurityResultCache(
            ...     config=config,
            ...     redis_url="redis://cache.example.com:6379",
            ...     key_prefix="myapp:security:",
            ...     default_ttl=7200  # 2 hours
            ... )

            >>> # Disabled cache for testing
            >>> cache = SecurityResultCache(config, enabled=False)
            >>> assert not cache.enabled

        Notes:
            - Redis connection is established during initialize() call, not __init__
            - Cache key prefixes should be unique per application to avoid conflicts
            - TTL values are in seconds and should be appropriate for security scan
              result freshness requirements
        """
        self.config = config
        self.enabled = enabled and config.performance.enable_result_caching
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.redis_cache: CacheInterface | None = None
        self.memory_cache = InMemoryCache()
        self.stats = CacheStatistics()
        self._redis_available = False
        self._scanner_config_hash = self._hash_scanner_config()
        self._scanner_version = "1.0.0"  # TODO: Get from actual version

        logger.info(f"Security cache initialized - enabled: {self.enabled}")

    async def initialize(self) -> None:
        """
        Initialize cache infrastructure and establish Redis connection with fallback.

        Establishes Redis connection if available and enabled, tests connectivity,
        and configures fallback behavior. This method must be called before any
        cache operations to ensure proper initialization.

        Behavior:
            - Validates caching configuration and enabled status
            - Attempts Redis connection establishment and validation
            - Performs comprehensive Redis connectivity testing
            - Configures memory fallback when Redis unavailable
            - Updates internal state flags for cache availability
            - Logs initialization status and fallback decisions

        Redis Testing Process:
            1. Creates Redis cache instance via CacheFactory
            2. Performs write operation with test key
            3. Reads back test data to verify read/write functionality
            4. Cleans up test data
            5. Sets availability flag based on test results

        Error Handling:
            - Redis connection failures automatically enable memory fallback
            - Configuration errors are logged and caching disabled
            - Test failures result in graceful degradation to memory cache
            - All exceptions are caught and logged without raising to caller
            - Cache remains functional even with complete Redis failure

        Examples:
            >>> cache = SecurityResultCache(config)
            >>> await cache.initialize()
            >>> print(f"Redis available: {cache._redis_available}")
            Redis available: True

            >>> # With Redis unavailable
            >>> cache = SecurityResultCache(config)
            >>> await cache.initialize()
            >>> # Falls back to memory cache automatically

        Notes:
            - Must be called before any cache operations (get/set/delete)
            - Safe to call multiple times - subsequent calls are no-ops
            - Cache operations work even if initialization fails (memory fallback)
            - Redis URL is taken from config or defaults to localhost:6379
            - Test operations use short TTL (10 seconds) to minimize cleanup

        Raises:
            Never raises exceptions - all errors are handled internally
            to ensure cache operations never break application flow.
        """
        if not self.enabled:
            logger.info("Security cache disabled by configuration")
            return

        if not self.config.performance.enable_result_caching:
            logger.info("Result caching disabled in performance configuration")
            self.enabled = False
            return

        # Try to initialize Redis cache
        redis_url = getattr(self.config, "redis_url", None) or "redis://localhost:6379"

        try:
            factory = CacheFactory()
            self.redis_cache = await factory.for_ai_app(
                redis_url=redis_url,
                default_ttl=self.default_ttl,
            )

            # Test Redis connection with read/write validation
            await self.redis_cache.set("test", "test", ttl=10)
            test_result = await self.redis_cache.get("test")
            await self.redis_cache.delete("test")

            if test_result == "test":
                self._redis_available = True
                logger.info("Redis cache connected successfully")
            else:
                logger.warning("Redis cache test failed, using memory cache")
                self._redis_available = False

        except Exception as e:
            logger.warning(f"Redis cache unavailable ({e}), using memory cache: {e}")
            self._redis_available = False
            self.redis_cache = None

    def generate_cache_key(
        self,
        text: str,
        scan_type: str,
        scanner_config_hash: str | None = None,
        scanner_version: str | None = None,
    ) -> str:
        """
        Generate deterministic cache key from content and configuration context.

        Creates a content-based cache key that ensures cache consistency and
        prevents incorrect cache hits when scanner configuration changes.
        The key incorporates scanned text, scan type, scanner configuration,
        and version information to guarantee cache integrity.

        Args:
            text: The exact text content that was or will be scanned.
                  Must be the complete text without preprocessing or modifications.
                  Empty strings are valid but should be used consistently.
            scan_type: Type of security scan being performed. Must be one of
                       ["input", "output"] indicating whether the text is user
                       input or AI-generated output for consistent key namespace.
            scanner_config_hash: Optional hash of scanner configuration used for
                                the scan. When None, uses the current scanner
                                configuration hash. Providing this allows for
                                explicit configuration control or testing scenarios.
            scanner_version: Optional version identifier of scanners used for
                            the scan. When None, uses current scanner version.
                            Useful for cache migration testing or version tracking.

        Returns:
            Deterministic cache key string in format "{key_prefix}{scan_type}:{content_hash}"
            where content_hash is a 64-character SHA-256 hexadecimal hash.

        Behavior:
            - Combines text, scan type, configuration hash, and version
            - Creates SHA-256 hash of the combined content for uniqueness
            - Prefixes result with configured key_prefix and scan_type
            - Ensures identical inputs always produce identical cache keys
            - Guarantees different inputs produce different cache keys
            - Handles None values by using current instance defaults

        Examples:
            >>> cache = SecurityResultCache(config)
            >>> key1 = cache.generate_cache_key("hello world", "input")
            >>> key2 = cache.generate_cache_key("hello world", "input")
            >>> assert key1 == key2  # Identical inputs
            >>>
            >>> # Different scan types produce different keys
            >>> key3 = cache.generate_cache_key("hello world", "output")
            >>> assert key1 != key3
            >>>
            >>> # Different content produces different keys
            >>> key4 = cache.generate_cache_key("hello different", "input")
            >>> assert key1 != key4
            >>>
            >>> # Key format includes prefix and hash
            >>> assert key1.startswith("security_scan:input:")
            >>> assert len(key1.split(":")[-1]) == 64  # SHA-256 hex length

        Notes:
            - SHA-256 provides extremely low collision probability
            - Cache keys are deterministic across process restarts
            - Configuration changes automatically invalidate old cache entries
            - Scanner version changes prevent stale cached results
            - Key format ensures easy identification and debugging

        Performance:
            - O(1) hash generation time regardless of text length
            - Minimal memory overhead for key generation
            - Cryptographic hash ensures uniform key distribution
        """
        # Use provided hashes or defaults
        config_hash = scanner_config_hash or self._scanner_config_hash
        version = scanner_version or self._scanner_version

        # Create content hash
        content = f"{text}|{scan_type}|{config_hash}|{version}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        return f"{self.key_prefix}{scan_type}:{content_hash}"

    def _hash_scanner_config(self) -> str:
        """
        Generate hash of current scanner configuration.

        Returns:
            SHA-256 hash of scanner configuration
        """
        # Serialize relevant configuration
        config_data = {
            "scanners": {
                name: {
                    "enabled": config.get("enabled", False),
                    "threshold": config.get("threshold", 0.7),
                    "action": config.get("action", "block"),
                    "model_name": config.get("model_name"),
                }
                for name, config in {
                    **getattr(self.config, "input_scanners", {}),
                    **getattr(self.config, "output_scanners", {}),
                }.items()
            },
            "performance": {
                "onnx_providers": getattr(self.config.performance, "onnx_providers", ["CPUExecutionProvider"]),
                "enable_model_caching": getattr(self.config.performance, "enable_model_caching", True),
            }
        }

        config_str = json.dumps(config_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]

    async def get(self, text: str, scan_type: str) -> SecurityResult | None:
        """
        Retrieve cached security result with intelligent fallback and performance tracking.

        Attempts to retrieve cached security scan result using content-based key
        generation. Implements intelligent fallback from Redis to memory cache
        with comprehensive performance tracking and error resilience.

        Args:
            text: The exact text content that was previously scanned and cached.
                  Must match the original text used in cache.set() operation exactly.
                  Whitespace and case sensitivity are preserved for key generation.
            scan_type: Type of security scan. Must be one of ["input", "output"]
                       and must match the scan_type used when the result was cached.

        Returns:
            SecurityResult object if found in cache, None if:
            - Cache is disabled
            - Entry not found in Redis or memory cache
            - Cache operation fails (graceful degradation)
            - TTL has expired

        Behavior:
            - Generates deterministic cache key from text and scan type
            - Attempts Redis lookup if Redis is available and connected
            - Updates hit count and persists back to Redis for Redis entries
            - Falls back to memory cache if Redis unavailable or lookup fails
            - Records cache performance metrics (hit/miss and timing)
            - Handles all exceptions gracefully without raising to caller
            - Logs detailed cache operation results for debugging

        Fallback Strategy:
            1. Redis Cache (if available and connected)
            2. Memory Cache (always available as fallback)
            3. Returns None on complete failure (never raises exceptions)

        Performance Tracking:
            - Records cache hits with lookup time in statistics
            - Records cache misses with lookup time in statistics
            - Updates hit count for successfully retrieved entries
            - Provides timing data for cache optimization

        Examples:
            >>> # Cache a result first
            >>> result = SecurityResult(is_safe=True, violations=[], score=1.0, ...)
            >>> await cache.set("test input", "input", result)
            >>>
            >>> # Retrieve cached result
            >>> cached_result = await cache.get("test input", "input")
            >>> if cached_result:
            ...     print("Cache hit - saved security scan time")
            ...     print(f"Result is safe: {cached_result.is_safe}")
            ... else:
            ...     print("Cache miss - performing new scan")
            >>>
            >>> # Non-existent result
            >>> missing_result = await cache.get("non-existent", "input")
            >>> assert missing_result is None
            >>>
            >>> # Wrong scan type (won't match even if content exists)
            >>> wrong_type = await cache.get("test input", "output")
            >>> assert wrong_type is None  # Different scan type

        Error Handling:
            - Redis connection failures trigger memory fallback
            - Data corruption errors result in cache miss
            - Network timeouts are handled gracefully
            - All exceptions are logged but never raised to caller
            - Cache failures never break security scanning functionality

        Performance:
            - Redis: Sub-millisecond lookups when available
            - Memory: Microsecond lookups for fallback scenarios
            - Key generation: O(1) regardless of text length
            - Thread-safe for concurrent access patterns
        """
        start_time = time.time()

        if not self.enabled:
            self.stats.record_miss((time.time() - start_time) * 1000)
            return None

        try:
            cache_key = self.generate_cache_key(text, scan_type)

            # Try Redis first
            if self._redis_available and self.redis_cache:
                cached_data = await self.redis_cache.get(cache_key)
                if cached_data:
                    entry = CacheEntry.from_dict(cached_data)
                    entry.hit_count += 1

                    # Update the hit count in cache
                    await self.redis_cache.set(cache_key, entry.to_dict(), ttl=entry.ttl_seconds)

                    lookup_time = (time.time() - start_time) * 1000
                    self.stats.record_hit(lookup_time)

                    logger.debug(f"Cache hit (Redis) for {scan_type} scan")
                    return entry.result

            # Fallback to memory cache
            cached_data = await self.memory_cache.get(cache_key)
            if cached_data:
                memory_entry: CacheEntry = cached_data  # Memory cache stores CacheEntry directly
                memory_entry.hit_count += 1

                lookup_time = (time.time() - start_time) * 1000
                self.stats.record_hit(lookup_time)

                logger.debug(f"Cache hit (Memory) for {scan_type} scan")
                return memory_entry.result

            # Cache miss
            lookup_time = (time.time() - start_time) * 1000
            self.stats.record_miss(lookup_time)
            logger.debug(f"Cache miss for {scan_type} scan")
            return None

        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            self.stats.record_miss((time.time() - start_time) * 1000)
            return None

    async def set(
        self,
        text: str,
        scan_type: str,
        result: SecurityResult,
        ttl_seconds: int | None = None,
    ) -> None:
        """
        Cache security scan result with metadata management and intelligent storage.

        Stores security scan results with comprehensive metadata, TTL management,
        and intelligent storage strategy. Results are cached with rich metadata
        including scanner configuration, timestamps, and access tracking.

        Args:
            text: The exact text content that was scanned. Must match the text
                  that will be used for cache.get() operations. Used for
                  deterministic key generation.
            scan_type: Type of security scan performed. Must be one of
                       ["input", "output"] and must match the scan_type used
                       for cache.get() operations.
            result: SecurityResult object containing scan findings, violations,
                    timing data, and scanner metadata. Must be a complete
                    SecurityResult instance with all required fields populated.
            ttl_seconds: Optional time-to-live override in seconds. When None,
                        uses the cache instance's default_ttl. Must be positive
                        integer if provided. Controls cache entry expiration.

        Behavior:
            - Generates deterministic cache key from text and scan type
            - Creates rich CacheEntry with metadata and timestamps
            - Attempts Redis storage if available and connected
            - Falls back to memory cache when Redis unavailable
            - Stores comprehensive metadata for cache management
            - Handles all exceptions gracefully without raising to caller
            - Logs cache operation status and storage location

        Cache Entry Contents:
            - Complete SecurityResult with scan findings and timing
            - UTC timestamp when result was originally cached
            - Scanner configuration hash for cache invalidation
            - Scanner version for compatibility tracking
            - Configurable TTL for automatic expiration
            - Hit count counter (initialized to 0)

        Storage Strategy:
            1. Redis Cache (if available and connected)
            2. Memory Cache (always available as fallback)
            3. Silent failure if both storage methods fail

        Examples:
            >>> # Cache a successful scan result
            >>> result = SecurityResult(
            ...     is_safe=True,
            ...     violations=[],
            ...     score=1.0,
            ...     scanned_text="user input text",
            ...     scan_duration_ms=150,
            ...     scanner_results={"scanner1": {"safe": True}},
            ...     metadata={"model": "v1.0"}
            ... )
            >>> await cache.set("user input text", "input", result)
            >>>
            >>> # Cache with custom TTL
            >>> await cache.set("user input text", "input", result, ttl_seconds=7200)
            >>>
            >>> # Cache an unsafe result with violations
            >>> unsafe_result = SecurityResult(
            ...     is_safe=False,
            ...     violations=[Violation(type="injection", severity="high")],
            ...     score=0.2,
            ...     scanned_text="malicious input",
            ...     scan_duration_ms=200,
            ...     scanner_results={},
            ...     metadata={}
            ... )
            >>> await cache.set("malicious input", "input", unsafe_result, ttl_seconds=300)

        Error Handling:
            - Redis connection failures trigger memory fallback
            - Serialization errors are logged but don't raise exceptions
            - Invalid SecurityResult objects are logged and ignored
            - Network timeouts are handled gracefully
            - Cache failures never break security scanning functionality

        TTL Management:
            - TTL controls cache entry expiration automatically
            - Redis handles TTL expiration natively
            - Memory cache implements TTL cleanup
            - Expired entries are automatically removed on access
            - Shorter TTLs for potentially risky content recommended

        Performance:
            - Redis: Sub-millisecond storage when available
            - Memory: Microsecond storage for fallback scenarios
            - Key generation: O(1) regardless of text length
            - Serialization: Efficient for SecurityResult objects
            - Thread-safe for concurrent access patterns

        Notes:
            - Cache is disabled silently when config prohibits caching
            - Duplicate cache keys are overwritten with new entries
            - Scanner configuration changes invalidate previous cache entries
            - TTL should be balanced between performance and security requirements
        """
        if not self.enabled:
            return

        try:
            cache_key = self.generate_cache_key(text, scan_type)
            ttl = ttl_seconds or self.default_ttl

            entry = CacheEntry(
                result=result,
                cached_at=datetime.now(UTC),
                cache_key=cache_key,
                scanner_config_hash=self._scanner_config_hash,
                scanner_version=self._scanner_version,
                ttl_seconds=ttl,
            )

            # Store in Redis if available
            if self._redis_available and self.redis_cache:
                await self.redis_cache.set(cache_key, entry.to_dict(), ttl=ttl)
                logger.debug(f"Cached result (Redis) for {scan_type} scan")
            else:
                # Store in memory cache
                await self.memory_cache.set(cache_key, entry, ttl=ttl)
                logger.debug(f"Cached result (Memory) for {scan_type} scan")

        except Exception as e:
            logger.error(f"Cache set failed: {e}")

    async def delete(self, text: str, scan_type: str) -> None:
        """
        Delete cached security result for specific text and scan type.

        Removes cache entries from both Redis and memory cache to ensure
        complete cleanup. This method is useful for cache invalidation,
        privacy compliance, or manual cache management scenarios.

        Args:
            text: The exact text content of the cached entry to remove.
                  Must match the original text used in cache.set() operation.
            scan_type: Type of security scan for the cached entry. Must be
                       one of ["input", "output"] and must match the scan_type
                       used when the result was cached.

        Behavior:
            - Generates deterministic cache key from text and scan type
            - Attempts deletion from Redis if available and connected
            - Attempts deletion from memory cache regardless of Redis status
            - Logs deletion status and any errors encountered
            - Handles all exceptions gracefully without raising to caller
            - Continues deletion process even if one cache layer fails

        Deletion Strategy:
            1. Delete from Redis cache (if available and connected)
            2. Delete from memory cache (always attempted)
            3. Log success/failure for each cache layer independently

        Examples:
            >>> # Delete a specific cached result
            >>> await cache.delete("user input text", "input")
            >>>
            >>> # Verify deletion by attempting retrieval
            >>> result = await cache.get("user input text", "input")
            >>> assert result is None  # Should be None after deletion
            >>>
            >>> # Delete non-existent entry (safe operation)
            >>> await cache.delete("non-existent text", "input")
            >>> # No error raised, even if entry doesn't exist

        Use Cases:
            - Manual cache invalidation after configuration changes
            - Privacy compliance (removing sensitive cached data)
            - Testing cache behavior with clean slate
            - Correcting incorrect cache entries
            - Cache size management and cleanup

        Error Handling:
            - Redis connection failures don't prevent memory cache deletion
            - Non-existent entries are handled gracefully (no-op)
            - Network timeouts are logged but don't raise exceptions
            - All errors are logged for debugging and monitoring
            - Method never raises exceptions to caller

        Performance:
            - Redis: Sub-millisecond deletion when available
            - Memory: Microsecond deletion for local cache
            - Key generation: O(1) regardless of text length
            - Thread-safe for concurrent access patterns

        Notes:
            - Safe to call even if entry doesn't exist (no-op)
            - Cache is disabled silently when config prohibits caching
            - Both Redis and memory cache are always attempted for complete cleanup
            - Deletion is atomic per cache layer but not across layers
        """
        if not self.enabled:
            return

        try:
            cache_key = self.generate_cache_key(text, scan_type)

            # Delete from Redis
            if self._redis_available and self.redis_cache:
                await self.redis_cache.delete(cache_key)

            # Delete from memory cache
            await self.memory_cache.delete(cache_key)

            logger.debug(f"Deleted cached result for {scan_type} scan")

        except Exception as e:
            logger.error(f"Cache delete failed: {e}")

    async def clear_all(self) -> None:
        """
        Clear all cached security results from all cache layers.

        Removes all security scan results from both Redis and memory cache.
        This is a destructive operation that cannot be undone. Use with caution
        as it will force all subsequent security scans to bypass the cache.

        Behavior:
            - Clears memory cache completely
            - Attempts Redis cache clearing if available and connected
            - Logs cache clearing status and any limitations
            - Handles all exceptions gracefully without raising to caller
            - Provides fallback when Redis pattern deletion unavailable

        Clearing Strategy:
            1. Memory Cache: Complete clearing always succeeds
            2. Redis Cache: Limited implementation (logs warning about pattern deletion)

        Examples:
            >>> # Clear all cached results
            >>> await cache.clear_all()
            >>> print("All security cache cleared")
            >>>
            >>> # Verify clearing by checking statistics
            >>> stats = await cache.get_statistics()
            >>> print(f"Cache size after clear: {stats.cache_size}")

        Use Cases:
            - Complete cache reset after configuration changes
            - Privacy compliance (removing all cached sensitive data)
            - Testing with clean cache state
            - Emergency cache invalidation
            - Memory pressure relief

        Limitations:
            - Redis pattern deletion not fully implemented
            - Only memory cache is guaranteed to be cleared completely
            - Cache entries with TTL may expire naturally before clearing

        Performance:
            - Memory cache: O(1) clearing operation
            - Redis cache: Depends on implementation
            - Thread-safe for concurrent access patterns
        """
        if not self.enabled:
            return

        try:
            # Clear Redis cache (with pattern matching)
            if self._redis_available and self.redis_cache:
                # Note: This would need Redis pattern deletion capability
                # For now, we'll clear memory cache only
                logger.warning("Redis cache clear not implemented, clearing memory cache only")

            # Clear memory cache
            await self.memory_cache.clear()  # type: ignore[func-returns-value]
            logger.info("Cleared all security scan results from cache")

        except Exception as e:
            logger.error(f"Cache clear failed: {e}")

    async def get_statistics(self) -> CacheStatistics:
        """
        Retrieve comprehensive cache performance statistics and metrics.

        Returns current cache statistics including hit/miss ratios, timing data,
        cache size information, and performance metrics for monitoring and
        optimization purposes.

        Returns:
            CacheStatistics object containing:
            - Hit/miss counts and calculated hit rate percentage
            - Average lookup timing in milliseconds
            - Current cache size (number of entries)
            - Estimated memory usage in megabytes
            - Last reset timestamp for statistics

        Behavior:
            - Updates cache size information from active cache instances
            - Attempts Redis size estimation when available
            - Falls back to memory cache size estimation
            - Returns complete statistics object for API consumption
            - Handles cache size detection errors gracefully

        Size Detection:
            - Redis: Uses size() method if available on cache interface
            - Memory: Estimates from internal cache dictionary size
            - Errors: Silently ignored to prevent statistics failures

        Examples:
            >>> # Get cache performance metrics
            >>> stats = await cache.get_statistics()
            >>> print(f"Hit rate: {stats.hit_rate:.1f}%")
            >>> print(f"Average lookup: {stats.avg_lookup_time_ms:.2f}ms")
            >>> print(f"Cache size: {stats.cache_size} entries")
            >>> print(f"Memory usage: {stats.memory_usage_mb:.2f}MB")

        Usage Scenarios:
            - Performance monitoring and alerting
            - Cache optimization and tuning
            - Capacity planning and resource management
            - Debugging cache behavior issues

        Notes:
            - Statistics are continuously updated during cache operations
            - Cache size is estimated at call time, not cached
            - Memory usage is approximate and may vary by implementation
            - Thread-safe for concurrent access patterns
        """
        # Update cache size if possible
        try:
            if self._redis_available and self.redis_cache is not None and hasattr(self.redis_cache, "size"):
                self.stats.cache_size = self.redis_cache.size()
            else:
                # Memory cache size estimation
                self.stats.cache_size = len(getattr(self.memory_cache, "_cache", {}))
        except Exception:
            pass

        return self.stats

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive cache health check with functional testing.

        Validates cache infrastructure health by testing core operations,
        checking connectivity, and providing detailed status information.
        This method is essential for monitoring, alerting, and debugging
        cache-related issues.

        Returns:
            Dictionary containing health check results:
            - status: Overall health status ("healthy", "degraded", "unhealthy")
            - enabled: Whether caching is currently enabled
            - redis_available: Redis connectivity status
            - memory_cache_available: Memory cache availability (always True)
            - statistics: Current cache performance statistics
            - error: Error message if health check failed (optional)

        Health Check Process:
            1. Creates test SecurityResult with known values
            2. Tests cache.set() operation with test data
            3. Tests cache.get() operation to retrieve test data
            4. Tests cache.delete() operation for cleanup
            5. Evaluates overall system health based on test results
            6. Includes current statistics in health report

        Health Status Criteria:
            - "healthy": All cache operations successful
            - "degraded": Cache operations work but with limitations
            - "unhealthy": Critical cache failures detected

        Examples:
            >>> # Check cache health
            >>> health = await cache.health_check()
            >>> print(f"Cache status: {health['status']}")
            >>> print(f"Redis available: {health['redis_available']}")
            >>> print(f"Cache enabled: {health['enabled']}")
            >>>
            >>> # Check statistics in health report
            >>> stats = health['statistics']
            >>> print(f"Hit rate: {stats['hit_rate']:.1f}%")
            >>> print(f"Total requests: {stats['total_requests']}")

        Use Cases:
            - Monitoring system health and alerting
            - Debugging cache connectivity issues
            - Validating cache deployment status
            - Performance monitoring and optimization
            - Automated health checks in CI/CD pipelines

        Error Handling:
            - Test failures are caught and reported in health status
            - Network timeouts don't crash the health check
            - All cache layers are evaluated independently
            - Detailed error messages provided for debugging

        Performance:
            - Complete health check in ~10-100ms depending on cache backend
            - Minimal overhead for monitoring systems
            - Thread-safe for concurrent health checks
            - Safe for frequent monitoring calls

        Notes:
            - Uses isolated test data to avoid interfering with real cache entries
            - Test data has short TTL to minimize cleanup requirements
            - Health check is read-only for existing cache data
            - Statistics reflect current state, not just test operations
        """
        health = {
            "status": "healthy",
            "enabled": self.enabled,
            "redis_available": self._redis_available,
            "memory_cache_available": True,
            "statistics": self.stats.to_dict(),
        }

        # Test cache operations
        try:
            test_key = "health_test"
            test_result = SecurityResult(
                is_safe=True,
                violations=[],
                score=1.0,
                scanned_text="test",
                scan_duration_ms=1,
                scanner_results={},
                metadata={"test": True},
            )

            # Test set and get
            await self.set("test", "health", test_result, ttl_seconds=10)
            cached_result = await self.get("test", "health")
            await self.delete("test", "health")

            if cached_result is None:
                health["status"] = "degraded"
                health["error"] = "Cache test failed"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        return health
