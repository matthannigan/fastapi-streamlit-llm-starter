import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.services.monitoring import (
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
    
    @patch('app.services.monitoring.logger')
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
    
    @patch('app.services.monitoring.logger')
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

    @patch('backend.app.services.monitoring.logger')
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

    @patch('backend.app.services.monitoring.logger')
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