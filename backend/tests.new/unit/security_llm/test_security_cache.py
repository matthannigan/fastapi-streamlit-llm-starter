"""
Comprehensive Security Cache Test Suite

This module provides comprehensive tests for the security result cache,
including cache operations, invalidation strategies, fallback behavior,
and performance characteristics.

## Test Coverage

- **Cache Operations**: get, set, delete, clear operations
- **Cache Keys**: Consistent key generation and collision prevention
- **Cache Values**: SecurityResult serialization and deserialization
- **Invalidation**: TTL expiration, configuration changes, version upgrades
- **Fallback**: Redis unavailable scenarios, memory cache fallback
- **Performance**: Lookup latency, hit rates, memory usage
- **Integration**: Cache integration with security scanner
"""

import asyncio
import time
from datetime import datetime, UTC
from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest

from app.infrastructure.security.llm.cache import (
    CacheEntry,
    CacheStatistics,
    SecurityResultCache,
)
from app.infrastructure.security.llm.config import SecurityConfig, PerformanceConfig
from app.infrastructure.security.llm.protocol import (
    SecurityResult,
    Violation,
    ViolationType,
    SeverityLevel,
)


class TestCacheEntry:
    """Test CacheEntry serialization and deserialization."""

    def test_cache_entry_creation(self) -> None:
        """Test creating a cache entry with valid data."""
        # Create a security result
        result = SecurityResult(
            is_safe=False,
            violations=[
                Violation(
                    type=ViolationType.PROMPT_INJECTION,
                    severity=SeverityLevel.HIGH,
                    description="Test violation",
                    confidence=0.9,
                    scanner_name="TestScanner",
                )
            ],
            score=0.5,
            scanned_text="test text",
            scan_duration_ms=100,
            scanner_results={},
            metadata={"test": True},
        )

        # Create cache entry
        entry = CacheEntry(
            result=result,
            cached_at=datetime.now(UTC),
            cache_key="test_key",
            scanner_config_hash="abc123",
            scanner_version="1.0.0",
            ttl_seconds=3600,
        )

        assert entry.result == result
        assert entry.cache_key == "test_key"
        assert entry.scanner_config_hash == "abc123"
        assert entry.scanner_version == "1.0.0"
        assert entry.ttl_seconds == 3600
        assert entry.hit_count == 0

    def test_cache_entry_serialization(self) -> None:
        """Test cache entry serialization to dictionary."""
        result = SecurityResult(
            is_safe=True,
            violations=[],
            score=1.0,
            scanned_text="test",
            scan_duration_ms=50,
            scanner_results={},
            metadata={},
        )

        entry = CacheEntry(
            result=result,
            cached_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
            cache_key="test_key",
            scanner_config_hash="hash123",
            scanner_version="1.0.0",
            ttl_seconds=1800,
        )

        # Convert to dict
        entry_dict = entry.to_dict()

        # Verify structure
        assert "result" in entry_dict
        assert "cached_at" in entry_dict
        assert "cache_key" in entry_dict
        assert "scanner_config_hash" in entry_dict
        assert "scanner_version" in entry_dict
        assert "ttl_seconds" in entry_dict
        assert "hit_count" in entry_dict

        # Verify values
        assert entry_dict["cache_key"] == "test_key"
        assert entry_dict["scanner_config_hash"] == "hash123"
        assert entry_dict["scanner_version"] == "1.0.0"
        assert entry_dict["ttl_seconds"] == 1800
        assert entry_dict["hit_count"] == 0

    def test_cache_entry_deserialization(self) -> None:
        """Test cache entry deserialization from dictionary."""
        entry_dict = {
            "result": {
                "is_safe": False,
                "violations": [
                    {
                        "type": "prompt_injection",
                        "severity": "high",
                        "description": "Test violation",
                        "confidence": 0.8,
                        "scanner_name": "TestScanner",
                        "text_snippet": None,
                        "start_index": None,
                        "end_index": None,
                        "metadata": None,
                    }
                ],
                "score": 0.6,
                "scanned_text": "test text",
                "scan_duration_ms": 75,
                "scanner_results": {},
                "metadata": {"test": True},
            },
            "cached_at": "2023-01-01T12:00:00+00:00",
            "cache_key": "test_key",
            "scanner_config_hash": "hash123",
            "scanner_version": "1.0.0",
            "ttl_seconds": 1800,
            "hit_count": 5,
        }

        # Deserialize
        entry = CacheEntry.from_dict(entry_dict)

        # Verify result
        assert entry.cache_key == "test_key"
        assert entry.scanner_config_hash == "hash123"
        assert entry.scanner_version == "1.0.0"
        assert entry.ttl_seconds == 1800
        assert entry.hit_count == 5
        assert not entry.result.is_safe
        assert len(entry.result.violations) == 1
        assert entry.result.violations[0].type == ViolationType.PROMPT_INJECTION
        assert entry.result.violations[0].severity == SeverityLevel.HIGH


class TestCacheStatistics:
    """Test cache statistics tracking."""

    def test_statistics_initialization(self) -> None:
        """Test statistics initialization with default values."""
        stats = CacheStatistics()

        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.total_requests == 0
        assert stats.hit_rate == 0.0
        assert stats.avg_lookup_time_ms == 0.0
        assert stats.cache_size == 0
        assert stats.memory_usage_mb == 0.0
        assert stats.last_reset is not None

    def test_record_hit(self) -> None:
        """Test recording cache hits."""
        stats = CacheStatistics()

        # Record first hit
        stats.record_hit(5.0)
        assert stats.hits == 1
        assert stats.total_requests == 1
        assert stats.hit_rate == 100.0
        assert stats.avg_lookup_time_ms == 5.0

        # Record second hit
        stats.record_hit(3.0)
        assert stats.hits == 2
        assert stats.total_requests == 2
        assert stats.hit_rate == 100.0
        assert stats.avg_lookup_time_ms == 4.0  # (5.0 + 3.0) / 2

    def test_record_miss(self) -> None:
        """Test recording cache misses."""
        stats = CacheStatistics()

        # Record miss
        stats.record_miss(10.0)
        assert stats.misses == 1
        assert stats.total_requests == 1
        assert stats.hit_rate == 0.0
        assert stats.avg_lookup_time_ms == 10.0

    def test_mixed_hits_and_misses(self) -> None:
        """Test recording both hits and misses."""
        stats = CacheStatistics()

        # Record mixed operations
        stats.record_hit(2.0)
        stats.record_miss(8.0)
        stats.record_hit(3.0)
        stats.record_miss(12.0)

        assert stats.hits == 2
        assert stats.misses == 2
        assert stats.total_requests == 4
        assert stats.hit_rate == 50.0
        assert stats.avg_lookup_time_ms == 6.25  # (2.0 + 8.0 + 3.0 + 12.0) / 4

    def test_statistics_reset(self) -> None:
        """Test resetting statistics."""
        stats = CacheStatistics()

        # Record some operations
        stats.record_hit(5.0)
        stats.record_miss(10.0)
        stats.cache_size = 100
        stats.memory_usage_mb = 50.0

        # Reset
        original_reset_time = stats.last_reset
        stats.reset()

        # Verify reset
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.total_requests == 0
        assert stats.hit_rate == 0.0
        assert stats.avg_lookup_time_ms == 0.0
        assert stats.last_reset is not None
        if original_reset_time is not None:
            assert stats.last_reset > original_reset_time
        # Cache size and memory usage are not reset by reset() method

    def test_statistics_to_dict(self) -> None:
        """Test statistics serialization to dictionary."""
        stats = CacheStatistics()
        stats.record_hit(5.0)
        stats.record_miss(10.0)
        stats.cache_size = 50
        stats.memory_usage_mb = 25.5

        stats_dict = stats.to_dict()

        assert "hits" in stats_dict
        assert "misses" in stats_dict
        assert "total_requests" in stats_dict
        assert "hit_rate" in stats_dict
        assert "avg_lookup_time_ms" in stats_dict
        assert "cache_size" in stats_dict
        assert "memory_usage_mb" in stats_dict
        assert "last_reset" in stats_dict

        assert stats_dict["hits"] == 1
        assert stats_dict["misses"] == 1
        assert stats_dict["total_requests"] == 2
        assert stats_dict["hit_rate"] == 50.0
        assert stats_dict["avg_lookup_time_ms"] == 7.5
        assert stats_dict["cache_size"] == 50
        assert stats_dict["memory_usage_mb"] == 25.5


class TestSecurityResultCache:
    """Test SecurityResultCache functionality."""

    @pytest.fixture
    def security_config(self) -> SecurityConfig:
        """Create a test security configuration."""
        return SecurityConfig(
            performance=PerformanceConfig(
                enable_result_caching=True,
                cache_ttl_seconds=3600,
                cache_redis_url=None,  # Use memory cache for testing
            )
        )

    @pytest.fixture
    def cache(self, security_config: SecurityConfig) -> SecurityResultCache:
        """Create a test cache instance."""
        return SecurityResultCache(
            config=security_config,
            redis_url=None,  # Force memory cache
            enabled=True,
            default_ttl=1800,
        )

    @pytest.mark.asyncio
    async def test_cache_initialization(self, cache: SecurityResultCache) -> None:
        """Test cache initialization."""
        await cache.initialize()

        assert cache.enabled is True
        assert cache.default_ttl == 1800
        assert cache._redis_available is False  # Memory cache only
        assert cache.memory_cache is not None

    @pytest.mark.asyncio
    async def test_cache_disabled(self, security_config: SecurityConfig) -> None:
        """Test cache when disabled."""
        # Create disabled cache
        security_config.performance.enable_result_caching = False
        cache = SecurityResultCache(config=security_config, enabled=False)

        await cache.initialize()

        assert cache.enabled is False

    @pytest.mark.asyncio
    async def test_generate_cache_key(self, cache: SecurityResultCache) -> None:
        """Test cache key generation."""
        # Test basic key generation
        key1 = cache.generate_cache_key("test text", "input")
        key2 = cache.generate_cache_key("test text", "input")
        key3 = cache.generate_cache_key("test text", "output")
        key4 = cache.generate_cache_key("different text", "input")

        # Same content and type should generate same key
        assert key1 == key2

        # Different scan type should generate different key
        assert key1 != key3

        # Different content should generate different key
        assert key1 != key4

        # Keys should have proper prefix
        assert key1.startswith("security_scan:input:")
        assert key3.startswith("security_scan:output:")

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache: SecurityResultCache) -> None:
        """Test basic cache set and get operations."""
        await cache.initialize()

        # Create test result
        result = SecurityResult(
            is_safe=True,
            violations=[],
            score=1.0,
            scanned_text="test content",
            scan_duration_ms=100,
            scanner_results={},
            metadata={},
        )

        # Set in cache
        await cache.set("test content", "input", result, ttl_seconds=300)

        # Get from cache
        cached_result = await cache.get("test content", "input")

        assert cached_result is not None
        assert cached_result.is_safe == result.is_safe
        assert cached_result.score == result.score
        assert cached_result.scanned_text == result.scanned_text
        assert cached_result.scan_duration_ms == result.scan_duration_ms

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache: SecurityResultCache) -> None:
        """Test cache miss scenario."""
        await cache.initialize()

        # Try to get non-existent entry
        result = await cache.get("nonexistent content", "input")

        assert result is None

        # Verify statistics
        stats = await cache.get_statistics()
        assert stats.misses == 1
        assert stats.hits == 0
        assert stats.total_requests == 1

    @pytest.mark.asyncio
    async def test_cache_hit(self, cache: SecurityResultCache) -> None:
        """Test cache hit scenario."""
        await cache.initialize()

        # Create and cache result
        result = SecurityResult(
            is_safe=False,
            violations=[
                Violation(
                    type=ViolationType.TOXIC_INPUT,
                    severity=SeverityLevel.MEDIUM,
                    description="Toxic content",
                    confidence=0.8,
                    scanner_name="ToxicityScanner",
                )
            ],
            score=0.6,
            scanned_text="toxic content",
            scan_duration_ms=150,
            scanner_results={},
            metadata={},
        )

        await cache.set("toxic content", "input", result)

        # Get from cache (hit)
        cached_result = await cache.get("toxic content", "input")

        assert cached_result is not None
        assert cached_result.is_safe == result.is_safe
        assert len(cached_result.violations) == len(result.violations)
        assert cached_result.violations[0].type == result.violations[0].type

        # Verify statistics
        stats = await cache.get_statistics()
        assert stats.hits == 1
        assert stats.misses == 0
        assert stats.total_requests == 1

    @pytest.mark.asyncio
    async def test_cache_delete(self, cache: SecurityResultCache) -> None:
        """Test cache delete operation."""
        await cache.initialize()

        # Create and cache result
        result = SecurityResult(
            is_safe=True,
            violations=[],
            score=1.0,
            scanned_text="test content",
            scan_duration_ms=100,
            scanner_results={},
            metadata={},
        )

        await cache.set("test content", "input", result)

        # Verify it's cached
        cached_result = await cache.get("test content", "input")
        assert cached_result is not None

        # Delete from cache
        await cache.delete("test content", "input")

        # Verify it's gone
        cached_result = await cache.get("test content", "input")
        assert cached_result is None

    @pytest.mark.asyncio
    async def test_cache_clear_all(self, cache: SecurityResultCache) -> None:
        """Test clearing all cache entries."""
        await cache.initialize()

        # Create and cache multiple results
        result1 = SecurityResult(
            is_safe=True, violations=[], score=1.0, scanned_text="text1",
            scan_duration_ms=100, scanner_results={}, metadata={}
        )
        result2 = SecurityResult(
            is_safe=False, violations=[], score=0.5, scanned_text="text2",
            scan_duration_ms=150, scanner_results={}, metadata={}
        )

        await cache.set("text1", "input", result1)
        await cache.set("text2", "output", result2)

        # Verify they're cached
        assert await cache.get("text1", "input") is not None
        assert await cache.get("text2", "output") is not None

        # Clear all
        await cache.clear_all()

        # Verify they're gone
        assert await cache.get("text1", "input") is None
        assert await cache.get("text2", "output") is None

    @pytest.mark.asyncio
    async def test_cache_statistics_tracking(self, cache: SecurityResultCache) -> None:
        """Test cache statistics tracking."""
        await cache.initialize()

        # Perform various cache operations
        result = SecurityResult(
            is_safe=True, violations=[], score=1.0, scanned_text="test",
            scan_duration_ms=100, scanner_results={}, metadata={}
        )

        # Miss
        await cache.get("nonexistent", "input")

        # Set and hit
        await cache.set("test", "input", result)
        await cache.get("test", "input")

        # Another miss
        await cache.get("nonexistent2", "input")

        # Check statistics
        stats = await cache.get_statistics()

        assert stats.hits == 1
        assert stats.misses == 2
        assert stats.total_requests == 3
        assert stats.hit_rate == 33.33  # 1/3 * 100

    @pytest.mark.asyncio
    async def test_cache_health_check(self, cache: SecurityResultCache) -> None:
        """Test cache health check."""
        await cache.initialize()

        # Perform health check
        health = await cache.health_check()

        assert "status" in health
        assert "enabled" in health
        assert "redis_available" in health
        assert "memory_cache_available" in health
        assert "statistics" in health

        assert health["enabled"] is True
        assert health["redis_available"] is False  # Memory cache only
        assert health["memory_cache_available"] is True
        assert health["status"] in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_cache_error_handling(self, cache: SecurityResultCache) -> None:
        """Test cache error handling."""
        await cache.initialize()

        # Test with invalid data that might cause serialization errors
        # This should not raise exceptions
        try:
            # Create result with potentially problematic data
            result = SecurityResult(
                is_safe=True,
                violations=[],
                score=1.0,
                scanned_text="test content",
                scan_duration_ms=100,
                scanner_results={},
                metadata={"complex_data": {"nested": "value"}},
            )

            await cache.set("test", "input", result)
            cached_result = await cache.get("test", "input")

            # Should work fine
            assert cached_result is not None

        except Exception as e:
            pytest.fail(f"Cache operation should not raise exceptions: {e}")

    @pytest.mark.asyncio
    async def test_scanner_config_hashing(self, cache: SecurityResultCache) -> None:
        """Test scanner configuration hashing."""
        await cache.initialize()

        # Generate keys with same content but different config hash
        key1 = cache.generate_cache_key("test", "input")
        key2 = cache.generate_cache_key("test", "input", scanner_config_hash="different")

        assert key1 != key2
        assert cache._scanner_config_hash in key1
        assert "different" in key2

    @pytest.mark.asyncio
    async def test_different_ttl_values(self, cache: SecurityResultCache) -> None:
        """Test cache operations with different TTL values."""
        await cache.initialize()

        result = SecurityResult(
            is_safe=True, violations=[], score=1.0, scanned_text="test",
            scan_duration_ms=100, scanner_results={}, metadata={}
        )

        # Set with custom TTL
        await cache.set("test", "input", result, ttl_seconds=600)

        # Should still be retrievable
        cached_result = await cache.get("test", "input")
        assert cached_result is not None

        # Check that TTL was stored correctly
        # Note: We can't easily test TTL expiration without time manipulation
        # but we can verify the cache entry structure
        stats = await cache.get_statistics()
        assert stats.total_requests == 1


class TestSecurityResultCacheWithRedis:
    """Test SecurityResultCache with Redis backend."""

    @pytest.fixture
    def security_config(self) -> SecurityConfig:
        """Create a test security configuration with Redis."""
        return SecurityConfig(
            performance=PerformanceConfig(
                enable_result_caching=True,
                cache_ttl_seconds=3600,
                cache_redis_url="redis://localhost:6379",
            )
        )

    @pytest.mark.asyncio
    async def test_redis_initialization_success(self, security_config: SecurityConfig) -> None:
        """Test successful Redis initialization."""
        # Mock Redis cache
        with patch("app.infrastructure.security.llm.cache.CacheFactory") as mock_factory:
            mock_cache = AsyncMock()
            mock_cache.set = AsyncMock()
            mock_cache.get = AsyncMock(return_value="test")
            mock_cache.delete = AsyncMock()

            mock_factory.return_value.for_ai_app = AsyncMock(return_value=mock_cache)

            cache = SecurityResultCache(config=security_config)
            await cache.initialize()

            assert cache._redis_available is True
            assert cache.redis_cache is mock_cache

    @pytest.mark.asyncio
    async def test_redis_initialization_failure(self, security_config: SecurityConfig) -> None:
        """Test Redis initialization failure falls back to memory cache."""
        with patch("app.infrastructure.security.llm.cache.CacheFactory") as mock_factory:
            mock_factory.return_value.for_ai_app = AsyncMock(side_effect=Exception("Redis unavailable"))

            cache = SecurityResultCache(config=security_config)
            await cache.initialize()

            assert cache._redis_available is False
            assert cache.redis_cache is None

    @pytest.mark.asyncio
    async def test_redis_cache_operations(self, security_config: SecurityConfig) -> None:
        """Test cache operations with Redis backend."""
        with patch("app.infrastructure.security.llm.cache.CacheFactory") as mock_factory:
            mock_cache = AsyncMock()

            # Mock successful get/set operations
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None

            mock_factory.return_value.for_ai_app = AsyncMock(return_value=mock_cache)

            cache = SecurityResultCache(config=security_config)
            await cache.initialize()

            result = SecurityResult(
                is_safe=True, violations=[], score=1.0, scanned_text="test",
                scan_duration_ms=100, scanner_results={}, metadata={}
            )

            # Test set operation
            await cache.set("test", "input", result)
            mock_cache.set.assert_called_once()

            # Test get operation (miss)
            await cache.get("test", "input")
            mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_cache_hit(self, security_config: SecurityConfig) -> None:
        """Test Redis cache hit scenario."""
        with patch("app.infrastructure.security.llm.cache.CacheFactory") as mock_factory:
            mock_cache = AsyncMock()

            # Create expected cache entry
            result = SecurityResult(
                is_safe=True, violations=[], score=1.0, scanned_text="test",
                scan_duration_ms=100, scanner_results={}, metadata={}
            )

            entry = CacheEntry(
                result=result,
                cached_at=datetime.now(UTC),
                cache_key="test_key",
                scanner_config_hash="hash",
                scanner_version="1.0.0",
                ttl_seconds=3600,
            )

            mock_cache.get.return_value = entry.to_dict()
            mock_cache.set.return_value = None

            mock_factory.return_value.for_ai_app = AsyncMock(return_value=mock_cache)

            cache = SecurityResultCache(config=security_config)
            await cache.initialize()

            # Test cache hit
            cached_result = await cache.get("test", "input")
            assert cached_result is not None
            assert cached_result.is_safe == result.is_safe
            assert cached_result.scanned_text == result.scanned_text

            # Verify Redis get was called
            mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_fallback_to_memory(self, security_config: SecurityConfig) -> None:
        """Test fallback to memory cache when Redis fails during operation."""
        with patch("app.infrastructure.security.llm.cache.CacheFactory") as mock_factory:
            mock_cache = AsyncMock()
            # First get fails, fallback should work
            mock_cache.get.side_effect = [Exception("Redis error"), None]
            mock_cache.set.return_value = None

            mock_factory.return_value.for_ai_app = AsyncMock(return_value=mock_cache)

            cache = SecurityResultCache(config=security_config)
            await cache.initialize()

            # This should fallback to memory cache
            result = await cache.get("test", "input")
            assert result is None  # Not in memory cache either

            # Verify statistics still track the miss
            stats = await cache.get_statistics()
            assert stats.total_requests == 1
            assert stats.misses == 1


class TestCacheIntegration:
    """Test cache integration with security scanner."""

    @pytest.mark.asyncio
    async def test_cache_integration_workflow(self) -> None:
        """Test complete cache integration workflow."""
        from app.infrastructure.security.llm.scanners.local_scanner import LocalLLMSecurityScanner
        from app.infrastructure.security.llm.config_loader import load_security_config

        # Load test configuration
        config = load_security_config(environment="testing")

        # Create scanner with cache
        scanner = LocalLLMSecurityScanner(config=config)
        await scanner.initialize()

        # Test text
        test_text = "This is a safe test message for scanning."

        # First scan should be a cache miss
        result1 = await scanner.validate_input(test_text)
        assert result1 is not None

        # Second scan should be a cache hit
        result2 = await scanner.validate_input(test_text)
        assert result2 is not None

        # Results should be identical
        assert result1.is_safe == result2.is_safe
        assert result1.score == result2.score
        assert result1.scanned_text == result2.scanned_text

        # Check cache statistics
        cache_stats = await scanner.get_cache_statistics()
        assert cache_stats["statistics"]["total_requests"] >= 2

    @pytest.mark.asyncio
    async def test_cache_different_content_types(self) -> None:
        """Test cache with different content types."""
        from app.infrastructure.security.llm.scanners.local_scanner import LocalLLMSecurityScanner
        from app.infrastructure.security.llm.config_loader import load_security_config

        config = load_security_config(environment="testing")
        scanner = LocalLLMSecurityScanner(config=config)
        await scanner.initialize()

        # Test different input texts
        text1 = "Safe message number one"
        text2 = "Safe message number two"
        text3 = "Safe message number one"  # Same as text1

        # Scan texts
        result1 = await scanner.validate_input(text1)
        result2 = await scanner.validate_input(text2)
        result3 = await scanner.validate_input(text3)  # Should hit cache

        # Verify results
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None

        # text1 and text3 should have identical results (cache hit)
        assert result1.scanned_text == result3.scanned_text
        assert result1.score == result3.score

        # text2 should be different from text1
        assert result2.scanned_text != result1.scanned_text

    @pytest.mark.asyncio
    async def test_cache_configuration_changes(self) -> None:
        """Test cache behavior when configuration changes."""
        from app.infrastructure.security.llm.scanners.local_scanner import LocalLLMSecurityScanner

        # Create scanner with one configuration
        config1 = SecurityConfig(
            performance=PerformanceConfig(
                enable_result_caching=True,
                cache_ttl_seconds=3600,
            )
        )
        scanner1 = LocalLLMSecurityScanner(config=config1)
        await scanner1.initialize()

        # Create scanner with different configuration
        config2 = SecurityConfig(
            performance=PerformanceConfig(
                enable_result_caching=True,
                cache_ttl_seconds=1800,  # Different TTL
            )
        )
        scanner2 = LocalLLMSecurityScanner(config=config2)
        await scanner2.initialize()

        # Test text
        test_text = "Test message for configuration change"

        # Scan with first scanner
        result1 = await scanner1.validate_input(test_text)

        # Scan with second scanner (should be cache miss due to different config)
        result2 = await scanner2.validate_input(test_text)

        # Both should produce results but from different cache entries
        assert result1 is not None
        assert result2 is not None

        # Configuration hashes should be different
        hash1 = scanner1.result_cache._scanner_config_hash
        hash2 = scanner2.result_cache._scanner_config_hash
        assert hash1 != hash2


class TestCachePerformance:
    """Test cache performance characteristics."""

    @pytest.mark.asyncio
    async def test_cache_lookup_performance(self) -> None:
        """Test cache lookup latency performance."""
        config = SecurityConfig(
            performance=PerformanceConfig(enable_result_caching=True)
        )
        cache = SecurityResultCache(config=config)
        await cache.initialize()

        # Create test result
        result = SecurityResult(
            is_safe=True, violations=[], score=1.0, scanned_text="test",
            scan_duration_ms=100, scanner_results={}, metadata={}
        )

        # Warm up cache
        await cache.set("test", "input", result)

        # Measure lookup performance
        start_time = time.time()
        for _ in range(100):
            await cache.get("test", "input")
        end_time = time.time()

        avg_time_ms = ((end_time - start_time) / 100) * 1000

        # Should be very fast (<1ms target)
        assert avg_time_ms < 1.0, f"Cache lookup too slow: {avg_time_ms:.3f}ms"

        # Check statistics
        stats = await cache.get_statistics()
        assert stats.avg_lookup_time_ms < 1.0

    @pytest.mark.asyncio
    async def test_cache_hit_rate_with_repeated_content(self) -> None:
        """Test cache hit rate with repeated content."""
        config = SecurityConfig(
            performance=PerformanceConfig(enable_result_caching=True)
        )
        cache = SecurityResultCache(config=config)
        await cache.initialize()

        # Create test result
        result = SecurityResult(
            is_safe=True, violations=[], score=1.0, scanned_text="test",
            scan_duration_ms=100, scanner_results={}, metadata={}
        )

        # Cache some content
        await cache.set("repeated_content", "input", result)

        # Perform repeated lookups
        hits = 0
        total = 20

        for i in range(total):
            cached_result = await cache.get("repeated_content", "input")
            if cached_result is not None:
                hits += 1

        # Should have high hit rate (>80% target)
        hit_rate = (hits / total) * 100
        assert hit_rate > 80.0, f"Cache hit rate too low: {hit_rate:.1f}%"

        # Verify statistics
        stats = await cache.get_statistics()
        assert stats.hit_rate > 80.0

    @pytest.mark.asyncio
    async def test_cache_memory_usage(self) -> None:
        """Test cache memory usage stays within limits."""
        config = SecurityConfig(
            performance=PerformanceConfig(enable_result_caching=True)
        )
        cache = SecurityResultCache(config=config)
        await cache.initialize()

        # Create and cache multiple results
        for i in range(10):
            result = SecurityResult(
                is_safe=i % 2 == 0,  # Alternate safe/unsafe
                violations=[],
                score=1.0 if i % 2 == 0 else 0.5,
                scanned_text=f"Test content {i}",
                scan_duration_ms=100 + i,
                scanner_results={},
                metadata={"index": i},
            )
            await cache.set(f"content_{i}", "input", result)

        # Check statistics
        stats = await cache.get_statistics()
        assert stats.cache_size == 10

        # Memory usage should be reasonable (no exact limit for memory cache)
        assert stats.memory_usage_mb >= 0

    @pytest.mark.asyncio
    async def test_cache_concurrent_access(self) -> None:
        """Test cache concurrent access safety."""
        config = SecurityConfig(
            performance=PerformanceConfig(enable_result_caching=True)
        )
        cache = SecurityResultCache(config=config)
        await cache.initialize()

        # Create test result
        result = SecurityResult(
            is_safe=True, violations=[], score=1.0, scanned_text="test",
            scan_duration_ms=100, scanner_results={}, metadata={}
        )

        # Concurrent cache operations
        async def cache_worker(worker_id: int) -> None:
            for i in range(10):
                key = f"worker_{worker_id}_item_{i}"
                await cache.set(key, "input", result)
                cached_result = await cache.get(key, "input")
                assert cached_result is not None

        # Run multiple workers concurrently
        tasks = [cache_worker(i) for i in range(5)]
        await asyncio.gather(*tasks)

        # Verify all operations completed
        stats = await cache.get_statistics()
        assert stats.total_requests == 100  # 5 workers * 10 operations each
        assert stats.hits == 50  # Each worker set and got their own items
        assert stats.misses == 50  # Initial lookups were misses
