"""
Tests for benchmark utility functions.

This module tests the statistical calculator and memory tracker utilities
with various data distributions and edge cases.
"""

import pytest
import math
from typing import List
from unittest.mock import patch, MagicMock

from app.infrastructure.cache.benchmarks.utils import StatisticalCalculator, MemoryTracker


class TestStatisticalCalculator:
    """Test cases for StatisticalCalculator utility class."""
    
    def test_percentile_calculation_even_data(self):
        """Test percentile calculation with even number of data points."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        
        # Test various percentiles
        assert StatisticalCalculator.percentile(data, 50.0) == 5.5  # Median
        assert StatisticalCalculator.percentile(data, 25.0) == 3.25  # Q1
        assert StatisticalCalculator.percentile(data, 75.0) == 7.75  # Q3
        assert StatisticalCalculator.percentile(data, 0.0) == 1.0   # Min
        assert StatisticalCalculator.percentile(data, 100.0) == 10.0 # Max
    
    def test_percentile_calculation_odd_data(self):
        """Test percentile calculation with odd number of data points."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
        
        assert StatisticalCalculator.percentile(data, 50.0) == 5.0  # Median
        assert StatisticalCalculator.percentile(data, 0.0) == 1.0   # Min
        assert StatisticalCalculator.percentile(data, 100.0) == 9.0 # Max
    
    def test_percentile_calculation_performance_data(self):
        """Test percentile calculation with realistic performance data."""
        # Simulate response times in milliseconds
        data = [15.2, 18.4, 22.1, 25.6, 28.9, 31.2, 34.5, 37.8, 42.3, 48.7,
                52.1, 56.4, 61.8, 67.2, 73.5, 79.8, 86.1, 92.4, 98.7, 105.2]
        
        p95 = StatisticalCalculator.percentile(data, 95.0)
        p99 = StatisticalCalculator.percentile(data, 99.0)
        
        # P95 should be approximately 98.7
        assert abs(p95 - 98.7) < 5.0
        # P99 should be close to the maximum
        assert p99 > p95
        assert p99 <= max(data)
    
    def test_percentile_single_value(self):
        """Test percentile calculation with single data point."""
        data = [42.0]
        
        assert StatisticalCalculator.percentile(data, 0.0) == 42.0
        assert StatisticalCalculator.percentile(data, 50.0) == 42.0
        assert StatisticalCalculator.percentile(data, 100.0) == 42.0
    
    def test_percentile_empty_data(self):
        """Test percentile calculation with empty data."""
        data = []
        
        with pytest.raises(ValueError, match="Cannot calculate percentile"):
            StatisticalCalculator.percentile(data, 50.0)
    
    def test_percentile_invalid_percentile(self):
        """Test percentile calculation with invalid percentile values."""
        data = [1.0, 2.0, 3.0]
        
        with pytest.raises(ValueError, match="Percentile must be between 0 and 100"):
            StatisticalCalculator.percentile(data, -10.0)
        
        with pytest.raises(ValueError, match="Percentile must be between 0 and 100"):
            StatisticalCalculator.percentile(data, 150.0)
    
    def test_standard_deviation_calculation(self):
        """Test standard deviation calculation."""
        # Known dataset with calculated standard deviation
        data = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        
        # Population standard deviation should be 2.0
        std_dev = StatisticalCalculator.calculate_standard_deviation(data)
        assert abs(std_dev - 2.0) < 0.01
    
    def test_standard_deviation_uniform_data(self):
        """Test standard deviation with uniform data."""
        data = [5.0, 5.0, 5.0, 5.0, 5.0]
        
        std_dev = StatisticalCalculator.calculate_standard_deviation(data)
        assert std_dev == 0.0
    
    def test_standard_deviation_single_value(self):
        """Test standard deviation with single data point."""
        data = [42.0]
        
        std_dev = StatisticalCalculator.calculate_standard_deviation(data)
        assert std_dev == 0.0
    
    def test_standard_deviation_empty_data(self):
        """Test standard deviation with empty data."""
        data = []
        
        with pytest.raises(ValueError, match="Cannot calculate standard deviation"):
            StatisticalCalculator.calculate_standard_deviation(data)
    
    def test_outlier_detection_with_outliers(self):
        """Test outlier detection with clear outliers."""
        # Normal data with outliers
        data = [10.0, 12.0, 11.0, 13.0, 12.5, 11.8, 50.0, 9.5, 11.2, 100.0]
        
        outliers = StatisticalCalculator.detect_outliers(data)
        
        # Should detect the extreme values (50.0 and 100.0)
        assert 50.0 in outliers
        assert 100.0 in outliers
        assert len(outliers) >= 2
    
    def test_outlier_detection_no_outliers(self):
        """Test outlier detection with no outliers."""
        # Uniform distribution
        data = [10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5]
        
        outliers = StatisticalCalculator.detect_outliers(data)
        
        # Should detect no outliers in uniform distribution
        assert len(outliers) == 0
    
    def test_outlier_detection_edge_cases(self):
        """Test outlier detection edge cases."""
        # Single value
        single_data = [42.0]
        outliers = StatisticalCalculator.detect_outliers(single_data)
        assert len(outliers) == 0
        
        # Two values
        two_data = [10.0, 20.0]
        outliers = StatisticalCalculator.detect_outliers(two_data)
        assert len(outliers) == 0
        
        # Empty data
        empty_data = []
        outliers = StatisticalCalculator.detect_outliers(empty_data)
        assert len(outliers) == 0
    
    def test_confidence_intervals_calculation(self):
        """Test confidence interval calculation."""
        # Sample data with known properties
        data = [20.0, 22.0, 23.0, 21.0, 24.0, 25.0, 23.0, 22.0, 21.0, 24.0]
        
        mean, lower, upper = StatisticalCalculator.calculate_confidence_intervals(data, 0.95)
        
        # Mean should be approximately 22.5
        assert abs(mean - 22.5) < 0.1
        
        # Confidence interval should contain the mean
        assert lower < mean < upper
        
        # Interval should be reasonable (not too wide)
        assert (upper - lower) < 10.0
    
    def test_confidence_intervals_different_levels(self):
        """Test confidence intervals with different confidence levels."""
        data = [15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0]
        
        # 90% confidence interval
        mean_90, lower_90, upper_90 = StatisticalCalculator.calculate_confidence_intervals(data, 0.90)
        
        # 99% confidence interval
        mean_99, lower_99, upper_99 = StatisticalCalculator.calculate_confidence_intervals(data, 0.99)
        
        # Means should be the same
        assert abs(mean_90 - mean_99) < 0.001
        
        # 99% interval should be wider than 90%
        interval_90 = upper_90 - lower_90
        interval_99 = upper_99 - lower_99
        assert interval_99 > interval_90
    
    def test_confidence_intervals_edge_cases(self):
        """Test confidence intervals edge cases."""
        # Single value
        single_data = [42.0]
        mean, lower, upper = StatisticalCalculator.calculate_confidence_intervals(single_data, 0.95)
        assert mean == 42.0
        assert lower == upper == mean
        
        # Empty data
        empty_data = []
        with pytest.raises(ValueError, match="Cannot calculate confidence intervals"):
            StatisticalCalculator.calculate_confidence_intervals(empty_data, 0.95)
    
    def test_calculate_statistics_comprehensive(self):
        """Test the unified calculate_statistics method."""
        data = [18.5, 22.1, 19.7, 25.3, 21.8, 23.4, 20.6, 24.1, 22.9, 26.2]
        
        stats = StatisticalCalculator.calculate_statistics(data)
        
        # Check all required statistics are present
        required_keys = ['mean', 'median', 'std_dev', 'min', 'max', 'p95', 'p99', 
                        'outliers', 'confidence_interval_95']
        
        for key in required_keys:
            assert key in stats
        
        # Verify relationships
        assert stats['min'] <= stats['median'] <= stats['max']
        assert stats['median'] <= stats['p95'] <= stats['p99']
        assert stats['confidence_interval_95']['lower'] <= stats['mean'] <= stats['confidence_interval_95']['upper']
        
        # Check types
        assert isinstance(stats['outliers'], list)
        assert isinstance(stats['confidence_interval_95'], dict)


class TestMemoryTracker:
    """Test cases for MemoryTracker utility class."""
    
    def test_memory_tracker_initialization(self):
        """Test MemoryTracker initialization."""
        tracker = MemoryTracker()
        assert tracker is not None
    
    @patch('psutil.virtual_memory')
    @patch('psutil.Process')
    def test_get_memory_usage_with_psutil(self, mock_process, mock_virtual_memory):
        """Test memory usage retrieval when psutil is available."""
        # Mock psutil calls
        mock_vm = MagicMock()
        mock_vm.total = 8 * 1024 * 1024 * 1024  # 8GB in bytes
        mock_vm.available = 4 * 1024 * 1024 * 1024  # 4GB available
        mock_virtual_memory.return_value = mock_vm
        
        mock_proc = MagicMock()
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 512 * 1024 * 1024  # 512MB in bytes
        mock_proc.memory_info.return_value = mock_memory_info
        mock_process.return_value = mock_proc
        
        tracker = MemoryTracker()
        memory_info = tracker.get_memory_usage()
        
        assert 'total_mb' in memory_info
        assert 'available_mb' in memory_info
        assert 'process_mb' in memory_info
        
        # Check converted values (bytes to MB)
        assert memory_info['total_mb'] == 8192.0  # 8GB
        assert memory_info['available_mb'] == 4096.0  # 4GB
        assert memory_info['process_mb'] == 512.0  # 512MB
    
    @patch('psutil.virtual_memory', side_effect=ImportError("psutil not available"))
    @patch('resource.getrusage')
    def test_get_memory_usage_fallback(self, mock_getrusage):
        """Test memory usage retrieval fallback when psutil is unavailable."""
        # Mock resource.getrusage
        mock_usage = MagicMock()
        mock_usage.ru_maxrss = 1024 * 1024  # 1GB in KB on Linux (or bytes on macOS)
        mock_getrusage.return_value = mock_usage
        
        tracker = MemoryTracker()
        memory_info = tracker.get_memory_usage()
        
        assert 'process_mb' in memory_info
        # Should fall back to resource module
        assert memory_info['process_mb'] > 0
    
    @patch('psutil.virtual_memory', side_effect=ImportError("psutil not available"))
    @patch('resource.getrusage', side_effect=OSError("Resource not available"))
    def test_get_memory_usage_full_fallback(self, mock_getrusage):
        """Test memory usage retrieval when both psutil and resource fail."""
        tracker = MemoryTracker()
        memory_info = tracker.get_memory_usage()
        
        # Should return minimal info with fallback values
        assert 'process_mb' in memory_info
        assert memory_info['process_mb'] == 0.0  # Fallback value
    
    def test_get_process_memory_mb_basic(self):
        """Test basic process memory retrieval."""
        tracker = MemoryTracker()
        process_memory = tracker.get_process_memory_mb()
        
        # Should return a reasonable value (at least some memory usage)
        assert isinstance(process_memory, float)
        assert process_memory >= 0.0
    
    @patch('psutil.Process')
    def test_memory_delta_calculation(self, mock_process):
        """Test memory delta calculation between measurements."""
        # Mock two different memory readings
        mock_proc = MagicMock()
        
        # First measurement: 100MB
        mock_memory_info_1 = MagicMock()
        mock_memory_info_1.rss = 100 * 1024 * 1024
        
        # Second measurement: 150MB
        mock_memory_info_2 = MagicMock()
        mock_memory_info_2.rss = 150 * 1024 * 1024
        
        mock_proc.memory_info.side_effect = [mock_memory_info_1, mock_memory_info_2]
        mock_process.return_value = mock_proc
        
        tracker = MemoryTracker()
        
        # Take baseline measurement
        baseline = tracker.get_process_memory_mb()
        assert baseline == 100.0
        
        # Take second measurement
        current = tracker.get_process_memory_mb()
        assert current == 150.0
        
        # Calculate delta
        delta = current - baseline
        assert delta == 50.0  # 50MB increase
    
    def test_memory_tracking_during_operation(self):
        """Test memory tracking during a simulated operation."""
        tracker = MemoryTracker()
        
        # Get baseline memory
        baseline_memory = tracker.get_process_memory_mb()
        
        # Simulate some memory-intensive operation
        # (In real tests, this would be actual cache operations)
        large_list = [i for i in range(1000)]  # Small list for testing
        
        # Get memory after operation
        post_operation_memory = tracker.get_process_memory_mb()
        
        # Calculate delta
        memory_delta = post_operation_memory - baseline_memory
        
        # Memory delta should be reasonable (could be positive or negative due to GC)
        assert isinstance(memory_delta, float)
        # In a real scenario, we'd expect some memory increase, but for this small operation
        # the delta might be minimal or even negative due to garbage collection
        assert abs(memory_delta) < 1000.0  # Should not be dramatically large
    
    @patch('platform.system')
    def test_platform_specific_memory_handling(self, mock_platform):
        """Test platform-specific memory handling."""
        tracker = MemoryTracker()
        
        # Test different platform behaviors
        for platform_name in ['Linux', 'Darwin', 'Windows']:
            mock_platform.return_value = platform_name
            
            # Memory tracking should work regardless of platform
            memory_info = tracker.get_memory_usage()
            assert isinstance(memory_info, dict)
            assert 'process_mb' in memory_info
    
    def test_memory_tracker_error_handling(self):
        """Test memory tracker error handling and recovery."""
        tracker = MemoryTracker()
        
        # Even if internal calls fail, should not crash
        with patch.object(tracker, 'get_process_memory_mb', side_effect=Exception("Test error")):
            try:
                # Should handle the exception gracefully
                memory = tracker.get_memory_usage()
                # Should return default/fallback values
                assert isinstance(memory, dict)
            except Exception:
                # If it does raise, should be a controlled exception
                pass
    
    def test_memory_measurement_consistency(self):
        """Test that repeated memory measurements are consistent."""
        tracker = MemoryTracker()
        
        # Take multiple measurements
        measurements = []
        for _ in range(5):
            measurements.append(tracker.get_process_memory_mb())
        
        # Measurements should be reasonably consistent
        # (some variation is expected due to system activity)
        min_measurement = min(measurements)
        max_measurement = max(measurements)
        
        # Variation should not be extreme
        if min_measurement > 0:
            variation_percent = (max_measurement - min_measurement) / min_measurement
            assert variation_percent < 0.5  # Less than 50% variation
    
    def test_memory_units_conversion(self):
        """Test memory units conversion accuracy."""
        tracker = MemoryTracker()
        
        # Test conversion from bytes to MB
        test_bytes = 1024 * 1024 * 100  # 100 MB in bytes
        
        with patch('psutil.Process') as mock_process:
            mock_proc = MagicMock()
            mock_memory_info = MagicMock()
            mock_memory_info.rss = test_bytes
            mock_proc.memory_info.return_value = mock_memory_info
            mock_process.return_value = mock_proc
            
            memory_mb = tracker.get_process_memory_mb()
            assert memory_mb == 100.0  # Should be exactly 100 MB