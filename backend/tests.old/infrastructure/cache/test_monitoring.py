import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.infrastructure.cache.monitoring import (
    CachePerformanceMonitor, 
    PerformanceMetric, 
    CompressionMetric, 
    MemoryUsageMetric,
    InvalidationMetric
)


class TestPerformanceMetric:
    """Test the PerformanceMetric dataclass."""
    
    def test_performance_metric_creation(self):
        """Test creating a PerformanceMetric with all fields."""
        metric = PerformanceMetric(
            duration=0.1,
            text_length=1000,
            timestamp=time.time(),
            operation_type="summarize",
            additional_data={"key": "value"}
        )
        
        assert metric.duration == 0.1
        assert metric.text_length == 1000
        assert metric.operation_type == "summarize"
        assert metric.additional_data == {"key": "value"}
    
    def test_performance_metric_defaults(self):
        """Test PerformanceMetric with default values."""
        metric = PerformanceMetric(
            duration=0.05,
            text_length=500,
            timestamp=time.time()
        )
        
        assert metric.operation_type == ""
        assert metric.additional_data == {}


class TestCompressionMetric:
    """Test the CompressionMetric dataclass."""
    
    def test_compression_metric_creation(self):
        """Test creating a CompressionMetric with all fields."""
        metric = CompressionMetric(
            original_size=1000,
            compressed_size=600,
            compression_ratio=0.6,
            compression_time=0.02,
            timestamp=time.time(),
            operation_type="summarize"
        )
        
        assert metric.original_size == 1000
        assert metric.compressed_size == 600
        assert metric.compression_ratio == 0.6
        assert metric.compression_time == 0.02
        assert metric.operation_type == "summarize"
    
    def test_compression_metric_auto_ratio_calculation(self):
        """Test automatic calculation of compression ratio when set to 0."""
        metric = CompressionMetric(
            original_size=1000,
            compressed_size=600,
            compression_ratio=0,  # Will be auto-calculated
            compression_time=0.02,
            timestamp=time.time()
        )
        
        assert metric.compression_ratio == 0.6  # 600/1000
    
    def test_compression_metric_zero_original_size(self):
        """Test compression ratio calculation with zero original size."""
        metric = CompressionMetric(
            original_size=0,
            compressed_size=0,
            compression_ratio=0,
            compression_time=0.02,
            timestamp=time.time()
        )
        
        assert metric.compression_ratio == 0  # Should remain 0


class TestMemoryUsageMetric:
    """Test the MemoryUsageMetric data class."""
    
    def test_memory_usage_metric_creation(self):
        """Test creating MemoryUsageMetric with all required fields."""
        metric = MemoryUsageMetric(
            total_cache_size_bytes=1024 * 1024,  # 1MB
            cache_entry_count=100,
            avg_entry_size_bytes=10240.0,
            memory_cache_size_bytes=512 * 1024,  # 512KB
            memory_cache_entry_count=50,
            process_memory_mb=256.5,
            timestamp=time.time(),
            cache_utilization_percent=2.0,
            warning_threshold_reached=False
        )
        
        assert metric.total_cache_size_bytes == 1024 * 1024
        assert metric.cache_entry_count == 100
        assert metric.avg_entry_size_bytes == 10240.0
        assert metric.memory_cache_size_bytes == 512 * 1024
        assert metric.memory_cache_entry_count == 50
        assert metric.process_memory_mb == 256.5
        assert metric.cache_utilization_percent == 2.0
        assert metric.warning_threshold_reached is False
        assert metric.additional_data == {}


class TestCachePerformanceMonitor:
    """Test the CachePerformanceMonitor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = CachePerformanceMonitor(retention_hours=1, max_measurements=100)
    
    def test_initialization(self):
        """Test monitor initialization with default and custom values."""
        # Test default initialization
        default_monitor = CachePerformanceMonitor()
        assert default_monitor.retention_hours == 1
        assert default_monitor.max_measurements == 1000
        assert default_monitor.cache_hits == 0
        assert default_monitor.cache_misses == 0
        assert default_monitor.total_operations == 0
        assert default_monitor.memory_warning_threshold_bytes == 50 * 1024 * 1024
        assert default_monitor.memory_critical_threshold_bytes == 100 * 1024 * 1024
        
        # Test custom initialization
        custom_monitor = CachePerformanceMonitor(
            retention_hours=2, 
            max_measurements=500,
            memory_warning_threshold_bytes=25 * 1024 * 1024,
            memory_critical_threshold_bytes=50 * 1024 * 1024
        )
        assert custom_monitor.retention_hours == 2
        assert custom_monitor.max_measurements == 500
        assert custom_monitor.memory_warning_threshold_bytes == 25 * 1024 * 1024
        assert custom_monitor.memory_critical_threshold_bytes == 50 * 1024 * 1024
    
    def test_record_key_generation_time(self):
        """Test recording key generation performance."""
        self.monitor.record_key_generation_time(
            duration=0.05,
            text_length=1000,
            operation_type="summarize",
            additional_data={"model": "gpt-4"}
        )
        
        assert len(self.monitor.key_generation_times) == 1
        
        metric = self.monitor.key_generation_times[0]
        assert metric.duration == 0.05
        assert metric.text_length == 1000
        assert metric.operation_type == "summarize"
        assert metric.additional_data == {"model": "gpt-4"}
    
    @patch('app.infrastructure.cache.monitoring.logger')
    def test_record_key_generation_time_slow_warning(self, mock_logger):
        """Test warning logging for slow key generation."""
        # Record a slow operation (above 0.1s threshold)
        self.monitor.record_key_generation_time(
            duration=0.15,
            text_length=5000,
            operation_type="summarize"
        )
        
        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "Slow key generation" in warning_call
        assert "0.150s" in warning_call
    
    def test_record_cache_operation_time(self):
        """Test recording cache operation performance."""
        self.monitor.record_cache_operation_time(
            operation="get",
            duration=0.02,
            cache_hit=True,
            text_length=500,
            additional_data={"tier": "small"}
        )
        
        assert len(self.monitor.cache_operation_times) == 1
        assert self.monitor.cache_hits == 1
        assert self.monitor.cache_misses == 0
        assert self.monitor.total_operations == 1
        
        metric = self.monitor.cache_operation_times[0]
        assert metric.duration == 0.02
        assert metric.operation_type == "get"
        assert metric.text_length == 500
        assert metric.additional_data == {"tier": "small"}
    
    def test_record_cache_operation_time_miss(self):
        """Test recording cache miss."""
        self.monitor.record_cache_operation_time(
            operation="get",
            duration=0.03,
            cache_hit=False,
            text_length=1000
        )
        
        assert self.monitor.cache_hits == 0
        assert self.monitor.cache_misses == 1
        assert self.monitor.total_operations == 1
    
    def test_record_cache_operation_time_non_get(self):
        """Test recording non-get operations don't affect hit/miss stats."""
        self.monitor.record_cache_operation_time(
            operation="set",
            duration=0.04,
            cache_hit=False,  # Irrelevant for set operations
            text_length=800
        )
        
        assert self.monitor.cache_hits == 0
        assert self.monitor.cache_misses == 0
        assert self.monitor.total_operations == 1
    
    @patch('app.infrastructure.cache.monitoring.logger')
    def test_record_cache_operation_time_slow_warning(self, mock_logger):
        """Test warning logging for slow cache operations."""
        # Record a slow operation (above 0.05s threshold)
        self.monitor.record_cache_operation_time(
            operation="get",
            duration=0.08,
            cache_hit=True,
            text_length=2000
        )
        
        # Check that warning was logged
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "Slow cache get" in warning_call
        assert "0.080s" in warning_call
    
    def test_record_compression_ratio(self):
        """Test recording compression performance."""
        self.monitor.record_compression_ratio(
            original_size=1000,
            compressed_size=600,
            compression_time=0.01,
            operation_type="summarize"
        )
        
        assert len(self.monitor.compression_ratios) == 1
        
        metric = self.monitor.compression_ratios[0]
        assert metric.original_size == 1000
        assert metric.compressed_size == 600
        assert metric.compression_ratio == 0.6
        assert metric.compression_time == 0.01
        assert metric.operation_type == "summarize"
    
    @patch('time.time')
    def test_cleanup_old_measurements(self, mock_time):
        """Test cleanup of old measurements based on retention policy."""
        current_time = 1000000
        mock_time.return_value = current_time
        
        # Add some measurements with different timestamps
        old_time = current_time - 7200  # 2 hours ago (should be cleaned)
        recent_time = current_time - 1800  # 30 minutes ago (should be kept)
        
        # Add old measurement
        old_metric = PerformanceMetric(
            duration=0.1,
            text_length=1000,
            timestamp=old_time
        )
        self.monitor.key_generation_times.append(old_metric)
        
        # Add recent measurement
        recent_metric = PerformanceMetric(
            duration=0.05,
            text_length=500,
            timestamp=recent_time
        )
        self.monitor.key_generation_times.append(recent_metric)
        
        # Trigger cleanup
        self.monitor._cleanup_old_measurements(self.monitor.key_generation_times)
        
        # Only recent measurement should remain
        assert len(self.monitor.key_generation_times) == 1
        assert self.monitor.key_generation_times[0].timestamp == recent_time
    
    def test_cleanup_max_measurements_limit(self):
        """Test cleanup based on maximum measurements limit."""
        # Set a very low limit for testing
        self.monitor.max_measurements = 3
        
        # Add more measurements than the limit
        for i in range(5):
            metric = PerformanceMetric(
                duration=0.01 * i,
                text_length=100 * i,
                timestamp=time.time() + i
            )
            self.monitor.key_generation_times.append(metric)
        
        # Trigger cleanup
        self.monitor._cleanup_old_measurements(self.monitor.key_generation_times)
        
        # Should only keep the most recent measurements
        assert len(self.monitor.key_generation_times) == 3
        # Check that the most recent measurements are kept
        assert self.monitor.key_generation_times[0].duration == 0.02  # 3rd measurement
        assert self.monitor.key_generation_times[1].duration == 0.03  # 4th measurement
        assert self.monitor.key_generation_times[2].duration == 0.04  # 5th measurement
    
    def test_get_performance_stats_empty(self):
        """Test performance stats with no measurements."""
        stats = self.monitor.get_performance_stats()
        
        assert stats["cache_hit_rate"] == 0.0
        assert stats["total_cache_operations"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert "key_generation" not in stats
        assert "cache_operations" not in stats
        assert "compression" not in stats
        assert "memory_usage" not in stats
    
    def test_get_performance_stats_with_data(self):
        """Test performance stats with various measurements."""
        # Add key generation measurements
        self.monitor.record_key_generation_time(0.05, 1000, "summarize")
        self.monitor.record_key_generation_time(0.08, 2000, "sentiment")
        self.monitor.record_key_generation_time(0.12, 3000, "summarize")  # Slow
        
        # Add cache operation measurements
        self.monitor.record_cache_operation_time("get", 0.02, True, 500)
        self.monitor.record_cache_operation_time("get", 0.03, False, 1000)
        self.monitor.record_cache_operation_time("set", 0.04, False, 800)
        
        # Add compression measurements
        self.monitor.record_compression_ratio(1000, 600, 0.01, "summarize")
        self.monitor.record_compression_ratio(2000, 1000, 0.02, "sentiment")
        
        # Add memory usage measurements
        memory_cache = {"key1": {"data": "value1"}}
        self.monitor.record_memory_usage(memory_cache)
        
        stats = self.monitor.get_performance_stats()
        
        # Check overall stats
        assert stats["cache_hit_rate"] == 33.33333333333333  # 1 hit out of 3 operations
        assert stats["total_cache_operations"] == 3
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        
        # Check key generation stats
        key_gen = stats["key_generation"]
        assert key_gen["total_operations"] == 3
        assert key_gen["avg_duration"] == (0.05 + 0.08 + 0.12) / 3
        assert key_gen["max_duration"] == 0.12
        assert key_gen["min_duration"] == 0.05
        assert key_gen["avg_text_length"] == (1000 + 2000 + 3000) / 3
        assert key_gen["max_text_length"] == 3000
        assert key_gen["slow_operations"] == 1  # One above 0.1s threshold
        
        # Check cache operation stats
        cache_ops = stats["cache_operations"]
        assert cache_ops["total_operations"] == 3
        assert cache_ops["avg_duration"] == (0.02 + 0.03 + 0.04) / 3
        assert cache_ops["max_duration"] == 0.04
        assert cache_ops["min_duration"] == 0.02
        assert cache_ops["slow_operations"] == 0  # None above 0.05s threshold
        
        # Check operation type breakdown
        assert "get" in cache_ops["by_operation_type"]
        assert "set" in cache_ops["by_operation_type"]
        assert cache_ops["by_operation_type"]["get"]["count"] == 2
        assert cache_ops["by_operation_type"]["set"]["count"] == 1
        
        # Check compression stats
        compression = stats["compression"]
        assert compression["total_operations"] == 2
        assert compression["avg_compression_ratio"] == (0.6 + 0.5) / 2
        assert compression["best_compression_ratio"] == 0.5  # min ratio (best compression)
        assert compression["worst_compression_ratio"] == 0.6  # max ratio (worst compression)
        assert compression["total_bytes_processed"] == 3000
        assert compression["total_bytes_saved"] == 1400  # (1000-600) + (2000-1000)
        assert compression["overall_savings_percent"] == (1400 / 3000) * 100
        
        # Check memory usage stats
        assert "memory_usage" in stats
        memory_usage = stats["memory_usage"]
        assert "current" in memory_usage
        assert "thresholds" in memory_usage
        assert "trends" in memory_usage
    
    def test_calculate_hit_rate(self):
        """Test cache hit rate calculation."""
        # No operations
        assert self.monitor._calculate_hit_rate() == 0.0
        
        # Some operations
        self.monitor.cache_hits = 7
        self.monitor.total_operations = 10
        assert self.monitor._calculate_hit_rate() == 70.0
    
    def test_get_recent_slow_operations(self):
        """Test identification of slow operations."""
        # Add mix of fast and slow operations with extreme differences
        self.monitor.record_key_generation_time(0.001, 1000, "summarize")  # Fast
        self.monitor.record_key_generation_time(0.001, 1200, "sentiment")  # Fast
        self.monitor.record_key_generation_time(10.0, 2000, "summarize")   # Extremely slow
        
        self.monitor.record_cache_operation_time("get", 0.001, True, 500)   # Fast
        self.monitor.record_cache_operation_time("get", 0.001, False, 800)  # Fast
        self.monitor.record_cache_operation_time("set", 10.0, False, 1000)  # Extremely slow
        
        self.monitor.record_compression_ratio(1000, 600, 0.001, "summarize")  # Fast
        self.monitor.record_compression_ratio(2000, 1000, 15.0, "sentiment") # Extremely slow
        
        slow_ops = self.monitor.get_recent_slow_operations(threshold_multiplier=1.5)
        
        # Check key generation slow operations
        assert len(slow_ops["key_generation"]) == 1
        slow_key_gen = slow_ops["key_generation"][0]
        assert slow_key_gen["duration"] == 10.0
        assert slow_key_gen["text_length"] == 2000
        assert slow_key_gen["operation_type"] == "summarize"
        assert slow_key_gen["times_slower"] > 1.5
        
        # Check cache operation slow operations
        assert len(slow_ops["cache_operations"]) == 1
        slow_cache_op = slow_ops["cache_operations"][0]
        assert slow_cache_op["duration"] == 10.0
        assert slow_cache_op["operation_type"] == "set"
        assert slow_cache_op["times_slower"] > 1.5
        
        # Check compression slow operations
        assert len(slow_ops["compression"]) == 1
        slow_compression = slow_ops["compression"][0]
        assert slow_compression["compression_time"] == 15.0
        assert slow_compression["operation_type"] == "sentiment"
        assert slow_compression["times_slower"] > 1.5
    
    def test_reset_stats(self):
        """Test resetting all statistics."""
        # Add some data
        self.monitor.record_key_generation_time(0.05, 1000, "summarize")
        self.monitor.record_cache_operation_time("get", 0.02, True, 500)
        self.monitor.record_compression_ratio(1000, 600, 0.01, "summarize")
        memory_cache = {"key1": {"data": "value1"}}
        self.monitor.record_memory_usage(memory_cache)
        
        assert len(self.monitor.key_generation_times) > 0
        assert len(self.monitor.cache_operation_times) > 0
        assert len(self.monitor.compression_ratios) > 0
        assert len(self.monitor.memory_usage_measurements) > 0
        assert self.monitor.cache_hits > 0
        assert self.monitor.total_operations > 0
        
        # Reset
        self.monitor.reset_stats()
        
        assert len(self.monitor.key_generation_times) == 0
        assert len(self.monitor.cache_operation_times) == 0
        assert len(self.monitor.compression_ratios) == 0
        assert len(self.monitor.memory_usage_measurements) == 0
        assert self.monitor.cache_hits == 0
        assert self.monitor.cache_misses == 0
        assert self.monitor.total_operations == 0

    def test_record_invalidation_event(self):
        """Test recording cache invalidation events."""
        self.monitor.record_invalidation_event(
            pattern="test_pattern",
            keys_invalidated=5,
            duration=0.025,
            invalidation_type="manual",
            operation_context="test_context",
            additional_data={"user": "test_user"}
        )
        
        assert len(self.monitor.invalidation_events) == 1
        assert self.monitor.total_invalidations == 1
        assert self.monitor.total_keys_invalidated == 5
        
        event = self.monitor.invalidation_events[0]
        assert event.pattern == "test_pattern"
        assert event.keys_invalidated == 5
        assert event.duration == 0.025
        assert event.invalidation_type == "manual"
        assert event.operation_context == "test_context"
        assert event.additional_data == {"user": "test_user"}

    @patch('app.infrastructure.cache.monitoring.logger')
    def test_record_invalidation_event_high_frequency_warning(self, mock_logger):
        """Test warning logging for high invalidation frequency."""
        # Set low thresholds for testing
        self.monitor.invalidation_rate_warning_per_hour = 2
        self.monitor.invalidation_rate_critical_per_hour = 4
        
        # Record invalidations to trigger warning
        for i in range(3):
            self.monitor.record_invalidation_event(
                pattern=f"pattern_{i}",
                keys_invalidated=1,
                duration=0.01
            )
        
        # Should trigger warning
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "High invalidation rate" in warning_call

    @patch('app.infrastructure.cache.monitoring.logger')
    def test_record_invalidation_event_critical_frequency(self, mock_logger):
        """Test critical logging for very high invalidation frequency."""
        # Set low thresholds for testing
        self.monitor.invalidation_rate_warning_per_hour = 2
        self.monitor.invalidation_rate_critical_per_hour = 4
        
        # Record invalidations to trigger critical
        for i in range(5):
            self.monitor.record_invalidation_event(
                pattern=f"pattern_{i}",
                keys_invalidated=1,
                duration=0.01
            )
        
        # Should trigger critical
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Critical invalidation rate" in error_call

    def test_get_invalidations_in_last_hour(self):
        """Test counting invalidations in the last hour."""
        import time
        current_time = time.time()
        
        # Add some old invalidations (more than 1 hour ago)
        old_event = InvalidationMetric(
            pattern="old_pattern",
            keys_invalidated=1,
            duration=0.01,
            timestamp=current_time - 3700  # More than 1 hour ago
        )
        self.monitor.invalidation_events.append(old_event)
        
        # Add some recent invalidations
        for i in range(3):
            self.monitor.record_invalidation_event(
                pattern=f"recent_pattern_{i}",
                keys_invalidated=1,
                duration=0.01
            )
        
        recent_count = self.monitor._get_invalidations_in_last_hour()
        assert recent_count == 3  # Only the recent ones

    def test_get_invalidation_frequency_stats_empty(self):
        """Test invalidation frequency stats with no invalidations."""
        stats = self.monitor.get_invalidation_frequency_stats()
        
        assert stats["no_invalidations"] is True
        assert stats["total_invalidations"] == 0
        assert stats["total_keys_invalidated"] == 0
        assert "warning_threshold_per_hour" in stats
        assert "critical_threshold_per_hour" in stats

    def test_get_invalidation_frequency_stats_with_data(self):
        """Test invalidation frequency stats with sample data."""
        # Add various invalidation events
        patterns = ["pattern_a", "pattern_b", "pattern_a", "pattern_c", "pattern_a"]
        types = ["manual", "automatic", "manual", "ttl_expired", "manual"]
        
        for i, (pattern, inv_type) in enumerate(zip(patterns, types)):
            self.monitor.record_invalidation_event(
                pattern=pattern,
                keys_invalidated=i + 1,
                duration=0.01 * (i + 1),
                invalidation_type=inv_type,
                operation_context=f"context_{i}"
            )
        
        stats = self.monitor.get_invalidation_frequency_stats()
        
        # Check basic stats
        assert stats["total_invalidations"] == 5
        assert stats["total_keys_invalidated"] == 15  # 1+2+3+4+5
        
        # Check rates
        assert stats["rates"]["last_hour"] == 5
        assert stats["rates"]["last_24_hours"] == 5
        
        # Check patterns
        assert stats["patterns"]["most_common_patterns"]["pattern_a"] == 3
        assert stats["patterns"]["most_common_patterns"]["pattern_b"] == 1
        assert stats["patterns"]["most_common_patterns"]["pattern_c"] == 1
        
        # Check types
        assert stats["patterns"]["invalidation_types"]["manual"] == 3
        assert stats["patterns"]["invalidation_types"]["automatic"] == 1
        assert stats["patterns"]["invalidation_types"]["ttl_expired"] == 1
        
        # Check efficiency
        assert stats["efficiency"]["avg_keys_per_invalidation"] == 3.0
        assert stats["efficiency"]["avg_duration"] > 0
        assert stats["efficiency"]["max_duration"] == 0.05

    def test_get_invalidation_recommendations_empty(self):
        """Test invalidation recommendations with no data."""
        recommendations = self.monitor.get_invalidation_recommendations()
        assert recommendations == []

    def test_get_invalidation_recommendations_high_frequency(self):
        """Test invalidation recommendations for high frequency."""
        # Set low threshold for testing
        self.monitor.invalidation_rate_warning_per_hour = 2
        
        # Add enough invalidations to trigger warning
        for i in range(3):
            self.monitor.record_invalidation_event(
                pattern=f"pattern_{i}",
                keys_invalidated=1,
                duration=0.01
            )
        
        recommendations = self.monitor.get_invalidation_recommendations()
        
        # Should have high frequency recommendation
        high_freq_rec = next((r for r in recommendations if r["issue"] == "High invalidation frequency"), None)
        assert high_freq_rec is not None
        assert high_freq_rec["severity"] == "warning"
        assert "times per hour" in high_freq_rec["message"]
        assert len(high_freq_rec["suggestions"]) > 0

    def test_get_invalidation_recommendations_dominant_pattern(self):
        """Test invalidation recommendations for dominant pattern."""
        # Add many invalidations with same pattern
        for i in range(10):
            self.monitor.record_invalidation_event(
                pattern="dominant_pattern",
                keys_invalidated=1,
                duration=0.01
            )
        
        # Add one with different pattern
        self.monitor.record_invalidation_event(
            pattern="other_pattern",
            keys_invalidated=1,
            duration=0.01
        )
        
        recommendations = self.monitor.get_invalidation_recommendations()
        
        # Should have dominant pattern recommendation
        dominant_rec = next((r for r in recommendations if r["issue"] == "Dominant invalidation pattern"), None)
        assert dominant_rec is not None
        assert dominant_rec["severity"] == "info"
        assert "dominant_pattern" in dominant_rec["message"]

    def test_get_invalidation_recommendations_low_efficiency(self):
        """Test invalidation recommendations for low efficiency."""
        # Add invalidations with low key counts
        for i in range(5):
            self.monitor.record_invalidation_event(
                pattern=f"pattern_{i}",
                keys_invalidated=0,  # No keys found
                duration=0.01
            )
        
        recommendations = self.monitor.get_invalidation_recommendations()
        
        # Should have low efficiency recommendation
        low_eff_rec = next((r for r in recommendations if r["issue"] == "Low invalidation efficiency"), None)
        assert low_eff_rec is not None
        assert low_eff_rec["severity"] == "info"
        assert "0.0 keys invalidated" in low_eff_rec["message"]

    def test_get_invalidation_recommendations_high_impact(self):
        """Test invalidation recommendations for high impact."""
        # Add invalidations with high key counts
        for i in range(3):
            self.monitor.record_invalidation_event(
                pattern=f"pattern_{i}",
                keys_invalidated=150,  # High impact
                duration=0.01
            )
        
        recommendations = self.monitor.get_invalidation_recommendations()
        
        # Should have high impact recommendation
        high_impact_rec = next((r for r in recommendations if r["issue"] == "High invalidation impact"), None)
        assert high_impact_rec is not None
        assert high_impact_rec["severity"] == "warning"
        assert "150 keys invalidated" in high_impact_rec["message"]

    def test_performance_stats_includes_invalidation(self):
        """Test that performance stats include invalidation data."""
        # Add some invalidation events
        self.monitor.record_invalidation_event("test_pattern", 5, 0.02, "manual")
        
        stats = self.monitor.get_performance_stats()
        
        # Should include invalidation stats
        assert "invalidation" in stats
        assert stats["invalidation"]["total_invalidations"] == 1
        assert stats["invalidation"]["total_keys_invalidated"] == 5

    def test_export_metrics_includes_invalidation(self):
        """Test that exported metrics include invalidation events."""
        # Add some invalidation events
        self.monitor.record_invalidation_event("test_pattern", 5, 0.02, "manual")
        
        metrics = self.monitor.export_metrics()
        
        # Should include invalidation events
        assert "invalidation_events" in metrics
        assert "total_invalidations" in metrics
        assert "total_keys_invalidated" in metrics
        assert len(metrics["invalidation_events"]) == 1
        assert metrics["total_invalidations"] == 1
        assert metrics["total_keys_invalidated"] == 5

    def test_reset_stats_includes_invalidation(self):
        """Test that reset clears invalidation data."""
        # Add some invalidation events
        self.monitor.record_invalidation_event("test_pattern", 5, 0.02, "manual")
        
        assert len(self.monitor.invalidation_events) == 1
        assert self.monitor.total_invalidations == 1
        assert self.monitor.total_keys_invalidated == 5
        
        # Reset stats
        self.monitor.reset_stats()
        
        # Should be cleared
        assert len(self.monitor.invalidation_events) == 0
        assert self.monitor.total_invalidations == 0
        assert self.monitor.total_keys_invalidated == 0

    def test_integration_workflow(self):
        """Test a complete workflow with multiple operations including memory tracking."""
        # Simulate a typical cache workflow
        
        # 1. Key generation for various operations
        self.monitor.record_key_generation_time(0.01, 500, "summarize")
        self.monitor.record_key_generation_time(0.02, 5000, "sentiment")
        self.monitor.record_key_generation_time(0.30, 10000, "key_points")  # Slow
        
        # 2. Cache operations with hits and misses
        self.monitor.record_cache_operation_time("get", 0.02, False, 500)  # Miss
        self.monitor.record_cache_operation_time("set", 0.04, False, 500)  # Store result
        self.monitor.record_cache_operation_time("get", 0.01, True, 500)   # Hit
        
        # 3. Compression for large responses
        self.monitor.record_compression_ratio(2000, 1200, 0.02, "summarize")
        self.monitor.record_compression_ratio(5000, 2000, 0.05, "key_points")
        
        # 4. Memory usage tracking
        memory_cache1 = {"key1": {"data": "value1"}}
        memory_cache2 = {"key1": {"data": "value1"}, "key2": {"data": "value2"}}
        self.monitor.record_memory_usage(memory_cache1)
        self.monitor.record_memory_usage(memory_cache2)
        
        # 5. Invalidation event
        self.monitor.record_invalidation_event("test_pattern", 5, 0.02, "manual")
        
        # Get comprehensive stats
        stats = self.monitor.get_performance_stats()
        
        # Verify overall health
        assert stats["cache_hit_rate"] == 33.33333333333333  # 1 hit out of 3 operations
        assert stats["key_generation"]["slow_operations"] == 1
        assert stats["compression"]["overall_savings_percent"] > 40  # Good compression
        assert "memory_usage" in stats
        
        # Check memory usage stats
        memory_stats = stats["memory_usage"]
        assert memory_stats["current"]["memory_cache_entry_count"] == 2  # Latest measurement
        assert memory_stats["trends"]["total_measurements"] == 2
        
        # Check slow operations
        slow_ops = self.monitor.get_recent_slow_operations()
        assert len(slow_ops["key_generation"]) >= 1  # At least the 0.30s operation
        
        # Check memory warnings
        warnings = self.monitor.get_memory_warnings()
        # Should be no warnings for small test data
        critical_warnings = [w for w in warnings if w["severity"] == "critical"]
        assert len(critical_warnings) == 0
        
        # Export for analysis
        exported = self.monitor.export_metrics()
        assert len(exported["key_generation_times"]) == 3
        assert len(exported["cache_operation_times"]) == 3
        assert len(exported["compression_ratios"]) == 2
        assert len(exported["memory_usage_measurements"]) == 2
        assert len(exported["invalidation_events"]) == 1
        assert exported["total_invalidations"] == 1
        assert exported["total_keys_invalidated"] == 5


class TestCachePerformanceMonitorDataRecording:
    """Additional comprehensive tests for data recording functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = CachePerformanceMonitor(retention_hours=1, max_measurements=100)
    
    def test_record_key_generation_time_with_minimal_data(self):
        """Test recording key generation time with minimal required data."""
        self.monitor.record_key_generation_time(
            duration=0.025,
            text_length=250
        )
        
        assert len(self.monitor.key_generation_times) == 1
        metric = self.monitor.key_generation_times[0]
        assert metric.duration == 0.025
        assert metric.text_length == 250
        assert metric.operation_type == ""  # Default empty
        assert metric.additional_data == {}  # Default empty
        assert isinstance(metric.timestamp, float)
        assert metric.timestamp > 0
    
    def test_record_key_generation_time_with_full_data(self):
        """Test recording key generation time with all optional data."""
        additional_data = {
            "user_id": "test_user",
            "request_id": "req_123",
            "text_hash": "abc123",
            "complexity": "high"
        }
        
        self.monitor.record_key_generation_time(
            duration=0.075,
            text_length=5000,
            operation_type="key_points",
            additional_data=additional_data
        )
        
        assert len(self.monitor.key_generation_times) == 1
        metric = self.monitor.key_generation_times[0]
        assert metric.duration == 0.075
        assert metric.text_length == 5000
        assert metric.operation_type == "key_points"
        assert metric.additional_data == additional_data
        
    def test_record_multiple_key_generation_times(self):
        """Test recording multiple key generation times preserves order."""
        durations = [0.01, 0.05, 0.02, 0.08]
        text_lengths = [100, 500, 200, 800]
        operations = ["summarize", "sentiment", "qa", "key_points"]
        
        for duration, text_length, operation in zip(durations, text_lengths, operations):
            self.monitor.record_key_generation_time(duration, text_length, operation)
        
        assert len(self.monitor.key_generation_times) == 4
        
        # Verify order is preserved
        for i, (expected_duration, expected_length, expected_op) in enumerate(zip(durations, text_lengths, operations)):
            metric = self.monitor.key_generation_times[i]
            assert metric.duration == expected_duration
            assert metric.text_length == expected_length
            assert metric.operation_type == expected_op
    
    def test_record_cache_operation_time_all_operation_types(self):
        """Test recording cache operation times for different operation types."""
        operations = [
            ("get", True, 1),   # Cache hit
            ("get", False, 0),  # Cache miss
            ("set", False, 0),  # Set operation (hit/miss irrelevant)
            ("delete", False, 0),  # Delete operation
            ("invalidate", False, 0)  # Invalidate operation
        ]
        
        for i, (operation, cache_hit, expected_hits) in enumerate(operations):
            self.monitor.record_cache_operation_time(
                operation=operation,
                duration=0.01 * (i + 1),
                cache_hit=cache_hit,
                text_length=100 * (i + 1),
                additional_data={"test_id": i}
            )
        
        assert len(self.monitor.cache_operation_times) == 5
        assert self.monitor.total_operations == 5
        assert self.monitor.cache_hits == 1  # Only one "get" with cache_hit=True
        assert self.monitor.cache_misses == 1  # Only one "get" with cache_hit=False
        
        # Verify each operation was recorded correctly
        for i, (expected_op, _, _) in enumerate(operations):
            metric = self.monitor.cache_operation_times[i]
            assert metric.operation_type == expected_op
            assert metric.duration == 0.01 * (i + 1)
            assert metric.text_length == 100 * (i + 1)
            assert metric.additional_data == {"test_id": i}
    
    def test_record_compression_ratio_edge_cases(self):
        """Test recording compression ratios with edge cases."""
        test_cases = [
            # (original_size, compressed_size, expected_ratio, operation_type)
            (1000, 500, 0.5, "summarize"),     # 50% compression
            (2000, 2000, 1.0, "sentiment"),   # No compression
            (500, 600, 1.2, "qa"),            # Expansion (rare but possible)
            (1, 1, 1.0, "key_points"),        # Tiny data
            (1000000, 100000, 0.1, "large"),  # Very good compression
        ]
        
        for original, compressed, expected_ratio, operation in test_cases:
            self.monitor.record_compression_ratio(
                original_size=original,
                compressed_size=compressed,
                compression_time=0.01,
                operation_type=operation
            )
        
        assert len(self.monitor.compression_ratios) == 5
        
        for i, (original, compressed, expected_ratio, operation) in enumerate(test_cases):
            metric = self.monitor.compression_ratios[i]
            assert metric.original_size == original
            assert metric.compressed_size == compressed
            assert abs(metric.compression_ratio - expected_ratio) < 0.001
            assert metric.operation_type == operation
            assert metric.compression_time == 0.01
    
    def test_record_compression_ratio_zero_original_size(self):
        """Test recording compression ratio with zero original size."""
        self.monitor.record_compression_ratio(
            original_size=0,
            compressed_size=0,
            compression_time=0.001,
            operation_type="empty"
        )
        
        assert len(self.monitor.compression_ratios) == 1
        metric = self.monitor.compression_ratios[0]
        assert metric.compression_ratio == 1.0  # Should default to 1.0
    
    def test_record_memory_usage_with_empty_cache(self):
        """Test recording memory usage with empty memory cache."""
        empty_cache = {}
        metric = self.monitor.record_memory_usage(empty_cache)
        
        assert len(self.monitor.memory_usage_measurements) == 1
        assert metric.memory_cache_entry_count == 0
        assert metric.memory_cache_size_bytes >= 0  # Even empty dict has some size
        assert metric.avg_entry_size_bytes == 0.0
        assert metric.total_cache_size_bytes >= 0
        assert metric.cache_entry_count == 0
    
    def test_record_memory_usage_with_redis_stats(self):
        """Test recording memory usage with Redis statistics."""
        memory_cache = {"key1": {"data": "test"}}
        redis_stats = {
            "memory_used_bytes": 1024 * 1024,  # 1MB
            "keys": 50
        }
        
        metric = self.monitor.record_memory_usage(memory_cache, redis_stats)
        
        assert len(self.monitor.memory_usage_measurements) == 1
        assert metric.cache_entry_count == 51  # 1 from memory + 50 from Redis
        assert metric.total_cache_size_bytes > 1024 * 1024  # Memory cache + Redis
        assert metric.memory_cache_entry_count == 1
    
    def test_record_memory_usage_threshold_warnings(self):
        """Test memory usage recording with threshold warnings."""
        # Set low thresholds for testing
        monitor = CachePerformanceMonitor(
            memory_warning_threshold_bytes=1000,
            memory_critical_threshold_bytes=2000
        )
        
        # Create a memory cache that will trigger warnings
        large_cache = {}
        for i in range(100):
            large_cache[f"key_{i}"] = {"data": "x" * 100}  # Large entries
        
        with patch('app.infrastructure.cache.monitoring.logger') as mock_logger:
            metric = monitor.record_memory_usage(large_cache)
            
            # Should trigger warning or critical logging
            assert mock_logger.warning.called or mock_logger.error.called
            assert metric.warning_threshold_reached
    
    def test_record_invalidation_event_full_data(self):
        """Test recording invalidation event with all optional data."""
        additional_data = {
            "user_id": "admin_user",
            "request_context": "bulk_update",
            "affected_operations": ["summarize", "sentiment"]
        }
        
        self.monitor.record_invalidation_event(
            pattern="test:*:cache",
            keys_invalidated=25,
            duration=0.125,
            invalidation_type="automatic",
            operation_context="scheduled_cleanup",
            additional_data=additional_data
        )
        
        assert len(self.monitor.invalidation_events) == 1
        assert self.monitor.total_invalidations == 1
        assert self.monitor.total_keys_invalidated == 25
        
        event = self.monitor.invalidation_events[0]
        assert event.pattern == "test:*:cache"
        assert event.keys_invalidated == 25
        assert event.duration == 0.125
        assert event.invalidation_type == "automatic"
        assert event.operation_context == "scheduled_cleanup"
        assert event.additional_data == additional_data
    
    def test_record_invalidation_event_minimal_data(self):
        """Test recording invalidation event with minimal data."""
        self.monitor.record_invalidation_event(
            pattern="simple_pattern",
            keys_invalidated=1,
            duration=0.01
        )
        
        assert len(self.monitor.invalidation_events) == 1
        event = self.monitor.invalidation_events[0]
        assert event.pattern == "simple_pattern"
        assert event.keys_invalidated == 1
        assert event.duration == 0.01
        assert event.invalidation_type == "manual"  # Default
        assert event.operation_context == ""  # Default
        assert event.additional_data == {}  # Default
    
    def test_record_zero_keys_invalidated(self):
        """Test recording invalidation event with zero keys invalidated."""
        self.monitor.record_invalidation_event(
            pattern="nonexistent:*",
            keys_invalidated=0,
            duration=0.005,
            invalidation_type="pattern_miss"
        )
        
        assert len(self.monitor.invalidation_events) == 1
        assert self.monitor.total_invalidations == 1
        assert self.monitor.total_keys_invalidated == 0
        
        event = self.monitor.invalidation_events[0]
        assert event.keys_invalidated == 0
        assert event.invalidation_type == "pattern_miss"
    
    def test_data_recording_preserves_timestamps(self):
        """Test that all data recording methods preserve proper timestamps."""
        import time
        
        start_time = time.time()
        
        # Record various types of data
        self.monitor.record_key_generation_time(0.01, 100)
        time.sleep(0.001)  # Small delay
        self.monitor.record_cache_operation_time("get", 0.01, True, 100)
        time.sleep(0.001)
        self.monitor.record_compression_ratio(1000, 500, 0.01)
        time.sleep(0.001)
        self.monitor.record_memory_usage({})
        time.sleep(0.001)
        self.monitor.record_invalidation_event("test", 1, 0.01)
        
        end_time = time.time()
        
        # Check that all timestamps are within the test time window
        assert start_time <= self.monitor.key_generation_times[0].timestamp <= end_time
        assert start_time <= self.monitor.cache_operation_times[0].timestamp <= end_time
        assert start_time <= self.monitor.compression_ratios[0].timestamp <= end_time
        assert start_time <= self.monitor.memory_usage_measurements[0].timestamp <= end_time
        assert start_time <= self.monitor.invalidation_events[0].timestamp <= end_time
        
        # Check that timestamps are in chronological order
        timestamps = [
            self.monitor.key_generation_times[0].timestamp,
            self.monitor.cache_operation_times[0].timestamp,
            self.monitor.compression_ratios[0].timestamp,
            self.monitor.memory_usage_measurements[0].timestamp,
            self.monitor.invalidation_events[0].timestamp
        ]
        
        # Timestamps should be in increasing order (with small tolerance for timing)
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i-1] - 0.001  # Small tolerance
    
    def test_data_recording_thread_safety_simulation(self):
        """Simulate concurrent data recording to test basic thread safety."""
        import threading
        import time
        
        results = []
        
        def record_data(thread_id):
            """Function to record data from a thread."""
            for i in range(10):
                self.monitor.record_key_generation_time(
                    duration=0.001 * thread_id,
                    text_length=100 * thread_id,
                    operation_type=f"thread_{thread_id}",
                    additional_data={"thread_id": thread_id, "iteration": i}
                )
                time.sleep(0.001)  # Small delay
            results.append(thread_id)
        
        # Create multiple threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=record_data, args=(thread_id,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all data was recorded
        assert len(self.monitor.key_generation_times) == 30  # 3 threads * 10 operations
        assert len(results) == 3  # All threads completed
        
        # Verify data integrity - each thread's data should be present
        thread_data = {}
        for metric in self.monitor.key_generation_times:
            thread_id = metric.additional_data["thread_id"]
            if thread_id not in thread_data:
                thread_data[thread_id] = []
            thread_data[thread_id].append(metric)
        
        # Each thread should have 10 entries
        assert len(thread_data) == 3
        for thread_id, metrics in thread_data.items():
            assert len(metrics) == 10
            for metric in metrics:
                assert metric.operation_type == f"thread_{thread_id}"
                assert metric.additional_data["thread_id"] == thread_id


class TestCachePerformanceMonitorStatisticCalculations:
    """Comprehensive tests for statistic calculation functionality in CachePerformanceMonitor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = CachePerformanceMonitor(retention_hours=1, max_measurements=100)
    
    def test_calculate_hit_rate_with_no_operations(self):
        """Test hit rate calculation with no operations."""
        hit_rate = self.monitor._calculate_hit_rate()
        assert hit_rate == 0.0
    
    def test_calculate_hit_rate_with_operations(self):
        """Test hit rate calculation with various operation scenarios."""
        # Test 100% hit rate
        self.monitor.cache_hits = 10
        self.monitor.total_operations = 10
        assert self.monitor._calculate_hit_rate() == 100.0
        
        # Test 50% hit rate
        self.monitor.cache_hits = 5
        self.monitor.cache_misses = 5
        self.monitor.total_operations = 10
        assert self.monitor._calculate_hit_rate() == 50.0
        
        # Test 0% hit rate
        self.monitor.cache_hits = 0
        self.monitor.cache_misses = 10
        self.monitor.total_operations = 10
        assert self.monitor._calculate_hit_rate() == 0.0
        
        # Test fractional hit rate
        self.monitor.cache_hits = 33
        self.monitor.cache_misses = 67
        self.monitor.total_operations = 100
        assert self.monitor._calculate_hit_rate() == 33.0
    
    def test_key_generation_statistics_calculations(self):
        """Test key generation statistics calculations with various data sets."""
        # Add a diverse set of key generation measurements
        test_data = [
            (0.001, 100, "summarize"),     # Very fast, small text
            (0.050, 1000, "sentiment"),   # Medium speed, medium text
            (0.200, 5000, "key_points"),  # Slow, large text
            (0.005, 500, "qa"),           # Fast, small-medium text
            (0.150, 3000, "summarize"),   # Slow, large text
            (0.025, 2000, "sentiment"),   # Medium, medium-large text
            (0.002, 200, "questions"),    # Very fast, small text
            (0.300, 8000, "key_points"),  # Very slow, very large text
        ]
        
        for duration, text_length, operation in test_data:
            self.monitor.record_key_generation_time(duration, text_length, operation)
        
        stats = self.monitor.get_performance_stats()
        key_gen_stats = stats["key_generation"]
        
        # Verify total operations count
        assert key_gen_stats["total_operations"] == 8
        
        # Verify duration calculations
        durations = [d[0] for d in test_data]
        expected_avg = sum(durations) / len(durations)
        expected_max = max(durations)
        expected_min = min(durations)
        
        assert abs(key_gen_stats["avg_duration"] - expected_avg) < 0.001
        assert key_gen_stats["max_duration"] == expected_max
        assert key_gen_stats["min_duration"] == expected_min
        
        # Verify text length calculations
        text_lengths = [d[1] for d in test_data]
        expected_avg_length = sum(text_lengths) / len(text_lengths)
        expected_max_length = max(text_lengths)
        
        assert abs(key_gen_stats["avg_text_length"] - expected_avg_length) < 0.1
        assert key_gen_stats["max_text_length"] == expected_max_length
        
        # Verify slow operations count (threshold is 0.1s)
        slow_operations = [d for d in durations if d > 0.1]
        assert key_gen_stats["slow_operations"] == len(slow_operations)
    
    def test_cache_operation_statistics_calculations(self):
        """Test cache operation statistics calculations with various operation types."""
        # Add diverse cache operation measurements
        operations_data = [
            ("get", 0.005, True, 500),     # Fast get hit
            ("get", 0.008, False, 1000),   # Slow get miss
            ("get", 0.003, True, 200),     # Very fast get hit
            ("set", 0.015, False, 800),    # Slow set operation
            ("set", 0.010, False, 600),    # Medium set operation
            ("get", 0.012, False, 1500),   # Slow get miss
            ("delete", 0.004, False, 0),   # Fast delete operation
            ("get", 0.002, True, 300),     # Very fast get hit
        ]
        
        for operation, duration, cache_hit, text_length in operations_data:
            self.monitor.record_cache_operation_time(operation, duration, cache_hit, text_length)
        
        stats = self.monitor.get_performance_stats()
        cache_ops_stats = stats["cache_operations"]
        
        # Verify total operations count
        assert cache_ops_stats["total_operations"] == 8
        
        # Verify duration calculations
        durations = [d[1] for d in operations_data]
        expected_avg = sum(durations) / len(durations)
        expected_max = max(durations)
        expected_min = min(durations)
        
        assert abs(cache_ops_stats["avg_duration"] - expected_avg) < 0.001
        assert cache_ops_stats["max_duration"] == expected_max
        assert cache_ops_stats["min_duration"] == expected_min
        
        # Verify slow operations count (threshold is 0.05s)
        slow_operations = [d for d in durations if d > 0.05]
        assert cache_ops_stats["slow_operations"] == len(slow_operations)
        
        # Verify operation type breakdown
        by_type = cache_ops_stats["by_operation_type"]
        
        # Count get operations
        get_ops = [op for op in operations_data if op[0] == "get"]
        assert by_type["get"]["count"] == len(get_ops)
        get_durations = [op[1] for op in get_ops]
        assert abs(by_type["get"]["avg_duration"] - (sum(get_durations) / len(get_durations))) < 0.001
        assert by_type["get"]["max_duration"] == max(get_durations)
        
        # Count set operations
        set_ops = [op for op in operations_data if op[0] == "set"]
        assert by_type["set"]["count"] == len(set_ops)
        set_durations = [op[1] for op in set_ops]
        assert abs(by_type["set"]["avg_duration"] - (sum(set_durations) / len(set_durations))) < 0.001
        assert by_type["set"]["max_duration"] == max(set_durations)
        
        # Count delete operations
        delete_ops = [op for op in operations_data if op[0] == "delete"]
        assert by_type["delete"]["count"] == len(delete_ops)
    
    def test_compression_statistics_calculations(self):
        """Test compression statistics calculations with various compression scenarios."""
        # Add diverse compression measurements
        compression_data = [
            (1000, 600, 0.010, "summarize"),    # 40% compression
            (2000, 1000, 0.020, "sentiment"),   # 50% compression  
            (5000, 1500, 0.050, "key_points"),  # 70% compression (very good)
            (500, 450, 0.005, "qa"),            # 10% compression (poor)
            (10000, 3000, 0.100, "summarize"),  # 70% compression (very good)
            (1500, 1350, 0.015, "questions"),   # 10% compression (poor)
            (3000, 900, 0.030, "sentiment"),    # 70% compression (very good)
        ]
        
        for original, compressed, comp_time, operation in compression_data:
            self.monitor.record_compression_ratio(original, compressed, comp_time, operation)
        
        stats = self.monitor.get_performance_stats()
        compression_stats = stats["compression"]
        
        # Verify total operations count
        assert compression_stats["total_operations"] == 7
        
        # Calculate expected values
        ratios = [compressed / original for original, compressed, _, _ in compression_data]
        comp_times = [comp_time for _, _, comp_time, _ in compression_data]
        original_sizes = [original for original, _, _, _ in compression_data]
        compressed_sizes = [compressed for _, compressed, _, _ in compression_data]
        
        total_original = sum(original_sizes)
        total_compressed = sum(compressed_sizes)
        total_saved = total_original - total_compressed
        
        # Verify compression ratio calculations
        expected_avg_ratio = sum(ratios) / len(ratios)
        expected_best_ratio = min(ratios)  # Best = lowest ratio
        expected_worst_ratio = max(ratios)  # Worst = highest ratio
        
        assert abs(compression_stats["avg_compression_ratio"] - expected_avg_ratio) < 0.001
        assert compression_stats["best_compression_ratio"] == expected_best_ratio
        assert compression_stats["worst_compression_ratio"] == expected_worst_ratio
        
        # Verify compression time calculations
        expected_avg_time = sum(comp_times) / len(comp_times)
        expected_max_time = max(comp_times)
        
        assert abs(compression_stats["avg_compression_time"] - expected_avg_time) < 0.001
        assert compression_stats["max_compression_time"] == expected_max_time
        
        # Verify total bytes calculations
        assert compression_stats["total_bytes_processed"] == total_original
        assert compression_stats["total_bytes_saved"] == total_saved
        
        expected_savings_percent = (total_saved / total_original) * 100
        assert abs(compression_stats["overall_savings_percent"] - expected_savings_percent) < 0.1
    
    def test_memory_usage_statistics_calculations(self):
        """Test memory usage statistics calculations with multiple measurements."""
        # Create test memory cache data with increasing sizes
        memory_cache_data = [
            {"key1": {"data": "small"}},
            {"key1": {"data": "small"}, "key2": {"data": "medium" * 10}},
            {"key1": {"data": "small"}, "key2": {"data": "medium" * 10}, "key3": {"data": "large" * 50}},
            {"key1": {"data": "small"}, "key2": {"data": "medium" * 10}},  # Decrease
            {"key1": {"data": "updated"}, "key2": {"data": "medium" * 10}, "key3": {"data": "large" * 50}, "key4": {"data": "new"}},
        ]
        
        # Record memory usage measurements
        for cache_data in memory_cache_data:
            self.monitor.record_memory_usage(cache_data)
        
        stats = self.monitor.get_performance_stats()
        memory_stats = stats["memory_usage"]
        
        # Verify current stats (latest measurement)
        current = memory_stats["current"]
        assert current["memory_cache_entry_count"] == 4  # Last cache had 4 entries
        assert current["cache_entry_count"] == 4  # No Redis stats, so same as memory cache
        assert current["total_cache_size_mb"] > 0
        assert current["avg_entry_size_bytes"] > 0
        
        # Verify trends calculations
        trends = memory_stats["trends"]
        assert trends["total_measurements"] == 5
        assert trends["avg_total_cache_size_mb"] > 0
        assert trends["max_total_cache_size_mb"] > 0
        assert trends["avg_memory_cache_size_mb"] > 0
        assert trends["avg_entry_count"] > 0
        assert trends["max_entry_count"] == 4  # Maximum from the measurements
        
        # Verify thresholds
        thresholds = memory_stats["thresholds"]
        assert thresholds["warning_threshold_mb"] == self.monitor.memory_warning_threshold_bytes / 1024 / 1024
        assert thresholds["critical_threshold_mb"] == self.monitor.memory_critical_threshold_bytes / 1024 / 1024
    
    def test_invalidation_statistics_calculations(self):
        """Test invalidation statistics calculations with various patterns and types."""
        # Add diverse invalidation events
        invalidation_data = [
            ("pattern_a:*", 10, 0.020, "manual", "user_action"),
            ("pattern_b:*", 5, 0.015, "automatic", "ttl_expired"),
            ("pattern_a:*", 15, 0.025, "manual", "bulk_update"),
            ("pattern_c:*", 0, 0.005, "automatic", "pattern_miss"),
            ("pattern_a:*", 8, 0.018, "manual", "user_action"),
            ("pattern_d:*", 25, 0.040, "manual", "cleanup"),
            ("pattern_b:*", 3, 0.012, "automatic", "ttl_expired"),
        ]
        
        for pattern, keys, duration, inv_type, context in invalidation_data:
            self.monitor.record_invalidation_event(pattern, keys, duration, inv_type, context)
        
        stats = self.monitor.get_performance_stats()
        invalidation_stats = stats["invalidation"]
        
        # Verify total counts
        expected_total_invalidations = len(invalidation_data)
        expected_total_keys = sum(keys for _, keys, _, _, _ in invalidation_data)
        
        assert invalidation_stats["total_invalidations"] == expected_total_invalidations
        assert invalidation_stats["total_keys_invalidated"] == expected_total_keys
        
        # Verify rates (all events are recent)
        assert invalidation_stats["rates"]["last_hour"] == expected_total_invalidations
        assert invalidation_stats["rates"]["last_24_hours"] == expected_total_invalidations
        
        # Verify pattern analysis
        patterns = invalidation_stats["patterns"]["most_common_patterns"]
        assert patterns["pattern_a:*"] == 3  # Appears 3 times
        assert patterns["pattern_b:*"] == 2  # Appears 2 times
        assert patterns["pattern_c:*"] == 1  # Appears 1 time
        assert patterns["pattern_d:*"] == 1  # Appears 1 time
        
        # Verify invalidation type counts
        types = invalidation_stats["patterns"]["invalidation_types"]
        assert types["manual"] == 4    # 4 manual invalidations
        assert types["automatic"] == 3  # 3 automatic invalidations
        
        # Verify efficiency calculations
        efficiency = invalidation_stats["efficiency"]
        expected_avg_keys = expected_total_keys / expected_total_invalidations
        assert abs(efficiency["avg_keys_per_invalidation"] - expected_avg_keys) < 0.1
        
        durations = [duration for _, _, duration, _, _ in invalidation_data]
        expected_avg_duration = sum(durations) / len(durations)
        expected_max_duration = max(durations)
        
        assert abs(efficiency["avg_duration"] - expected_avg_duration) < 0.001
        assert efficiency["max_duration"] == expected_max_duration
    
    def test_statistics_with_edge_cases(self):
        """Test statistics calculations with edge cases and empty data sets."""
        # Test with no data - should return basic structure without optional sections
        empty_stats = self.monitor.get_performance_stats()
        
        assert empty_stats["cache_hit_rate"] == 0.0
        assert empty_stats["total_cache_operations"] == 0
        assert empty_stats["cache_hits"] == 0
        assert empty_stats["cache_misses"] == 0
        assert "key_generation" not in empty_stats
        assert "cache_operations" not in empty_stats
        assert "compression" not in empty_stats
        assert "memory_usage" not in empty_stats
        assert "invalidation" not in empty_stats
        
        # Test with single data point for each metric type
        self.monitor.record_key_generation_time(0.050, 1000, "test")
        self.monitor.record_cache_operation_time("get", 0.020, True, 500)
        self.monitor.record_compression_ratio(2000, 1000, 0.015, "test")
        self.monitor.record_memory_usage({"key": "value"})
        self.monitor.record_invalidation_event("test:*", 5, 0.010, "manual")
        
        single_point_stats = self.monitor.get_performance_stats()
        
        # With single data points, avg = median = min = max
        key_gen = single_point_stats["key_generation"]
        assert key_gen["avg_duration"] == key_gen["median_duration"]
        assert key_gen["avg_duration"] == key_gen["max_duration"]
        assert key_gen["avg_duration"] == key_gen["min_duration"]
        assert key_gen["avg_duration"] == 0.050
        
        cache_ops = single_point_stats["cache_operations"]
        assert cache_ops["avg_duration"] == cache_ops["median_duration"]
        assert cache_ops["avg_duration"] == cache_ops["max_duration"]
        assert cache_ops["avg_duration"] == cache_ops["min_duration"]
        assert cache_ops["avg_duration"] == 0.020
        
        compression = single_point_stats["compression"]
        assert compression["avg_compression_ratio"] == compression["median_compression_ratio"]
        assert compression["avg_compression_ratio"] == compression["best_compression_ratio"]
        assert compression["avg_compression_ratio"] == compression["worst_compression_ratio"]
        assert compression["avg_compression_ratio"] == 0.5  # 1000/2000
    
    def test_statistics_precision_and_accuracy(self):
        """Test that statistical calculations maintain precision with various data ranges."""
        # Test with very small numbers
        small_durations = [0.0001, 0.0002, 0.0003, 0.0004, 0.0005]
        for i, duration in enumerate(small_durations):
            self.monitor.record_key_generation_time(duration, 100 * (i + 1), "test")
        
        # Test with very large numbers
        large_sizes = [1000000, 2000000, 3000000, 4000000, 5000000]
        for i, size in enumerate(large_sizes):
            self.monitor.record_compression_ratio(size, size // 2, 0.001 * (i + 1), "test")
        
        stats = self.monitor.get_performance_stats()
        
        # Verify small number precision
        key_gen = stats["key_generation"]
        expected_avg_small = sum(small_durations) / len(small_durations)
        assert abs(key_gen["avg_duration"] - expected_avg_small) < 0.0001
        
        # Verify large number accuracy
        compression = stats["compression"]
        expected_total_original = sum(large_sizes)
        expected_total_compressed = sum(size // 2 for size in large_sizes)
        assert compression["total_bytes_processed"] == expected_total_original
        assert compression["total_bytes_saved"] == expected_total_original - expected_total_compressed
    
    def test_statistics_with_mixed_operation_types(self):
        """Test statistics calculations with mixed operation types and patterns."""
        # Add mixed key generation operations
        operations = ["summarize", "sentiment", "qa", "key_points", "questions"]
        for i, operation in enumerate(operations * 3):  # 15 total operations
            duration = 0.01 + (i * 0.005)  # Varying durations
            text_length = 500 + (i * 100)   # Varying text lengths
            self.monitor.record_key_generation_time(duration, text_length, operation)
        
        # Add mixed cache operations  
        cache_operations = ["get", "set", "delete", "invalidate"]
        for i, operation in enumerate(cache_operations * 4):  # 16 total operations
            duration = 0.005 + (i * 0.002)
            cache_hit = operation == "get" and i % 2 == 0  # Some hits for get operations
            self.monitor.record_cache_operation_time(operation, duration, cache_hit, 200 + i * 50)
        
        stats = self.monitor.get_performance_stats()
        
        # Verify key generation operation type distribution isn't tracked in basic stats
        # (operation types are in the raw data but not aggregated in main stats)
        key_gen = stats["key_generation"]
        assert key_gen["total_operations"] == 15
        
        # Verify cache operation type breakdown
        cache_ops = stats["cache_operations"]
        assert cache_ops["total_operations"] == 16
        
        by_type = cache_ops["by_operation_type"]
        assert by_type["get"]["count"] == 4
        assert by_type["set"]["count"] == 4
        assert by_type["delete"]["count"] == 4
        assert by_type["invalidate"]["count"] == 4
        
        # Verify hit rate calculation with mixed operations
        # cache_operations = ["get", "set", "delete", "invalidate"] * 4 = 16 operations
        # get operations at indices: 0, 4, 8, 12 (all even indices)
        # cache_hit = operation == "get" and i % 2 == 0
        # All get operations are at even indices, so all 4 are hits
        # That's 4 cache hits out of 16 total operations
        expected_hit_rate = (4 / 16) * 100  # 4 hits out of 16 total operations = 25.0%
        assert abs(stats["cache_hit_rate"] - expected_hit_rate) < 0.1


class TestCachePerformanceMonitorTimeBasedEviction:
    """Comprehensive tests for time-based data eviction functionality in CachePerformanceMonitor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = CachePerformanceMonitor(retention_hours=1, max_measurements=100)
    
    def test_eviction_respects_retention_hours(self):
        """Test that data older than retention_hours is evicted."""
        import time
        from unittest.mock import patch
        
        # Mock current time to control the test
        base_time = 1000000
        
        with patch('time.time') as mock_time:
            # Set initial time
            mock_time.return_value = base_time
            
            # Add measurements at different times
            # Recent measurement (within retention)
            recent_time = base_time - 1800  # 30 minutes ago
            recent_metric = PerformanceMetric(
                duration=0.05,
                text_length=1000,
                timestamp=recent_time
            )
            self.monitor.key_generation_times.append(recent_metric)
            
            # Old measurement (outside retention - 2 hours ago)
            old_time = base_time - 7200  # 2 hours ago
            old_metric = PerformanceMetric(
                duration=0.08,
                text_length=2000,
                timestamp=old_time
            )
            self.monitor.key_generation_times.append(old_metric)
            
            # Very old measurement (outside retention - 3 hours ago)
            very_old_time = base_time - 10800  # 3 hours ago
            very_old_metric = PerformanceMetric(
                duration=0.12,
                text_length=3000,
                timestamp=very_old_time
            )
            self.monitor.key_generation_times.append(very_old_metric)
            
            # Trigger cleanup
            self.monitor._cleanup_old_measurements(self.monitor.key_generation_times)
            
            # Only recent measurement should remain
            assert len(self.monitor.key_generation_times) == 1
            assert self.monitor.key_generation_times[0].timestamp == recent_time
            assert self.monitor.key_generation_times[0].duration == 0.05
    
    def test_eviction_with_exact_boundary_conditions(self):
        """Test eviction behavior at exact retention boundary."""
        import time
        from unittest.mock import patch
        
        base_time = 1000000
        retention_seconds = self.monitor.retention_hours * 3600  # 1 hour = 3600 seconds
        
        with patch('time.time') as mock_time:
            mock_time.return_value = base_time
            
            # Add measurement exactly at retention boundary
            boundary_time = base_time - retention_seconds
            boundary_metric = PerformanceMetric(
                duration=0.05,
                text_length=1000,
                timestamp=boundary_time
            )
            self.monitor.key_generation_times.append(boundary_metric)
            
            # Add measurement just inside retention (1 second newer)
            inside_time = base_time - retention_seconds + 1
            inside_metric = PerformanceMetric(
                duration=0.06,
                text_length=1100,
                timestamp=inside_time
            )
            self.monitor.key_generation_times.append(inside_metric)
            
            # Add measurement just outside retention (1 second older)
            outside_time = base_time - retention_seconds - 1
            outside_metric = PerformanceMetric(
                duration=0.07,
                text_length=1200,
                timestamp=outside_time
            )
            self.monitor.key_generation_times.append(outside_metric)
            
            # Trigger cleanup
            self.monitor._cleanup_old_measurements(self.monitor.key_generation_times)
            
            # Only the inside measurement should remain (boundary condition: > cutoff_time)
            assert len(self.monitor.key_generation_times) == 1
            assert self.monitor.key_generation_times[0].timestamp == inside_time
            assert self.monitor.key_generation_times[0].duration == 0.06
    
    def test_eviction_across_all_measurement_types(self):
        """Test that eviction works across all types of measurements."""
        import time
        from unittest.mock import patch
        
        base_time = 1000000
        
        with patch('time.time') as mock_time:
            mock_time.return_value = base_time
            
            # Add old and new measurements for each type
            old_time = base_time - 7200  # 2 hours ago
            recent_time = base_time - 1800  # 30 minutes ago
            
            # Key generation times
            self.monitor.key_generation_times.extend([
                PerformanceMetric(0.05, 1000, old_time, "old"),
                PerformanceMetric(0.06, 1100, recent_time, "recent")
            ])
            
            # Cache operation times
            self.monitor.cache_operation_times.extend([
                PerformanceMetric(0.02, 500, old_time, "get"),
                PerformanceMetric(0.03, 600, recent_time, "set")
            ])
            
            # Compression ratios
            self.monitor.compression_ratios.extend([
                CompressionMetric(1000, 600, 0.6, 0.01, old_time, "old"),
                CompressionMetric(2000, 1000, 0.5, 0.02, recent_time, "recent")
            ])
            
            # Memory usage measurements
            self.monitor.memory_usage_measurements.extend([
                MemoryUsageMetric(1000, 10, 100.0, 800, 8, 50.0, old_time, 2.0, False),
                MemoryUsageMetric(2000, 20, 100.0, 1600, 16, 60.0, recent_time, 4.0, False)
            ])
            
            # Invalidation events
            self.monitor.invalidation_events.extend([
                InvalidationMetric("old:*", 5, 0.01, old_time, "manual"),
                InvalidationMetric("recent:*", 10, 0.02, recent_time, "automatic")
            ])
            
            # Trigger cleanup for all measurement types
            self.monitor._cleanup_old_measurements(self.monitor.key_generation_times)
            self.monitor._cleanup_old_measurements(self.monitor.cache_operation_times)
            self.monitor._cleanup_old_measurements(self.monitor.compression_ratios)
            self.monitor._cleanup_old_measurements(self.monitor.memory_usage_measurements)
            self.monitor._cleanup_old_measurements(self.monitor.invalidation_events)
            
            # Verify only recent measurements remain for each type
            assert len(self.monitor.key_generation_times) == 1
            assert self.monitor.key_generation_times[0].operation_type == "recent"
            
            assert len(self.monitor.cache_operation_times) == 1
            assert self.monitor.cache_operation_times[0].operation_type == "set"
            
            assert len(self.monitor.compression_ratios) == 1
            assert self.monitor.compression_ratios[0].operation_type == "recent"
            
            assert len(self.monitor.memory_usage_measurements) == 1
            assert self.monitor.memory_usage_measurements[0].cache_entry_count == 20
            
            assert len(self.monitor.invalidation_events) == 1
            assert self.monitor.invalidation_events[0].invalidation_type == "automatic"
    
    def test_max_measurements_limit_eviction(self):
        """Test that eviction respects max_measurements limit even with recent data."""
        # Set a low limit for testing
        self.monitor.max_measurements = 5
        
        # Add more measurements than the limit, all recent
        current_time = time.time()
        for i in range(10):
            metric = PerformanceMetric(
                duration=0.01 * (i + 1),
                text_length=100 * (i + 1),
                timestamp=current_time + i  # All in the future to ensure they're "recent"
            )
            self.monitor.key_generation_times.append(metric)
        
        # Trigger cleanup
        self.monitor._cleanup_old_measurements(self.monitor.key_generation_times)
        
        # Should only keep the most recent measurements
        assert len(self.monitor.key_generation_times) == 5
        
        # Verify the kept measurements are the most recent ones (last 5)
        expected_durations = [0.06, 0.07, 0.08, 0.09, 0.10]  # Last 5 measurements
        actual_durations = [m.duration for m in self.monitor.key_generation_times]
        assert actual_durations == expected_durations
    
    def test_eviction_with_mixed_time_and_size_constraints(self):
        """Test eviction when both time and size constraints apply."""
        import time
        from unittest.mock import patch
        
        # Set a low max_measurements limit
        self.monitor.max_measurements = 3
        
        base_time = 1000000
        
        with patch('time.time') as mock_time:
            mock_time.return_value = base_time
            
            # Add measurements: some old, some recent, more than max limit
            measurements = [
                PerformanceMetric(0.01, 100, base_time - 7200, "very_old"),    # 2 hours ago (should be evicted by time)
                PerformanceMetric(0.02, 200, base_time - 3600, "old"),        # 1 hour ago (should be evicted by time)
                PerformanceMetric(0.03, 300, base_time - 1800, "recent_1"),   # 30 min ago (recent)
                PerformanceMetric(0.04, 400, base_time - 1200, "recent_2"),   # 20 min ago (recent)
                PerformanceMetric(0.05, 500, base_time - 600, "recent_3"),    # 10 min ago (recent)
                PerformanceMetric(0.06, 600, base_time - 300, "recent_4"),    # 5 min ago (recent)
                PerformanceMetric(0.07, 700, base_time - 60, "very_recent"),  # 1 min ago (recent)
            ]
            
            self.monitor.key_generation_times.extend(measurements)
            
            # Trigger cleanup
            self.monitor._cleanup_old_measurements(self.monitor.key_generation_times)
            
            # Should first remove old measurements by time, then limit by size
            assert len(self.monitor.key_generation_times) == 3
            
            # Should keep the 3 most recent measurements
            expected_operations = ["recent_3", "recent_4", "very_recent"]
            actual_operations = [m.operation_type for m in self.monitor.key_generation_times]
            assert actual_operations == expected_operations
    
    def test_eviction_during_get_performance_stats(self):
        """Test that eviction is triggered when getting performance stats."""
        import time
        from unittest.mock import patch
        
        base_time = 1000000
        
        with patch('time.time') as mock_time:
            mock_time.return_value = base_time
            
            # Add old and recent measurements
            old_time = base_time - 7200  # 2 hours ago
            recent_time = base_time - 1800  # 30 minutes ago
            
            self.monitor.key_generation_times.extend([
                PerformanceMetric(0.05, 1000, old_time, "old_1"),
                PerformanceMetric(0.06, 1100, old_time - 100, "old_2"),
                PerformanceMetric(0.07, 1200, recent_time, "recent_1"),
                PerformanceMetric(0.08, 1300, recent_time + 100, "recent_2")
            ])
            
            self.monitor.cache_operation_times.extend([
                PerformanceMetric(0.02, 500, old_time, "get"),
                PerformanceMetric(0.03, 600, recent_time, "set")
            ])
            
            # Initially all measurements are present
            assert len(self.monitor.key_generation_times) == 4
            assert len(self.monitor.cache_operation_times) == 2
            
            # Get performance stats should trigger cleanup
            stats = self.monitor.get_performance_stats()
            
            # Old measurements should be evicted
            assert len(self.monitor.key_generation_times) == 2
            assert len(self.monitor.cache_operation_times) == 1
            
            # Verify the stats reflect only recent data
            assert stats["key_generation"]["total_operations"] == 2
            assert stats["cache_operations"]["total_operations"] == 1
            
            # Verify the remaining measurements are the recent ones
            remaining_key_ops = [m.operation_type for m in self.monitor.key_generation_times]
            assert "recent_1" in remaining_key_ops
            assert "recent_2" in remaining_key_ops
            assert "old_1" not in remaining_key_ops
            assert "old_2" not in remaining_key_ops
    
    def test_eviction_with_different_retention_periods(self):
        """Test eviction behavior with different retention periods."""
        import time
        from unittest.mock import patch
        
        # Test with shorter retention period
        short_monitor = CachePerformanceMonitor(retention_hours=0.5, max_measurements=100)  # 30 minutes
        
        base_time = 1000000
        
        with patch('time.time') as mock_time:
            mock_time.return_value = base_time
            
            # Add measurements at different intervals
            measurements = [
                PerformanceMetric(0.01, 100, base_time - 3600, "1_hour_ago"),    # 1 hour ago
                PerformanceMetric(0.02, 200, base_time - 2700, "45_min_ago"),    # 45 minutes ago
                PerformanceMetric(0.03, 300, base_time - 1800, "30_min_ago"),    # 30 minutes ago
                PerformanceMetric(0.04, 400, base_time - 900, "15_min_ago"),     # 15 minutes ago
                PerformanceMetric(0.05, 500, base_time - 300, "5_min_ago")       # 5 minutes ago
            ]
            
            short_monitor.key_generation_times.extend(measurements)
            
            # Trigger cleanup
            short_monitor._cleanup_old_measurements(short_monitor.key_generation_times)
            
            # With 0.5 hour retention, only measurements newer than 30 minutes should remain
            assert len(short_monitor.key_generation_times) == 2
            
            remaining_operations = [m.operation_type for m in short_monitor.key_generation_times]
            assert "15_min_ago" in remaining_operations
            assert "5_min_ago" in remaining_operations
            assert "30_min_ago" not in remaining_operations  # Exactly at boundary, should be evicted
            assert "45_min_ago" not in remaining_operations
            assert "1_hour_ago" not in remaining_operations
    
    def test_eviction_with_empty_measurements_list(self):
        """Test that eviction handles empty measurements list gracefully."""
        # Test with empty list should not crash
        self.monitor._cleanup_old_measurements([])
        
        # Verify other lists are still empty
        assert len(self.monitor.key_generation_times) == 0
        assert len(self.monitor.cache_operation_times) == 0
        assert len(self.monitor.compression_ratios) == 0
        assert len(self.monitor.memory_usage_measurements) == 0
        assert len(self.monitor.invalidation_events) == 0
    
    def test_eviction_preserves_measurement_order(self):
        """Test that eviction preserves the order of remaining measurements."""
        import time
        from unittest.mock import patch
        
        base_time = 1000000
        
        with patch('time.time') as mock_time:
            mock_time.return_value = base_time
            
            # Add measurements in specific order (all recent)
            recent_measurements = []
            for i in range(5):
                timestamp = base_time - 1800 + (i * 100)  # Spread over 30 minutes, all recent
                metric = PerformanceMetric(
                    duration=0.01 * (i + 1),
                    text_length=100 * (i + 1),
                    timestamp=timestamp,
                    operation_type=f"measurement_{i}"
                )
                recent_measurements.append(metric)
            
            self.monitor.key_generation_times.extend(recent_measurements)
            
            # Add one old measurement at the beginning
            old_metric = PerformanceMetric(
                duration=0.99,
                text_length=9900,
                timestamp=base_time - 7200,  # 2 hours ago
                operation_type="old_measurement"
            )
            self.monitor.key_generation_times.insert(0, old_metric)
            
            # Trigger cleanup
            self.monitor._cleanup_old_measurements(self.monitor.key_generation_times)
            
            # Should have 5 recent measurements, old one evicted
            assert len(self.monitor.key_generation_times) == 5
            
            # Verify order is preserved for remaining measurements
            for i, metric in enumerate(self.monitor.key_generation_times):
                assert metric.operation_type == f"measurement_{i}"
                assert metric.duration == 0.01 * (i + 1)
                assert metric.text_length == 100 * (i + 1)
            
            # Verify old measurement was removed
            operations = [m.operation_type for m in self.monitor.key_generation_times]
            assert "old_measurement" not in operations
    
    def test_eviction_with_recording_methods(self):
        """Test that eviction is automatically triggered by recording methods."""
        import time
        from unittest.mock import patch
        
        base_time = 1000000
        
        with patch('time.time') as mock_time:
            # Set initial time and add old measurement manually
            mock_time.return_value = base_time - 7200  # 2 hours ago
            old_metric = PerformanceMetric(
                duration=0.99,
                text_length=9999,
                timestamp=base_time - 7200
            )
            self.monitor.key_generation_times.append(old_metric)
            
            # Now advance time to present and record new measurements
            mock_time.return_value = base_time
            
            # Record new measurements - should trigger cleanup
            self.monitor.record_key_generation_time(0.05, 1000, "new_measurement")
            self.monitor.record_cache_operation_time("get", 0.02, True, 500)
            self.monitor.record_compression_ratio(2000, 1000, 0.01, "new_compression")
            self.monitor.record_memory_usage({"key": "value"})
            self.monitor.record_invalidation_event("test:*", 5, 0.01, "manual")
            
            # Old measurements should be automatically evicted
            assert len(self.monitor.key_generation_times) == 1
            assert self.monitor.key_generation_times[0].operation_type == "new_measurement"
            assert self.monitor.key_generation_times[0].duration == 0.05
            
            # New measurements should be present
            assert len(self.monitor.cache_operation_times) == 1
            assert len(self.monitor.compression_ratios) == 1
            assert len(self.monitor.memory_usage_measurements) == 1
            assert len(self.monitor.invalidation_events) == 1
    
    def test_eviction_stress_with_large_dataset(self):
        """Test eviction performance with large datasets."""
        import time
        from unittest.mock import patch
        
        # Set reasonable limits
        self.monitor.max_measurements = 50
        
        base_time = 1000000
        
        with patch('time.time') as mock_time:
            mock_time.return_value = base_time
            
            # Add many measurements spanning old and new times
            measurements = []
            for i in range(200):  # Large dataset
                # Mix of old and recent measurements
                if i < 100:
                    timestamp = base_time - 7200 - i  # Old measurements (2+ hours ago)
                    operation = f"old_{i}"
                else:
                    timestamp = base_time - 1800 + (i - 100)  # Recent measurements (30 min ago to now)
                    operation = f"recent_{i}"
                
                metric = PerformanceMetric(
                    duration=0.001 * i,
                    text_length=10 * i,
                    timestamp=timestamp,
                    operation_type=operation
                )
                measurements.append(metric)
            
            self.monitor.key_generation_times.extend(measurements)
            
            # Initially 200 measurements
            assert len(self.monitor.key_generation_times) == 200
            
            # Trigger cleanup
            self.monitor._cleanup_old_measurements(self.monitor.key_generation_times)
            
            # Should be limited to max_measurements after time-based eviction
            assert len(self.monitor.key_generation_times) == 50
            
            # All remaining measurements should be recent ones
            for metric in self.monitor.key_generation_times:
                assert metric.operation_type.startswith("recent_")
            
            # Should keep the 50 most recent measurements
            expected_operations = [f"recent_{i}" for i in range(150, 200)]  # Last 50 recent measurements
            actual_operations = [m.operation_type for m in self.monitor.key_generation_times]
            assert actual_operations == expected_operations 