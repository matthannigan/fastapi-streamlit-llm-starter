import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.services.monitoring import (
    CachePerformanceMonitor, 
    PerformanceMetric, 
    CompressionMetric
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
        
        # Test custom initialization
        custom_monitor = CachePerformanceMonitor(retention_hours=2, max_measurements=500)
        assert custom_monitor.retention_hours == 2
        assert custom_monitor.max_measurements == 500
    
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
        
        assert len(self.monitor.key_generation_times) > 0
        assert len(self.monitor.cache_operation_times) > 0
        assert len(self.monitor.compression_ratios) > 0
        assert self.monitor.cache_hits > 0
        assert self.monitor.total_operations > 0
        
        # Reset
        self.monitor.reset_stats()
        
        assert len(self.monitor.key_generation_times) == 0
        assert len(self.monitor.cache_operation_times) == 0
        assert len(self.monitor.compression_ratios) == 0
        assert self.monitor.cache_hits == 0
        assert self.monitor.cache_misses == 0
        assert self.monitor.total_operations == 0
    
    def test_export_metrics(self):
        """Test exporting all metrics data."""
        # Add some data
        self.monitor.record_key_generation_time(0.05, 1000, "summarize", {"model": "gpt-4"})
        self.monitor.record_cache_operation_time("get", 0.02, True, 500, {"tier": "small"})
        self.monitor.record_compression_ratio(1000, 600, 0.01, "summarize")
        
        exported = self.monitor.export_metrics()
        
        assert "key_generation_times" in exported
        assert "cache_operation_times" in exported
        assert "compression_ratios" in exported
        assert "cache_hits" in exported
        assert "cache_misses" in exported
        assert "total_operations" in exported
        assert "export_timestamp" in exported
        
        # Check that data is properly serialized
        assert len(exported["key_generation_times"]) == 1
        assert len(exported["cache_operation_times"]) == 1
        assert len(exported["compression_ratios"]) == 1
        
        # Check that dataclass is converted to dict
        key_gen_data = exported["key_generation_times"][0]
        assert isinstance(key_gen_data, dict)
        assert key_gen_data["duration"] == 0.05
        assert key_gen_data["text_length"] == 1000
        assert key_gen_data["operation_type"] == "summarize"
        assert key_gen_data["additional_data"] == {"model": "gpt-4"}
    
    def test_integration_workflow(self):
        """Test a complete workflow with multiple operations."""
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
        
        # Get comprehensive stats
        stats = self.monitor.get_performance_stats()
        
        # Verify overall health
        assert stats["cache_hit_rate"] == 33.33333333333333  # 1 hit out of 3 operations
        assert stats["key_generation"]["slow_operations"] == 1
        assert stats["compression"]["overall_savings_percent"] > 40  # Good compression
        
        # Check slow operations
        slow_ops = self.monitor.get_recent_slow_operations()
        assert len(slow_ops["key_generation"]) >= 1  # At least the 0.15s operation
        
        # Export for analysis
        exported = self.monitor.export_metrics()
        assert len(exported["key_generation_times"]) == 3
        assert len(exported["cache_operation_times"]) == 3
        assert len(exported["compression_ratios"]) == 2 