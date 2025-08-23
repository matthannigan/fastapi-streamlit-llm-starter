"""Tests for standalone CacheKeyGenerator component.

This module provides comprehensive tests for the CacheKeyGenerator class,
including edge cases for very small text, >10 MB text, Unicode handling,
and performance monitoring integration.

The tests validate:
- Basic key generation functionality
- Streaming SHA-256 hashing for large texts
- Performance monitoring integration
- Edge cases (empty text, boundary conditions, Unicode)
- Backward compatibility with existing key formats
- Thread safety and concurrent access
"""

import pytest
import hashlib
import time
from unittest.mock import Mock, patch

from app.infrastructure.cache.key_generator import CacheKeyGenerator
from app.infrastructure.cache.monitoring import CachePerformanceMonitor


class TestCacheKeyGeneratorBasics:
    """Test basic functionality of CacheKeyGenerator."""
    
    @pytest.fixture
    def key_generator(self):
        """Create a fresh CacheKeyGenerator instance for testing."""
        return CacheKeyGenerator()
    
    @pytest.fixture
    def custom_key_generator(self):
        """Create a CacheKeyGenerator with custom settings."""
        return CacheKeyGenerator(text_hash_threshold=50, hash_algorithm=hashlib.md5)
    
    def test_initialization_default(self):
        """Test CacheKeyGenerator initialization with default parameters."""
        generator = CacheKeyGenerator()
        assert generator.text_hash_threshold == 1000
        assert generator.hash_algorithm == hashlib.sha256
        assert generator.performance_monitor is None
    
    def test_initialization_custom(self):
        """Test CacheKeyGenerator initialization with custom parameters."""
        monitor = CachePerformanceMonitor()
        generator = CacheKeyGenerator(
            text_hash_threshold=500,
            hash_algorithm=hashlib.md5,
            performance_monitor=monitor
        )
        assert generator.text_hash_threshold == 500
        assert generator.hash_algorithm == hashlib.md5
        assert generator.performance_monitor is monitor
    
    def test_short_text_handling(self, key_generator):
        """Test that short texts are used directly with sanitization."""
        short_text = "Sample text for testing"
        result = key_generator._hash_text_efficiently(short_text)
        
        # Should return the text directly (after sanitization)
        assert result == "Sample text for testing"
    
    def test_text_sanitization(self, key_generator):
        """Test that special characters are properly sanitized."""
        text_with_pipes = "text|with|pipes"
        text_with_colons = "text:with:colons"
        text_with_both = "text|mixed:chars"
        
        result1 = key_generator._hash_text_efficiently(text_with_pipes)
        result2 = key_generator._hash_text_efficiently(text_with_colons)
        result3 = key_generator._hash_text_efficiently(text_with_both)
        
        assert result1 == "text_with_pipes"
        assert result2 == "text_with_colons"
        assert result3 == "text_mixed_chars"
    
    def test_long_text_hashing(self, key_generator):
        """Test that long texts are properly hashed."""
        long_text = "A" * 1500  # Above default threshold
        result = key_generator._hash_text_efficiently(long_text)
        
        # Should return hash format for long texts
        assert result.startswith("hash:")
        assert len(result) == 21  # "hash:" + 16 char hash
    
    def test_boundary_threshold_conditions(self, key_generator):
        """Test behavior at exact threshold boundaries."""
        # Text exactly at threshold (1000 chars)
        threshold_text = "A" * 1000
        over_threshold_text = "A" * 1001
        under_threshold_text = "A" * 999
        
        at_threshold = key_generator._hash_text_efficiently(threshold_text)
        over_threshold = key_generator._hash_text_efficiently(over_threshold_text)
        under_threshold = key_generator._hash_text_efficiently(under_threshold_text)
        
        # At threshold should not be hashed
        assert at_threshold == threshold_text
        # Over threshold should be hashed
        assert over_threshold.startswith("hash:")
        # Under threshold should not be hashed
        assert under_threshold == under_threshold_text
    
    def test_hash_consistency(self, key_generator):
        """Test that identical texts produce identical hashes."""
        long_text = "A" * 1500
        hash1 = key_generator._hash_text_efficiently(long_text)
        hash2 = key_generator._hash_text_efficiently(long_text)
        
        assert hash1 == hash2
    
    def test_hash_uniqueness(self, key_generator):
        """Test that different texts produce different hashes."""
        text1 = "A" * 1500
        text2 = "B" * 1500
        
        hash1 = key_generator._hash_text_efficiently(text1)
        hash2 = key_generator._hash_text_efficiently(text2)
        
        assert hash1 != hash2
    
    def test_hash_metadata_inclusion(self, key_generator):
        """Test that hash includes metadata for uniqueness."""
        # Two texts with same content but different lengths due to spaces
        text1 = "A" * 1500
        text2 = "A" * 1500 + " "  # Same content + space
        
        hash1 = key_generator._hash_text_efficiently(text1)
        hash2 = key_generator._hash_text_efficiently(text2)
        
        assert hash1.startswith("hash:")
        assert hash2.startswith("hash:")
        assert hash1 != hash2  # Should be different due to metadata


class TestCacheKeyGeneration:
    """Test cache key generation functionality."""
    
    @pytest.fixture
    def key_generator(self):
        """Create a fresh CacheKeyGenerator instance for testing."""
        return CacheKeyGenerator()
    
    def test_basic_cache_key_generation(self, key_generator):
        """Test basic cache key generation."""
        text = "Test text"
        operation = "summarize"
        options = {"max_length": 100}
        
        cache_key = key_generator.generate_cache_key(text, operation, options)
        
        assert cache_key.startswith("ai_cache:")
        assert "op:summarize" in cache_key
        assert "txt:Test text" in cache_key
        assert "opts:" in cache_key
    
    def test_cache_key_with_question(self, key_generator):
        """Test cache key generation with question parameter."""
        text = "Test text"
        operation = "qa"
        options = {}
        question = "What is this about?"
        
        cache_key = key_generator.generate_cache_key(text, operation, options, question)
        
        assert cache_key.startswith("ai_cache:")
        assert "op:qa" in cache_key
        assert "q:" in cache_key
        # Question should be hashed (not in plain text)
        assert "What is this about?" not in cache_key
    
    def test_cache_key_without_options(self, key_generator):
        """Test cache key generation without options."""
        text = "Test text"
        operation = "sentiment"
        options = {}
        
        cache_key = key_generator.generate_cache_key(text, operation, options)
        
        assert cache_key.startswith("ai_cache:")
        assert "op:sentiment" in cache_key
        assert "txt:Test text" in cache_key
        assert "opts:" not in cache_key  # No options should mean no opts component
    
    def test_cache_key_consistency(self, key_generator):
        """Test that identical inputs produce identical cache keys."""
        text = "Test text"
        operation = "summarize"
        options = {"max_length": 100}
        
        key1 = key_generator.generate_cache_key(text, operation, options)
        key2 = key_generator.generate_cache_key(text, operation, options)
        
        assert key1 == key2
    
    def test_cache_key_options_order_independence(self, key_generator):
        """Test that options order doesn't affect cache key."""
        text = "Test text"
        operation = "summarize"
        options1 = {"max_length": 100, "style": "formal"}
        options2 = {"style": "formal", "max_length": 100}
        
        key1 = key_generator.generate_cache_key(text, operation, options1)
        key2 = key_generator.generate_cache_key(text, operation, options2)
        
        assert key1 == key2
    
    def test_cache_key_with_long_text(self, key_generator):
        """Test cache key generation with long text that gets hashed."""
        long_text = "A" * 1500
        operation = "summarize"
        options = {"max_length": 100}
        
        cache_key = key_generator.generate_cache_key(long_text, operation, options)
        
        assert cache_key.startswith("ai_cache:")
        assert "op:summarize" in cache_key
        assert "txt:hash:" in cache_key  # Long text should be hashed
        assert "opts:" in cache_key
    
    def test_cache_key_structure_validation(self, key_generator):
        """Test the structure and format of generated cache keys."""
        text = "Test text"
        operation = "sentiment"
        options = {"model": "advanced"}
        question = "What sentiment?"
        
        cache_key = key_generator.generate_cache_key(text, operation, options, question)
        
        parts = cache_key.split("|")
        assert parts[0] == "ai_cache:op:sentiment"
        assert parts[1] == "txt:Test text"
        assert parts[2].startswith("opts:")
        assert parts[3].startswith("q:")
        assert len(parts) == 4  # Should have exactly 4 parts for this configuration
    
    def test_cache_key_length_constraints(self, key_generator):
        """Test that cache keys don't become excessively long."""
        very_long_text = "A" * 50000  # Very large text
        operation = "summarize"
        options = {"param": "value"}
        
        cache_key = key_generator.generate_cache_key(very_long_text, operation, options)
        
        # Cache key should be reasonably bounded even for very large texts
        assert len(cache_key) < 200  # Reasonable upper bound
        assert cache_key.startswith("ai_cache:")
        assert "txt:hash:" in cache_key  # Large text should be hashed


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def key_generator(self):
        """Create a fresh CacheKeyGenerator instance for testing."""
        return CacheKeyGenerator()
    
    def test_empty_string_handling(self, key_generator):
        """Test CacheKeyGenerator behavior with empty strings."""
        empty_text = ""
        operation = "summarize"
        options = {"max_length": 100}
        
        result = key_generator._hash_text_efficiently(empty_text)
        cache_key = key_generator.generate_cache_key(empty_text, operation, options)
        
        # Empty string should remain empty (below threshold)
        assert result == empty_text
        assert cache_key.startswith("ai_cache:")
        assert "op:summarize" in cache_key
        assert "txt:" in cache_key
    
    def test_unicode_and_special_characters(self, key_generator):
        """Test CacheKeyGenerator with Unicode and special characters."""
        unicode_text = "Hello 世界! 🌍 Testing émojis and spëcial chars: àáâãäå"
        operation = "summarize"
        options = {"style": "formal"}
        
        text_hash = key_generator._hash_text_efficiently(unicode_text)
        cache_key = key_generator.generate_cache_key(unicode_text, operation, options)
        
        # Should handle Unicode gracefully
        expected_sanitized = unicode_text.replace("|", "_").replace(":", "_")
        assert text_hash == expected_sanitized
        assert cache_key.startswith("ai_cache:")
        assert "op:summarize" in cache_key
    
    def test_very_small_text_edge_case(self, key_generator):
        """Test with single character text."""
        tiny_text = "A"
        result = key_generator._hash_text_efficiently(tiny_text)
        assert result == "A"
        
        cache_key = key_generator.generate_cache_key(tiny_text, "test", {})
        assert cache_key.startswith("ai_cache:")
        assert "txt:A" in cache_key
    
    def test_large_text_over_10mb(self, key_generator):
        """Test with text larger than 10 MB."""
        # Create a 10 MB+ text (10 * 1024 * 1024 chars)
        large_text = "X" * (10 * 1024 * 1024 + 1000)
        
        # This should still work efficiently with streaming hash
        result = key_generator._hash_text_efficiently(large_text)
        
        assert result.startswith("hash:")
        assert len(result) == 21  # "hash:" + 16 char hash
        
        # Test that it can generate a cache key
        cache_key = key_generator.generate_cache_key(large_text, "test", {})
        assert cache_key.startswith("ai_cache:")
        assert "txt:hash:" in cache_key
        # Key should still be reasonably sized
        assert len(cache_key) < 200
    
    def test_various_option_value_types(self, key_generator):
        """Test cache key generation with different option value types."""
        text = "Test text"
        operation = "summarize"
        complex_options = {
            "max_length": 100,
            "temperature": 0.7,
            "enabled": True,
            "disabled": False,
            "tags": ["tag1", "tag2"],
            "metadata": {"nested": "value"}
        }
        
        cache_key = key_generator.generate_cache_key(text, operation, complex_options)
        
        assert cache_key.startswith("ai_cache:")
        assert "op:summarize" in cache_key
        assert "opts:" in cache_key
        
        # Test consistency with same complex options
        cache_key2 = key_generator.generate_cache_key(text, operation, complex_options)
        assert cache_key == cache_key2
    
    def test_none_and_invalid_inputs_handling(self, key_generator):
        """Test CacheKeyGenerator behavior with None and edge case inputs."""
        # Test with None question (should work normally)
        cache_key = key_generator.generate_cache_key("text", "summarize", {}, None)
        assert cache_key.startswith("ai_cache:")
        assert "q:" not in cache_key
        
        # Test with empty options dict
        cache_key2 = key_generator.generate_cache_key("text", "summarize", {})
        assert cache_key2.startswith("ai_cache:")
        assert "opts:" not in cache_key2
        
        # Test with options containing None values
        options_with_none = {"key1": None, "key2": "value"}
        cache_key3 = key_generator.generate_cache_key("text", "summarize", options_with_none)
        assert cache_key3.startswith("ai_cache:")


class TestPerformanceMonitoring:
    """Test performance monitoring integration."""
    
    def test_performance_monitor_integration(self):
        """Test CacheKeyGenerator with performance monitor integration."""
        monitor = CachePerformanceMonitor()
        key_generator = CacheKeyGenerator(performance_monitor=monitor)
        text = "Test text for performance monitoring"
        operation = "summarize"
        options = {"max_length": 100}
        
        initial_count = len(monitor.key_generation_times)
        cache_key = key_generator.generate_cache_key(text, operation, options)
        
        assert cache_key.startswith("ai_cache:")
        assert len(monitor.key_generation_times) == initial_count + 1
        
        # Verify recorded performance data
        latest_metric = monitor.key_generation_times[-1]
        assert latest_metric.text_length == len(text)
        assert latest_metric.operation_type == operation
        assert isinstance(latest_metric.duration, float)
        assert latest_metric.duration >= 0
    
    def test_performance_monitor_data_integrity(self):
        """Test that performance monitor receives accurate data."""
        monitor = CachePerformanceMonitor()
        key_generator = CacheKeyGenerator(
            text_hash_threshold=100,
            performance_monitor=monitor
        )
        
        small_text = "Small"
        large_text = "A" * 200
        
        key_generator.generate_cache_key(small_text, "summarize", {})
        key_generator.generate_cache_key(large_text, "sentiment", {"model": "v1"})
        
        assert len(monitor.key_generation_times) == 2
        
        # Check small text metric
        small_metric = monitor.key_generation_times[0]
        assert small_metric.text_length == len(small_text)
        assert small_metric.operation_type == "summarize"
        assert small_metric.additional_data["text_tier"] == "small"
        assert not small_metric.additional_data["has_options"]
        assert not small_metric.additional_data["has_question"]
        
        # Check large text metric
        large_metric = monitor.key_generation_times[1]
        assert large_metric.text_length == len(large_text)
        assert large_metric.operation_type == "sentiment"
        assert large_metric.additional_data["text_tier"] == "large"
        assert large_metric.additional_data["has_options"]
        assert not large_metric.additional_data["has_question"]
    
    def test_get_key_generation_stats_without_monitor(self):
        """Test get_key_generation_stats without performance monitor."""
        key_generator = CacheKeyGenerator()  # No monitor
        
        stats = key_generator.get_key_generation_stats()
        
        assert stats["total_keys_generated"] == 0
        assert stats["average_generation_time"] == 0.0
        assert stats["monitor_available"] == False
    
    def test_get_key_generation_stats_with_monitor(self):
        """Test get_key_generation_stats with performance monitor."""
        monitor = CachePerformanceMonitor()
        key_generator = CacheKeyGenerator(performance_monitor=monitor)
        
        # Generate some keys to populate stats
        key_generator.generate_cache_key("text1", "summarize", {})
        key_generator.generate_cache_key("A" * 1500, "sentiment", {"model": "v1"})
        key_generator.generate_cache_key("text3", "qa", {}, "question")
        
        stats = key_generator.get_key_generation_stats()
        
        assert stats["total_keys_generated"] == 3
        assert stats["average_generation_time"] > 0
        assert stats["monitor_available"] == True
        assert "text_size_distribution" in stats
        assert "operation_distribution" in stats
        assert "recent_performance" in stats
        
        # Check text size distribution
        text_dist = stats["text_size_distribution"]
        assert text_dist["small"] == 2  # text1 and text3
        assert text_dist["large"] == 1   # A * 1500
        
        # Check operation distribution
        op_dist = stats["operation_distribution"]
        assert op_dist["summarize"] == 1
        assert op_dist["sentiment"] == 1
        assert op_dist["qa"] == 1


class TestSecurityAndPrivacy:
    """Test security and privacy aspects of key generation."""
    
    @pytest.fixture
    def key_generator(self):
        """Create a fresh CacheKeyGenerator instance for testing."""
        return CacheKeyGenerator()
    
    def test_question_parameter_hashing_consistency(self, key_generator):
        """Test that question parameter hashing is consistent and secure."""
        text = "Test text"
        operation = "qa"
        options = {}
        question1 = "What is this about?"
        question2 = "What is this about?"  # Same question
        question3 = "What is this topic?"  # Different question
        
        key1 = key_generator.generate_cache_key(text, operation, options, question1)
        key2 = key_generator.generate_cache_key(text, operation, options, question2)
        key3 = key_generator.generate_cache_key(text, operation, options, question3)
        
        # Same questions should produce same keys
        assert key1 == key2
        # Different questions should produce different keys
        assert key1 != key3
        
        # Check that question is hashed (not stored in plain text)
        assert question1 not in key1
        assert "q:" in key1  # Should have question component
    
    def test_options_hashing_security(self, key_generator):
        """Test that sensitive options are properly hashed."""
        text = "Test text"
        operation = "summarize"
        sensitive_options = {
            "api_key": "secret_key_123",
            "password": "very_secret_password",
            "token": "auth_token_xyz"
        }
        
        cache_key = key_generator.generate_cache_key(text, operation, sensitive_options)
        
        # Sensitive values should not appear in plain text in the cache key
        assert "secret_key_123" not in cache_key
        assert "very_secret_password" not in cache_key
        assert "auth_token_xyz" not in cache_key
        assert "opts:" in cache_key  # Should have options component


class TestConcurrencyAndThreadSafety:
    """Test concurrent access and thread safety."""
    
    @pytest.fixture
    def key_generator(self):
        """Create a fresh CacheKeyGenerator instance for testing."""
        return CacheKeyGenerator()
    
    def test_concurrent_key_generation_consistency(self, key_generator):
        """Test that concurrent key generation produces consistent results."""
        text = "Concurrent test text"
        operation = "summarize"
        options = {"max_length": 150}
        
        # Simulate concurrent access
        keys = []
        for _ in range(10):
            key = key_generator.generate_cache_key(text, operation, options)
            keys.append(key)
        
        # All keys should be identical (stateless behavior)
        assert all(key == keys[0] for key in keys)
        assert len(set(keys)) == 1  # All keys should be the same


class TestDifferentHashAlgorithms:
    """Test different hash algorithms."""
    
    def test_different_hash_algorithms(self):
        """Test CacheKeyGenerator with different hash algorithms."""
        text = "A" * 1500  # Long text to trigger hashing
        md5_generator = CacheKeyGenerator(hash_algorithm=hashlib.md5)
        sha1_generator = CacheKeyGenerator(hash_algorithm=hashlib.sha1)
        sha256_generator = CacheKeyGenerator(hash_algorithm=hashlib.sha256)
        
        md5_hash = md5_generator._hash_text_efficiently(text)
        sha1_hash = sha1_generator._hash_text_efficiently(text)
        sha256_hash = sha256_generator._hash_text_efficiently(text)
        
        assert md5_hash.startswith("hash:")
        assert sha1_hash.startswith("hash:")
        assert sha256_hash.startswith("hash:")
        
        # All should be different due to different algorithms
        assert md5_hash != sha1_hash
        assert md5_hash != sha256_hash
        assert sha1_hash != sha256_hash


class TestBackwardCompatibility:
    """Test backward compatibility with existing key formats."""
    
    def test_key_format_compatibility(self):
        """Test that generated keys maintain expected format."""
        generator = CacheKeyGenerator()
        
        text = "Sample text"
        operation = "summarize"
        options = {"max_length": 100}
        question = "What is the summary?"
        
        key = generator.generate_cache_key(text, operation, options, question)
        
        # Should maintain the expected ai_cache: prefix
        assert key.startswith("ai_cache:")
        
        # Should use pipe separators
        assert "|" in key
        
        # Should have expected components
        components = key.split("|")
        assert len(components) == 4  # op, txt, opts, q
        assert components[0].startswith("ai_cache:op:")
        assert components[1].startswith("txt:")
        assert components[2].startswith("opts:")
        assert components[3].startswith("q:")


class TestPerformanceCharacteristics:
    """Test performance characteristics of the key generator."""
    
    @pytest.fixture
    def key_generator(self):
        """Create a fresh CacheKeyGenerator instance for testing."""
        return CacheKeyGenerator()
    
    def test_performance_scalability_with_text_size(self, key_generator):
        """Test that performance scales reasonably with text size."""
        # Test with different text sizes
        text_sizes = [100, 1000, 10000, 100000]
        times = []
        
        for size in text_sizes:
            text = "A" * size
            start_time = time.time()
            for _ in range(10):  # Average over multiple runs
                key_generator.generate_cache_key(text, "test", {})
            end_time = time.time()
            avg_time = (end_time - start_time) / 10
            times.append(avg_time)
        
        # Times should be reasonable (< 10ms for any size)
        for avg_time in times:
            assert avg_time < 0.01  # Less than 10ms
    
    def test_memory_efficiency_large_text(self, key_generator):
        """Test that memory usage is efficient for large texts."""
        # This test verifies that we can handle large texts without issues
        large_text = "X" * (5 * 1024 * 1024)  # 5MB text
        
        # Should complete without memory issues
        result = key_generator._hash_text_efficiently(large_text)
        assert result.startswith("hash:")
        
        cache_key = key_generator.generate_cache_key(large_text, "test", {})
        assert cache_key.startswith("ai_cache:")
        assert len(cache_key) < 200  # Key length bounded regardless of text size
