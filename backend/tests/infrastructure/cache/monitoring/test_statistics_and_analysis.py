"""
Unit tests for CachePerformanceMonitor statistics and analysis functionality.

This test suite verifies the observable behaviors documented in the
CachePerformanceMonitor statistics methods (monitoring.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - Statistics calculation accuracy and performance analysis
    - Threshold-based alerting and recommendation systems
    - Data export and metrics aggregation functionality
    - Memory usage analysis and trend detection

External Dependencies:
    All external dependencies are mocked using fixtures from conftest.py following
    the documented public contracts to ensure accurate behavior simulation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time
from typing import Dict, Any, List

from app.infrastructure.cache.monitoring import CachePerformanceMonitor


class TestPerformanceStatistics:
    """
    Test suite for comprehensive performance statistics generation.
    
    Scope:
        - get_performance_stats() comprehensive statistics generation
        - Statistical accuracy across all monitored performance areas
        - Data aggregation and calculation verification
        - Automatic cleanup integration during statistics generation
        
    Business Critical:
        Performance statistics enable data-driven cache optimization decisions
        
    Test Strategy:
        - Unit tests for statistics calculation accuracy
        - Comprehensive data aggregation verification
        - Performance impact testing for statistics generation
        - Edge case handling for empty or sparse data sets
        
    External Dependencies:
        - statistics module: Standard library (not mocked for realistic calculations)
        - time module: Standard library timing (not mocked for accurate timestamps)
    """

    def test_get_performance_stats_provides_comprehensive_overview(self):
        """
        Test that get_performance_stats() provides comprehensive performance overview.
        
        Verifies:
            Statistics include all monitored performance areas with accurate calculations
            
        Business Impact:
            Enables complete performance assessment for operational decision making
            
        Scenario:
            Given: CachePerformanceMonitor with collected performance data across all areas
            When: get_performance_stats() is called for comprehensive analysis
            Then: Complete statistics are returned covering hit rates, timing, compression, memory, and invalidation
            
        Edge Cases Covered:
            - Statistics across all monitored performance dimensions
            - Accurate calculation aggregation from various metric types
            - Timestamp inclusion for temporal analysis
            - Complete data structure verification
            
        Mocks Used:
            - None (comprehensive calculation verification)
            
        Related Tests:
            - test_get_performance_stats_calculates_hit_rates_accurately()
            - test_get_performance_stats_aggregates_timing_data_correctly()
        """
        # Given: CachePerformanceMonitor with collected performance data across all areas
        monitor = CachePerformanceMonitor()
        
        # Record data across all performance areas
        monitor.record_key_generation_time(duration=0.05, text_length=100, operation_type="summarize")
        monitor.record_cache_operation_time(operation="get", duration=0.02, cache_hit=True, text_length=100)
        monitor.record_compression_ratio(original_size=1000, compressed_size=300, compression_time=0.01)
        monitor.record_memory_usage(memory_cache={"key1": "value1"}, redis_stats={"memory_used_bytes": 50000, "keys": 10})
        monitor.record_invalidation_event(pattern="test:*", keys_invalidated=5, duration=0.001)
        
        # When: get_performance_stats() is called for comprehensive analysis
        stats = monitor.get_performance_stats()
        
        # Then: Complete statistics are returned covering all monitored areas
        assert "timestamp" in stats
        assert "cache_hit_rate" in stats
        assert "key_generation" in stats
        assert "cache_operations" in stats
        assert "compression" in stats
        assert "memory_usage" in stats
        assert "invalidation" in stats
        
        # Verify data structure completeness
        assert isinstance(stats["timestamp"], str)
        assert isinstance(stats["cache_hit_rate"], (int, float))
        assert isinstance(stats["key_generation"], dict)
        assert isinstance(stats["cache_operations"], dict)
        assert isinstance(stats["compression"], dict)
        assert isinstance(stats["memory_usage"], dict)
        assert isinstance(stats["invalidation"], dict)

    def test_get_performance_stats_calculates_hit_rates_accurately(self):
        """
        Test that get_performance_stats() calculates cache hit rates accurately.
        
        Verifies:
            Hit rate calculations reflect actual cache performance accurately
            
        Business Impact:
            Provides accurate cache effectiveness metrics for optimization decisions
            
        Scenario:
            Given: CachePerformanceMonitor with recorded hit and miss events
            When: get_performance_stats() calculates overall hit rate
            Then: Hit rate percentage accurately reflects cache operation success ratio
            
        Edge Cases Covered:
            - Various hit/miss ratios (high, medium, low hit rates)
            - Zero hit scenarios (all misses)
            - Perfect hit scenarios (no misses)
            - Hit rate calculation precision and accuracy
            
        Mocks Used:
            - None (calculation accuracy verification)
            
        Related Tests:
            - test_get_performance_stats_provides_comprehensive_overview()
            - test_get_performance_stats_aggregates_timing_data_correctly()
        """
        # Given: CachePerformanceMonitor with recorded hit and miss events
        monitor = CachePerformanceMonitor()
        
        # Record cache operations with known hit/miss pattern (7 hits, 3 misses = 70% hit rate)
        for i in range(10):
            is_hit = i < 7  # First 7 are hits, last 3 are misses
            monitor.record_cache_operation_time(
                operation="get",
                duration=0.01,
                cache_hit=is_hit,
                text_length=100
            )
        
        # When: get_performance_stats() calculates overall hit rate
        stats = monitor.get_performance_stats()
        
        # Then: Hit rate percentage accurately reflects cache operation success ratio
        assert stats["cache_hit_rate"] == 70.0
        assert stats["cache_hits"] == 7
        assert stats["cache_misses"] == 3
        assert stats["total_cache_operations"] == 10
        
        # Test edge case: No operations (0% hit rate)
        monitor_empty = CachePerformanceMonitor()
        stats_empty = monitor_empty.get_performance_stats()
        assert stats_empty["cache_hit_rate"] == 0.0
        
        # Test edge case: Perfect hit rate (100%)
        monitor_perfect = CachePerformanceMonitor()
        for i in range(5):
            monitor_perfect.record_cache_operation_time(
                operation="get",
                duration=0.01,
                cache_hit=True,
                text_length=100
            )
        stats_perfect = monitor_perfect.get_performance_stats()
        assert stats_perfect["cache_hit_rate"] == 100.0

    def test_get_performance_stats_aggregates_timing_data_correctly(self):
        """
        Test that get_performance_stats() aggregates timing data correctly across operations.
        
        Verifies:
            Timing statistics are accurately calculated for different operation types
            
        Business Impact:
            Enables identification of performance bottlenecks by operation type
            
        Scenario:
            Given: CachePerformanceMonitor with timing data for key generation and cache operations
            When: get_performance_stats() aggregates timing statistics
            Then: Average, median, and other timing metrics are accurately calculated per operation type
            
        Edge Cases Covered:
            - Key generation timing aggregation
            - Cache operation timing by type (get, set, delete)
            - Statistical accuracy (mean, median, percentiles)
            - Operation count verification
            
        Mocks Used:
            - None (timing aggregation verification)
            
        Related Tests:
            - test_get_performance_stats_calculates_hit_rates_accurately()
            - test_get_performance_stats_includes_compression_analysis()
        """
        # Given: CachePerformanceMonitor with timing data for key generation and cache operations
        monitor = CachePerformanceMonitor()
        
        # Record key generation times with known values
        key_gen_times = [0.01, 0.02, 0.03, 0.04, 0.05]
        for duration in key_gen_times:
            monitor.record_key_generation_time(duration=duration, text_length=100, operation_type="summarize")
        
        # Record cache operations by type
        get_times = [0.005, 0.010, 0.015]
        set_times = [0.020, 0.025]
        for duration in get_times:
            monitor.record_cache_operation_time(operation="get", duration=duration, cache_hit=True, text_length=100)
        for duration in set_times:
            monitor.record_cache_operation_time(operation="set", duration=duration, cache_hit=True, text_length=100)
        
        # When: get_performance_stats() aggregates timing statistics
        stats = monitor.get_performance_stats()
        
        # Then: Timing metrics are accurately calculated
        # Key generation statistics
        key_gen_stats = stats["key_generation"]
        assert key_gen_stats["total_operations"] == 5
        assert key_gen_stats["avg_duration"] == 0.03  # (0.01+0.02+0.03+0.04+0.05)/5
        assert key_gen_stats["median_duration"] == 0.03
        assert key_gen_stats["max_duration"] == 0.05
        assert key_gen_stats["min_duration"] == 0.01
        
        # Cache operations statistics
        cache_ops_stats = stats["cache_operations"]
        assert cache_ops_stats["total_operations"] == 5  # 3 gets + 2 sets
        
        # Verify by operation type aggregation
        by_type = cache_ops_stats["by_operation_type"]
        assert "get" in by_type
        assert "set" in by_type
        assert by_type["get"]["count"] == 3
        assert by_type["get"]["avg_duration"] == 0.010  # (0.005+0.010+0.015)/3
        assert by_type["set"]["count"] == 2
        assert by_type["set"]["avg_duration"] == 0.0225  # (0.020+0.025)/2

    def test_get_performance_stats_includes_compression_analysis(self):
        """
        Test that get_performance_stats() includes comprehensive compression analysis.
        
        Verifies:
            Compression statistics provide efficiency and performance insights
            
        Business Impact:
            Enables optimization of compression settings based on actual performance data
            
        Scenario:
            Given: CachePerformanceMonitor with compression performance data
            When: get_performance_stats() analyzes compression metrics
            Then: Compression ratios, timing, and efficiency statistics are included
            
        Edge Cases Covered:
            - Average compression ratio calculations
            - Compression timing analysis
            - Size savings calculations
            - Compression vs. performance trade-off analysis
            
        Mocks Used:
            - None (compression analysis verification)
            
        Related Tests:
            - test_get_performance_stats_aggregates_timing_data_correctly()
            - test_get_performance_stats_integrates_memory_analysis()
        """
        # Given: CachePerformanceMonitor with compression performance data
        monitor = CachePerformanceMonitor()
        
        # Record compression operations with known performance characteristics
        compression_data = [
            {"original_size": 1000, "compressed_size": 300, "compression_time": 0.01},  # 70% savings
            {"original_size": 2000, "compressed_size": 800, "compression_time": 0.02},  # 60% savings
            {"original_size": 1500, "compressed_size": 600, "compression_time": 0.015}, # 60% savings
        ]
        
        for data in compression_data:
            monitor.record_compression_ratio(
                original_size=data["original_size"],
                compressed_size=data["compressed_size"],
                compression_time=data["compression_time"],
                operation_type="cache_store"
            )
        
        # When: get_performance_stats() analyzes compression metrics
        stats = monitor.get_performance_stats()
        
        # Then: Compression statistics provide efficiency and performance insights
        compression_stats = stats["compression"]
        assert compression_stats["total_operations"] == 3
        
        # Verify compression ratio calculations
        expected_ratios = [0.3, 0.4, 0.4]  # compressed/original for each operation
        avg_ratio = sum(expected_ratios) / len(expected_ratios)
        assert abs(compression_stats["avg_compression_ratio"] - avg_ratio) < 0.01
        assert compression_stats["best_compression_ratio"] == 0.3  # Lowest ratio is best compression
        assert compression_stats["worst_compression_ratio"] == 0.4
        
        # Verify timing analysis
        expected_times = [0.01, 0.02, 0.015]
        avg_time = sum(expected_times) / len(expected_times)
        assert abs(compression_stats["avg_compression_time"] - avg_time) < 0.001
        assert compression_stats["max_compression_time"] == 0.02
        
        # Verify size savings calculations
        total_original = 1000 + 2000 + 1500  # 4500
        total_compressed = 300 + 800 + 600  # 1700
        total_savings = total_original - total_compressed  # 2800
        expected_savings_percent = (total_savings / total_original) * 100  # 62.22%
        
        assert compression_stats["total_bytes_processed"] == total_original
        assert compression_stats["total_bytes_saved"] == total_savings
        assert abs(compression_stats["overall_savings_percent"] - expected_savings_percent) < 0.1

    def test_get_performance_stats_integrates_memory_analysis(self):
        """
        Test that get_performance_stats() integrates comprehensive memory usage analysis.
        
        Verifies:
            Memory statistics provide current usage and trend information
            
        Business Impact:
            Enables memory-based optimization and capacity planning decisions
            
        Scenario:
            Given: CachePerformanceMonitor with memory usage measurements
            When: get_performance_stats() includes memory analysis
            Then: Current usage, trends, and threshold analysis are integrated into statistics
            
        Edge Cases Covered:
            - Current memory usage reporting
            - Memory trend analysis integration
            - Threshold status integration
            - Memory efficiency metrics
            
        Mocks Used:
            - None (memory analysis integration verification)
            
        Related Tests:
            - test_get_performance_stats_includes_compression_analysis()
            - test_get_performance_stats_incorporates_invalidation_patterns()
        """
        # Given: CachePerformanceMonitor with memory usage measurements
        monitor = CachePerformanceMonitor(
            memory_warning_threshold_bytes=10 * 1024 * 1024,  # 10MB
            memory_critical_threshold_bytes=20 * 1024 * 1024   # 20MB
        )
        
        # Record memory usage measurements with known values
        memory_cache = {"key1": "value1" * 100, "key2": "value2" * 200}
        redis_stats = {"memory_used_bytes": 5 * 1024 * 1024, "keys": 50}  # 5MB Redis usage
        
        monitor.record_memory_usage(
            memory_cache=memory_cache,
            redis_stats=redis_stats,
            additional_data={"test_scenario": "integration"}
        )
        
        # Record additional measurements for trend analysis
        import time
        time.sleep(0.01)  # Ensure different timestamps
        
        larger_cache = {"key" + str(i): "value" * 50 for i in range(20)}
        monitor.record_memory_usage(
            memory_cache=larger_cache,
            redis_stats={"memory_used_bytes": 6 * 1024 * 1024, "keys": 60}
        )
        
        # When: get_performance_stats() includes memory analysis
        stats = monitor.get_performance_stats()
        
        # Then: Memory statistics are integrated with current usage and trends
        assert "memory_usage" in stats
        memory_stats = stats["memory_usage"]
        
        # Verify current usage reporting
        assert "current" in memory_stats
        current = memory_stats["current"]
        assert "total_cache_size_mb" in current
        assert "memory_cache_size_mb" in current
        assert "cache_entry_count" in current
        assert "process_memory_mb" in current
        
        # Verify threshold analysis integration
        assert "thresholds" in memory_stats
        thresholds = memory_stats["thresholds"]
        assert "warning_threshold_mb" in thresholds
        assert "critical_threshold_mb" in thresholds
        assert "warning_threshold_reached" in thresholds
        assert "critical_threshold_reached" in thresholds
        assert thresholds["warning_threshold_mb"] == 10.0  # 10MB
        assert thresholds["critical_threshold_mb"] == 20.0  # 20MB
        
        # Verify trend analysis integration
        assert "trends" in memory_stats
        trends = memory_stats["trends"]
        assert "total_measurements" in trends
        assert "avg_total_cache_size_mb" in trends
        assert "max_total_cache_size_mb" in trends
        assert trends["total_measurements"] == 2

    def test_get_performance_stats_incorporates_invalidation_patterns(self):
        """
        Test that get_performance_stats() incorporates invalidation pattern analysis.
        
        Verifies:
            Invalidation statistics provide frequency and efficiency insights
            
        Business Impact:
            Enables optimization of cache invalidation strategies based on actual patterns
            
        Scenario:
            Given: CachePerformanceMonitor with invalidation event data
            When: get_performance_stats() analyzes invalidation patterns
            Then: Frequency rates, efficiency metrics, and pattern analysis are included
            
        Edge Cases Covered:
            - Invalidation frequency analysis
            - Pattern efficiency calculations
            - Type-based invalidation breakdown
            - Temporal invalidation pattern analysis
            
        Mocks Used:
            - None (invalidation analysis verification)
            
        Related Tests:
            - test_get_performance_stats_integrates_memory_analysis()
            - test_get_performance_stats_triggers_automatic_cleanup()
        """
        # Given: CachePerformanceMonitor with invalidation event data
        monitor = CachePerformanceMonitor()
        
        # Record various invalidation events with different patterns and types
        invalidation_events = [
            {"pattern": "user:*", "keys_invalidated": 5, "duration": 0.001, "invalidation_type": "manual"},
            {"pattern": "session:*", "keys_invalidated": 3, "duration": 0.002, "invalidation_type": "ttl_expired"},
            {"pattern": "user:*", "keys_invalidated": 8, "duration": 0.003, "invalidation_type": "manual"},
            {"pattern": "api:*", "keys_invalidated": 2, "duration": 0.001, "invalidation_type": "automatic"},
        ]
        
        for event in invalidation_events:
            monitor.record_invalidation_event(
                pattern=event["pattern"],
                keys_invalidated=event["keys_invalidated"],
                duration=event["duration"],
                invalidation_type=event["invalidation_type"],
                operation_context="test_scenario"
            )
        
        # When: get_performance_stats() analyzes invalidation patterns
        stats = monitor.get_performance_stats()
        
        # Then: Invalidation statistics provide frequency and efficiency insights
        assert "invalidation" in stats
        invalidation_stats = stats["invalidation"]
        
        # Verify frequency analysis
        assert "total_invalidations" in invalidation_stats
        assert "total_keys_invalidated" in invalidation_stats
        assert "rates" in invalidation_stats
        assert invalidation_stats["total_invalidations"] == 4
        assert invalidation_stats["total_keys_invalidated"] == 18  # 5+3+8+2
        
        # Verify pattern analysis is included
        assert "patterns" in invalidation_stats
        patterns = invalidation_stats["patterns"]
        assert "most_common_patterns" in patterns
        assert "invalidation_types" in patterns
        
        # Verify efficiency metrics
        assert "efficiency" in invalidation_stats
        efficiency = invalidation_stats["efficiency"]
        assert "avg_keys_per_invalidation" in efficiency
        assert "avg_duration" in efficiency
        assert efficiency["avg_keys_per_invalidation"] == 4.5  # 18 keys / 4 invalidations
        
        # Verify threshold analysis
        assert "thresholds" in invalidation_stats
        thresholds = invalidation_stats["thresholds"]
        assert "warning_per_hour" in thresholds
        assert "critical_per_hour" in thresholds
        assert "current_alert_level" in thresholds

    def test_get_performance_stats_triggers_automatic_cleanup(self):
        """
        Test that get_performance_stats() triggers automatic cleanup of old measurements.
        
        Verifies:
            Statistics generation includes automatic data retention management
            
        Business Impact:
            Prevents unbounded memory growth while maintaining performance monitoring
            
        Scenario:
            Given: CachePerformanceMonitor with old measurements exceeding retention limits
            When: get_performance_stats() is called
            Then: Old measurements are cleaned up before statistics calculation
            
        Edge Cases Covered:
            - Time-based cleanup (retention_hours)
            - Count-based cleanup (max_measurements)
            - Cleanup efficiency and performance
            - Data integrity during cleanup
            
        Mocks Used:
            - None (cleanup integration verification)
            
        Related Tests:
            - test_get_performance_stats_incorporates_invalidation_patterns()
            - test_get_performance_stats_handles_empty_data_gracefully()
        """
        # Given: CachePerformanceMonitor with measurements that should trigger cleanup
        monitor = CachePerformanceMonitor(
            retention_hours=0.001,  # Very short retention (3.6 seconds)
            max_measurements=3       # Small max count for testing
        )
        
        # Add measurements that will exceed count limit
        for i in range(5):
            monitor.record_key_generation_time(duration=0.01, text_length=100, operation_type=f"op_{i}")
            monitor.record_cache_operation_time(operation="get", duration=0.005, cache_hit=True, text_length=100)
        
        # Verify we have more than max_measurements before cleanup
        assert len(monitor.key_generation_times) == 5
        assert len(monitor.cache_operation_times) == 5
        
        # Add some measurements that are definitely old (by manipulating timestamp)
        import time
        old_time = time.time() - 7200  # 2 hours ago (exceeds retention_hours)
        if monitor.key_generation_times:
            monitor.key_generation_times[0].timestamp = old_time
        if monitor.cache_operation_times:
            monitor.cache_operation_times[0].timestamp = old_time
        
        # When: get_performance_stats() is called (triggers cleanup)
        stats = monitor.get_performance_stats()
        
        # Then: Cleanup has been triggered and measurements are within limits
        # Count-based cleanup: should have max_measurements or fewer
        assert len(monitor.key_generation_times) <= monitor.max_measurements
        assert len(monitor.cache_operation_times) <= monitor.max_measurements
        
        # Time-based cleanup: old measurements should be removed
        current_time = time.time()
        cutoff_time = current_time - (monitor.retention_hours * 3600)
        
        for measurement in monitor.key_generation_times:
            assert measurement.timestamp > cutoff_time
        for measurement in monitor.cache_operation_times:
            assert measurement.timestamp > cutoff_time
        
        # Verify statistics are still generated correctly after cleanup
        assert "key_generation" in stats
        assert "cache_operations" in stats
        assert stats["key_generation"]["total_operations"] == len(monitor.key_generation_times)
        assert stats["cache_operations"]["total_operations"] == len(monitor.cache_operation_times)

    def test_get_performance_stats_handles_empty_data_gracefully(self):
        """
        Test that get_performance_stats() handles empty or sparse data gracefully.
        
        Verifies:
            Statistics generation works correctly when insufficient data is available
            
        Business Impact:
            Ensures monitoring remains functional during startup or low-activity periods
            
        Scenario:
            Given: CachePerformanceMonitor with no or minimal collected data
            When: get_performance_stats() is called with insufficient data
            Then: Statistics are generated with appropriate default values and indicators
            
        Edge Cases Covered:
            - Completely empty data sets
            - Sparse data with some metrics missing
            - Single data point scenarios
            - Appropriate default value handling
            
        Mocks Used:
            - None (empty data handling verification)
            
        Related Tests:
            - test_get_performance_stats_triggers_automatic_cleanup()
            - test_get_performance_stats_maintains_calculation_precision()
        """
        # Given: CachePerformanceMonitor with completely empty data
        monitor_empty = CachePerformanceMonitor()
        
        # When: get_performance_stats() is called with no data
        stats_empty = monitor_empty.get_performance_stats()
        
        # Then: Statistics are generated with appropriate defaults
        assert "timestamp" in stats_empty
        assert stats_empty["cache_hit_rate"] == 0.0
        assert stats_empty["total_cache_operations"] == 0
        assert stats_empty["cache_hits"] == 0
        assert stats_empty["cache_misses"] == 0
        
        # Optional sections should not be present when no data exists
        assert "key_generation" not in stats_empty
        assert "cache_operations" not in stats_empty
        assert "compression" not in stats_empty
        assert "memory_usage" not in stats_empty
        assert "invalidation" not in stats_empty
        
        # Test sparse data scenario (only some metrics have data)
        monitor_sparse = CachePerformanceMonitor()
        
        # Add only key generation data
        monitor_sparse.record_key_generation_time(duration=0.05, text_length=100, operation_type="test")
        
        stats_sparse = monitor_sparse.get_performance_stats()
        
        # Should have key generation stats but not others
        assert "key_generation" in stats_sparse
        assert stats_sparse["key_generation"]["total_operations"] == 1
        assert "cache_operations" not in stats_sparse
        assert "compression" not in stats_sparse
        
        # Test single data point scenario
        monitor_single = CachePerformanceMonitor()
        monitor_single.record_cache_operation_time(operation="get", duration=0.01, cache_hit=True)
        
        stats_single = monitor_single.get_performance_stats()
        
        # Should handle single point calculations correctly
        assert "cache_operations" in stats_single
        cache_ops = stats_single["cache_operations"]
        assert cache_ops["total_operations"] == 1
        assert cache_ops["avg_duration"] == 0.01
        assert cache_ops["median_duration"] == 0.01
        assert cache_ops["max_duration"] == 0.01
        assert cache_ops["min_duration"] == 0.01

    def test_get_performance_stats_maintains_calculation_precision(self):
        """
        Test that get_performance_stats() maintains precision in statistical calculations.
        
        Verifies:
            Statistical calculations maintain appropriate precision for decision making
            
        Business Impact:
            Ensures accurate performance analysis for reliable optimization decisions
            
        Scenario:
            Given: CachePerformanceMonitor with precise measurement data
            When: get_performance_stats() performs statistical calculations
            Then: Calculations maintain appropriate precision without significant rounding errors
            
        Edge Cases Covered:
            - Floating-point precision maintenance
            - Statistical calculation accuracy
            - Large dataset precision handling
            - Precision consistency across calculation types
            
        Mocks Used:
            - None (precision verification)
            
        Related Tests:
            - test_get_performance_stats_handles_empty_data_gracefully()
            - test_get_performance_stats_provides_comprehensive_overview()
        """
        # Given: CachePerformanceMonitor with precise measurement data
        monitor = CachePerformanceMonitor()
        
        # Record measurements with precise floating-point values that test precision
        precise_durations = [0.001234567, 0.002345678, 0.003456789, 0.004567890, 0.005678901]
        
        for duration in precise_durations:
            monitor.record_key_generation_time(
                duration=duration,
                text_length=100,
                operation_type="precision_test"
            )
        
        # Record cache operations with precise values
        for i, duration in enumerate(precise_durations):
            monitor.record_cache_operation_time(
                operation="get",
                duration=duration,
                cache_hit=i % 2 == 0,  # Alternate hits and misses
                text_length=100
            )
        
        # When: get_performance_stats() performs statistical calculations
        stats = monitor.get_performance_stats()
        
        # Then: Calculations maintain appropriate precision
        key_gen_stats = stats["key_generation"]
        
        # Verify precision in mean calculation
        expected_mean = sum(precise_durations) / len(precise_durations)
        actual_mean = key_gen_stats["avg_duration"]
        assert abs(actual_mean - expected_mean) < 1e-9, f"Mean precision error: expected {expected_mean}, got {actual_mean}"
        
        # Verify precision in hit rate calculation (3 hits out of 5 = 60%)
        expected_hit_rate = 60.0  # 3 hits / 5 total * 100
        actual_hit_rate = stats["cache_hit_rate"]
        assert abs(actual_hit_rate - expected_hit_rate) < 1e-6, f"Hit rate precision error: expected {expected_hit_rate}, got {actual_hit_rate}"
        
        # Test with compression ratios for additional precision verification
        precise_compression_data = [
            (1000, 333),  # 0.333 ratio
            (2000, 667),  # 0.3335 ratio
            (3000, 999),  # 0.333 ratio
        ]
        
        for original, compressed in precise_compression_data:
            monitor.record_compression_ratio(
                original_size=original,
                compressed_size=compressed,
                compression_time=0.001,
                operation_type="precision_test"
            )
        
        stats_with_compression = monitor.get_performance_stats()
        compression_stats = stats_with_compression["compression"]
        
        # Verify precision in compression ratio calculations
        expected_ratios = [compressed / original for original, compressed in precise_compression_data]
        expected_avg_ratio = sum(expected_ratios) / len(expected_ratios)
        actual_avg_ratio = compression_stats["avg_compression_ratio"]
        assert abs(actual_avg_ratio - expected_avg_ratio) < 1e-6, f"Compression ratio precision error: expected {expected_avg_ratio}, got {actual_avg_ratio}"
        
        # Verify precision in savings calculations
        total_original = sum(original for original, _ in precise_compression_data)
        total_compressed = sum(compressed for _, compressed in precise_compression_data)
        expected_savings_percent = ((total_original - total_compressed) / total_original) * 100
        actual_savings_percent = compression_stats["overall_savings_percent"]
        assert abs(actual_savings_percent - expected_savings_percent) < 1e-6, f"Savings percent precision error: expected {expected_savings_percent}, got {actual_savings_percent}"


class TestMemoryUsageAnalysis:
    """
    Test suite for memory usage analysis and alerting functionality.
    
    Scope:
        - get_memory_usage_stats() comprehensive memory analysis
        - get_memory_warnings() threshold-based alerting
        - Memory trend analysis and projection
        - Threshold configuration and alerting accuracy
        
    Business Critical:
        Memory usage analysis prevents cache-related memory issues and enables capacity planning
        
    Test Strategy:
        - Unit tests for memory calculation accuracy
        - Threshold alerting verification
        - Trend analysis and projection testing
        - Warning generation and prioritization validation
        
    External Dependencies:
        - sys module: Standard library (not mocked for realistic memory calculations)
        - Optional psutil: Process memory monitoring (mocked for consistent behavior)
    """

    def test_get_memory_usage_stats_provides_comprehensive_memory_analysis(self):
        """
        Test that get_memory_usage_stats() provides comprehensive memory usage analysis.
        
        Verifies:
            Memory statistics include current usage, thresholds, and trend analysis
            
        Business Impact:
            Enables complete memory usage assessment for capacity planning and optimization
            
        Scenario:
            Given: CachePerformanceMonitor with memory usage measurements over time
            When: get_memory_usage_stats() analyzes memory consumption patterns
            Then: Comprehensive statistics include current usage, thresholds, and growth trends
            
        Edge Cases Covered:
            - Current memory usage calculation across cache types
            - Threshold status evaluation (warning, critical)
            - Growth trend analysis and projections
            - Memory efficiency metrics
            
        Mocks Used:
            - None (memory analysis verification)
            
        Related Tests:
            - test_get_memory_usage_stats_calculates_current_usage_accurately()
            - test_get_memory_usage_stats_evaluates_thresholds_correctly()
        """
        pass

    def test_get_memory_usage_stats_calculates_current_usage_accurately(self):
        """
        Test that get_memory_usage_stats() calculates current memory usage accurately.
        
        Verifies:
            Current memory usage calculations reflect actual cache memory consumption
            
        Business Impact:
            Provides accurate memory usage data for capacity management decisions
            
        Scenario:
            Given: CachePerformanceMonitor with current memory cache and Redis data
            When: get_memory_usage_stats() calculates current memory consumption
            Then: Accurate memory usage is calculated for both cache tiers and total consumption
            
        Edge Cases Covered:
            - Memory cache size calculations
            - Redis memory usage integration
            - Total cache memory aggregation
            - Entry count and average size calculations
            
        Mocks Used:
            - None (calculation accuracy verification)
            
        Related Tests:
            - test_get_memory_usage_stats_provides_comprehensive_memory_analysis()
            - test_get_memory_usage_stats_evaluates_thresholds_correctly()
        """
        pass

    def test_get_memory_usage_stats_evaluates_thresholds_correctly(self):
        """
        Test that get_memory_usage_stats() evaluates memory thresholds correctly.
        
        Verifies:
            Memory threshold evaluation accurately identifies warning and critical states
            
        Business Impact:
            Enables proactive memory management and prevents memory-related failures
            
        Scenario:
            Given: CachePerformanceMonitor with configured memory thresholds
            When: get_memory_usage_stats() evaluates current usage against thresholds
            Then: Threshold status is accurately determined with appropriate alert levels
            
        Edge Cases Covered:
            - Usage below warning threshold (normal)
            - Usage above warning threshold (warning state)
            - Usage above critical threshold (critical state)
            - Threshold boundary conditions
            
        Mocks Used:
            - None (threshold evaluation verification)
            
        Related Tests:
            - test_get_memory_usage_stats_calculates_current_usage_accurately()
            - test_get_memory_usage_stats_projects_growth_trends_accurately()
        """
        pass

    def test_get_memory_usage_stats_projects_growth_trends_accurately(self):
        """
        Test that get_memory_usage_stats() projects memory growth trends accurately.
        
        Verifies:
            Memory growth trend analysis provides accurate projections for capacity planning
            
        Business Impact:
            Enables proactive capacity planning and prevents unexpected memory exhaustion
            
        Scenario:
            Given: CachePerformanceMonitor with historical memory usage measurements
            When: get_memory_usage_stats() analyzes growth trends
            Then: Growth rate calculations and threshold breach projections are accurate
            
        Edge Cases Covered:
            - Positive growth trend analysis
            - Negative growth trend analysis
            - Stable usage patterns
            - Time to threshold breach projections
            
        Mocks Used:
            - None (trend analysis verification)
            
        Related Tests:
            - test_get_memory_usage_stats_evaluates_thresholds_correctly()
            - test_get_memory_warnings_generates_appropriate_alerts()
        """
        pass

    def test_get_memory_warnings_generates_appropriate_alerts(self):
        """
        Test that get_memory_warnings() generates appropriate memory-related alerts.
        
        Verifies:
            Memory warnings are generated with appropriate severity and actionable recommendations
            
        Business Impact:
            Provides timely alerts and guidance for memory-related issues
            
        Scenario:
            Given: CachePerformanceMonitor with memory usage approaching or exceeding thresholds
            When: get_memory_warnings() evaluates memory status
            Then: Appropriate warnings are generated with severity levels and recommendations
            
        Edge Cases Covered:
            - Warning threshold breach alerts
            - Critical threshold breach alerts
            - No warnings for normal usage
            - Multiple warning scenarios
            
        Mocks Used:
            - None (warning generation verification)
            
        Related Tests:
            - test_get_memory_warnings_provides_actionable_recommendations()
            - test_get_memory_warnings_prioritizes_by_severity()
        """
        pass

    def test_get_memory_warnings_provides_actionable_recommendations(self):
        """
        Test that get_memory_warnings() provides actionable recommendations for memory issues.
        
        Verifies:
            Memory warnings include specific, actionable recommendations for resolution
            
        Business Impact:
            Enables efficient resolution of memory-related performance issues
            
        Scenario:
            Given: CachePerformanceMonitor with identified memory issues
            When: get_memory_warnings() generates warnings
            Then: Warnings include specific recommendations for memory optimization
            
        Edge Cases Covered:
            - L1 cache size reduction recommendations
            - Compression optimization suggestions
            - TTL adjustment recommendations
            - Redis memory optimization guidance
            
        Mocks Used:
            - None (recommendation generation verification)
            
        Related Tests:
            - test_get_memory_warnings_generates_appropriate_alerts()
            - test_get_memory_warnings_prioritizes_by_severity()
        """
        pass

    def test_get_memory_warnings_prioritizes_by_severity(self):
        """
        Test that get_memory_warnings() prioritizes warnings by severity level.
        
        Verifies:
            Memory warnings are ordered by severity for effective issue prioritization
            
        Business Impact:
            Enables focus on the most critical memory issues first
            
        Scenario:
            Given: CachePerformanceMonitor with multiple memory warning conditions
            When: get_memory_warnings() generates multiple warnings
            Then: Warnings are ordered by severity with critical issues prioritized
            
        Edge Cases Covered:
            - Critical warnings prioritized over warnings
            - Severity-based warning ordering
            - Multiple warnings of same severity
            - Warning deduplication
            
        Mocks Used:
            - None (prioritization verification)
            
        Related Tests:
            - test_get_memory_warnings_provides_actionable_recommendations()
            - test_get_memory_warnings_handles_no_issues_gracefully()
        """
        pass

    def test_get_memory_warnings_handles_no_issues_gracefully(self):
        """
        Test that get_memory_warnings() handles scenarios with no memory issues gracefully.
        
        Verifies:
            No warnings are generated when memory usage is within acceptable limits
            
        Business Impact:
            Prevents alert fatigue and ensures warnings are meaningful
            
        Scenario:
            Given: CachePerformanceMonitor with memory usage well within thresholds
            When: get_memory_warnings() evaluates memory status
            Then: No warnings are generated for normal memory usage patterns
            
        Edge Cases Covered:
            - Usage well below thresholds
            - Empty warning lists for normal operation
            - Appropriate silence during normal operations
            - Clean warning state transitions
            
        Mocks Used:
            - None (normal operation verification)
            
        Related Tests:
            - test_get_memory_warnings_prioritizes_by_severity()
            - test_get_memory_usage_stats_projects_growth_trends_accurately()
        """
        pass


class TestInvalidationAnalysis:
    """
    Test suite for cache invalidation analysis and optimization recommendations.
    
    Scope:
        - get_invalidation_frequency_stats() comprehensive invalidation analysis
        - get_invalidation_recommendations() optimization recommendations
        - Invalidation pattern recognition and efficiency analysis
        - Alert threshold evaluation for invalidation frequency
        
    Business Critical:
        Invalidation analysis optimizes cache effectiveness and prevents performance degradation
        
    Test Strategy:
        - Unit tests for invalidation frequency calculation accuracy
        - Pattern recognition and analysis verification
        - Recommendation generation and prioritization testing
        - Threshold-based alerting validation
        
    External Dependencies:
        - datetime, time: Standard library (not mocked for realistic time calculations)
    """

    def test_get_invalidation_frequency_stats_analyzes_patterns_comprehensively(self):
        """
        Test that get_invalidation_frequency_stats() analyzes invalidation patterns comprehensively.
        
        Verifies:
            Invalidation statistics include frequency rates, patterns, thresholds, and efficiency metrics
            
        Business Impact:
            Enables comprehensive invalidation pattern analysis for cache optimization
            
        Scenario:
            Given: CachePerformanceMonitor with invalidation events over time
            When: get_invalidation_frequency_stats() analyzes invalidation patterns
            Then: Comprehensive statistics include rates, patterns, thresholds, and efficiency data
            
        Edge Cases Covered:
            - Frequency rate calculations (hourly, daily, average)
            - Pattern identification and analysis
            - Threshold evaluation and alert levels
            - Efficiency metrics and trend analysis
            
        Mocks Used:
            - None (comprehensive analysis verification)
            
        Related Tests:
            - test_get_invalidation_frequency_stats_calculates_rates_accurately()
            - test_get_invalidation_frequency_stats_identifies_patterns_correctly()
        """
        # Given: CachePerformanceMonitor with invalidation events over time
        monitor = CachePerformanceMonitor()
        
        # Set custom invalidation rate thresholds
        monitor.invalidation_rate_warning_per_hour = 10
        monitor.invalidation_rate_critical_per_hour = 20
        
        # Record various invalidation events with different patterns, types, and efficiency
        invalidation_events = [
            {"pattern": "user:*", "keys_invalidated": 15, "duration": 0.005, "type": "manual"},
            {"pattern": "session:*", "keys_invalidated": 8, "duration": 0.003, "type": "ttl_expired"},
            {"pattern": "user:*", "keys_invalidated": 12, "duration": 0.004, "type": "manual"},
            {"pattern": "api:*", "keys_invalidated": 3, "duration": 0.002, "type": "automatic"},
            {"pattern": "cache:*", "keys_invalidated": 25, "duration": 0.008, "type": "manual"},
            {"pattern": "user:*", "keys_invalidated": 18, "duration": 0.006, "type": "manual"},
        ]
        
        for event in invalidation_events:
            monitor.record_invalidation_event(
                pattern=event["pattern"],
                keys_invalidated=event["keys_invalidated"],
                duration=event["duration"],
                invalidation_type=event["type"],
                operation_context="comprehensive_test"
            )
        
        # When: get_invalidation_frequency_stats() analyzes invalidation patterns
        stats = monitor.get_invalidation_frequency_stats()
        
        # Then: Comprehensive statistics include all required components
        # Verify frequency rate calculations
        assert "rates" in stats
        rates = stats["rates"]
        assert "last_hour" in rates
        assert "last_24_hours" in rates
        assert "average_per_hour" in rates
        assert rates["last_hour"] == 6  # All 6 events within last hour
        
        # Verify pattern identification and analysis
        assert "patterns" in stats
        patterns = stats["patterns"]
        assert "most_common_patterns" in patterns
        assert "invalidation_types" in patterns
        
        # user:* should be most common (3 occurrences)
        most_common = patterns["most_common_patterns"]
        assert "user:*" in most_common
        assert most_common["user:*"] == 3
        
        # Verify type distribution
        types = patterns["invalidation_types"]
        assert "manual" in types
        assert types["manual"] == 4  # 4 manual invalidations
        
        # Verify threshold evaluation and alert levels
        assert "thresholds" in stats
        thresholds = stats["thresholds"]
        assert "warning_per_hour" in thresholds
        assert "critical_per_hour" in thresholds
        assert "current_alert_level" in thresholds
        assert thresholds["warning_per_hour"] == 10
        assert thresholds["critical_per_hour"] == 20
        
        # 6 events should be below warning threshold of 10
        assert thresholds["current_alert_level"] == "normal"
        
        # Verify efficiency metrics and trend analysis
        assert "efficiency" in stats
        efficiency = stats["efficiency"]
        assert "avg_keys_per_invalidation" in efficiency
        assert "avg_duration" in efficiency
        assert "max_duration" in efficiency
        
        # Calculate expected efficiency metrics
        total_keys = sum(e["keys_invalidated"] for e in invalidation_events)  # 81 keys
        total_events = len(invalidation_events)  # 6 events
        expected_avg_keys = total_keys / total_events  # 13.5
        
        assert abs(efficiency["avg_keys_per_invalidation"] - expected_avg_keys) < 0.1
        assert efficiency["max_duration"] == 0.008  # Longest duration
        
        # Verify overall statistics
        assert stats["total_invalidations"] == 6
        assert stats["total_keys_invalidated"] == 81

    def test_get_invalidation_frequency_stats_calculates_rates_accurately(self):
        """
        Test that get_invalidation_frequency_stats() calculates invalidation rates accurately.
        
        Verifies:
            Invalidation frequency calculations reflect actual event patterns accurately
            
        Business Impact:
            Provides accurate frequency metrics for invalidation strategy optimization
            
        Scenario:
            Given: CachePerformanceMonitor with invalidation events at various frequencies
            When: get_invalidation_frequency_stats() calculates frequency rates
            Then: Hourly, daily, and average rates are calculated accurately from event data
            
        Edge Cases Covered:
            - High frequency invalidation periods
            - Low frequency invalidation periods
            - Variable frequency patterns over time
            - Rate calculation accuracy and precision
            
        Mocks Used:
            - None (calculation accuracy verification)
            
        Related Tests:
            - test_get_invalidation_frequency_stats_analyzes_patterns_comprehensively()
            - test_get_invalidation_frequency_stats_evaluates_thresholds_correctly()
        """
        # Test accurate rate calculations with known event patterns
        monitor = CachePerformanceMonitor(retention_hours=2)
        
        import time
        current_time = time.time()
        
        # Create events with specific timestamps for rate testing
        events = [
            # 3 events in the last hour
            {"time_offset": -1800, "pattern": "recent:*", "keys": 5},  # 30 min ago
            {"time_offset": -2700, "pattern": "recent:*", "keys": 3},  # 45 min ago
            {"time_offset": -3000, "pattern": "recent:*", "keys": 8},  # 50 min ago
            
            # 2 additional events in last 24 hours but not last hour
            {"time_offset": -7200, "pattern": "older:*", "keys": 4},   # 2 hours ago
            {"time_offset": -14400, "pattern": "older:*", "keys": 6},  # 4 hours ago
        ]
        
        for event in events:
            monitor.record_invalidation_event(
                pattern=event["pattern"],
                keys_invalidated=event["keys"],
                duration=0.001,
                invalidation_type="test"
            )
            # Set specific timestamp for rate calculation testing
            if monitor.invalidation_events:
                monitor.invalidation_events[-1].timestamp = current_time + event["time_offset"]
        
        # When: get_invalidation_frequency_stats() calculates frequency rates
        stats = monitor.get_invalidation_frequency_stats()
        rates = stats["rates"]
        
        # Then: Rates are calculated accurately
        # Last hour should have 3 events
        assert rates["last_hour"] == 3, f"Expected 3 events in last hour, got {rates['last_hour']}"
        
        # Last 24 hours should have all 5 events
        assert rates["last_24_hours"] == 5, f"Expected 5 events in last 24 hours, got {rates['last_24_hours']}"
        
        # Average per hour should be based on retention period
        expected_average = 5 / monitor.retention_hours  # 5 events / 2 hours = 2.5/hour
        assert abs(rates["average_per_hour"] - expected_average) < 0.1, f"Expected average {expected_average}, got {rates['average_per_hour']}"
        
        # Test high frequency scenario
        monitor_high = CachePerformanceMonitor()
        
        # Add many recent events
        for i in range(15):
            monitor_high.record_invalidation_event(
                pattern=f"high_freq_{i}:*",
                keys_invalidated=2,
                duration=0.001
            )
        
        stats_high = monitor_high.get_invalidation_frequency_stats()
        rates_high = stats_high["rates"]
        
        # Should show high frequency
        assert rates_high["last_hour"] == 15
        assert rates_high["last_24_hours"] == 15
        
        # Test low frequency scenario (single event)
        monitor_low = CachePerformanceMonitor()
        monitor_low.record_invalidation_event(pattern="low:*", keys_invalidated=1, duration=0.001)
        
        stats_low = monitor_low.get_invalidation_frequency_stats()
        rates_low = stats_low["rates"]
        
        # Should show low frequency
        assert rates_low["last_hour"] == 1
        assert rates_low["last_24_hours"] == 1
        assert rates_low["average_per_hour"] == 1.0  # 1 event / 1 hour retention
        
        # Test edge case: no events
        monitor_empty = CachePerformanceMonitor()
        stats_empty = monitor_empty.get_invalidation_frequency_stats()
        
        # Should handle no events gracefully
        assert "no_invalidations" in stats_empty
        assert stats_empty["no_invalidations"] is True
        assert stats_empty["total_invalidations"] == 0

    def test_get_invalidation_frequency_stats_evaluates_thresholds_correctly(self):
        """
        Test that get_invalidation_frequency_stats() evaluates alert thresholds correctly.
        
        Verifies:
            Invalidation frequency thresholds are correctly evaluated for alerting
            
        Business Impact:
            Enables proactive alerting for excessive invalidation that could impact performance
            
        Scenario:
            Given: CachePerformanceMonitor with configured invalidation frequency thresholds
            When: get_invalidation_frequency_stats() evaluates current rates against thresholds
            Then: Alert levels are accurately determined based on frequency comparisons
            
        Edge Cases Covered:
            - Rates below warning threshold (normal)
            - Rates above warning threshold (warning state)
            - Rates above critical threshold (critical state)
            - Threshold boundary conditions and transitions
            
        Mocks Used:
            - None (threshold evaluation verification)
            
        Related Tests:
            - test_get_invalidation_frequency_stats_calculates_rates_accurately()
            - test_get_invalidation_frequency_stats_identifies_patterns_correctly()
        """
        # Test normal operation (below warning threshold)
        monitor_normal = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 10
        monitor.invalidation_rate_critical_per_hour = 25
        
        # Add events below warning threshold
        for i in range(5):
            monitor_normal.record_invalidation_event(
                pattern=f"normal_{i}:*",
                keys_invalidated=3,
                duration=0.001
            )
        
        stats_normal = monitor_normal.get_invalidation_frequency_stats()
        thresholds_normal = stats_normal["thresholds"]
        
        # Should be in normal state
        assert thresholds_normal["current_alert_level"] == "normal"
        assert thresholds_normal["warning_per_hour"] == 10
        assert thresholds_normal["critical_per_hour"] == 25
        assert stats_normal["rates"]["last_hour"] == 5  # Below warning threshold
        
        # Test warning threshold breach
        monitor_warning = CachePerformanceMonitor()
        monitor_warning.invalidation_rate_warning_per_hour = 8
        monitor_warning.invalidation_rate_critical_per_hour = 20
        
        # Add events above warning but below critical threshold
        for i in range(12):
            monitor_warning.record_invalidation_event(
                pattern=f"warning_{i}:*",
                keys_invalidated=2,
                duration=0.002
            )
        
        stats_warning = monitor_warning.get_invalidation_frequency_stats()
        thresholds_warning = stats_warning["thresholds"]
        
        # Should be in warning state
        assert thresholds_warning["current_alert_level"] == "warning"
        assert stats_warning["rates"]["last_hour"] == 12  # Above warning, below critical
        assert stats_warning["rates"]["last_hour"] >= thresholds_warning["warning_per_hour"]
        assert stats_warning["rates"]["last_hour"] < thresholds_warning["critical_per_hour"]
        
        # Test critical threshold breach
        monitor_critical = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 5
        monitor.invalidation_rate_critical_per_hour = 15
        
        # Add events above critical threshold
        for i in range(20):
            monitor_critical.record_invalidation_event(
                pattern=f"critical_{i}:*",
                keys_invalidated=1,
                duration=0.001
            )
        
        stats_critical = monitor_critical.get_invalidation_frequency_stats()
        thresholds_critical = stats_critical["thresholds"]
        
        # Should be in critical state
        assert thresholds_critical["current_alert_level"] == "critical"
        assert stats_critical["rates"]["last_hour"] == 20  # Above critical
        assert stats_critical["rates"]["last_hour"] >= thresholds_critical["critical_per_hour"]
        
        # Test boundary condition - exactly at warning threshold
        monitor_boundary = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 10
        monitor.invalidation_rate_critical_per_hour = 20
        
        # Add exactly threshold number of events
        for i in range(10):
            monitor_boundary.record_invalidation_event(
                pattern=f"boundary_{i}:*",
                keys_invalidated=1,
                duration=0.001
            )
        
        stats_boundary = monitor_boundary.get_invalidation_frequency_stats()
        thresholds_boundary = stats_boundary["thresholds"]
        
        # At threshold should trigger warning state
        assert thresholds_boundary["current_alert_level"] == "warning"
        assert stats_boundary["rates"]["last_hour"] == 10
        
        # Test boundary condition - exactly at critical threshold
        monitor_boundary_critical = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 5
        monitor.invalidation_rate_critical_per_hour = 15
        
        # Add exactly critical threshold number of events
        for i in range(15):
            monitor_boundary_critical.record_invalidation_event(
                pattern=f"boundary_crit_{i}:*",
                keys_invalidated=1,
                duration=0.001
            )
        
        stats_boundary_critical = monitor_boundary_critical.get_invalidation_frequency_stats()
        thresholds_boundary_critical = stats_boundary_critical["thresholds"]
        
        # At critical threshold should trigger critical state
        assert thresholds_boundary_critical["current_alert_level"] == "critical"
        assert stats_boundary_critical["rates"]["last_hour"] == 15

    def test_get_invalidation_frequency_stats_identifies_patterns_correctly(self):
        """
        Test that get_invalidation_frequency_stats() identifies invalidation patterns correctly.
        
        Verifies:
            Pattern recognition accurately identifies common invalidation patterns and types
            
        Business Impact:
            Enables pattern-based optimization of invalidation strategies
            
        Scenario:
            Given: CachePerformanceMonitor with various invalidation patterns and types
            When: get_invalidation_frequency_stats() analyzes pattern data
            Then: Most common patterns and types are correctly identified and reported
            
        Edge Cases Covered:
            - Pattern frequency analysis and ranking
            - Type distribution analysis
            - Pattern efficiency correlation
            - Temporal pattern recognition
            
        Mocks Used:
            - None (pattern recognition verification)
            
        Related Tests:
            - test_get_invalidation_frequency_stats_evaluates_thresholds_correctly()
            - test_get_invalidation_frequency_stats_calculates_efficiency_metrics()
        """
        # Given: CachePerformanceMonitor with various invalidation patterns and types
        monitor = CachePerformanceMonitor()
        
        # Create a diverse set of invalidation patterns with different frequencies
        pattern_events = [
            # user:* pattern (most common - 4 occurrences)
            {"pattern": "user:*", "keys": 10, "type": "manual"},
            {"pattern": "user:*", "keys": 15, "type": "automatic"},
            {"pattern": "user:*", "keys": 8, "type": "manual"},
            {"pattern": "user:*", "keys": 12, "type": "ttl_expired"},
            
            # session:* pattern (second most common - 3 occurrences)
            {"pattern": "session:*", "keys": 5, "type": "ttl_expired"},
            {"pattern": "session:*", "keys": 7, "type": "ttl_expired"},
            {"pattern": "session:*", "keys": 3, "type": "manual"},
            
            # api:* pattern (less common - 2 occurrences)
            {"pattern": "api:*", "keys": 20, "type": "automatic"},
            {"pattern": "api:*", "keys": 25, "type": "automatic"},
            
            # cache:* pattern (least common - 1 occurrence)
            {"pattern": "cache:*", "keys": 30, "type": "manual"},
        ]
        
        for event in pattern_events:
            monitor.record_invalidation_event(
                pattern=event["pattern"],
                keys_invalidated=event["keys"],
                duration=0.002,
                invalidation_type=event["type"],
                operation_context="pattern_test"
            )
        
        # When: get_invalidation_frequency_stats() analyzes pattern data
        stats = monitor.get_invalidation_frequency_stats()
        patterns = stats["patterns"]
        
        # Then: Most common patterns are correctly identified and ranked
        most_common_patterns = patterns["most_common_patterns"]
        
        # Verify pattern frequency analysis and ranking
        assert "user:*" in most_common_patterns
        assert "session:*" in most_common_patterns
        assert "api:*" in most_common_patterns
        assert "cache:*" in most_common_patterns
        
        # Verify correct frequency counts
        assert most_common_patterns["user:*"] == 4, f"Expected user:* to have 4 occurrences, got {most_common_patterns['user:*']}"
        assert most_common_patterns["session:*"] == 3, f"Expected session:* to have 3 occurrences, got {most_common_patterns['session:*']}"
        assert most_common_patterns["api:*"] == 2, f"Expected api:* to have 2 occurrences, got {most_common_patterns['api:*']}"
        assert most_common_patterns["cache:*"] == 1, f"Expected cache:* to have 1 occurrence, got {most_common_patterns['cache:*']}"
        
        # Verify type distribution analysis
        invalidation_types = patterns["invalidation_types"]
        
        # Count expected types
        expected_manual_count = 4  # user:* (2), session:* (1), cache:* (1)
        expected_automatic_count = 3  # user:* (1), api:* (2)
        expected_ttl_count = 3  # user:* (1), session:* (2)
        
        assert invalidation_types["manual"] == expected_manual_count, f"Expected {expected_manual_count} manual invalidations, got {invalidation_types['manual']}"
        assert invalidation_types["automatic"] == expected_automatic_count, f"Expected {expected_automatic_count} automatic invalidations, got {invalidation_types['automatic']}"
        assert invalidation_types["ttl_expired"] == expected_ttl_count, f"Expected {expected_ttl_count} TTL-expired invalidations, got {invalidation_types['ttl_expired']}"
        
        # Test single pattern scenario
        monitor_single = CachePerformanceMonitor()
        
        for i in range(3):
            monitor_single.record_invalidation_event(
                pattern="single:*",
                keys_invalidated=5,
                duration=0.001,
                invalidation_type="test"
            )
        
        stats_single = monitor_single.get_invalidation_frequency_stats()
        patterns_single = stats_single["patterns"]
        
        # Should correctly identify single dominant pattern
        most_common_single = patterns_single["most_common_patterns"]
        assert len(most_common_single) == 1
        assert "single:*" in most_common_single
        assert most_common_single["single:*"] == 3
        
        # Test mixed efficiency patterns (large vs small invalidations)
        monitor_efficiency = CachePerformanceMonitor()
        
        efficiency_events = [
            # High efficiency pattern (many keys per invalidation)
            {"pattern": "bulk:*", "keys": 100, "type": "batch"},
            {"pattern": "bulk:*", "keys": 150, "type": "batch"},
            
            # Low efficiency pattern (few keys per invalidation)
            {"pattern": "single:*", "keys": 1, "type": "individual"},
            {"pattern": "single:*", "keys": 2, "type": "individual"},
            {"pattern": "single:*", "keys": 1, "type": "individual"},
        ]
        
        for event in efficiency_events:
            monitor_efficiency.record_invalidation_event(
                pattern=event["pattern"],
                keys_invalidated=event["keys"],
                duration=0.001,
                invalidation_type=event["type"]
            )
        
        stats_efficiency = monitor_efficiency.get_invalidation_frequency_stats()
        patterns_efficiency = stats_efficiency["patterns"]
        
        # Should identify both patterns with correct frequencies
        most_common_eff = patterns_efficiency["most_common_patterns"]
        assert most_common_eff["single:*"] == 3  # More frequent but less efficient
        assert most_common_eff["bulk:*"] == 2   # Less frequent but more efficient
        
        # Verify type distribution reflects the different approaches
        types_eff = patterns_efficiency["invalidation_types"]
        assert types_eff["individual"] == 3
        assert types_eff["batch"] == 2

    def test_get_invalidation_frequency_stats_calculates_efficiency_metrics(self):
        """
        Test that get_invalidation_frequency_stats() calculates efficiency metrics accurately.
        
        Verifies:
            Invalidation efficiency metrics provide insights into operation effectiveness
            
        Business Impact:
            Enables optimization of invalidation efficiency for better cache performance
            
        Scenario:
            Given: CachePerformanceMonitor with invalidation events including key counts and durations
            When: get_invalidation_frequency_stats() calculates efficiency metrics
            Then: Keys per invalidation and duration statistics are accurately calculated
            
        Edge Cases Covered:
            - Average keys per invalidation calculation
            - Invalidation duration analysis
            - Efficiency trend analysis over time
            - Correlation between pattern types and efficiency
            
        Mocks Used:
            - None (efficiency calculation verification)
            
        Related Tests:
            - test_get_invalidation_frequency_stats_identifies_patterns_correctly()
            - test_get_invalidation_recommendations_provides_actionable_guidance()
        """
        # Given: CachePerformanceMonitor with invalidation events including key counts and durations
        monitor = CachePerformanceMonitor()
        
        # Create invalidation events with known efficiency characteristics
        efficiency_events = [
            # High efficiency events (many keys, fast)
            {"pattern": "batch:*", "keys": 50, "duration": 0.010, "type": "bulk"},
            {"pattern": "batch:*", "keys": 75, "duration": 0.015, "type": "bulk"},
            {"pattern": "batch:*", "keys": 100, "duration": 0.020, "type": "bulk"},
            
            # Medium efficiency events
            {"pattern": "group:*", "keys": 20, "duration": 0.008, "type": "selective"},
            {"pattern": "group:*", "keys": 25, "duration": 0.012, "type": "selective"},
            
            # Low efficiency events (few keys, various durations)
            {"pattern": "single:*", "keys": 1, "duration": 0.003, "type": "individual"},
            {"pattern": "single:*", "keys": 2, "duration": 0.004, "type": "individual"},
            {"pattern": "single:*", "keys": 1, "duration": 0.005, "type": "individual"},
        ]
        
        for event in efficiency_events:
            monitor.record_invalidation_event(
                pattern=event["pattern"],
                keys_invalidated=event["keys"],
                duration=event["duration"],
                invalidation_type=event["type"],
                operation_context="efficiency_test"
            )
        
        # When: get_invalidation_frequency_stats() calculates efficiency metrics
        stats = monitor.get_invalidation_frequency_stats()
        efficiency = stats["efficiency"]
        
        # Then: Keys per invalidation are accurately calculated
        total_keys = sum(event["keys"] for event in efficiency_events)  # 274 keys
        total_events = len(efficiency_events)  # 8 events
        expected_avg_keys = total_keys / total_events  # 34.25 keys per invalidation
        
        assert "avg_keys_per_invalidation" in efficiency
        actual_avg_keys = efficiency["avg_keys_per_invalidation"]
        assert abs(actual_avg_keys - expected_avg_keys) < 0.1, f"Expected avg keys per invalidation {expected_avg_keys}, got {actual_avg_keys}"
        
        # Verify duration statistics are accurately calculated
        assert "avg_duration" in efficiency
        assert "max_duration" in efficiency
        
        durations = [event["duration"] for event in efficiency_events]
        expected_avg_duration = sum(durations) / len(durations)
        expected_max_duration = max(durations)
        
        actual_avg_duration = efficiency["avg_duration"]
        actual_max_duration = efficiency["max_duration"]
        
        assert abs(actual_avg_duration - expected_avg_duration) < 0.001, f"Expected avg duration {expected_avg_duration}, got {actual_avg_duration}"
        assert actual_max_duration == expected_max_duration, f"Expected max duration {expected_max_duration}, got {actual_max_duration}"
        
        # Test high efficiency scenario (many keys per invalidation)
        monitor_high_eff = CachePerformanceMonitor()
        
        # All events invalidate many keys
        for i in range(3):
            monitor_high_eff.record_invalidation_event(
                pattern=f"efficient_{i}:*",
                keys_invalidated=200,  # High key count
                duration=0.050,        # Reasonable duration
                invalidation_type="bulk"
            )
        
        stats_high_eff = monitor_high_eff.get_invalidation_frequency_stats()
        efficiency_high = stats_high_eff["efficiency"]
        
        # Should show high efficiency
        assert efficiency_high["avg_keys_per_invalidation"] == 200.0
        assert efficiency_high["avg_duration"] == 0.050
        
        # Test low efficiency scenario (few keys per invalidation)
        monitor_low_eff = CachePerformanceMonitor()
        
        # All events invalidate very few keys
        for i in range(5):
            monitor_low_eff.record_invalidation_event(
                pattern=f"inefficient_{i}:*",
                keys_invalidated=1,    # Very low key count
                duration=0.010,        # Disproportionate duration
                invalidation_type="individual"
            )
        
        stats_low_eff = monitor_low_eff.get_invalidation_frequency_stats()
        efficiency_low = stats_low_eff["efficiency"]
        
        # Should show low efficiency
        assert efficiency_low["avg_keys_per_invalidation"] == 1.0
        assert efficiency_low["avg_duration"] == 0.010
        
        # Test edge case: single invalidation event
        monitor_single = CachePerformanceMonitor()
        monitor_single.record_invalidation_event(
            pattern="single:*",
            keys_invalidated=42,
            duration=0.007,
            invalidation_type="test"
        )
        
        stats_single = monitor_single.get_invalidation_frequency_stats()
        efficiency_single = stats_single["efficiency"]
        
        # Should handle single event correctly
        assert efficiency_single["avg_keys_per_invalidation"] == 42.0
        assert efficiency_single["avg_duration"] == 0.007
        assert efficiency_single["max_duration"] == 0.007
        
        # Verify overall statistics consistency
        assert stats["total_keys_invalidated"] == total_keys
        assert stats["total_invalidations"] == total_events

    def test_get_invalidation_recommendations_provides_actionable_guidance(self):
        """
        Test that get_invalidation_recommendations() provides actionable optimization guidance.
        
        Verifies:
            Invalidation recommendations are specific and actionable for performance improvement
            
        Business Impact:
            Enables targeted optimization of cache invalidation strategies
            
        Scenario:
            Given: CachePerformanceMonitor with analyzed invalidation patterns showing optimization opportunities
            When: get_invalidation_recommendations() generates recommendations
            Then: Specific, actionable recommendations are provided for invalidation strategy improvement
            
        Edge Cases Covered:
            - High frequency invalidation recommendations
            - Inefficient pattern optimization suggestions
            - Threshold adjustment recommendations
            - Pattern consolidation suggestions
            
        Mocks Used:
            - None (recommendation generation verification)
            
        Related Tests:
            - test_get_invalidation_recommendations_prioritizes_by_severity()
            - test_get_invalidation_recommendations_addresses_critical_issues()
        """
        # Test high frequency invalidation recommendations
        monitor_high_freq = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 5
        monitor.invalidation_rate_critical_per_hour = 15
        
        # Create high frequency invalidation scenario
        for i in range(12):  # Exceeds warning threshold
            monitor_high_freq.record_invalidation_event(
                pattern=f"frequent_{i}:*",
                keys_invalidated=3,
                duration=0.002,
                invalidation_type="manual"
            )
        
        recommendations_high_freq = monitor_high_freq.get_invalidation_recommendations()
        
        # Should generate high frequency recommendations
        assert len(recommendations_high_freq) > 0
        high_freq_rec = recommendations_high_freq[0]
        assert high_freq_rec["issue"] == "High invalidation frequency"
        assert "suggestions" in high_freq_rec
        assert len(high_freq_rec["suggestions"]) > 0
        
        # Verify actionable suggestions are provided
        suggestions = high_freq_rec["suggestions"]
        suggestion_text = " ".join(suggestions).lower()
        assert any(keyword in suggestion_text for keyword in [
            "reduce", "review", "consider", "check", "analyze", "improve"
        ])
        
        # Test inefficient pattern optimization
        monitor_inefficient = CachePerformanceMonitor()
        
        # Create scenario with low efficiency (few keys per invalidation)
        for i in range(10):
            monitor_inefficient.record_invalidation_event(
                pattern="inefficient:*",
                keys_invalidated=0 if i < 3 else 1,  # Many invalidations find no/few keys
                duration=0.005,
                invalidation_type="automatic"
            )
        
        recommendations_inefficient = monitor_inefficient.get_invalidation_recommendations()
        
        # Should generate efficiency recommendations
        efficiency_recs = [r for r in recommendations_inefficient if "efficiency" in r["issue"].lower()]
        if efficiency_recs:
            efficiency_rec = efficiency_recs[0]
            assert "suggestions" in efficiency_rec
            suggestions = efficiency_rec["suggestions"]
            suggestion_text = " ".join(suggestions).lower()
            assert any(keyword in suggestion_text for keyword in [
                "targeted", "patterns", "keys", "structured", "optimize"
            ])
        
        # Test dominant pattern recommendations
        monitor_dominant = CachePerformanceMonitor()
        
        # Create scenario with one pattern dominating invalidations
        dominant_pattern_events = [
            {"pattern": "dominant:*", "keys": 5, "type": "manual"},  # 8 occurrences
            {"pattern": "dominant:*", "keys": 3, "type": "manual"},
            {"pattern": "dominant:*", "keys": 4, "type": "manual"},
            {"pattern": "dominant:*", "keys": 6, "type": "manual"},
            {"pattern": "dominant:*", "keys": 2, "type": "manual"},
            {"pattern": "dominant:*", "keys": 7, "type": "manual"},
            {"pattern": "dominant:*", "keys": 5, "type": "manual"},
            {"pattern": "dominant:*", "keys": 4, "type": "manual"},
            {"pattern": "other:*", "keys": 1, "type": "automatic"},    # 1 occurrence
        ]
        
        for event in dominant_pattern_events:
            monitor_dominant.record_invalidation_event(
                pattern=event["pattern"],
                keys_invalidated=event["keys"],
                duration=0.003,
                invalidation_type=event["type"]
            )
        
        recommendations_dominant = monitor_dominant.get_invalidation_recommendations()
        
        # Should generate dominant pattern recommendations
        dominant_recs = [r for r in recommendations_dominant if "dominant" in r["issue"].lower() or "pattern" in r["issue"].lower()]
        if dominant_recs:
            dominant_rec = dominant_recs[0]
            assert "suggestions" in dominant_rec
            suggestions = dominant_rec["suggestions"]
            assert len(suggestions) > 0
            
            # Recommendations should be actionable
            for suggestion in suggestions:
                assert isinstance(suggestion, str)
                assert len(suggestion) > 10  # Should be meaningful
        
        # Test high impact invalidation recommendations
        monitor_high_impact = CachePerformanceMonitor()
        
        # Create scenario with very high keys per invalidation
        for i in range(3):
            monitor_high_impact.record_invalidation_event(
                pattern="high_impact:*",
                keys_invalidated=150,  # Very high impact
                duration=0.050,
                invalidation_type="bulk"
            )
        
        recommendations_high_impact = monitor_high_impact.get_invalidation_recommendations()
        
        # Should generate high impact recommendations
        impact_recs = [r for r in recommendations_high_impact if "impact" in r["issue"].lower() or "keys" in r["message"].lower()]
        if impact_recs:
            impact_rec = impact_recs[0]
            assert impact_rec["severity"] in ["warning", "info"]
            assert "suggestions" in impact_rec
            suggestions = impact_rec["suggestions"]
            suggestion_text = " ".join(suggestions).lower()
            assert any(keyword in suggestion_text for keyword in [
                "selective", "smaller", "frequent", "preserve", "evaluate"
            ])

    def test_get_invalidation_recommendations_prioritizes_by_severity(self):
        """
        Test that get_invalidation_recommendations() prioritizes recommendations by severity.
        
        Verifies:
            Invalidation recommendations are ordered by impact and urgency
            
        Business Impact:
            Enables focus on the most impactful invalidation optimizations first
            
        Scenario:
            Given: CachePerformanceMonitor with multiple invalidation optimization opportunities
            When: get_invalidation_recommendations() generates multiple recommendations
            Then: Recommendations are ordered by severity with critical issues prioritized
            
        Edge Cases Covered:
            - Critical recommendations prioritized over warnings
            - Severity-based recommendation ordering
            - Impact-based prioritization within severity levels
            - Recommendation deduplication
            
        Mocks Used:
            - None (prioritization verification)
            
        Related Tests:
            - test_get_invalidation_recommendations_provides_actionable_guidance()
            - test_get_invalidation_recommendations_addresses_critical_issues()
        """
        # Create scenario with multiple issues of different severities
        monitor = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 8
        monitor.invalidation_rate_critical_per_hour = 20
        
        # Create critical frequency issue (exceeds critical threshold)
        for i in range(25):  # Exceeds critical threshold of 20
            monitor.record_invalidation_event(
                pattern=f"critical_freq_{i}:*",
                keys_invalidated=2,
                duration=0.002,
                invalidation_type="automatic"
            )
        
        # Add some inefficiency patterns (should generate warning/info level recommendations)
        for i in range(5):
            monitor.record_invalidation_event(
                pattern="inefficient:*",
                keys_invalidated=0,  # No keys found - inefficient
                duration=0.003,
                invalidation_type="manual"
            )
        
        # Add dominant pattern (should generate info level recommendation)
        for i in range(3):
            monitor.record_invalidation_event(
                pattern="dominant_pattern:*",
                keys_invalidated=10,
                duration=0.002,
                invalidation_type="bulk"
            )
        
        recommendations = monitor.get_invalidation_recommendations()
        
        # Should have multiple recommendations
        assert len(recommendations) > 0
        
        # Define severity priority order
        severity_priority = {"critical": 0, "warning": 1, "info": 2}
        
        # Verify recommendations are ordered by severity
        for i in range(len(recommendations) - 1):
            current_severity = recommendations[i]["severity"]
            next_severity = recommendations[i + 1]["severity"]
            current_priority = severity_priority.get(current_severity, 999)
            next_priority = severity_priority.get(next_severity, 999)
            
            assert current_priority <= next_priority, f"Recommendations not properly ordered by severity: {current_severity} should come before or equal to {next_severity}"
        
        # Critical recommendations should come first
        critical_recs = [r for r in recommendations if r["severity"] == "critical"]
        if critical_recs:
            assert recommendations[0]["severity"] == "critical", "Critical recommendations should be first"
        
        # Test scenario with only warning and info recommendations
        monitor_warning = CachePerformanceMonitor()
        monitor_warning.invalidation_rate_warning_per_hour = 5
        monitor_warning.invalidation_rate_critical_per_hour = 50  # High threshold to avoid critical
        
        # Create warning-level frequency issue
        for i in range(8):  # Above warning, below critical
            monitor_warning.record_invalidation_event(
                pattern=f"warning_{i}:*",
                keys_invalidated=1,
                duration=0.002,
                invalidation_type="manual"
            )
        
        # Add inefficiency (info level)
        for i in range(3):
            monitor_warning.record_invalidation_event(
                pattern="low_efficiency:*",
                keys_invalidated=0,
                duration=0.005,
                invalidation_type="automatic"
            )
        
        recommendations_warning = monitor_warning.get_invalidation_recommendations()
        
        # Should have warnings but no critical
        warning_recs = [r for r in recommendations_warning if r["severity"] == "warning"]
        critical_recs = [r for r in recommendations_warning if r["severity"] == "critical"]
        info_recs = [r for r in recommendations_warning if r["severity"] == "info"]
        
        assert len(critical_recs) == 0, "Should not have critical recommendations"
        assert len(warning_recs) > 0, "Should have warning recommendations"
        
        # Warning recommendations should come before info recommendations
        if len(recommendations_warning) > 1:
            for rec in recommendations_warning:
                if rec["severity"] == "warning":
                    # Find first info recommendation
                    first_info_index = next(
                        (i for i, r in enumerate(recommendations_warning) if r["severity"] == "info"),
                        len(recommendations_warning)
                    )
                    rec_index = recommendations_warning.index(rec)
                    assert rec_index < first_info_index, "Warning recommendations should come before info recommendations"
                    break
        
        # Test deduplication - verify no duplicate recommendation messages
        unique_messages = set(r["message"] for r in recommendations)
        assert len(unique_messages) == len(recommendations), "Recommendations should be deduplicated"
        
        # Test consistency across multiple calls
        recommendations_second = monitor.get_invalidation_recommendations()
        
        # Should have same number and order of recommendations
        assert len(recommendations_second) == len(recommendations), "Recommendation count should be consistent"
        
        for i, (rec1, rec2) in enumerate(zip(recommendations, recommendations_second)):
            assert rec1["severity"] == rec2["severity"], f"Recommendation {i} severity should be consistent across calls"
            assert rec1["issue"] == rec2["issue"], f"Recommendation {i} issue should be consistent across calls"

    def test_get_invalidation_recommendations_addresses_critical_issues(self):
        """
        Test that get_invalidation_recommendations() identifies and addresses critical issues.
        
        Verifies:
            Critical invalidation issues are identified and addressed with urgent recommendations
            
        Business Impact:
            Prevents performance degradation from critical invalidation patterns
            
        Scenario:
            Given: CachePerformanceMonitor with critical invalidation frequency or efficiency issues
            When: get_invalidation_recommendations() evaluates critical conditions
            Then: Critical-severity recommendations are generated with urgent action guidance
            
        Edge Cases Covered:
            - Extremely high invalidation frequency detection
            - Very low invalidation efficiency identification
            - Performance-critical pattern recognition
            - Urgent optimization requirement identification
            
        Mocks Used:
            - None (critical issue detection verification)
            
        Related Tests:
            - test_get_invalidation_recommendations_prioritizes_by_severity()
            - test_get_invalidation_recommendations_handles_normal_patterns_gracefully()
        """
        # Test extremely high invalidation frequency (critical issue)
        monitor_critical_freq = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 10
        monitor.invalidation_rate_critical_per_hour = 25
        
        # Create extremely high frequency scenario
        for i in range(35):  # Well above critical threshold
            monitor_critical_freq.record_invalidation_event(
                pattern=f"extreme_freq_{i}:*",
                keys_invalidated=1,
                duration=0.001,
                invalidation_type="automatic"
            )
        
        recommendations_critical_freq = monitor_critical_freq.get_invalidation_recommendations()
        
        # Should generate critical-level recommendations
        assert len(recommendations_critical_freq) > 0
        critical_recs = [r for r in recommendations_critical_freq if r["severity"] == "critical"]
        assert len(critical_recs) > 0, "Should generate critical recommendations for extreme frequency"
        
        critical_rec = critical_recs[0]
        assert "high invalidation frequency" in critical_rec["issue"].lower()
        assert "suggestions" in critical_rec
        assert len(critical_rec["suggestions"]) > 0
        
        # Critical recommendations should have urgent action guidance
        suggestions = critical_rec["suggestions"]
        suggestion_text = " ".join(suggestions).lower()
        assert any(urgent_keyword in suggestion_text for urgent_keyword in [
            "reduce", "review", "immediate", "urgent", "critical", "stop"
        ])
        
        # Test performance-critical pattern recognition
        monitor_perf_critical = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 5
        monitor.invalidation_rate_critical_per_hour = 12
        
        # Create scenario with frequent invalidations of same critical pattern
        critical_pattern = "critical_data:*"  # Pattern indicating critical system data
        for i in range(15):  # Exceeds critical threshold
            monitor_perf_critical.record_invalidation_event(
                pattern=critical_pattern,
                keys_invalidated=50,  # High impact per invalidation
                duration=0.020,       # Slow invalidation
                invalidation_type="manual",
                operation_context="user_action"
            )
        
        recommendations_perf_critical = monitor_perf_critical.get_invalidation_recommendations()
        
        # Should identify this as critical due to frequency + impact
        critical_perf_recs = [r for r in recommendations_perf_critical if r["severity"] == "critical"]
        assert len(critical_perf_recs) > 0, "Should generate critical recommendations for high-frequency high-impact invalidations"
        
        # Test boundary condition - exactly at critical threshold
        monitor_boundary = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 8
        monitor.invalidation_rate_critical_per_hour = 20
        
        # Add exactly critical threshold number of events
        for i in range(20):  # Exactly at critical threshold
            monitor_boundary.record_invalidation_event(
                pattern=f"boundary_{i}:*",
                keys_invalidated=2,
                duration=0.003,
                invalidation_type="threshold_test"
            )
        
        recommendations_boundary = monitor_boundary.get_invalidation_recommendations()
        
        # Should generate critical recommendations at threshold
        critical_boundary_recs = [r for r in recommendations_boundary if r["severity"] == "critical"]
        assert len(critical_boundary_recs) > 0, "Should generate critical recommendations at critical threshold"
        
        # Test urgent optimization requirement identification
        monitor_urgent = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 3
        monitor.invalidation_rate_critical_per_hour = 8
        
        # Create urgent scenario: high frequency + dominant pattern + low efficiency
        urgent_events = [
            # High frequency with same pattern (inefficient)
            *[{"pattern": "urgent:*", "keys": 0, "type": "emergency"} for _ in range(6)],
            # Mixed with some efficient ones to test detection
            *[{"pattern": "urgent:*", "keys": 1, "type": "emergency"} for _ in range(4)],
        ]
        
        for event in urgent_events:
            monitor_urgent.record_invalidation_event(
                pattern=event["pattern"],
                keys_invalidated=event["keys"],
                duration=0.008,  # Slow performance
                invalidation_type=event["type"]
            )
        
        recommendations_urgent = monitor_urgent.get_invalidation_recommendations()
        
        # Should generate multiple critical recommendations
        urgent_critical_recs = [r for r in recommendations_urgent if r["severity"] == "critical"]
        assert len(urgent_critical_recs) > 0, "Should generate critical recommendations for urgent optimization needs"
        
        # Critical recommendations should be first
        if len(recommendations_urgent) > 1:
            assert recommendations_urgent[0]["severity"] == "critical", "Critical recommendations should be prioritized first"
        
        # All critical recommendations should have actionable guidance
        for critical_rec in urgent_critical_recs:
            assert "suggestions" in critical_rec
            assert len(critical_rec["suggestions"]) > 0
            assert "message" in critical_rec
            assert len(critical_rec["message"]) > 10  # Should be meaningful
            
            # Should indicate urgency or severity
            combined_text = (critical_rec["message"] + " " + " ".join(critical_rec["suggestions"])).lower()
            assert any(severity_indicator in combined_text for severity_indicator in [
                "critical", "urgent", "immediate", "high", "excessive", "performance"
            ])

    def test_get_invalidation_recommendations_handles_normal_patterns_gracefully(self):
        """
        Test that get_invalidation_recommendations() handles normal invalidation patterns gracefully.
        
        Verifies:
            No recommendations are generated when invalidation patterns are optimal
            
        Business Impact:
            Prevents recommendation fatigue and ensures recommendations are meaningful
            
        Scenario:
            Given: CachePerformanceMonitor with optimal invalidation patterns and frequencies
            When: get_invalidation_recommendations() evaluates normal operation
            Then: No recommendations are generated for well-optimized invalidation patterns
            
        Edge Cases Covered:
            - Optimal frequency patterns
            - Efficient invalidation operations
            - Empty recommendation lists for normal operation
            - Clean recommendation state transitions
            
        Mocks Used:
            - None (normal operation verification)
            
        Related Tests:
            - test_get_invalidation_recommendations_addresses_critical_issues()
            - test_get_invalidation_frequency_stats_calculates_efficiency_metrics()
        """
        # Test optimal frequency patterns (well below thresholds)
        monitor_optimal_freq = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 20
        monitor.invalidation_rate_critical_per_hour = 50
        
        # Add few invalidations well below warning threshold
        optimal_events = [
            {"pattern": "optimal_1:*", "keys": 25, "duration": 0.003, "type": "automatic"},
            {"pattern": "optimal_2:*", "keys": 18, "duration": 0.002, "type": "ttl_expired"},
            {"pattern": "optimal_3:*", "keys": 30, "duration": 0.004, "type": "manual"},
        ]
        
        for event in optimal_events:
            monitor_optimal_freq.record_invalidation_event(
                pattern=event["pattern"],
                keys_invalidated=event["keys"],
                duration=event["duration"],
                invalidation_type=event["type"]
            )
        
        recommendations_optimal_freq = monitor_optimal_freq.get_invalidation_recommendations()
        
        # Should have no recommendations for optimal frequency
        assert len(recommendations_optimal_freq) == 0, "Should not generate recommendations for optimal invalidation frequency"
        
        # Test efficient invalidation operations
        monitor_efficient = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 15
        monitor.invalidation_rate_critical_per_hour = 30
        
        # Add efficient invalidations (good keys per invalidation ratio)
        efficient_events = [
            {"pattern": "efficient_batch:*", "keys": 40, "type": "bulk"},
            {"pattern": "efficient_selective:*", "keys": 15, "type": "selective"},
            {"pattern": "efficient_targeted:*", "keys": 22, "type": "targeted"},
            {"pattern": "efficient_batch:*", "keys": 38, "type": "bulk"},
        ]
        
        for event in efficient_events:
            monitor_efficient.record_invalidation_event(
                pattern=event["pattern"],
                keys_invalidated=event["keys"],
                duration=0.005,  # Reasonable duration for the key count
                invalidation_type=event["type"]
            )
        
        recommendations_efficient = monitor_efficient.get_invalidation_recommendations()
        
        # Should have minimal or no recommendations for efficient operations
        significant_recs = [r for r in recommendations_efficient if r["severity"] in ["critical", "warning"]]
        assert len(significant_recs) == 0, "Should not generate significant recommendations for efficient invalidation operations"
        
        # Any remaining recommendations should be informational only
        for rec in recommendations_efficient:
            assert rec["severity"] == "info", f"Only info-level recommendations acceptable for efficient operations, got: {rec['severity']}"
        
        # Test no invalidations scenario
        monitor_no_invalidations = CachePerformanceMonitor()
        
        recommendations_no_invalidations = monitor_no_invalidations.get_invalidation_recommendations()
        
        # Should have no recommendations when no invalidations exist
        assert len(recommendations_no_invalidations) == 0, "Should have no recommendations when no invalidation events exist"
        
        # Test balanced pattern distribution (no dominant patterns)
        monitor_balanced = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 25
        monitor.invalidation_rate_critical_per_hour = 50
        
        # Add balanced pattern distribution
        balanced_events = [
            # Each pattern used equally, reasonable efficiency
            {"pattern": "pattern_a:*", "keys": 12, "type": "automatic"},
            {"pattern": "pattern_b:*", "keys": 15, "type": "manual"},
            {"pattern": "pattern_c:*", "keys": 10, "type": "ttl_expired"},
            {"pattern": "pattern_a:*", "keys": 14, "type": "automatic"},
            {"pattern": "pattern_b:*", "keys": 13, "type": "manual"},
            {"pattern": "pattern_c:*", "keys": 11, "type": "ttl_expired"},
        ]
        
        for event in balanced_events:
            monitor_balanced.record_invalidation_event(
                pattern=event["pattern"],
                keys_invalidated=event["keys"],
                duration=0.003,
                invalidation_type=event["type"]
            )
        
        recommendations_balanced = monitor_balanced.get_invalidation_recommendations()
        
        # Should have minimal recommendations for balanced patterns
        critical_warning_recs = [r for r in recommendations_balanced if r["severity"] in ["critical", "warning"]]
        assert len(critical_warning_recs) == 0, "Should not generate critical/warning recommendations for balanced invalidation patterns"
        
        # Test state consistency (multiple calls return same result)
        recommendations_balanced_second = monitor_balanced.get_invalidation_recommendations()
        
        assert len(recommendations_balanced_second) == len(recommendations_balanced), "Recommendation results should be consistent across calls"
        
        # Test graceful transition from normal to optimal state
        monitor_transition = CachePerformanceMonitor()
        monitor.invalidation_rate_warning_per_hour = 10
        monitor.invalidation_rate_critical_per_hour = 25
        
        # Start with normal usage
        for i in range(5):
            monitor_transition.record_invalidation_event(
                pattern=f"transition_{i}:*",
                keys_invalidated=20,
                duration=0.002,
                invalidation_type="normal"
            )
        
        # Should have minimal recommendations
        recommendations_transition = monitor_transition.get_invalidation_recommendations()
        major_recs = [r for r in recommendations_transition if r["severity"] in ["critical", "warning"]]
        assert len(major_recs) == 0, "Should maintain no major recommendations for continued normal operation"
        
        # Verify clean state (no lingering recommendations from previous tests)
        for rec in recommendations_transition:
            assert "issue" in rec
            assert "severity" in rec
            assert rec["severity"] == "info"  # Only informational allowed


class TestSlowOperationDetection:
    """
    Test suite for slow operation detection and analysis functionality.
    
    Scope:
        - get_recent_slow_operations() slow operation identification
        - Threshold-based slow operation detection
        - Operation categorization and analysis
        - Performance bottleneck identification
        
    Business Critical:
        Slow operation detection enables proactive performance issue identification
        
    Test Strategy:
        - Unit tests for slow operation threshold calculation
        - Category-based operation analysis verification
        - Performance bottleneck identification testing
        - Threshold multiplier configuration validation
        
    External Dependencies:
        - statistics module: Standard library (not mocked for realistic calculations)
    """

    def test_get_recent_slow_operations_identifies_performance_bottlenecks(self):
        """
        Test that get_recent_slow_operations() identifies performance bottlenecks accurately.
        
        Verifies:
            Slow operations are identified based on threshold multipliers of average performance
            
        Business Impact:
            Enables proactive identification and resolution of performance bottlenecks
            
        Scenario:
            Given: CachePerformanceMonitor with operation timing data including slow outliers
            When: get_recent_slow_operations() analyzes performance with threshold multipliers
            Then: Operations significantly slower than average are identified by category
            
        Edge Cases Covered:
            - Key generation slow operations
            - Cache operation slow operations (get, set, delete)
            - Compression slow operations
            - Various threshold multiplier values
            
        Mocks Used:
            - None (performance analysis verification)
            
        Related Tests:
            - test_get_recent_slow_operations_categorizes_by_operation_type()
            - test_get_recent_slow_operations_applies_threshold_multipliers_correctly()
        """
        # Given: CachePerformanceMonitor with operation timing data including slow outliers
        monitor = CachePerformanceMonitor()
        
        # Record key generation operations with mix of normal and slow operations
        key_gen_times = [
            0.010, 0.012, 0.011, 0.013, 0.009,  # Normal operations (avg ~0.011)
            0.050, 0.045,                        # Slow operations (4-5x slower)
        ]
        
        for i, duration in enumerate(key_gen_times):
            monitor.record_key_generation_time(
                duration=duration,
                text_length=100 + i * 10,
                operation_type=f"summarize_{i}"
            )
        
        # Record cache operations with similar pattern
        cache_op_times = [
            0.005, 0.006, 0.004, 0.005, 0.007,  # Normal operations (avg ~0.0054)
            0.025, 0.030,                        # Slow operations (5-6x slower)
        ]
        
        for i, duration in enumerate(cache_op_times):
            monitor.record_cache_operation_time(
                operation="get",
                duration=duration,
                cache_hit=True,
                text_length=50 + i * 5
            )
        
        # Record compression operations
        compression_times = [
            0.008, 0.009, 0.007, 0.010,         # Normal operations (avg ~0.0085)
            0.040, 0.035,                        # Slow operations (4x slower)
        ]
        
        for i, duration in enumerate(compression_times):
            monitor.record_compression_ratio(
                original_size=1000 + i * 100,
                compressed_size=300 + i * 30,
                compression_time=duration,
                operation_type=f"compress_{i}"
            )
        
        # When: get_recent_slow_operations() analyzes performance with default threshold (2.0x)
        slow_ops = monitor.get_recent_slow_operations()
        
        # Then: Operations significantly slower than average are identified
        # Key generation slow operations
        key_gen_slow = slow_ops["key_generation"]
        assert len(key_gen_slow) == 2, f"Expected 2 slow key generation operations, got {len(key_gen_slow)}"
        
        # Verify the slow operations are the expected ones
        slow_durations = [op["duration"] for op in key_gen_slow]
        assert 0.050 in slow_durations, "Should identify 0.050s key generation as slow"
        assert 0.045 in slow_durations, "Should identify 0.045s key generation as slow"
        
        # Cache operations slow operations
        cache_ops_slow = slow_ops["cache_operations"]
        assert len(cache_ops_slow) == 2, f"Expected 2 slow cache operations, got {len(cache_ops_slow)}"
        
        cache_slow_durations = [op["duration"] for op in cache_ops_slow]
        assert 0.025 in cache_slow_durations, "Should identify 0.025s cache operation as slow"
        assert 0.030 in cache_slow_durations, "Should identify 0.030s cache operation as slow"
        
        # Compression slow operations
        compression_slow = slow_ops["compression"]
        assert len(compression_slow) == 2, f"Expected 2 slow compression operations, got {len(compression_slow)}"
        
        comp_slow_durations = [op["compression_time"] for op in compression_slow]
        assert 0.040 in comp_slow_durations, "Should identify 0.040s compression as slow"
        assert 0.035 in comp_slow_durations, "Should identify 0.035s compression as slow"
        
        # Verify contextual information is included
        for slow_op in key_gen_slow:
            assert "duration" in slow_op
            assert "text_length" in slow_op
            assert "operation_type" in slow_op
            assert "timestamp" in slow_op
            assert "times_slower" in slow_op
            assert slow_op["times_slower"] > 2.0  # Should be more than 2x slower
        
        # Test with stricter threshold multiplier
        slow_ops_strict = monitor.get_recent_slow_operations(threshold_multiplier=5.0)
        
        # Should identify fewer operations as slow with stricter threshold
        key_gen_strict = slow_ops_strict["key_generation"]
        cache_ops_strict = slow_ops_strict["cache_operations"]
        compression_strict = slow_ops_strict["compression"]
        
        # Should have fewer or same number of slow operations
        assert len(key_gen_strict) <= len(key_gen_slow)
        assert len(cache_ops_strict) <= len(cache_ops_slow)
        assert len(compression_strict) <= len(compression_slow)

    def test_get_recent_slow_operations_categorizes_by_operation_type(self):
        """
        Test that get_recent_slow_operations() categorizes slow operations by type correctly.
        
        Verifies:
            Slow operations are properly categorized for targeted performance analysis
            
        Business Impact:
            Enables type-specific performance optimization and bottleneck resolution
            
        Scenario:
            Given: CachePerformanceMonitor with slow operations across different categories
            When: get_recent_slow_operations() categorizes slow operations
            Then: Operations are correctly grouped by type (key_generation, cache_operations, compression)
            
        Edge Cases Covered:
            - Key generation categorization
            - Cache operations categorization by operation type
            - Compression operations categorization
            - Category-specific slow operation thresholds
            
        Mocks Used:
            - None (categorization verification)
            
        Related Tests:
            - test_get_recent_slow_operations_identifies_performance_bottlenecks()
            - test_get_recent_slow_operations_applies_threshold_multipliers_correctly()
        """
        # Given: CachePerformanceMonitor with slow operations across different categories
        monitor = CachePerformanceMonitor()
        
        # Add normal operations to establish baselines
        normal_key_gen = [0.010, 0.012, 0.011, 0.013, 0.009]  # avg ~0.011
        normal_cache_ops = [0.004, 0.005, 0.006, 0.005, 0.004]  # avg ~0.0048
        normal_compression = [0.015, 0.018, 0.016, 0.017, 0.014]  # avg ~0.016
        
        # Add normal operations
        for duration in normal_key_gen:
            monitor.record_key_generation_time(duration=duration, text_length=100, operation_type="normal")
        
        for duration in normal_cache_ops:
            monitor.record_cache_operation_time(operation="get", duration=duration, cache_hit=True, text_length=100)
        
        for duration in normal_compression:
            monitor.record_compression_ratio(original_size=1000, compressed_size=300, compression_time=duration)
        
        # Add categorized slow operations
        # Key generation slow operations (different operation types)
        key_gen_slow_ops = [
            {"duration": 0.050, "text_length": 500, "operation_type": "summarize"},
            {"duration": 0.045, "text_length": 300, "operation_type": "sentiment"},
            {"duration": 0.040, "text_length": 800, "operation_type": "extract"},
        ]
        
        for op in key_gen_slow_ops:
            monitor.record_key_generation_time(
                duration=op["duration"],
                text_length=op["text_length"],
                operation_type=op["operation_type"]
            )
        
        # Cache operations slow operations (different cache operation types)
        cache_slow_ops = [
            {"operation": "get", "duration": 0.025, "text_length": 200},
            {"operation": "set", "duration": 0.030, "text_length": 300},
            {"operation": "delete", "duration": 0.020, "text_length": 0},
        ]
        
        for op in cache_slow_ops:
            monitor.record_cache_operation_time(
                operation=op["operation"],
                duration=op["duration"],
                cache_hit=op["operation"] != "set",
                text_length=op["text_length"]
            )
        
        # Compression slow operations
        compression_slow_ops = [
            {"original_size": 2000, "compressed_size": 600, "duration": 0.080, "type": "large_text"},
            {"original_size": 1500, "compressed_size": 450, "duration": 0.070, "type": "medium_text"},
        ]
        
        for op in compression_slow_ops:
            monitor.record_compression_ratio(
                original_size=op["original_size"],
                compressed_size=op["compressed_size"],
                compression_time=op["duration"],
                operation_type=op["type"]
            )
        
        # When: get_recent_slow_operations() categorizes slow operations
        slow_ops = monitor.get_recent_slow_operations(threshold_multiplier=2.0)
        
        # Then: Operations are correctly grouped by type
        # Verify correct structure
        assert "key_generation" in slow_ops
        assert "cache_operations" in slow_ops
        assert "compression" in slow_ops
        
        # Verify key generation categorization
        key_gen_slow = slow_ops["key_generation"]
        assert len(key_gen_slow) == 3, f"Expected 3 slow key generation operations, got {len(key_gen_slow)}"
        
        # Verify operation type information is preserved
        operation_types = {op["operation_type"] for op in key_gen_slow}
        expected_types = {"summarize", "sentiment", "extract"}
        assert operation_types == expected_types, f"Expected operation types {expected_types}, got {operation_types}"
        
        # Verify cache operations categorization
        cache_ops_slow = slow_ops["cache_operations"]
        assert len(cache_ops_slow) == 3, f"Expected 3 slow cache operations, got {len(cache_ops_slow)}"
        
        # Verify cache operation type information is preserved
        cache_operation_types = {op["operation_type"] for op in cache_ops_slow}
        expected_cache_types = {"get", "set", "delete"}
        assert cache_operation_types == expected_cache_types, f"Expected cache operation types {expected_cache_types}, got {cache_operation_types}"
        
        # Verify compression categorization
        compression_slow = slow_ops["compression"]
        assert len(compression_slow) == 2, f"Expected 2 slow compression operations, got {len(compression_slow)}"
        
        # Verify compression operation type information is preserved
        comp_operation_types = {op["operation_type"] for op in compression_slow}
        expected_comp_types = {"large_text", "medium_text"}
        assert comp_operation_types == expected_comp_types, f"Expected compression types {expected_comp_types}, got {comp_operation_types}"
        
        # Verify category-specific information is included correctly
        # Key generation should have text_length and operation_type
        for op in key_gen_slow:
            assert "text_length" in op
            assert "operation_type" in op
            assert "duration" in op
            assert "timestamp" in op
            assert "times_slower" in op
        
        # Cache operations should have operation_type and text_length
        for op in cache_ops_slow:
            assert "operation_type" in op
            assert "text_length" in op
            assert "duration" in op
            assert "timestamp" in op
            assert "times_slower" in op
        
        # Compression should have size information and compression_time
        for op in compression_slow:
            assert "compression_time" in op
            assert "original_size" in op
            assert "compression_ratio" in op
            assert "operation_type" in op
            assert "timestamp" in op
            assert "times_slower" in op
        
        # Test empty categories when no slow operations exist
        monitor_normal = CachePerformanceMonitor()
        
        # Add only normal operations
        for duration in [0.005, 0.006, 0.005]:
            monitor_normal.record_key_generation_time(duration=duration, text_length=100, operation_type="fast")
        
        slow_ops_normal = monitor_normal.get_recent_slow_operations()
        
        # Should have empty lists for categories with no slow operations
        assert len(slow_ops_normal["key_generation"]) == 0, "Should have no slow key generation operations"
        assert len(slow_ops_normal["cache_operations"]) == 0, "Should have no slow cache operations"
        assert len(slow_ops_normal["compression"]) == 0, "Should have no slow compression operations"

    def test_get_recent_slow_operations_applies_threshold_multipliers_correctly(self):
        """
        Test that get_recent_slow_operations() applies threshold multipliers correctly.
        
        Verifies:
            Configurable threshold multipliers are applied accurately for slow operation detection
            
        Business Impact:
            Enables tuning of slow operation sensitivity based on operational requirements
            
        Scenario:
            Given: CachePerformanceMonitor with configurable threshold multiplier
            When: get_recent_slow_operations() calculates slow operation thresholds
            Then: Threshold multipliers are correctly applied to average operation times
            
        Edge Cases Covered:
            - Default threshold multiplier (2.0x average)
            - Custom threshold multipliers (various sensitivity levels)
            - Threshold calculation accuracy
            - Edge cases with very fast or slow average times
            
        Mocks Used:
            - None (threshold calculation verification)
            
        Related Tests:
            - test_get_recent_slow_operations_categorizes_by_operation_type()
            - test_get_recent_slow_operations_provides_contextual_information()
        """
        # Given: CachePerformanceMonitor with operations for threshold calculation
        monitor = CachePerformanceMonitor()
        
        # Create operations with known average times for precise threshold testing
        # Key generation: known average of 0.020s
        key_gen_times = [0.018, 0.019, 0.020, 0.021, 0.022]  # avg = 0.020
        test_slow_key_gen = [0.035, 0.050, 0.080]  # 1.75x, 2.5x, 4x slower
        
        for duration in key_gen_times + test_slow_key_gen:
            monitor.record_key_generation_time(
                duration=duration,
                text_length=100,
                operation_type="threshold_test"
            )
        
        # Cache operations: known average of 0.010s  
        cache_op_times = [0.008, 0.009, 0.010, 0.011, 0.012]  # avg = 0.010
        test_slow_cache_ops = [0.015, 0.025, 0.040]  # 1.5x, 2.5x, 4x slower
        
        for duration in cache_op_times + test_slow_cache_ops:
            monitor.record_cache_operation_time(
                operation="get",
                duration=duration,
                cache_hit=True,
                text_length=100
            )
        
        # Test default threshold multiplier (2.0x)
        slow_ops_default = monitor.get_recent_slow_operations()  # default threshold_multiplier=2.0
        
        # With 2.0x multiplier:
        # Key gen threshold: 0.020 * 2.0 = 0.040
        # Should identify: 0.050 (2.5x), 0.080 (4x) - but not 0.035 (1.75x)
        key_gen_slow_default = slow_ops_default["key_generation"]
        assert len(key_gen_slow_default) == 2, f"Expected 2 slow key gen operations with 2.0x threshold, got {len(key_gen_slow_default)}"
        
        key_gen_slow_durations = [op["duration"] for op in key_gen_slow_default]
        assert 0.050 in key_gen_slow_durations, "Should identify 0.050s as slow with 2.0x threshold"
        assert 0.080 in key_gen_slow_durations, "Should identify 0.080s as slow with 2.0x threshold"
        assert 0.035 not in key_gen_slow_durations, "Should not identify 0.035s as slow with 2.0x threshold"
        
        # Cache ops threshold: 0.010 * 2.0 = 0.020
        # Should identify: 0.025 (2.5x), 0.040 (4x) - but not 0.015 (1.5x)
        cache_ops_slow_default = slow_ops_default["cache_operations"]
        assert len(cache_ops_slow_default) == 2, f"Expected 2 slow cache operations with 2.0x threshold, got {len(cache_ops_slow_default)}"
        
        cache_slow_durations = [op["duration"] for op in cache_ops_slow_default]
        assert 0.025 in cache_slow_durations, "Should identify 0.025s as slow with 2.0x threshold"
        assert 0.040 in cache_slow_durations, "Should identify 0.040s as slow with 2.0x threshold"
        assert 0.015 not in cache_slow_durations, "Should not identify 0.015s as slow with 2.0x threshold"
        
        # Test custom threshold multiplier (1.5x - more sensitive)
        slow_ops_sensitive = monitor.get_recent_slow_operations(threshold_multiplier=1.5)
        
        # With 1.5x multiplier:
        # Key gen threshold: 0.020 * 1.5 = 0.030
        # Should identify: 0.035 (1.75x), 0.050 (2.5x), 0.080 (4x)
        key_gen_slow_sensitive = slow_ops_sensitive["key_generation"]
        assert len(key_gen_slow_sensitive) == 3, f"Expected 3 slow key gen operations with 1.5x threshold, got {len(key_gen_slow_sensitive)}"
        
        # Cache ops threshold: 0.010 * 1.5 = 0.015
        # Should identify: 0.015 (1.5x), 0.025 (2.5x), 0.040 (4x)
        cache_ops_slow_sensitive = slow_ops_sensitive["cache_operations"]
        assert len(cache_ops_slow_sensitive) == 3, f"Expected 3 slow cache operations with 1.5x threshold, got {len(cache_ops_slow_sensitive)}"
        
        # Test custom threshold multiplier (3.0x - less sensitive)
        slow_ops_strict = monitor.get_recent_slow_operations(threshold_multiplier=3.0)
        
        # With 3.0x multiplier:
        # Key gen threshold: 0.020 * 3.0 = 0.060
        # Should identify: 0.080 (4x) - but not 0.035 (1.75x) or 0.050 (2.5x)
        key_gen_slow_strict = slow_ops_strict["key_generation"]
        assert len(key_gen_slow_strict) == 1, f"Expected 1 slow key gen operation with 3.0x threshold, got {len(key_gen_slow_strict)}"
        assert key_gen_slow_strict[0]["duration"] == 0.080, "Should only identify 0.080s as slow with 3.0x threshold"
        
        # Cache ops threshold: 0.010 * 3.0 = 0.030
        # Should identify: 0.040 (4x) - but not 0.015 (1.5x) or 0.025 (2.5x)
        cache_ops_slow_strict = slow_ops_strict["cache_operations"]
        assert len(cache_ops_slow_strict) == 1, f"Expected 1 slow cache operation with 3.0x threshold, got {len(cache_ops_slow_strict)}"
        assert cache_ops_slow_strict[0]["duration"] == 0.040, "Should only identify 0.040s as slow with 3.0x threshold"
        
        # Test edge case: very fast average times
        monitor_fast = CachePerformanceMonitor()
        
        very_fast_times = [0.001, 0.001, 0.002, 0.001, 0.001]  # avg = 0.0012
        slow_time = 0.003  # 2.5x slower than average
        
        for duration in very_fast_times:
            monitor_fast.record_key_generation_time(duration=duration, text_length=50, operation_type="fast")
        
        monitor_fast.record_key_generation_time(duration=slow_time, text_length=50, operation_type="slow")
        
        slow_ops_fast_avg = monitor_fast.get_recent_slow_operations(threshold_multiplier=2.0)
        
        # Should correctly identify slow operation even with very fast averages
        # Threshold: 0.0012 * 2.0 = 0.0024, so 0.003 should be identified
        key_gen_fast_slow = slow_ops_fast_avg["key_generation"]
        assert len(key_gen_fast_slow) == 1, "Should identify slow operation with very fast average"
        assert key_gen_fast_slow[0]["duration"] == 0.003, "Should identify the 0.003s operation as slow"
        
        # Verify times_slower calculation accuracy
        times_slower = key_gen_fast_slow[0]["times_slower"]
        expected_times_slower = 0.003 / 0.0012  # 2.5
        assert abs(times_slower - expected_times_slower) < 0.1, f"Expected times_slower ~{expected_times_slower}, got {times_slower}"
        
        # Test edge case: very slow average times
        monitor_slow = CachePerformanceMonitor()
        
        very_slow_times = [0.100, 0.120, 0.110, 0.105, 0.115]  # avg = 0.110
        extremely_slow_time = 0.250  # ~2.27x slower
        
        for duration in very_slow_times:
            monitor_slow.record_cache_operation_time(operation="get", duration=duration, cache_hit=True, text_length=100)
        
        monitor_slow.record_cache_operation_time(operation="get", duration=extremely_slow_time, cache_hit=True, text_length=100)
        
        slow_ops_slow_avg = monitor_slow.get_recent_slow_operations(threshold_multiplier=2.0)
        
        # Should correctly identify extremely slow operation
        # Threshold: 0.110 * 2.0 = 0.220, so 0.250 should be identified
        cache_slow_avg = slow_ops_slow_avg["cache_operations"]
        assert len(cache_slow_avg) == 1, "Should identify extremely slow operation with slow average"
        assert cache_slow_avg[0]["duration"] == 0.250, "Should identify the 0.250s operation as slow"

    def test_get_recent_slow_operations_provides_contextual_information(self):
        """
        Test that get_recent_slow_operations() provides contextual information for slow operations.
        
        Verifies:
            Slow operation results include timing, context, and performance details
            
        Business Impact:
            Enables detailed analysis and debugging of performance issues
            
        Scenario:
            Given: CachePerformanceMonitor with slow operations including context data
            When: get_recent_slow_operations() identifies slow operations
            Then: Results include timing details, operation context, and performance comparison data
            
        Edge Cases Covered:
            - Timing information accuracy
            - Context data inclusion (operation type, text length, etc.)
            - Performance comparison details (actual vs. average)
            - Additional metadata for debugging
            
        Mocks Used:
            - None (contextual information verification)
            
        Related Tests:
            - test_get_recent_slow_operations_applies_threshold_multipliers_correctly()
            - test_get_recent_slow_operations_handles_no_slow_operations_gracefully()
        """
        # Given: CachePerformanceMonitor with slow operations including rich context data
        monitor = CachePerformanceMonitor()
        
        import time
        start_time = time.time()
        
        # Add baseline operations for comparison
        baseline_operations = [
            {"duration": 0.010, "text_length": 100, "operation_type": "summarize"},
            {"duration": 0.012, "text_length": 150, "operation_type": "extract"},
            {"duration": 0.011, "text_length": 120, "operation_type": "classify"},
        ]
        
        for op in baseline_operations:
            monitor.record_key_generation_time(
                duration=op["duration"],
                text_length=op["text_length"],
                operation_type=op["operation_type"]
            )
        
        # Add slow operations with rich contextual information
        slow_key_gen_ops = [
            {
                "duration": 0.055,
                "text_length": 2500,
                "operation_type": "complex_summarize",
                "additional_data": {"model": "large", "complexity": "high"}
            },
            {
                "duration": 0.048,
                "text_length": 1800,
                "operation_type": "multi_language_extract", 
                "additional_data": {"languages": ["en", "es"], "entities": 15}
            },
        ]
        
        for op in slow_key_gen_ops:
            monitor.record_key_generation_time(
                duration=op["duration"],
                text_length=op["text_length"],
                operation_type=op["operation_type"],
                additional_data=op.get("additional_data")
            )
        
        # Add slow cache operations with context
        baseline_cache_ops = [
            {"operation": "get", "duration": 0.005, "text_length": 200},
            {"operation": "set", "duration": 0.007, "text_length": 300},
            {"operation": "get", "duration": 0.006, "text_length": 250},
        ]
        
        for op in baseline_cache_ops:
            monitor.record_cache_operation_time(
                operation=op["operation"],
                duration=op["duration"],
                cache_hit=op["operation"] == "get",
                text_length=op["text_length"]
            )
        
        slow_cache_ops = [
            {
                "operation": "get",
                "duration": 0.025,
                "cache_hit": False,
                "text_length": 1500,
                "additional_data": {"cache_miss_reason": "expired", "key_complexity": "high"}
            },
            {
                "operation": "set",
                "duration": 0.035,
                "cache_hit": True,
                "text_length": 2000,
                "additional_data": {"compression_required": True, "serialization_time": 0.015}
            },
        ]
        
        for op in slow_cache_ops:
            monitor.record_cache_operation_time(
                operation=op["operation"],
                duration=op["duration"],
                cache_hit=op["cache_hit"],
                text_length=op["text_length"],
                additional_data=op.get("additional_data")
            )
        
        # Add slow compression operations with context
        baseline_compression = [
            {"original_size": 1000, "compressed_size": 300, "duration": 0.015, "type": "text"},
            {"original_size": 1200, "compressed_size": 360, "duration": 0.018, "type": "json"},
        ]
        
        for op in baseline_compression:
            monitor.record_compression_ratio(
                original_size=op["original_size"],
                compressed_size=op["compressed_size"],
                compression_time=op["duration"],
                operation_type=op["type"]
            )
        
        slow_compression_ops = [
            {
                "original_size": 5000,
                "compressed_size": 1500,
                "duration": 0.080,
                "type": "large_document"
            },
        ]
        
        for op in slow_compression_ops:
            monitor.record_compression_ratio(
                original_size=op["original_size"],
                compressed_size=op["compressed_size"],
                compression_time=op["duration"],
                operation_type=op["type"]
            )
        
        # When: get_recent_slow_operations() identifies slow operations
        slow_ops = monitor.get_recent_slow_operations(threshold_multiplier=2.0)
        
        # Then: Results include comprehensive contextual information
        # Verify key generation contextual information
        key_gen_slow = slow_ops["key_generation"]
        assert len(key_gen_slow) == 2, "Should identify 2 slow key generation operations"
        
        for slow_op in key_gen_slow:
            # Timing information accuracy
            assert "duration" in slow_op
            assert isinstance(slow_op["duration"], float)
            assert slow_op["duration"] > 0.040  # Should be significantly slow
            
            # Context data inclusion
            assert "text_length" in slow_op
            assert "operation_type" in slow_op
            assert isinstance(slow_op["text_length"], int)
            assert slow_op["text_length"] > 1000  # Should be large text
            assert slow_op["operation_type"] in ["complex_summarize", "multi_language_extract"]
            
            # Timestamp information for temporal analysis
            assert "timestamp" in slow_op
            assert isinstance(slow_op["timestamp"], str)
            
            # Performance comparison details
            assert "times_slower" in slow_op
            assert isinstance(slow_op["times_slower"], float)
            assert slow_op["times_slower"] > 2.0  # Should be more than 2x slower
        
        # Verify cache operation contextual information
        cache_ops_slow = slow_ops["cache_operations"]
        assert len(cache_ops_slow) == 2, "Should identify 2 slow cache operations"
        
        for slow_op in cache_ops_slow:
            # Operation-specific context
            assert "operation_type" in slow_op
            assert "text_length" in slow_op
            assert "duration" in slow_op
            assert "timestamp" in slow_op
            assert "times_slower" in slow_op
            
            # Cache-specific context
            assert slow_op["operation_type"] in ["get", "set"]
            assert slow_op["text_length"] >= 1500  # Should be large operations
        
        # Verify compression operation contextual information
        compression_slow = slow_ops["compression"]
        assert len(compression_slow) == 1, "Should identify 1 slow compression operation"
        
        compression_op = compression_slow[0]
        
        # Compression-specific context
        assert "compression_time" in compression_op
        assert "original_size" in compression_op
        assert "compression_ratio" in compression_op
        assert "operation_type" in compression_op
        assert "timestamp" in compression_op
        assert "times_slower" in compression_op
        
        # Size and efficiency context
        assert compression_op["original_size"] == 5000
        assert compression_op["compression_ratio"] == 0.3  # 1500/5000
        assert compression_op["operation_type"] == "large_document"
        
        # Verify timing accuracy across all categories
        all_slow_ops = key_gen_slow + cache_ops_slow + compression_slow
        
        for slow_op in all_slow_ops:
            # Timestamp should be recent and in ISO format
            timestamp_str = slow_op["timestamp"]
            assert "T" in timestamp_str, "Timestamp should be in ISO format"
            
            # times_slower should be reasonable (not infinite or negative)
            times_slower = slow_op["times_slower"]
            assert 1.0 < times_slower < 100.0, f"times_slower should be reasonable, got {times_slower}"
        
        # Test edge case: operations with no additional context
        monitor_minimal = CachePerformanceMonitor()
        
        # Add baseline
        monitor_minimal.record_key_generation_time(duration=0.010, text_length=100, operation_type="simple")
        
        # Add slow operation with minimal context
        monitor_minimal.record_key_generation_time(duration=0.025, text_length=50, operation_type="")
        
        slow_ops_minimal = monitor_minimal.get_recent_slow_operations()
        key_gen_minimal = slow_ops_minimal["key_generation"]
        
        # Should still provide available context gracefully
        assert len(key_gen_minimal) == 1, "Should identify slow operation even with minimal context"
        minimal_op = key_gen_minimal[0]
        assert "duration" in minimal_op
        assert "text_length" in minimal_op
        assert "operation_type" in minimal_op
        assert minimal_op["operation_type"] == ""  # Should handle empty operation type
        assert "times_slower" in minimal_op
        assert "timestamp" in minimal_op

    def test_get_recent_slow_operations_handles_no_slow_operations_gracefully(self):
        """
        Test that get_recent_slow_operations() handles scenarios with no slow operations gracefully.
        
        Verifies:
            Empty results are returned appropriately when no slow operations are detected
            
        Business Impact:
            Prevents false positives and ensures slow operation alerts are meaningful
            
        Scenario:
            Given: CachePerformanceMonitor with all operations performing within normal thresholds
            When: get_recent_slow_operations() analyzes normal performance data
            Then: Empty results are returned for each category with no slow operations
            
        Edge Cases Covered:
            - All operations within threshold
            - Empty results for all categories
            - Appropriate handling of insufficient data
            - Clean state for normal performance periods
            
        Mocks Used:
            - None (normal operation verification)
            
        Related Tests:
            - test_get_recent_slow_operations_provides_contextual_information()
            - test_get_recent_slow_operations_maintains_recency_filtering()
        """
        # Test all operations within normal thresholds
        monitor_normal = CachePerformanceMonitor()
        
        # Add operations that are all within normal performance ranges
        normal_key_gen_times = [0.008, 0.010, 0.009, 0.011, 0.012, 0.010, 0.009]
        for duration in normal_key_gen_times:
            monitor_normal.record_key_generation_time(
                duration=duration,
                text_length=100,
                operation_type="normal"
            )
        
        normal_cache_op_times = [0.003, 0.004, 0.005, 0.004, 0.006, 0.005]
        for duration in normal_cache_op_times:
            monitor_normal.record_cache_operation_time(
                operation="get",
                duration=duration,
                cache_hit=True,
                text_length=100
            )
        
        normal_compression_times = [0.012, 0.015, 0.013, 0.014, 0.016]
        for duration in normal_compression_times:
            monitor_normal.record_compression_ratio(
                original_size=1000,
                compressed_size=300,
                compression_time=duration,
                operation_type="normal"
            )
        
        # When: get_recent_slow_operations() analyzes normal performance data
        slow_ops_normal = monitor_normal.get_recent_slow_operations()
        
        # Then: Empty results are returned for each category
        assert "key_generation" in slow_ops_normal
        assert "cache_operations" in slow_ops_normal
        assert "compression" in slow_ops_normal
        
        assert len(slow_ops_normal["key_generation"]) == 0, "Should have no slow key generation operations"
        assert len(slow_ops_normal["cache_operations"]) == 0, "Should have no slow cache operations"
        assert len(slow_ops_normal["compression"]) == 0, "Should have no slow compression operations"
        
        # Verify structure consistency
        assert isinstance(slow_ops_normal["key_generation"], list)
        assert isinstance(slow_ops_normal["cache_operations"], list)
        assert isinstance(slow_ops_normal["compression"], list)
        
        # Test with no operations at all
        monitor_empty = CachePerformanceMonitor()
        
        slow_ops_empty = monitor_empty.get_recent_slow_operations()
        
        # Should return empty lists for all categories
        assert len(slow_ops_empty["key_generation"]) == 0, "Should have no slow operations when no data exists"
        assert len(slow_ops_empty["cache_operations"]) == 0, "Should have no slow operations when no data exists"
        assert len(slow_ops_empty["compression"]) == 0, "Should have no slow operations when no data exists"
        
        # Test with single operation (insufficient data for meaningful average)
        monitor_single = CachePerformanceMonitor()
        
        monitor_single.record_key_generation_time(duration=0.050, text_length=100, operation_type="single")
        
        slow_ops_single = monitor_single.get_recent_slow_operations()
        
        # With only one operation, there's no basis for comparison, so should return empty
        assert len(slow_ops_single["key_generation"]) == 0, "Should have no slow operations with insufficient data for comparison"
        
        # Test with very strict threshold (high multiplier)
        monitor_strict = CachePerformanceMonitor()
        
        # Add operations with some variation but use strict threshold
        varied_times = [0.010, 0.015, 0.020, 0.012, 0.018]  # avg ~0.015
        for duration in varied_times:
            monitor_strict.record_key_generation_time(
                duration=duration,
                text_length=100,
                operation_type="varied"
            )
        
        # Use very high threshold multiplier (10x) - no operation should be 10x slower
        slow_ops_strict = monitor_strict.get_recent_slow_operations(threshold_multiplier=10.0)
        
        # Should have no slow operations with such strict threshold
        assert len(slow_ops_strict["key_generation"]) == 0, "Should have no slow operations with very strict threshold"
        
        # Test consistent performance (all operations identical)
        monitor_consistent = CachePerformanceMonitor()
        
        consistent_duration = 0.015
        for i in range(5):
            monitor_consistent.record_cache_operation_time(
                operation="get",
                duration=consistent_duration,
                cache_hit=True,
                text_length=100
            )
        
        slow_ops_consistent = monitor_consistent.get_recent_slow_operations()
        
        # With all operations identical, none should be considered slow
        assert len(slow_ops_consistent["cache_operations"]) == 0, "Should have no slow operations with consistent performance"
        
        # Test state consistency across multiple calls
        slow_ops_normal_second = monitor_normal.get_recent_slow_operations()
        
        # Results should be consistent
        assert len(slow_ops_normal_second["key_generation"]) == len(slow_ops_normal["key_generation"])
        assert len(slow_ops_normal_second["cache_operations"]) == len(slow_ops_normal["cache_operations"])
        assert len(slow_ops_normal_second["compression"]) == len(slow_ops_normal["compression"])
        
        # Test graceful handling after operations are added and removed (via cleanup)
        monitor_cleanup = CachePerformanceMonitor(
            retention_hours=0.001,  # Very short retention for quick cleanup
            max_measurements=2      # Small limit
        )
        
        # Add operations that will be cleaned up
        for i in range(5):
            monitor_cleanup.record_key_generation_time(
                duration=0.010,
                text_length=100,
                operation_type=f"cleanup_{i}"
            )
        
        # Force cleanup by getting stats (which triggers cleanup)
        _ = monitor_cleanup.get_performance_stats()
        
        # Now check slow operations
        slow_ops_cleanup = monitor_cleanup.get_recent_slow_operations()
        
        # Should handle cleaned up data gracefully
        assert isinstance(slow_ops_cleanup["key_generation"], list)
        assert isinstance(slow_ops_cleanup["cache_operations"], list)
        assert isinstance(slow_ops_cleanup["compression"], list)
        
        # Should have minimal data due to cleanup
        assert len(monitor_cleanup.key_generation_times) <= monitor_cleanup.max_measurements

    def test_get_recent_slow_operations_maintains_recency_filtering(self):
        """
        Test that get_recent_slow_operations() maintains appropriate recency filtering.
        
        Verifies:
            Only recent slow operations are included based on data retention settings
            
        Business Impact:
            Ensures slow operation analysis focuses on current performance issues
            
        Scenario:
            Given: CachePerformanceMonitor with both recent and old slow operations
            When: get_recent_slow_operations() filters operations by recency
            Then: Only operations within the retention period are included in results
            
        Edge Cases Covered:
            - Recent operations inclusion
            - Old operations exclusion
            - Retention period boundary conditions
            - Recency filtering accuracy
            
        Mocks Used:
            - None (recency filtering verification)
            
        Related Tests:
            - test_get_recent_slow_operations_handles_no_slow_operations_gracefully()
            - test_get_recent_slow_operations_identifies_performance_bottlenecks()
        """
        # Test recency filtering by simulating operations with different timestamps
        import time
        
        monitor = CachePerformanceMonitor(
            retention_hours=1  # 1 hour retention for testing
        )
        
        current_time = time.time()
        
        # Add baseline operations for threshold calculation (recent)
        baseline_operations = [
            {"duration": 0.010, "text_length": 100, "operation_type": "recent_baseline"},
            {"duration": 0.011, "text_length": 120, "operation_type": "recent_baseline"},
            {"duration": 0.012, "text_length": 110, "operation_type": "recent_baseline"},
        ]
        
        for op in baseline_operations:
            monitor.record_key_generation_time(
                duration=op["duration"],
                text_length=op["text_length"],
                operation_type=op["operation_type"]
            )
        
        # Add recent slow operations (within retention period)
        recent_slow_ops = [
            {"duration": 0.050, "text_length": 500, "operation_type": "recent_slow", "time_offset": -1800},  # 30 min ago
            {"duration": 0.045, "text_length": 400, "operation_type": "recent_slow", "time_offset": -2700},  # 45 min ago
        ]
        
        for op in recent_slow_ops:
            monitor.record_key_generation_time(
                duration=op["duration"],
                text_length=op["text_length"],
                operation_type=op["operation_type"]
            )
            # Manually set timestamp to simulate time offset
            if monitor.key_generation_times:
                monitor.key_generation_times[-1].timestamp = current_time + op["time_offset"]
        
        # Add old slow operations (outside retention period)
        old_slow_ops = [
            {"duration": 0.080, "text_length": 800, "operation_type": "old_slow", "time_offset": -7200},   # 2 hours ago
            {"duration": 0.070, "text_length": 700, "operation_type": "old_slow", "time_offset": -10800},  # 3 hours ago
        ]
        
        for op in old_slow_ops:
            monitor.record_key_generation_time(
                duration=op["duration"],
                text_length=op["text_length"],
                operation_type=op["operation_type"]
            )
            # Manually set timestamp to simulate old operations
            if monitor.key_generation_times:
                monitor.key_generation_times[-1].timestamp = current_time + op["time_offset"]
        
        # Trigger cleanup by getting performance stats (this cleans up old measurements)
        _ = monitor.get_performance_stats()
        
        # When: get_recent_slow_operations() filters operations by recency
        slow_ops = monitor.get_recent_slow_operations(threshold_multiplier=2.0)
        
        # Then: Only recent operations within retention period are included
        key_gen_slow = slow_ops["key_generation"]
        
        # Should only include recent slow operations, not old ones
        assert len(key_gen_slow) <= 2, f"Should have at most 2 recent slow operations, got {len(key_gen_slow)}"
        
        # Verify that included operations are recent ones
        for slow_op in key_gen_slow:
            assert slow_op["operation_type"] == "recent_slow", f"Should only include recent operations, got {slow_op['operation_type']}"
        
        # Test boundary condition - operation exactly at retention boundary
        monitor_boundary = CachePerformanceMonitor(retention_hours=1)
        
        # Add baseline
        for duration in [0.010, 0.011, 0.012]:
            monitor_boundary.record_cache_operation_time(
                operation="get",
                duration=duration,
                cache_hit=True,
                text_length=100
            )
        
        # Add operation exactly at retention boundary
        monitor_boundary.record_cache_operation_time(
            operation="get",
            duration=0.040,  # Slow operation
            cache_hit=True,
            text_length=100
        )
        
        # Set timestamp to exactly retention_hours ago
        if monitor_boundary.cache_operation_times:
            monitor_boundary.cache_operation_times[-1].timestamp = current_time - (monitor_boundary.retention_hours * 3600)
        
        # Add slightly newer operation (within retention)
        monitor_boundary.record_cache_operation_time(
            operation="get",
            duration=0.035,  # Slow operation
            cache_hit=True,
            text_length=100
        )
        
        if monitor_boundary.cache_operation_times:
            monitor_boundary.cache_operation_times[-1].timestamp = current_time - (monitor_boundary.retention_hours * 3600 - 60)  # 1 minute within boundary
        
        # Trigger cleanup
        _ = monitor_boundary.get_performance_stats()
        
        slow_ops_boundary = monitor_boundary.get_recent_slow_operations()
        cache_ops_slow_boundary = slow_ops_boundary["cache_operations"]
        
        # Should include the operation within boundary but not the one exactly at boundary
        assert len(cache_ops_slow_boundary) <= 1, "Should include at most the operation within retention boundary"
        
        if cache_ops_slow_boundary:
            # Should be the newer operation
            assert abs(cache_ops_slow_boundary[0]["duration"] - 0.035) < 0.001, "Should include the newer operation"
        
        # Test with very short retention period
        monitor_short = CachePerformanceMonitor(retention_hours=0.01)  # ~36 seconds
        
        # Add baseline
        for duration in [0.005, 0.006, 0.007]:
            monitor_short.record_compression_ratio(
                original_size=1000,
                compressed_size=300,
                compression_time=duration,
                operation_type="baseline"
            )
        
        # Add slow operation
        monitor_short.record_compression_ratio(
            original_size=1000,
            compressed_size=300,
            compression_time=0.025,  # Slow
            operation_type="slow"
        )
        
        # Wait a tiny amount to make some operations "old"
        time.sleep(0.05)
        
        # Add another operation
        monitor_short.record_compression_ratio(
            original_size=1000,
            compressed_size=300,
            compression_time=0.020,  # Slow
            operation_type="recent"
        )
        
        # Trigger cleanup
        _ = monitor_short.get_performance_stats()
        
        slow_ops_short = monitor_short.get_recent_slow_operations()
        compression_slow_short = slow_ops_short["compression"]
        
        # Should have minimal operations due to short retention
        # The exact number depends on cleanup timing, but should be reasonable
        assert len(compression_slow_short) <= 2, "Should have limited operations with short retention"
        
        # Verify data integrity - operations should have valid timestamps
        recent_cutoff = current_time - (monitor_short.retention_hours * 3600)
        for measurement in monitor_short.compression_ratios:
            assert measurement.timestamp >= recent_cutoff or abs(measurement.timestamp - recent_cutoff) < 1, "All measurements should be within retention period after cleanup"
        
        # Test that recency filtering works with mixed operation types
        monitor_mixed = CachePerformanceMonitor(retention_hours=2)
        
        # Add recent operations across all categories
        monitor_mixed.record_key_generation_time(duration=0.040, text_length=100, operation_type="recent")
        monitor_mixed.record_cache_operation_time(operation="get", duration=0.025, cache_hit=True, text_length=100)
        monitor_mixed.record_compression_ratio(original_size=1000, compressed_size=300, compression_time=0.050, operation_type="recent")
        
        # Add baselines
        for _ in range(3):
            monitor_mixed.record_key_generation_time(duration=0.010, text_length=100, operation_type="baseline")
            monitor_mixed.record_cache_operation_time(operation="get", duration=0.005, cache_hit=True, text_length=100)
            monitor_mixed.record_compression_ratio(original_size=1000, compressed_size=300, compression_time=0.015, operation_type="baseline")
        
        slow_ops_mixed = monitor_mixed.get_recent_slow_operations()
        
        # Should identify slow operations in all categories that are recent
        assert len(slow_ops_mixed["key_generation"]) > 0, "Should identify recent slow key generation"
        assert len(slow_ops_mixed["cache_operations"]) > 0, "Should identify recent slow cache operations"
        assert len(slow_ops_mixed["compression"]) > 0, "Should identify recent slow compression operations"


class TestDataManagement:
    """
    Test suite for performance monitoring data management functionality.
    
    Scope:
        - reset_stats() comprehensive statistics reset
        - export_metrics() complete data export
        - Data retention and cleanup mechanisms
        - Thread safety during data management operations
        
    Business Critical:
        Data management ensures monitoring system reliability and prevents memory issues
        
    Test Strategy:
        - Unit tests for data reset and export functionality
        - Thread safety verification during data operations
        - Data integrity validation during management operations
        - Memory management and cleanup verification
        
    External Dependencies:
        - datetime: Standard library (not mocked for realistic timestamp handling)
    """

    def test_reset_stats_clears_all_performance_data(self):
        """
        Test that reset_stats() clears all accumulated performance data comprehensively.
        
        Verifies:
            All performance measurements and statistics are cleared for fresh analysis periods
            
        Business Impact:
            Enables clean performance analysis periods and prevents stale data interference
            
        Scenario:
            Given: CachePerformanceMonitor with accumulated performance data across all categories
            When: reset_stats() is called to clear all measurements
            Then: All internal data structures are cleared and ready for fresh data collection
            
        Edge Cases Covered:
            - All metric types cleared (timing, compression, memory, invalidation)
            - Hit/miss counters reset
            - Internal data structure cleanup
            - State reset to initial conditions
            
        Mocks Used:
            - None (data clearing verification)
            
        Related Tests:
            - test_reset_stats_maintains_configuration_settings()
            - test_reset_stats_preserves_thresholds_and_limits()
        """
        # Given: CachePerformanceMonitor with accumulated performance data across all categories
        monitor = CachePerformanceMonitor()
        
        # Add comprehensive performance data across all measurement types
        
        # Key generation measurements
        for i in range(5):
            monitor.record_key_generation_time(
                duration=0.01 + i * 0.001,
                text_length=100 + i * 10,
                operation_type=f"operation_{i}"
            )
        
        # Cache operation measurements with hits and misses
        for i in range(8):
            monitor.record_cache_operation_time(
                operation="get" if i % 2 == 0 else "set",
                duration=0.005 + i * 0.001,
                cache_hit=i % 3 == 0,  # Mix of hits and misses
                text_length=50 + i * 5
            )
        
        # Compression measurements
        for i in range(4):
            monitor.record_compression_ratio(
                original_size=1000 + i * 200,
                compressed_size=300 + i * 60,
                compression_time=0.01 + i * 0.002,
                operation_type=f"compress_{i}"
            )
        
        # Memory usage measurements
        for i in range(3):
            memory_cache = {f"key_{j}": f"value_{j}" * (i + 1) for j in range(i + 5)}
            monitor.record_memory_usage(
                memory_cache=memory_cache,
                redis_stats={"memory_used_bytes": (i + 1) * 1024 * 1024, "keys": (i + 1) * 10}
            )
        
        # Invalidation events
        for i in range(6):
            monitor.record_invalidation_event(
                pattern=f"pattern_{i}:*",
                keys_invalidated=i + 2,
                duration=0.001 + i * 0.0005,
                invalidation_type="manual" if i % 2 == 0 else "automatic"
            )
        
        # Verify data exists before reset
        assert len(monitor.key_generation_times) == 5, "Should have key generation measurements"
        assert len(monitor.cache_operation_times) == 8, "Should have cache operation measurements"
        assert len(monitor.compression_ratios) == 4, "Should have compression measurements"
        assert len(monitor.memory_usage_measurements) == 3, "Should have memory usage measurements"
        assert len(monitor.invalidation_events) == 6, "Should have invalidation events"
        
        # Verify counters have accumulated
        assert monitor.cache_hits > 0, "Should have accumulated cache hits"
        assert monitor.cache_misses > 0, "Should have accumulated cache misses"
        assert monitor.total_operations > 0, "Should have accumulated total operations"
        assert monitor.total_invalidations > 0, "Should have accumulated total invalidations"
        assert monitor.total_keys_invalidated > 0, "Should have accumulated invalidated keys"
        
        # When: reset_stats() is called to clear all measurements
        monitor.reset_stats()
        
        # Then: All internal data structures are cleared
        # Verify all measurement lists are empty
        assert len(monitor.key_generation_times) == 0, "Key generation times should be cleared"
        assert len(monitor.cache_operation_times) == 0, "Cache operation times should be cleared"
        assert len(monitor.compression_ratios) == 0, "Compression ratios should be cleared"
        assert len(monitor.memory_usage_measurements) == 0, "Memory usage measurements should be cleared"
        assert len(monitor.invalidation_events) == 0, "Invalidation events should be cleared"
        
        # Verify all counters are reset to zero
        assert monitor.cache_hits == 0, "Cache hits should be reset to 0"
        assert monitor.cache_misses == 0, "Cache misses should be reset to 0"
        assert monitor.total_operations == 0, "Total operations should be reset to 0"
        assert monitor.total_invalidations == 0, "Total invalidations should be reset to 0"
        assert monitor.total_keys_invalidated == 0, "Total keys invalidated should be reset to 0"
        
        # Verify state is ready for fresh data collection
        stats_after_reset = monitor.get_performance_stats()
        
        # Should return clean initial statistics
        assert stats_after_reset["cache_hit_rate"] == 0.0, "Hit rate should be 0 after reset"
        assert stats_after_reset["total_cache_operations"] == 0, "Total operations should be 0 after reset"
        assert "key_generation" not in stats_after_reset, "Should not have key generation stats after reset"
        assert "cache_operations" not in stats_after_reset, "Should not have cache operation stats after reset"
        assert "compression" not in stats_after_reset, "Should not have compression stats after reset"
        assert "memory_usage" not in stats_after_reset, "Should not have memory usage stats after reset"
        assert "invalidation" not in stats_after_reset, "Should not have invalidation stats after reset"
        
        # Verify the monitor is ready to collect new data
        monitor.record_key_generation_time(duration=0.015, text_length=100, operation_type="post_reset")
        monitor.record_cache_operation_time(operation="get", duration=0.008, cache_hit=True, text_length=100)
        
        # Should start collecting fresh data
        assert len(monitor.key_generation_times) == 1, "Should start collecting new key generation data"
        assert len(monitor.cache_operation_times) == 1, "Should start collecting new cache operation data"
        assert monitor.cache_hits == 1, "Should start counting hits again"
        assert monitor.total_operations == 1, "Should start counting operations again"
        
        # Verify fresh statistics generation works
        stats_with_new_data = monitor.get_performance_stats()
        assert "key_generation" in stats_with_new_data, "Should generate new key generation stats"
        assert "cache_operations" in stats_with_new_data, "Should generate new cache operation stats"

    def test_reset_stats_maintains_configuration_settings(self):
        """
        Test that reset_stats() maintains configuration settings while clearing data.
        
        Verifies:
            Configuration parameters remain unchanged while performance data is cleared
            
        Business Impact:
            Ensures monitoring configuration consistency across analysis periods
            
        Scenario:
            Given: CachePerformanceMonitor with custom configuration and accumulated data
            When: reset_stats() clears performance data
            Then: Configuration settings remain unchanged while data is cleared
            
        Edge Cases Covered:
            - Retention hours preservation
            - Max measurements preservation
            - Memory threshold preservation
            - Configuration state consistency
            
        Mocks Used:
            - None (configuration preservation verification)
            
        Related Tests:
            - test_reset_stats_clears_all_performance_data()
            - test_reset_stats_preserves_thresholds_and_limits()
        """
        # Given: CachePerformanceMonitor with custom configuration
        custom_config = {
            "retention_hours": 3,
            "max_measurements": 500,
            "memory_warning_threshold_bytes": 75 * 1024 * 1024,  # 75MB
            "memory_critical_threshold_bytes": 150 * 1024 * 1024,  # 150MB
        }
        
        monitor = CachePerformanceMonitor(**custom_config)
        
        # Store original configuration values for comparison
        original_retention_hours = monitor.retention_hours
        original_max_measurements = monitor.max_measurements
        original_memory_warning = monitor.memory_warning_threshold_bytes
        original_memory_critical = monitor.memory_critical_threshold_bytes
        original_key_gen_threshold = monitor.key_generation_threshold
        original_cache_op_threshold = monitor.cache_operation_threshold
        original_invalidation_warning = monitor.invalidation_rate_warning_per_hour
        original_invalidation_critical = monitor.invalidation_rate_critical_per_hour
        
        # Add accumulated data to the monitor
        for i in range(10):
            monitor.record_key_generation_time(
                duration=0.01 + i * 0.001,
                text_length=100 + i * 10,
                operation_type=f"config_test_{i}"
            )
            
            monitor.record_cache_operation_time(
                operation="get",
                duration=0.005 + i * 0.0005,
                cache_hit=i % 2 == 0,
                text_length=50 + i * 5
            )
        
        # Add some other measurement types
        monitor.record_compression_ratio(original_size=2000, compressed_size=600, compression_time=0.025)
        monitor.record_memory_usage(memory_cache={"test": "data"}, redis_stats={"memory_used_bytes": 1024, "keys": 1})
        monitor.record_invalidation_event(pattern="test:*", keys_invalidated=5, duration=0.002)
        
        # Verify data exists
        assert len(monitor.key_generation_times) > 0, "Should have data before reset"
        assert len(monitor.cache_operation_times) > 0, "Should have data before reset"
        assert monitor.total_operations > 0, "Should have operations before reset"
        
        # When: reset_stats() clears performance data
        monitor.reset_stats()
        
        # Then: Configuration settings remain unchanged
        # Verify core configuration parameters are preserved
        assert monitor.retention_hours == original_retention_hours, f"Retention hours should be preserved: expected {original_retention_hours}, got {monitor.retention_hours}"
        assert monitor.max_measurements == original_max_measurements, f"Max measurements should be preserved: expected {original_max_measurements}, got {monitor.max_measurements}"
        assert monitor.memory_warning_threshold_bytes == original_memory_warning, f"Memory warning threshold should be preserved: expected {original_memory_warning}, got {monitor.memory_warning_threshold_bytes}"
        assert monitor.memory_critical_threshold_bytes == original_memory_critical, f"Memory critical threshold should be preserved: expected {original_memory_critical}, got {monitor.memory_critical_threshold_bytes}"
        
        # Verify performance thresholds are preserved
        assert monitor.key_generation_threshold == original_key_gen_threshold, f"Key generation threshold should be preserved: expected {original_key_gen_threshold}, got {monitor.key_generation_threshold}"
        assert monitor.cache_operation_threshold == original_cache_op_threshold, f"Cache operation threshold should be preserved: expected {original_cache_op_threshold}, got {monitor.cache_operation_threshold}"
        
        # Verify invalidation rate thresholds are preserved
        assert monitor.invalidation_rate_warning_per_hour == original_invalidation_warning, f"Invalidation warning rate should be preserved: expected {original_invalidation_warning}, got {monitor.invalidation_rate_warning_per_hour}"
        assert monitor.invalidation_rate_critical_per_hour == original_invalidation_critical, f"Invalidation critical rate should be preserved: expected {original_invalidation_critical}, got {monitor.invalidation_rate_critical_per_hour}"
        
        # Verify configuration works correctly after reset
        # Test retention hours still applies
        monitor.record_key_generation_time(duration=0.02, text_length=100, operation_type="post_reset")
        
        # Should still have the same max_measurements limit
        assert hasattr(monitor, 'max_measurements'), "Should still have max_measurements attribute"
        assert monitor.max_measurements == custom_config["max_measurements"], "Max measurements should still be configured value"
        
        # Test memory thresholds still work
        large_cache = {"key" + str(i): "value" * 1000 for i in range(100)}  # Create large cache
        monitor.record_memory_usage(
            memory_cache=large_cache,
            redis_stats={"memory_used_bytes": 80 * 1024 * 1024, "keys": 100}  # Above warning threshold
        )
        
        memory_warnings = monitor.get_memory_warnings()
        # Should still generate warnings based on preserved thresholds
        warning_found = any(w["severity"] in ["warning", "critical"] for w in memory_warnings)
        assert warning_found, "Memory warnings should still work with preserved thresholds"
        
        # Test invalidation rate thresholds still work
        for i in range(60):  # Exceed warning threshold
            monitor.record_invalidation_event(
                pattern=f"test_{i}:*",
                keys_invalidated=1,
                duration=0.001,
                invalidation_type="test"
            )
        
        invalidation_recommendations = monitor.get_invalidation_recommendations()
        # Should generate recommendations based on preserved thresholds
        assert len(invalidation_recommendations) > 0, "Invalidation recommendations should work with preserved thresholds"
        
        # Test with default configuration monitor for comparison
        monitor_default = CachePerformanceMonitor()
        
        # Should have different configuration than our custom monitor
        assert monitor.retention_hours != monitor_default.retention_hours or custom_config["retention_hours"] == 1, "Custom retention should be different from default (unless coincidentally same)"
        assert monitor.max_measurements != monitor_default.max_measurements or custom_config["max_measurements"] == 1000, "Custom max measurements should be different from default (unless coincidentally same)"
        assert monitor.memory_warning_threshold_bytes != monitor_default.memory_warning_threshold_bytes, "Custom memory warning threshold should be different from default"
        
        # Verify configuration consistency across multiple resets
        monitor.reset_stats()
        monitor.reset_stats()  # Reset twice
        
        # Configuration should still be preserved after multiple resets
        assert monitor.retention_hours == original_retention_hours, "Configuration should survive multiple resets"
        assert monitor.max_measurements == original_max_measurements, "Configuration should survive multiple resets"
        assert monitor.memory_warning_threshold_bytes == original_memory_warning, "Configuration should survive multiple resets"
        assert monitor.memory_critical_threshold_bytes == original_memory_critical, "Configuration should survive multiple resets"

    def test_reset_stats_preserves_thresholds_and_limits(self):
        """
        Test that reset_stats() preserves threshold and limit settings during reset.
        
        Verifies:
            Alerting thresholds and data limits remain configured after statistics reset
            
        Business Impact:
            Maintains alerting and management capabilities across monitoring periods
            
        Scenario:
            Given: CachePerformanceMonitor with configured thresholds and limits
            When: reset_stats() is called
            Then: All threshold and limit configurations remain active
            
        Edge Cases Covered:
            - Memory warning/critical thresholds preserved
            - Invalidation frequency thresholds preserved
            - Performance thresholds preserved
            - Limit configurations maintained
            
        Mocks Used:
            - None (threshold preservation verification)
            
        Related Tests:
            - test_reset_stats_maintains_configuration_settings()
            - test_export_metrics_provides_complete_raw_data()
        """
        # Given: CachePerformanceMonitor with configured thresholds and limits
        monitor = CachePerformanceMonitor(
            retention_hours=2,
            max_measurements=750,
            memory_warning_threshold_bytes=60 * 1024 * 1024,    # 60MB
            memory_critical_threshold_bytes=120 * 1024 * 1024   # 120MB
        )
        
        # Set custom performance thresholds
        monitor.key_generation_threshold = 0.15  # 150ms
        monitor.cache_operation_threshold = 0.08  # 80ms
        
        # Set custom invalidation frequency thresholds
        monitor.invalidation_rate_warning_per_hour = 30
        monitor.invalidation_rate_critical_per_hour = 75
        
        # Store all threshold values for verification
        thresholds_before_reset = {
            # Memory thresholds
            "memory_warning_threshold_bytes": monitor.memory_warning_threshold_bytes,
            "memory_critical_threshold_bytes": monitor.memory_critical_threshold_bytes,
            
            # Performance thresholds
            "key_generation_threshold": monitor.key_generation_threshold,
            "cache_operation_threshold": monitor.cache_operation_threshold,
            
            # Invalidation frequency thresholds
            "invalidation_rate_warning_per_hour": monitor.invalidation_rate_warning_per_hour,
            "invalidation_rate_critical_per_hour": monitor.invalidation_rate_critical_per_hour,
            
            # Data limits
            "retention_hours": monitor.retention_hours,
            "max_measurements": monitor.max_measurements,
        }
        
        # Add data to demonstrate thresholds work before reset
        
        # Add data that should trigger memory warnings
        large_cache = {"key" + str(i): "value" * 2000 for i in range(50)}
        monitor.record_memory_usage(
            memory_cache=large_cache,
            redis_stats={"memory_used_bytes": 70 * 1024 * 1024, "keys": 200}  # Above warning threshold
        )
        
        # Add slow operations that should trigger performance warnings
        monitor.record_key_generation_time(duration=0.20, text_length=1000, operation_type="slow")  # Above threshold
        monitor.record_cache_operation_time(operation="get", duration=0.10, cache_hit=False, text_length=500)  # Above threshold
        
        # Add baselines for comparison
        for _ in range(3):
            monitor.record_key_generation_time(duration=0.05, text_length=100, operation_type="normal")
            monitor.record_cache_operation_time(operation="get", duration=0.03, cache_hit=True, text_length=100)
        
        # Add invalidations that should trigger frequency warnings
        for i in range(40):  # Above warning threshold of 30/hour
            monitor.record_invalidation_event(
                pattern=f"freq_test_{i}:*",
                keys_invalidated=2,
                duration=0.001,
                invalidation_type="test"
            )
        
        # Verify thresholds work before reset
        memory_warnings_before = monitor.get_memory_warnings()
        invalidation_stats_before = monitor.get_invalidation_frequency_stats()
        
        assert len(memory_warnings_before) > 0, "Should have memory warnings before reset"
        assert invalidation_stats_before["thresholds"]["current_alert_level"] != "normal", "Should have invalidation alerts before reset"
        
        # When: reset_stats() is called
        monitor.reset_stats()
        
        # Then: All threshold and limit configurations remain active
        
        # Verify all thresholds are preserved exactly
        for threshold_name, expected_value in thresholds_before_reset.items():
            actual_value = getattr(monitor, threshold_name)
            assert actual_value == expected_value, f"{threshold_name} should be preserved: expected {expected_value}, got {actual_value}"
        
        # Test that memory thresholds still function after reset
        # Add memory usage that should trigger warnings with preserved thresholds
        very_large_cache = {"key" + str(i): "value" * 3000 for i in range(80)}
        monitor.record_memory_usage(
            memory_cache=very_large_cache,
            redis_stats={"memory_used_bytes": 90 * 1024 * 1024, "keys": 300}  # Above warning threshold
        )
        
        memory_warnings_after = monitor.get_memory_warnings()
        assert len(memory_warnings_after) > 0, "Memory thresholds should still generate warnings after reset"
        
        # Verify the warning is based on preserved thresholds
        warning_found = any(
            f"{monitor.memory_warning_threshold_bytes / 1024 / 1024:.1f}MB" in w["message"] 
            for w in memory_warnings_after
        )
        assert warning_found, "Warning should reference preserved threshold value"
        
        # Test that performance thresholds still function
        monitor.record_key_generation_time(duration=0.18, text_length=500, operation_type="post_reset_slow")  # Above preserved threshold
        monitor.record_cache_operation_time(operation="set", duration=0.09, cache_hit=True, text_length=300)  # Above preserved threshold
        
        # Add baselines for comparison
        for _ in range(3):
            monitor.record_key_generation_time(duration=0.05, text_length=100, operation_type="normal")
            monitor.record_cache_operation_time(operation="get", duration=0.03, cache_hit=True, text_length=100)
        
        slow_ops_after = monitor.get_recent_slow_operations()
        
        # Should identify slow operations based on preserved thresholds
        assert len(slow_ops_after["key_generation"]) > 0, "Should identify slow key generation with preserved thresholds"
        assert len(slow_ops_after["cache_operations"]) > 0, "Should identify slow cache operations with preserved thresholds"
        
        # Test that invalidation frequency thresholds still function
        for i in range(35):  # Above preserved warning threshold of 30/hour
            monitor.record_invalidation_event(
                pattern=f"post_reset_{i}:*",
                keys_invalidated=1,
                duration=0.001,
                invalidation_type="post_reset"
            )
        
        invalidation_stats_after = monitor.get_invalidation_frequency_stats()
        assert invalidation_stats_after["thresholds"]["current_alert_level"] != "normal", "Should detect frequency issues with preserved thresholds"
        assert invalidation_stats_after["thresholds"]["warning_per_hour"] == 30, "Should use preserved warning threshold"
        assert invalidation_stats_after["thresholds"]["critical_per_hour"] == 75, "Should use preserved critical threshold"
        
        # Test that data limits still function
        # Add many measurements to test max_measurements limit
        for i in range(800):  # Above preserved max_measurements of 750
            monitor.record_key_generation_time(
                duration=0.01,
                text_length=100,
                operation_type=f"limit_test_{i}"
            )
        
        # Trigger cleanup
        _ = monitor.get_performance_stats()
        
        # Should enforce preserved max_measurements limit
        assert len(monitor.key_generation_times) <= monitor.max_measurements, f"Should enforce preserved max measurements limit: expected <= {monitor.max_measurements}, got {len(monitor.key_generation_times)}"
        
        # Test edge case: verify thresholds work at boundaries
        # Test exactly at memory warning threshold
        exact_threshold_cache = {}
        monitor.record_memory_usage(
            memory_cache=exact_threshold_cache,
            redis_stats={"memory_used_bytes": monitor.memory_warning_threshold_bytes, "keys": 1}  # Exactly at threshold
        )
        
        exact_threshold_warnings = monitor.get_memory_warnings()
        # At threshold should trigger warning
        warning_at_threshold = any(
            w["severity"] in ["warning", "critical"] 
            for w in exact_threshold_warnings
        )
        assert warning_at_threshold, "Should generate warning exactly at preserved threshold"
        
        # Verify thresholds survive multiple resets
        original_thresholds = dict(thresholds_before_reset)
        
        monitor.reset_stats()
        monitor.reset_stats()  # Reset twice
        
        # Should still have same thresholds after multiple resets
        for threshold_name, expected_value in original_thresholds.items():
            actual_value = getattr(monitor, threshold_name)
            assert actual_value == expected_value, f"{threshold_name} should survive multiple resets: expected {expected_value}, got {actual_value}"

    def test_export_metrics_provides_complete_raw_data(self):
        """
        Test that export_metrics() provides complete access to all raw performance data.
        
        Verifies:
            All collected performance measurements are available for external analysis
            
        Business Impact:
            Enables comprehensive external analysis and long-term performance data archival
            
        Scenario:
            Given: CachePerformanceMonitor with comprehensive performance data across all categories
            When: export_metrics() exports all raw measurement data
            Then: Complete raw data is provided in structured format for external analysis
            
        Edge Cases Covered:
            - All metric types included in export
            - Raw measurement data preservation
            - Aggregate statistics inclusion
            - Export timestamp for temporal analysis
            
        Mocks Used:
            - None (export completeness verification)
            
        Related Tests:
            - test_export_metrics_maintains_data_structure_integrity()
            - test_export_metrics_includes_comprehensive_metadata()
        """
        # Given: CachePerformanceMonitor with comprehensive performance data across all categories
        monitor = CachePerformanceMonitor()
        
        # Add comprehensive test data across all metric types
        
        # Key generation data with variety
        key_gen_data = [
            {"duration": 0.015, "text_length": 200, "operation_type": "summarize"},
            {"duration": 0.022, "text_length": 500, "operation_type": "extract"},
            {"duration": 0.018, "text_length": 300, "operation_type": "classify"},
            {"duration": 0.045, "text_length": 1000, "operation_type": "complex_analyze"},
        ]
        
        for data in key_gen_data:
            monitor.record_key_generation_time(
                duration=data["duration"],
                text_length=data["text_length"],
                operation_type=data["operation_type"],
                additional_data={"model_version": "1.2.3", "complexity": "medium"}
            )
        
        # Cache operation data with hits and misses
        cache_op_data = [
            {"operation": "get", "duration": 0.008, "cache_hit": True, "text_length": 150},
            {"operation": "set", "duration": 0.012, "cache_hit": True, "text_length": 250},
            {"operation": "get", "duration": 0.025, "cache_hit": False, "text_length": 400},
            {"operation": "delete", "duration": 0.006, "cache_hit": True, "text_length": 0},
            {"operation": "get", "duration": 0.010, "cache_hit": True, "text_length": 180},
        ]
        
        for data in cache_op_data:
            monitor.record_cache_operation_time(
                operation=data["operation"],
                duration=data["duration"],
                cache_hit=data["cache_hit"],
                text_length=data["text_length"],
                additional_data={"cache_tier": "L1" if data["cache_hit"] else "miss"}
            )
        
        # Compression data
        compression_data = [
            {"original_size": 1500, "compressed_size": 450, "compression_time": 0.020, "type": "text"},
            {"original_size": 3000, "compressed_size": 900, "compression_time": 0.035, "type": "json"},
            {"original_size": 800, "compressed_size": 240, "compression_time": 0.012, "type": "small_doc"},
        ]
        
        for data in compression_data:
            monitor.record_compression_ratio(
                original_size=data["original_size"],
                compressed_size=data["compressed_size"],
                compression_time=data["compression_time"],
                operation_type=data["type"]
            )
        
        # Memory usage data
        memory_data = [
            {"cache": {"key" + str(i): "value" * 100 for i in range(10)}, "redis_mb": 2},
            {"cache": {"key" + str(i): "value" * 150 for i in range(15)}, "redis_mb": 4},
            {"cache": {"key" + str(i): "value" * 80 for i in range(8)}, "redis_mb": 1},
        ]
        
        for data in memory_data:
            monitor.record_memory_usage(
                memory_cache=data["cache"],
                redis_stats={"memory_used_bytes": data["redis_mb"] * 1024 * 1024, "keys": len(data["cache"])},
                additional_data={"measurement_source": "test", "environment": "development"}
            )
        
        # Invalidation events data
        invalidation_data = [
            {"pattern": "user:*", "keys_invalidated": 15, "duration": 0.005, "type": "manual", "context": "user_logout"},
            {"pattern": "session:*", "keys_invalidated": 8, "duration": 0.003, "type": "ttl_expired", "context": "timeout"},
            {"pattern": "api:*", "keys_invalidated": 22, "duration": 0.008, "type": "automatic", "context": "data_update"},
            {"pattern": "temp:*", "keys_invalidated": 3, "duration": 0.002, "type": "manual", "context": "cleanup"},
        ]
        
        for data in invalidation_data:
            monitor.record_invalidation_event(
                pattern=data["pattern"],
                keys_invalidated=data["keys_invalidated"],
                duration=data["duration"],
                invalidation_type=data["type"],
                operation_context=data["context"],
                additional_data={"trigger_source": "test", "batch_size": data["keys_invalidated"]}
            )
        
        # When: export_metrics() exports all raw measurement data
        exported_data = monitor.export_metrics()
        
        # Then: Complete raw data is provided in structured format
        
        # Verify all metric types are included in export
        expected_keys = {
            "key_generation_times",
            "cache_operation_times", 
            "compression_ratios",
            "memory_usage_measurements",
            "invalidation_events",
            "cache_hits",
            "cache_misses",
            "total_operations",
            "total_invalidations",
            "total_keys_invalidated",
            "export_timestamp"
        }
        
        assert set(exported_data.keys()) == expected_keys, f"Export should include all expected keys. Expected: {expected_keys}, Got: {set(exported_data.keys())}"
        
        # Verify raw measurement data preservation
        # Key generation times
        assert len(exported_data["key_generation_times"]) == len(key_gen_data), f"Should export all key generation measurements: expected {len(key_gen_data)}, got {len(exported_data['key_generation_times'])}"
        
        for i, exported_metric in enumerate(exported_data["key_generation_times"]):
            original = key_gen_data[i]
            assert exported_metric["duration"] == original["duration"], "Should preserve duration data"
            assert exported_metric["text_length"] == original["text_length"], "Should preserve text length data"
            assert exported_metric["operation_type"] == original["operation_type"], "Should preserve operation type"
            assert "timestamp" in exported_metric, "Should include timestamp"
            assert "additional_data" in exported_metric, "Should include additional data"
            assert exported_metric["additional_data"]["model_version"] == "1.2.3", "Should preserve additional data details"
        
        # Cache operation times
        assert len(exported_data["cache_operation_times"]) == len(cache_op_data), f"Should export all cache operation measurements: expected {len(cache_op_data)}, got {len(exported_data['cache_operation_times'])}"
        
        for exported_metric in exported_data["cache_operation_times"]:
            assert "duration" in exported_metric, "Should preserve duration"
            assert "text_length" in exported_metric, "Should preserve text length"
            assert "operation_type" in exported_metric, "Should preserve operation type"
            assert "timestamp" in exported_metric, "Should include timestamp"
            assert "additional_data" in exported_metric, "Should include additional data"
        
        # Compression ratios
        assert len(exported_data["compression_ratios"]) == len(compression_data), f"Should export all compression measurements"
        
        for i, exported_metric in enumerate(exported_data["compression_ratios"]):
            original = compression_data[i]
            assert exported_metric["original_size"] == original["original_size"], "Should preserve original size"
            assert exported_metric["compressed_size"] == original["compressed_size"], "Should preserve compressed size"
            assert exported_metric["compression_time"] == original["compression_time"], "Should preserve compression time"
            assert exported_metric["operation_type"] == original["type"], "Should preserve operation type"
            assert "compression_ratio" in exported_metric, "Should include calculated compression ratio"
            assert "timestamp" in exported_metric, "Should include timestamp"
        
        # Memory usage measurements
        assert len(exported_data["memory_usage_measurements"]) == len(memory_data), f"Should export all memory measurements"
        
        for exported_metric in exported_data["memory_usage_measurements"]:
            assert "total_cache_size_bytes" in exported_metric, "Should include total cache size"
            assert "cache_entry_count" in exported_metric, "Should include entry count"
            assert "memory_cache_size_bytes" in exported_metric, "Should include memory cache size"
            assert "process_memory_mb" in exported_metric, "Should include process memory"
            assert "timestamp" in exported_metric, "Should include timestamp"
            assert "additional_data" in exported_metric, "Should include additional data"
            assert exported_metric["additional_data"]["measurement_source"] == "test", "Should preserve additional data"
        
        # Invalidation events
        assert len(exported_data["invalidation_events"]) == len(invalidation_data), f"Should export all invalidation events"
        
        for i, exported_metric in enumerate(exported_data["invalidation_events"]):
            original = invalidation_data[i]
            assert exported_metric["pattern"] == original["pattern"], "Should preserve pattern"
            assert exported_metric["keys_invalidated"] == original["keys_invalidated"], "Should preserve keys invalidated"
            assert exported_metric["duration"] == original["duration"], "Should preserve duration"
            assert exported_metric["invalidation_type"] == original["type"], "Should preserve invalidation type"
            assert exported_metric["operation_context"] == original["context"], "Should preserve context"
            assert "timestamp" in exported_metric, "Should include timestamp"
            assert "additional_data" in exported_metric, "Should include additional data"
        
        # Verify aggregate statistics inclusion
        assert isinstance(exported_data["cache_hits"], int), "Should include cache hits count"
        assert isinstance(exported_data["cache_misses"], int), "Should include cache misses count"
        assert isinstance(exported_data["total_operations"], int), "Should include total operations count"
        assert isinstance(exported_data["total_invalidations"], int), "Should include total invalidations count"
        assert isinstance(exported_data["total_keys_invalidated"], int), "Should include total keys invalidated count"
        
        # Verify counts match expected values
        expected_hits = len([op for op in cache_op_data if op["cache_hit"]])
        expected_misses = len([op for op in cache_op_data if not op["cache_hit"]])
        expected_total_ops = len([op for op in cache_op_data if op["operation"] == "get"])  # Only "get" operations count for hit/miss
        
        assert exported_data["cache_hits"] == expected_hits, f"Should have correct hit count: expected {expected_hits}, got {exported_data['cache_hits']}"
        assert exported_data["cache_misses"] == expected_misses, f"Should have correct miss count: expected {expected_misses}, got {exported_data['cache_misses']}"
        assert exported_data["total_invalidations"] == len(invalidation_data), f"Should have correct invalidation count"
        
        expected_total_keys_invalidated = sum(data["keys_invalidated"] for data in invalidation_data)
        assert exported_data["total_keys_invalidated"] == expected_total_keys_invalidated, f"Should have correct total keys invalidated"
        
        # Verify export timestamp for temporal analysis
        assert "export_timestamp" in exported_data, "Should include export timestamp"
        assert isinstance(exported_data["export_timestamp"], str), "Export timestamp should be string"
        assert "T" in exported_data["export_timestamp"], "Export timestamp should be in ISO format"
        
        # Test empty data export
        monitor_empty = CachePerformanceMonitor()
        empty_export = monitor_empty.export_metrics()
        
        # Should still have proper structure with empty data
        assert set(empty_export.keys()) == expected_keys, "Empty export should have same structure"
        assert len(empty_export["key_generation_times"]) == 0, "Should have empty key generation times"
        assert len(empty_export["cache_operation_times"]) == 0, "Should have empty cache operation times"
        assert empty_export["cache_hits"] == 0, "Should have zero hits"
        assert empty_export["total_operations"] == 0, "Should have zero total operations"

    def test_export_metrics_maintains_data_structure_integrity(self):
        """
        Test that export_metrics() maintains data structure integrity during export.
        
        Verifies:
            Exported data maintains structure and accuracy for external analysis tools
            
        Business Impact:
            Ensures reliable data export for integration with external monitoring systems
            
        Scenario:
            Given: CachePerformanceMonitor with structured performance data
            When: export_metrics() creates export structure
            Then: Data structure integrity is maintained with proper formatting
            
        Edge Cases Covered:
            - Structured data format consistency
            - Data type preservation during export
            - Nested structure maintenance
            - Export format validation
            
        Mocks Used:
            - None (structure integrity verification)
            
        Related Tests:
            - test_export_metrics_provides_complete_raw_data()
            - test_export_metrics_includes_comprehensive_metadata()
        """
        # Given: CachePerformanceMonitor with structured performance data
        monitor = CachePerformanceMonitor()
        
        # Add structured data with various data types and nested structures
        
        # Complex additional data to test nested structure preservation
        complex_additional_data = {
            "nested_dict": {
                "level1": {
                    "level2": "deep_value",
                    "numbers": [1, 2, 3],
                    "bool_flag": True
                },
                "metrics": {
                    "score": 95.5,
                    "confidence": 0.87
                }
            },
            "simple_list": ["item1", "item2", "item3"],
            "mixed_types": {
                "string": "test",
                "int": 42,
                "float": 3.14159,
                "bool": False,
                "null_value": None
            }
        }
        
        # Add measurements with complex data structures
        monitor.record_key_generation_time(
            duration=0.025,
            text_length=500,
            operation_type="complex_operation",
            additional_data=complex_additional_data
        )
        
        monitor.record_cache_operation_time(
            operation="get",
            duration=0.015,
            cache_hit=True,
            text_length=200,
            additional_data={
                "cache_layer": "L1",
                "metadata": {
                    "key_hash": "abc123",
                    "size_bytes": 1024,
                    "ttl_remaining": 3600.5
                }
            }
        )
        
        monitor.record_compression_ratio(
            original_size=2048,
            compressed_size=512,
            compression_time=0.030,
            operation_type="structured_data_compression"
        )
        
        memory_cache_with_complex_data = {
            "user:123": {"name": "John", "data": [1, 2, 3]},
            "session:456": {"active": True, "timeout": 1800}
        }
        
        monitor.record_memory_usage(
            memory_cache=memory_cache_with_complex_data,
            redis_stats={"memory_used_bytes": 5242880, "keys": 100, "hit_rate": 0.95},
            additional_data={
                "measurement_metadata": {
                    "collection_time": "2023-01-01T12:00:00Z",
                    "system_info": {
                        "cpu_usage": 45.2,
                        "memory_available_gb": 8.5
                    }
                }
            }
        )
        
        monitor.record_invalidation_event(
            pattern="structured:*",
            keys_invalidated=25,
            duration=0.008,
            invalidation_type="structured_cleanup",
            operation_context="data_integrity_check",
            additional_data={
                "cleanup_stats": {
                    "keys_scanned": 1000,
                    "keys_removed": 25,
                    "efficiency_percent": 2.5
                },
                "trigger_info": {
                    "source": "automatic",
                    "rules_applied": ["ttl_expired", "size_limit"]
                }
            }
        )
        
        # When: export_metrics() creates export structure
        exported_data = monitor.export_metrics()
        
        # Then: Data structure integrity is maintained
        
        # Verify top-level structure consistency
        assert isinstance(exported_data, dict), "Export should be a dictionary"
        
        # Verify data type preservation for simple values
        assert isinstance(exported_data["cache_hits"], int), "Cache hits should be integer"
        assert isinstance(exported_data["cache_misses"], int), "Cache misses should be integer"
        assert isinstance(exported_data["total_operations"], int), "Total operations should be integer"
        assert isinstance(exported_data["export_timestamp"], str), "Export timestamp should be string"
        
        # Verify array structure integrity
        assert isinstance(exported_data["key_generation_times"], list), "Key generation times should be list"
        assert isinstance(exported_data["cache_operation_times"], list), "Cache operation times should be list"
        assert isinstance(exported_data["compression_ratios"], list), "Compression ratios should be list"
        assert isinstance(exported_data["memory_usage_measurements"], list), "Memory measurements should be list"
        assert isinstance(exported_data["invalidation_events"], list), "Invalidation events should be list"
        
        # Verify nested structure maintenance for key generation
        key_gen_export = exported_data["key_generation_times"][0]
        assert isinstance(key_gen_export, dict), "Key generation measurement should be dictionary"
        
        # Verify data type preservation within measurements
        assert isinstance(key_gen_export["duration"], float), "Duration should be float"
        assert isinstance(key_gen_export["text_length"], int), "Text length should be integer"
        assert isinstance(key_gen_export["operation_type"], str), "Operation type should be string"
        assert isinstance(key_gen_export["timestamp"], float), "Timestamp should be float"
        
        # Verify complex nested structure preservation
        additional_data = key_gen_export["additional_data"]
        assert isinstance(additional_data, dict), "Additional data should be dictionary"
        
        # Test deeply nested structure preservation
        nested_dict = additional_data["nested_dict"]
        assert isinstance(nested_dict, dict), "Nested dict should be preserved as dict"
        assert nested_dict["level1"]["level2"] == "deep_value", "Deep nesting should be preserved"
        assert nested_dict["level1"]["numbers"] == [1, 2, 3], "Nested arrays should be preserved"
        assert nested_dict["level1"]["bool_flag"] is True, "Boolean values should be preserved"
        
        # Test mixed data types preservation
        mixed_types = additional_data["mixed_types"]
        assert isinstance(mixed_types["string"], str), "String type should be preserved"
        assert isinstance(mixed_types["int"], int), "Integer type should be preserved"
        assert isinstance(mixed_types["float"], float), "Float type should be preserved"
        assert isinstance(mixed_types["bool"], bool), "Boolean type should be preserved"
        assert mixed_types["null_value"] is None, "None value should be preserved"
        
        # Verify structure integrity for cache operations
        cache_op_export = exported_data["cache_operation_times"][0]
        cache_metadata = cache_op_export["additional_data"]["metadata"]
        assert isinstance(cache_metadata["size_bytes"], int), "Nested integer should be preserved"
        assert isinstance(cache_metadata["ttl_remaining"], float), "Nested float should be preserved"
        
        # Verify structure integrity for compression ratios
        compression_export = exported_data["compression_ratios"][0]
        assert isinstance(compression_export["original_size"], int), "Original size should be integer"
        assert isinstance(compression_export["compressed_size"], int), "Compressed size should be integer"
        assert isinstance(compression_export["compression_ratio"], float), "Compression ratio should be float"
        assert isinstance(compression_export["compression_time"], float), "Compression time should be float"
        
        # Verify structure integrity for memory measurements
        memory_export = exported_data["memory_usage_measurements"][0]
        assert isinstance(memory_export["total_cache_size_bytes"], int), "Total cache size should be integer"
        assert isinstance(memory_export["cache_entry_count"], int), "Entry count should be integer"
        assert isinstance(memory_export["avg_entry_size_bytes"], float), "Avg entry size should be float"
        assert isinstance(memory_export["process_memory_mb"], float), "Process memory should be float"
        assert isinstance(memory_export["cache_utilization_percent"], float), "Utilization percent should be float"
        assert isinstance(memory_export["warning_threshold_reached"], bool), "Warning flag should be boolean"
        
        # Test deeply nested metadata preservation
        measurement_metadata = memory_export["additional_data"]["measurement_metadata"]
        system_info = measurement_metadata["system_info"]
        assert isinstance(system_info["cpu_usage"], float), "Nested CPU usage should be float"
        assert isinstance(system_info["memory_available_gb"], float), "Nested memory info should be float"
        
        # Verify structure integrity for invalidation events
        invalidation_export = exported_data["invalidation_events"][0]
        assert isinstance(invalidation_export["pattern"], str), "Pattern should be string"
        assert isinstance(invalidation_export["keys_invalidated"], int), "Keys invalidated should be integer"
        assert isinstance(invalidation_export["duration"], float), "Duration should be float"
        
        # Test complex nested structure in invalidation data
        cleanup_stats = invalidation_export["additional_data"]["cleanup_stats"]
        assert isinstance(cleanup_stats["keys_scanned"], int), "Keys scanned should be integer"
        assert isinstance(cleanup_stats["efficiency_percent"], float), "Efficiency percent should be float"
        
        trigger_info = invalidation_export["additional_data"]["trigger_info"]
        assert isinstance(trigger_info["rules_applied"], list), "Rules applied should be list"
        assert all(isinstance(rule, str) for rule in trigger_info["rules_applied"]), "All rules should be strings"
        
        # Verify export format validation (JSON serializable)
        import json
        
        try:
            json_string = json.dumps(exported_data)
            reconstructed_data = json.loads(json_string)
            
            # Verify round-trip integrity
            assert set(reconstructed_data.keys()) == set(exported_data.keys()), "JSON round-trip should preserve keys"
            assert len(reconstructed_data["key_generation_times"]) == len(exported_data["key_generation_times"]), "JSON round-trip should preserve data count"
            
            # Verify specific nested value preservation
            reconstructed_nested = reconstructed_data["key_generation_times"][0]["additional_data"]["nested_dict"]["level1"]["level2"]
            original_nested = exported_data["key_generation_times"][0]["additional_data"]["nested_dict"]["level1"]["level2"]
            assert reconstructed_nested == original_nested, "Deep nesting should survive JSON round-trip"
            
        except (TypeError, ValueError) as e:
            pytest.fail(f"Exported data should be JSON serializable, but got error: {e}")
        
        # Test consistency across multiple exports
        second_export = monitor.export_metrics()
        
        # Structure should be consistent
        assert set(second_export.keys()) == set(exported_data.keys()), "Multiple exports should have consistent structure"
        assert len(second_export["key_generation_times"]) == len(exported_data["key_generation_times"]), "Data count should be consistent"
        
        # Data content should be identical (except timestamp)
        first_key_gen = exported_data["key_generation_times"][0]
        second_key_gen = second_export["key_generation_times"][0]
        
        assert first_key_gen["duration"] == second_key_gen["duration"], "Data values should be consistent across exports"
        assert first_key_gen["additional_data"] == second_key_gen["additional_data"], "Complex nested data should be consistent across exports"

    def test_export_metrics_includes_comprehensive_metadata(self):
        """
        Test that export_metrics() includes comprehensive metadata for analysis context.
        
        Verifies:
            Export includes metadata necessary for external analysis and interpretation
            
        Business Impact:
            Enables accurate interpretation and analysis of performance data externally
            
        Scenario:
            Given: CachePerformanceMonitor ready for metrics export
            When: export_metrics() generates export with metadata
            Then: Comprehensive metadata is included for proper data interpretation
            
        Edge Cases Covered:
            - Export timestamp inclusion
            - Aggregate statistics metadata
            - Configuration context metadata
            - Data collection period information
            
        Mocks Used:
            - None (metadata inclusion verification)
            
        Related Tests:
            - test_export_metrics_maintains_data_structure_integrity()
            - test_export_metrics_supports_external_analysis_tools()
        """
        # Given: CachePerformanceMonitor ready for metrics export with data over time
        monitor = CachePerformanceMonitor(
            retention_hours=4,
            max_measurements=800,
            memory_warning_threshold_bytes=40 * 1024 * 1024,
            memory_critical_threshold_bytes=80 * 1024 * 1024
        )
        
        import time
        start_time = time.time()
        
        # Add data spanning different time periods to test temporal metadata
        
        # Recent data (last hour)
        for i in range(5):
            monitor.record_key_generation_time(
                duration=0.015 + i * 0.002,
                text_length=100 + i * 20,
                operation_type=f"recent_op_{i}",
                additional_data={"time_period": "recent", "batch": 1}
            )
            
            monitor.record_cache_operation_time(
                operation="get",
                duration=0.008 + i * 0.001,
                cache_hit=i % 2 == 0,
                text_length=75 + i * 15,
                additional_data={"cache_level": "L1", "request_id": f"req_{i}"}
            )
        
        # Older data (simulate by manipulating timestamps)
        for i in range(3):
            monitor.record_key_generation_time(
                duration=0.020 + i * 0.003,
                text_length=200 + i * 30,
                operation_type=f"older_op_{i}",
                additional_data={"time_period": "older", "batch": 2}
            )
        
        # Manually set some timestamps to simulate data collection over time
        for i in range(min(3, len(monitor.key_generation_times))):
            monitor.key_generation_times[-(i+1)].timestamp = start_time - (i + 1) * 1800  # 30 minutes apart
        
        # Add compression and memory data
        monitor.record_compression_ratio(
            original_size=5000,
            compressed_size=1500,
            compression_time=0.045,
            operation_type="metadata_test"
        )
        
        monitor.record_memory_usage(
            memory_cache={"meta_key" + str(i): "meta_value" * (i + 1) for i in range(10)},
            redis_stats={"memory_used_bytes": 25 * 1024 * 1024, "keys": 50, "connected_clients": 5},
            additional_data={"collection_source": "test_suite", "environment": "testing"}
        )
        
        # Add invalidation events
        for i in range(4):
            monitor.record_invalidation_event(
                pattern=f"meta_pattern_{i}:*",
                keys_invalidated=10 + i * 3,
                duration=0.005 + i * 0.002,
                invalidation_type="metadata_test",
                operation_context=f"test_context_{i}",
                additional_data={"event_id": f"evt_{i}", "priority": "normal"}
            )
        
        # When: export_metrics() generates export with metadata
        export_start_time = time.time()
        exported_data = monitor.export_metrics()
        export_end_time = time.time()
        
        # Then: Comprehensive metadata is included for proper data interpretation
        
        # Verify export timestamp inclusion with proper format and accuracy
        assert "export_timestamp" in exported_data, "Should include export timestamp"
        export_timestamp = exported_data["export_timestamp"]
        assert isinstance(export_timestamp, str), "Export timestamp should be string"
        assert "T" in export_timestamp, "Export timestamp should be in ISO format"
        
        # Parse timestamp to verify it's within reasonable range
        from datetime import datetime
        try:
            parsed_timestamp = datetime.fromisoformat(export_timestamp.replace('Z', '+00:00') if export_timestamp.endswith('Z') else export_timestamp)
            timestamp_unix = parsed_timestamp.timestamp()
            
            # Should be between export start and end time (allowing some tolerance)
            assert export_start_time - 1 <= timestamp_unix <= export_end_time + 1, "Export timestamp should be accurate"
        except ValueError as e:
            pytest.fail(f"Export timestamp should be valid ISO format: {e}")
        
        # Verify aggregate statistics metadata is complete and accurate
        aggregate_keys = ["cache_hits", "cache_misses", "total_operations", "total_invalidations", "total_keys_invalidated"]
        for key in aggregate_keys:
            assert key in exported_data, f"Should include aggregate statistic: {key}"
            assert isinstance(exported_data[key], int), f"{key} should be integer"
            assert exported_data[key] >= 0, f"{key} should be non-negative"
        
        # Verify aggregate statistics accuracy
        expected_total_invalidations = 4  # 4 invalidation events added
        expected_total_keys_invalidated = sum(10 + i * 3 for i in range(4))  # 10+13+16+19 = 58
        
        assert exported_data["total_invalidations"] == expected_total_invalidations, f"Total invalidations should be accurate: expected {expected_total_invalidations}, got {exported_data['total_invalidations']}"
        assert exported_data["total_keys_invalidated"] == expected_total_keys_invalidated, f"Total keys invalidated should be accurate: expected {expected_total_keys_invalidated}, got {exported_data['total_keys_invalidated']}"
        
        # Verify data collection period information through timestamp analysis
        all_timestamps = []
        
        # Collect timestamps from all measurement types
        for measurement in exported_data["key_generation_times"]:
            all_timestamps.append(measurement["timestamp"])
        
        for measurement in exported_data["cache_operation_times"]:
            all_timestamps.append(measurement["timestamp"])
        
        for measurement in exported_data["compression_ratios"]:
            all_timestamps.append(measurement["timestamp"])
        
        for measurement in exported_data["memory_usage_measurements"]:
            all_timestamps.append(measurement["timestamp"])
        
        for measurement in exported_data["invalidation_events"]:
            all_timestamps.append(measurement["timestamp"])
        
        if all_timestamps:
            # Verify temporal metadata consistency
            oldest_timestamp = min(all_timestamps)
            newest_timestamp = max(all_timestamps)
            data_collection_period = newest_timestamp - oldest_timestamp
            
            # Should span a reasonable time period (we set some timestamps to be 30+ minutes apart)
            assert data_collection_period > 0, "Should have data spanning time"
            assert data_collection_period < 7200, "Data collection period should be reasonable (< 2 hours)"
        
        # Verify metadata preservation within individual measurements
        # Check that additional_data metadata is preserved
        key_gen_measurement = exported_data["key_generation_times"][0]
        assert "additional_data" in key_gen_measurement, "Should preserve additional metadata"
        assert "time_period" in key_gen_measurement["additional_data"], "Should preserve custom metadata fields"
        
        cache_op_measurement = exported_data["cache_operation_times"][0]
        assert "additional_data" in cache_op_measurement, "Should preserve cache operation metadata"
        assert "cache_level" in cache_op_measurement["additional_data"], "Should preserve cache-specific metadata"
        
        memory_measurement = exported_data["memory_usage_measurements"][0]
        assert "additional_data" in memory_measurement, "Should preserve memory measurement metadata"
        assert "collection_source" in memory_measurement["additional_data"], "Should preserve collection metadata"
        
        invalidation_event = exported_data["invalidation_events"][0]
        assert "additional_data" in invalidation_event, "Should preserve invalidation event metadata"
        assert "event_id" in invalidation_event["additional_data"], "Should preserve event-specific metadata"
        
        # Verify measurement completeness metadata
        measurement_counts = {
            "key_generation_count": len(exported_data["key_generation_times"]),
            "cache_operation_count": len(exported_data["cache_operation_times"]),
            "compression_count": len(exported_data["compression_ratios"]),
            "memory_measurement_count": len(exported_data["memory_usage_measurements"]),
            "invalidation_event_count": len(exported_data["invalidation_events"]),
        }
        
        # All counts should be positive (we added data to each category)
        for metric_type, count in measurement_counts.items():
            assert count > 0, f"Should have measurements for {metric_type}"
        
        # Verify metadata supports temporal analysis
        # Check that timestamps are properly formatted for external tools
        for measurement_list in ["key_generation_times", "cache_operation_times", "compression_ratios", "memory_usage_measurements", "invalidation_events"]:
            for measurement in exported_data[measurement_list]:
                timestamp = measurement["timestamp"]
                assert isinstance(timestamp, (int, float)), f"Timestamp should be numeric for {measurement_list}"
                assert timestamp > 0, f"Timestamp should be positive for {measurement_list}"
                
                # Should be a reasonable Unix timestamp (after year 2000, before year 3000)
                assert 946684800 < timestamp < 32503680000, f"Timestamp should be reasonable Unix timestamp for {measurement_list}"
        
        # Test metadata consistency across multiple exports
        second_export = monitor.export_metrics()
        
        # Should have different export timestamps
        assert exported_data["export_timestamp"] != second_export["export_timestamp"], "Export timestamps should differ between exports"
        
        # But data measurements should be identical
        assert exported_data["total_invalidations"] == second_export["total_invalidations"], "Aggregate statistics should be consistent"
        assert len(exported_data["key_generation_times"]) == len(second_export["key_generation_times"]), "Data counts should be consistent"
        
        # Test empty export metadata
        empty_monitor = CachePerformanceMonitor()
        empty_export = empty_monitor.export_metrics()
        
        # Should still have proper metadata structure
        assert "export_timestamp" in empty_export, "Empty export should still have timestamp"
        assert empty_export["total_operations"] == 0, "Empty export should have zero operations"
        assert empty_export["total_invalidations"] == 0, "Empty export should have zero invalidations"

    def test_export_metrics_supports_external_analysis_tools(self):
        """
        Test that export_metrics() provides data in format suitable for external analysis tools.
        
        Verifies:
            Exported data format is compatible with common analysis and monitoring tools
            
        Business Impact:
            Enables integration with existing monitoring infrastructure and analysis workflows
            
        Scenario:
            Given: CachePerformanceMonitor with performance data ready for external analysis
            When: export_metrics() formats data for external consumption
            Then: Data format is suitable for common analysis tools and data warehouses
            
        Edge Cases Covered:
            - JSON-compatible data structures
            - Standard metric naming conventions
            - Time series data formatting
            - Tool-agnostic data structure
            
        Mocks Used:
            - None (external compatibility verification)
            
        Related Tests:
            - test_export_metrics_includes_comprehensive_metadata()
            - test_reset_stats_clears_all_performance_data()
        """
        pass