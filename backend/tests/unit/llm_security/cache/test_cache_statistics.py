"""
Test suite for CacheStatistics performance metrics tracking.

Tests verify CacheStatistics hit/miss recording, metrics calculation, and state
management according to the public contract defined in cache.pyi.
"""

import pytest
from datetime import datetime, UTC
from app.infrastructure.security.llm.cache import CacheStatistics


class TestCacheStatisticsInitialization:
    """Test CacheStatistics instantiation and initial state."""

    def test_statistics_initialization_with_zero_values(self):
        """
        Test that CacheStatistics initializes with zero counters and metrics.

        Verifies:
            CacheStatistics instance starts with all counters at zero (hits, misses,
            total_requests) and avg_lookup_time_ms at 0.0 per contract.

        Business Impact:
            Ensures clean baseline for cache performance monitoring without
            inherited state from previous measurements.

        Scenario:
            Given: No parameters provided to CacheStatistics constructor.
            When: CacheStatistics instance is created.
            Then: All counters are 0, avg_lookup_time_ms is 0.0, and last_reset is set to current UTC time.

        Fixtures Used:
            None - tests default initialization.
        """
        # Given: No parameters provided to CacheStatistics constructor
        # When: CacheStatistics instance is created
        stats = CacheStatistics()

        # Then: All counters are 0, avg_lookup_time_ms is 0.0
        assert stats.hits == 0, "Hits counter should initialize to 0"
        assert stats.misses == 0, "Misses counter should initialize to 0"
        assert stats.total_requests == 0, "Total requests counter should initialize to 0"
        assert stats.avg_lookup_time_ms == 0.0, "Average lookup time should initialize to 0.0"
        assert stats.cache_size == 0, "Cache size should initialize to 0"
        assert stats.memory_usage_mb == 0.0, "Memory usage should initialize to 0.0"

    def test_statistics_last_reset_timestamp_is_set(self):
        """
        Test that last_reset timestamp is automatically set during initialization.

        Verifies:
            CacheStatistics.__post_init__() automatically sets last_reset to current
            UTC time as documented in State Management section.

        Business Impact:
            Enables tracking of measurement periods for cache performance analysis
            and monitoring dashboard time ranges.

        Scenario:
            Given: CacheStatistics instance is created.
            When: The instance is initialized.
            Then: last_reset attribute contains a valid datetime object representing initialization time.

        Fixtures Used:
            None - tests initialization behavior.
        """
        # Given: CacheStatistics instance is created
        before_creation = datetime.now(UTC)
        stats = CacheStatistics()
        after_creation = datetime.now(UTC)

        # When: The instance is initialized (happens in __post_init__)
        # Then: last_reset attribute contains a valid datetime object
        assert stats.last_reset is not None, "Last reset timestamp should be set"
        assert isinstance(stats.last_reset, datetime), "Last reset should be a datetime object"
        assert stats.last_reset.tzinfo == UTC, "Last reset should be in UTC timezone"

        # Verify timestamp is within reasonable time window (within creation time)
        assert before_creation <= stats.last_reset <= after_creation, "Last reset should be set during initialization"


class TestCacheStatisticsHitRateCalculation:
    """Test hit rate property calculation logic."""

    def test_hit_rate_with_no_requests_returns_zero(self):
        """
        Test that hit_rate returns 0.0 when no requests have been recorded.

        Verifies:
            hit_rate property returns 0.0 to avoid division by zero when total_requests
            is 0, per contract's Returns section.

        Business Impact:
            Prevents mathematical errors in monitoring dashboards when cache is newly
            initialized or statistics have been reset.

        Scenario:
            Given: A CacheStatistics instance with zero hits and zero misses.
            When: The hit_rate property is accessed.
            Then: Returns 0.0 without raising division by zero error.

        Fixtures Used:
            None - tests calculation with zero state.
        """
        # Given: A CacheStatistics instance with zero hits and zero misses
        stats = CacheStatistics()

        # When: The hit_rate property is accessed
        hit_rate = stats.hit_rate

        # Then: Returns 0.0 without raising division by zero error
        assert hit_rate == 0.0, "Hit rate should be 0.0 when no requests have been recorded"
        assert isinstance(hit_rate, float), "Hit rate should be a float"

    def test_hit_rate_with_all_hits_returns_hundred_percent(self):
        """
        Test that hit_rate returns 100.0 when all requests are cache hits.

        Verifies:
            hit_rate correctly calculates percentage as (hits / total_requests) * 100
            when no misses have occurred.

        Business Impact:
            Provides accurate cache performance metrics for optimization decisions
            and capacity planning.

        Scenario:
            Given: CacheStatistics with 10 recorded hits and 0 misses.
            When: The hit_rate property is accessed.
            Then: Returns 100.0 indicating perfect cache hit rate.

        Fixtures Used:
            None - uses record_hit() calls to set up state.
        """
        # Given: CacheStatistics with 10 recorded hits and 0 misses
        stats = CacheStatistics()
        for _ in range(10):
            stats.record_hit(1.0)  # Use 1.0ms lookup time for consistency

        # When: The hit_rate property is accessed
        hit_rate = stats.hit_rate

        # Then: Returns 100.0 indicating perfect cache hit rate
        assert hit_rate == 100.0, "Hit rate should be 100.0 when all requests are hits"
        assert stats.hits == 10, "Should have 10 hits recorded"
        assert stats.misses == 0, "Should have 0 misses recorded"
        assert stats.total_requests == 10, "Should have 10 total requests"

    def test_hit_rate_with_mixed_hits_and_misses_calculates_correctly(self):
        """
        Test that hit_rate correctly calculates percentage with mixed hits and misses.

        Verifies:
            hit_rate accurately computes percentage for realistic mixed hit/miss scenarios
            per contract's calculation formula.

        Business Impact:
            Ensures monitoring dashboards display accurate cache effectiveness metrics
            for performance tuning decisions.

        Scenario:
            Given: CacheStatistics with 7 hits and 3 misses (total 10 requests).
            When: The hit_rate property is accessed.
            Then: Returns 70.0 (7/10 * 100).

        Fixtures Used:
            None - uses record_hit() and record_miss() to set up state.
        """
        # Given: CacheStatistics with 7 hits and 3 misses (total 10 requests)
        stats = CacheStatistics()

        # Record 7 hits
        for _ in range(7):
            stats.record_hit(1.0)

        # Record 3 misses
        for _ in range(3):
            stats.record_miss(1.0)

        # When: The hit_rate property is accessed
        hit_rate = stats.hit_rate

        # Then: Returns 70.0 (7/10 * 100)
        expected_hit_rate = 70.0  # (7 hits / 10 total requests) * 100
        assert hit_rate == expected_hit_rate, f"Hit rate should be {expected_hit_rate}, got {hit_rate}"
        assert stats.hits == 7, "Should have 7 hits recorded"
        assert stats.misses == 3, "Should have 3 misses recorded"
        assert stats.total_requests == 10, "Should have 10 total requests"


class TestCacheStatisticsRecordHit:
    """Test cache hit recording and metrics updates."""

    def test_record_hit_increments_hit_counter(self):
        """
        Test that record_hit() increments the hit counter by 1.

        Verifies:
            record_hit() properly increments the hits attribute per contract's Behavior section.

        Business Impact:
            Ensures accurate tracking of successful cache retrievals for performance
            analysis and optimization decisions.

        Scenario:
            Given: CacheStatistics instance with 0 hits.
            When: record_hit() is called with lookup time of 1.0ms.
            Then: hits counter is incremented to 1.

        Fixtures Used:
            None - tests state changes from method calls.
        """
        # Given: CacheStatistics instance with 0 hits
        stats = CacheStatistics()
        initial_hits = stats.hits

        # When: record_hit() is called with lookup time of 1.0ms
        stats.record_hit(1.0)

        # Then: hits counter is incremented to 1
        assert stats.hits == initial_hits + 1, "Hit counter should be incremented by 1"
        assert stats.hits == 1, "Hit counter should be 1 after first hit"

    def test_record_hit_increments_total_requests(self):
        """
        Test that record_hit() increments total_requests counter.

        Verifies:
            record_hit() updates both hits and total_requests counters per contract's Behavior section.

        Business Impact:
            Maintains accurate total request count for hit rate calculation and
            overall cache usage metrics.

        Scenario:
            Given: CacheStatistics instance with 0 total_requests.
            When: record_hit() is called.
            Then: total_requests counter is incremented to 1.

        Fixtures Used:
            None - tests state changes from method calls.
        """
        # Given: CacheStatistics instance with 0 total_requests
        stats = CacheStatistics()
        initial_total_requests = stats.total_requests

        # When: record_hit() is called
        stats.record_hit(1.5)

        # Then: total_requests counter is incremented to 1
        assert stats.total_requests == initial_total_requests + 1, "Total requests should be incremented by 1"
        assert stats.total_requests == 1, "Total requests should be 1 after first hit"
        assert stats.hits == 1, "Hit counter should also be incremented"

    def test_record_hit_updates_average_lookup_time_first_request(self):
        """
        Test that record_hit() correctly sets average lookup time for first request.

        Verifies:
            record_hit() handles first request case by setting avg_lookup_time_ms
            to the provided lookup time value per contract's Behavior section.

        Business Impact:
            Ensures accurate performance metrics from the first cache operation
            for immediate monitoring visibility.

        Scenario:
            Given: CacheStatistics instance with no previous requests.
            When: record_hit() is called with lookup_time_ms of 2.5.
            Then: avg_lookup_time_ms is set to 2.5.

        Fixtures Used:
            None - tests first request initialization.
        """
        # Given: CacheStatistics instance with no previous requests
        stats = CacheStatistics()
        lookup_time = 2.5

        # When: record_hit() is called with lookup_time_ms of 2.5
        stats.record_hit(lookup_time)

        # Then: avg_lookup_time_ms is set to 2.5
        assert stats.avg_lookup_time_ms == lookup_time, f"Average lookup time should be {lookup_time} for first request"
        assert stats.total_requests == 1, "Should have 1 total request recorded"

    def test_record_hit_updates_rolling_average_lookup_time(self):
        """
        Test that record_hit() maintains rolling average of lookup times.

        Verifies:
            record_hit() updates avg_lookup_time_ms using mathematical rolling average
            formula per contract's Behavior section.

        Business Impact:
            Provides accurate average performance metrics across all cache operations
            for identifying performance degradation trends.

        Scenario:
            Given: CacheStatistics with avg_lookup_time_ms of 2.0 from previous request.
            When: record_hit() is called with lookup_time_ms of 4.0.
            Then: avg_lookup_time_ms is updated to approximately 3.0 (rolling average).

        Fixtures Used:
            None - tests rolling average calculation.
        """
        # Given: CacheStatistics with avg_lookup_time_ms of 2.0 from previous request
        stats = CacheStatistics()
        stats.record_hit(2.0)  # First request sets average to 2.0
        assert stats.avg_lookup_time_ms == 2.0, "Initial average should be 2.0"

        # When: record_hit() is called with lookup_time_ms of 4.0
        new_lookup_time = 4.0
        stats.record_hit(new_lookup_time)

        # Then: avg_lookup_time_ms is updated to approximately 3.0 (rolling average)
        # Expected average = (2.0 * (2-1) + 4.0) / 2 = (2.0 + 4.0) / 2 = 3.0
        expected_avg = 3.0
        assert abs(stats.avg_lookup_time_ms - expected_avg) < 0.001, f"Average should be {expected_avg}, got {stats.avg_lookup_time_ms}"
        assert stats.hits == 2, "Should have 2 hits recorded"
        assert stats.total_requests == 2, "Should have 2 total requests"


class TestCacheStatisticsRecordMiss:
    """Test cache miss recording and metrics updates."""

    def test_record_miss_increments_miss_counter(self):
        """
        Test that record_miss() increments the miss counter by 1.

        Verifies:
            record_miss() properly increments the misses attribute per contract's Behavior section.

        Business Impact:
            Ensures accurate tracking of cache misses for identifying cache
            effectiveness issues and optimization opportunities.

        Scenario:
            Given: CacheStatistics instance with 0 misses.
            When: record_miss() is called with lookup time of 1.5ms.
            Then: misses counter is incremented to 1.

        Fixtures Used:
            None - tests state changes from method calls.
        """
        # Given: CacheStatistics instance with 0 misses
        stats = CacheStatistics()
        initial_misses = stats.misses

        # When: record_miss() is called with lookup time of 1.5ms
        stats.record_miss(1.5)

        # Then: misses counter is incremented to 1
        assert stats.misses == initial_misses + 1, "Miss counter should be incremented by 1"
        assert stats.misses == 1, "Miss counter should be 1 after first miss"

    def test_record_miss_increments_total_requests(self):
        """
        Test that record_miss() increments total_requests counter.

        Verifies:
            record_miss() updates both misses and total_requests counters per contract's Behavior section.

        Business Impact:
            Maintains accurate total request count for hit rate calculation and
            overall cache usage metrics.

        Scenario:
            Given: CacheStatistics instance with 0 total_requests.
            When: record_miss() is called.
            Then: total_requests counter is incremented to 1.

        Fixtures Used:
            None - tests state changes from method calls.
        """
        # Given: CacheStatistics instance with 0 total_requests
        stats = CacheStatistics()
        initial_total_requests = stats.total_requests

        # When: record_miss() is called
        stats.record_miss(2.0)

        # Then: total_requests counter is incremented to 1
        assert stats.total_requests == initial_total_requests + 1, "Total requests should be incremented by 1"
        assert stats.total_requests == 1, "Total requests should be 1 after first miss"
        assert stats.misses == 1, "Miss counter should also be incremented"
        assert stats.hits == 0, "Hit counter should remain 0 for a miss"

    def test_record_miss_updates_rolling_average_lookup_time(self):
        """
        Test that record_miss() maintains rolling average including miss timing.

        Verifies:
            record_miss() updates avg_lookup_time_ms including miss timing data,
            maintaining consistent averaging across hits and misses per contract's Behavior section.

        Business Impact:
            Provides complete performance picture including unsuccessful cache
            lookups for accurate performance analysis.

        Scenario:
            Given: CacheStatistics with avg_lookup_time_ms of 1.0 from previous requests.
            When: record_miss() is called with lookup_time_ms of 3.0.
            Then: avg_lookup_time_ms is updated to include the miss timing in rolling average.

        Fixtures Used:
            None - tests rolling average with mixed operations.
        """
        # Given: CacheStatistics with avg_lookup_time_ms of 1.0 from previous requests
        stats = CacheStatistics()
        # First, record a hit to establish an average
        stats.record_hit(1.0)
        assert stats.avg_lookup_time_ms == 1.0, "Initial average should be 1.0"
        assert stats.total_requests == 1, "Should have 1 total request initially"

        # When: record_miss() is called with lookup_time_ms of 3.0
        miss_lookup_time = 3.0
        stats.record_miss(miss_lookup_time)

        # Then: avg_lookup_time_ms is updated to include the miss timing in rolling average
        # Expected average = (1.0 * (2-1) + 3.0) / 2 = (1.0 + 3.0) / 2 = 2.0
        expected_avg = 2.0
        assert abs(stats.avg_lookup_time_ms - expected_avg) < 0.001, f"Average should be {expected_avg}, got {stats.avg_lookup_time_ms}"
        assert stats.misses == 1, "Should have 1 miss recorded"
        assert stats.hits == 1, "Should still have 1 hit recorded"
        assert stats.total_requests == 2, "Should have 2 total requests"


class TestCacheStatisticsReset:
    """Test statistics reset functionality."""

    def test_reset_clears_all_counters(self):
        """
        Test that reset() clears all counters back to zero.

        Verifies:
            reset() sets hits, misses, and total_requests to 0 per contract's Behavior section.

        Business Impact:
            Enables periodic monitoring by allowing clean measurement periods for
            cache performance analysis.

        Scenario:
            Given: CacheStatistics with non-zero hits, misses, and total_requests.
            When: reset() method is called.
            Then: All counters (hits, misses, total_requests) are set to 0.

        Fixtures Used:
            None - tests reset behavior.
        """
        # Given: CacheStatistics with non-zero hits, misses, and total_requests
        stats = CacheStatistics()
        # Add some statistics data
        stats.record_hit(1.0)
        stats.record_hit(1.5)
        stats.record_miss(2.0)

        # Verify we have non-zero values
        assert stats.hits > 0, "Should have non-zero hits before reset"
        assert stats.misses > 0, "Should have non-zero misses before reset"
        assert stats.total_requests > 0, "Should have non-zero total requests before reset"

        # When: reset() method is called
        stats.reset()

        # Then: All counters (hits, misses, total_requests) are set to 0
        assert stats.hits == 0, "Hits should be reset to 0"
        assert stats.misses == 0, "Misses should be reset to 0"
        assert stats.total_requests == 0, "Total requests should be reset to 0"

    def test_reset_clears_average_lookup_time(self):
        """
        Test that reset() clears average lookup time metric.

        Verifies:
            reset() sets avg_lookup_time_ms to 0.0 for clean measurement period
            per contract's Behavior section.

        Business Impact:
            Ensures performance metrics reflect only the current measurement period
            without influence from historical data.

        Scenario:
            Given: CacheStatistics with non-zero avg_lookup_time_ms.
            When: reset() method is called.
            Then: avg_lookup_time_ms is set to 0.0.

        Fixtures Used:
            None - tests reset behavior.
        """
        # Given: CacheStatistics with non-zero avg_lookup_time_ms
        stats = CacheStatistics()
        # Add some timing data to create a non-zero average
        stats.record_hit(1.0)
        stats.record_miss(2.0)

        # Verify we have a non-zero average
        assert stats.avg_lookup_time_ms > 0, "Should have non-zero average lookup time before reset"

        # When: reset() method is called
        stats.reset()

        # Then: avg_lookup_time_ms is set to 0.0
        assert stats.avg_lookup_time_ms == 0.0, "Average lookup time should be reset to 0.0"

    def test_reset_updates_last_reset_timestamp(self):
        """
        Test that reset() updates last_reset timestamp to current UTC time.

        Verifies:
            reset() updates last_reset attribute to mark the start of new measurement
            period per contract's Behavior section.

        Business Impact:
            Enables tracking of measurement period boundaries for time-series
            performance analysis and reporting.

        Scenario:
            Given: CacheStatistics with last_reset from initialization.
            When: reset() method is called.
            Then: last_reset is updated to current UTC time (newer than original timestamp).

        Fixtures Used:
            None - tests timestamp update behavior.
        """
        # Given: CacheStatistics with last_reset from initialization
        stats = CacheStatistics()
        original_last_reset = stats.last_reset
        assert original_last_reset is not None, "Should have initial last_reset timestamp"

        # Wait a short moment to ensure timestamp difference
        import time
        time.sleep(0.001)  # 1ms delay

        # When: reset() method is called
        before_reset = datetime.now(UTC)
        stats.reset()
        after_reset = datetime.now(UTC)

        # Then: last_reset is updated to current UTC time (newer than original timestamp)
        new_last_reset = stats.last_reset
        assert new_last_reset is not None, "Should have updated last_reset timestamp"
        assert new_last_reset != original_last_reset, "Last reset timestamp should be updated"
        assert original_last_reset < new_last_reset, "New timestamp should be newer than original"
        assert before_reset <= new_last_reset <= after_reset, "New timestamp should be within reset time window"

    def test_reset_preserves_cache_size_and_memory_usage(self):
        """
        Test that reset() does not modify cache_size and memory_usage_mb attributes.

        Verifies:
            reset() only clears counters and timing metrics, preserving cache size
            information which is set externally per contract's Behavior section.

        Business Impact:
            Maintains accurate cache size reporting across statistics resets for
            capacity monitoring and resource management.

        Scenario:
            Given: CacheStatistics with cache_size of 100 and memory_usage_mb of 5.2.
            When: reset() method is called.
            Then: cache_size remains 100 and memory_usage_mb remains 5.2.

        Fixtures Used:
            None - tests preservation of external state.
        """
        # Given: CacheStatistics with cache_size of 100 and memory_usage_mb of 5.2
        stats = CacheStatistics()
        # Set external state values
        stats.cache_size = 100
        stats.memory_usage_mb = 5.2

        # Add some internal statistics data
        stats.record_hit(1.0)
        stats.record_miss(2.0)

        # Verify initial state
        assert stats.cache_size == 100, "Initial cache size should be 100"
        assert stats.memory_usage_mb == 5.2, "Initial memory usage should be 5.2"
        assert stats.total_requests > 0, "Should have recorded some requests"

        # When: reset() method is called
        stats.reset()

        # Then: cache_size remains 100 and memory_usage_mb remains 5.2
        assert stats.cache_size == 100, "Cache size should be preserved at 100"
        assert stats.memory_usage_mb == 5.2, "Memory usage should be preserved at 5.2"
        # But internal counters should be reset
        assert stats.hits == 0, "Hits should be reset"
        assert stats.misses == 0, "Misses should be reset"
        assert stats.total_requests == 0, "Total requests should be reset"
        assert stats.avg_lookup_time_ms == 0.0, "Average lookup time should be reset"


class TestCacheStatisticsToDictSerialization:
    """Test statistics export to dictionary format."""

    def test_to_dict_includes_all_documented_fields(self):
        """
        Test that to_dict() includes all 8 documented statistics fields.

        Verifies:
            to_dict() returns dictionary containing hits, misses, total_requests, hit_rate,
            avg_lookup_time_ms, cache_size, memory_usage_mb, and last_reset per contract's Returns section.

        Business Impact:
            Ensures complete statistics export for API responses and monitoring
            dashboards without missing metrics.

        Scenario:
            Given: CacheStatistics instance with various recorded metrics.
            When: to_dict() method is called.
            Then: Dictionary contains all 8 documented field names.

        Fixtures Used:
            None - tests export completeness.
        """
        # Given: CacheStatistics instance with various recorded metrics
        stats = CacheStatistics()
        stats.record_hit(1.0)
        stats.record_miss(2.0)
        stats.cache_size = 50
        stats.memory_usage_mb = 2.5

        # When: to_dict() method is called
        result = stats.to_dict()

        # Then: Dictionary contains all 8 documented field names
        expected_fields = {
            "hits", "misses", "total_requests", "hit_rate",
            "avg_lookup_time_ms", "cache_size", "memory_usage_mb", "last_reset"
        }

        actual_fields = set(result.keys())
        assert actual_fields == expected_fields, f"Dictionary should contain all expected fields: {expected_fields}, got: {actual_fields}"

        # Verify all values are present
        assert result["hits"] == 1, "Hits should be 1"
        assert result["misses"] == 1, "Misses should be 1"
        assert result["total_requests"] == 2, "Total requests should be 2"
        assert result["cache_size"] == 50, "Cache size should be 50"
        assert result["memory_usage_mb"] == 2.5, "Memory usage should be 2.5"

    def test_to_dict_formats_hit_rate_with_two_decimals(self):
        """
        Test that to_dict() rounds hit_rate to 2 decimal places.

        Verifies:
            to_dict() formats hit_rate percentage with 2 decimal precision for
            consistent API responses per contract's Returns section.

        Business Impact:
            Provides consistent metric formatting across monitoring systems and
            prevents excessive precision in dashboard displays.

        Scenario:
            Given: CacheStatistics with calculated hit_rate of 66.666666%.
            When: to_dict() is called.
            Then: Dictionary contains hit_rate rounded to 66.67.

        Fixtures Used:
            None - tests numeric formatting.
        """
        # Given: CacheStatistics with calculated hit_rate of 66.666666%
        stats = CacheStatistics()
        # Record 2 hits and 1 miss to get 66.666...% hit rate
        stats.record_hit(1.0)
        stats.record_hit(1.0)
        stats.record_miss(1.0)

        # Verify actual hit rate is approximately 66.666...%
        expected_hit_rate = 66.66666666666667  # (2/3) * 100
        assert abs(stats.hit_rate - expected_hit_rate) < 0.001, f"Hit rate should be approximately {expected_hit_rate}"

        # When: to_dict() is called
        result = stats.to_dict()

        # Then: Dictionary contains hit_rate rounded to 66.67
        assert "hit_rate" in result, "Hit rate should be in dictionary"
        assert result["hit_rate"] == 66.67, f"Hit rate should be rounded to 2 decimal places: 66.67, got {result['hit_rate']}"
        assert isinstance(result["hit_rate"], float), "Hit rate should remain a float type"

    def test_to_dict_formats_avg_lookup_time_with_three_decimals(self):
        """
        Test that to_dict() rounds avg_lookup_time_ms to 3 decimal places.

        Verifies:
            to_dict() formats timing data with 3 decimal precision for consistent
            performance metric reporting per contract's Returns section.

        Business Impact:
            Provides precise timing data for performance analysis while avoiding
            excessive precision in monitoring displays.

        Scenario:
            Given: CacheStatistics with avg_lookup_time_ms of 1.23456789.
            When: to_dict() is called.
            Then: Dictionary contains avg_lookup_time_ms rounded to 1.235.

        Fixtures Used:
            None - tests numeric formatting.
        """
        # Given: CacheStatistics with avg_lookup_time_ms of 1.23456789
        stats = CacheStatistics()
        # Create timing data that will result in a precise average
        stats.record_hit(1.23456789)

        # Verify the actual average has more precision
        assert abs(stats.avg_lookup_time_ms - 1.23456789) < 0.001, f"Average should be approximately 1.23456789, got {stats.avg_lookup_time_ms}"

        # When: to_dict() is called
        result = stats.to_dict()

        # Then: Dictionary contains avg_lookup_time_ms rounded to 1.235
        assert "avg_lookup_time_ms" in result, "Average lookup time should be in dictionary"
        assert result["avg_lookup_time_ms"] == 1.235, f"Average lookup time should be rounded to 3 decimal places: 1.235, got {result['avg_lookup_time_ms']}"
        assert isinstance(result["avg_lookup_time_ms"], float), "Average lookup time should remain a float type"

    def test_to_dict_formats_memory_usage_with_two_decimals(self):
        """
        Test that to_dict() rounds memory_usage_mb to 2 decimal places.

        Verifies:
            to_dict() formats memory usage with 2 decimal precision for consistent
            resource metric reporting per contract's Returns section.

        Business Impact:
            Provides consistent memory usage formatting across monitoring systems
            for capacity planning and resource management.

        Scenario:
            Given: CacheStatistics with memory_usage_mb of 5.6789.
            When: to_dict() is called.
            Then: Dictionary contains memory_usage_mb rounded to 5.68.

        Fixtures Used:
            None - tests numeric formatting.
        """
        # Given: CacheStatistics with memory_usage_mb of 5.6789
        stats = CacheStatistics()
        stats.memory_usage_mb = 5.6789

        # When: to_dict() is called
        result = stats.to_dict()

        # Then: Dictionary contains memory_usage_mb rounded to 5.68
        assert "memory_usage_mb" in result, "Memory usage should be in dictionary"
        assert result["memory_usage_mb"] == 5.68, f"Memory usage should be rounded to 2 decimal places: 5.68, got {result['memory_usage_mb']}"
        assert isinstance(result["memory_usage_mb"], float), "Memory usage should remain a float type"

    def test_to_dict_formats_last_reset_as_iso_string(self):
        """
        Test that to_dict() converts last_reset datetime to ISO string format.

        Verifies:
            to_dict() serializes last_reset timestamp to ISO-formatted string for
            JSON compatibility per contract's Returns section.

        Business Impact:
            Ensures timestamps are serializable in API responses and can be parsed
            by monitoring systems for time-series analysis.

        Scenario:
            Given: CacheStatistics with last_reset datetime object.
            When: to_dict() is called.
            Then: Dictionary contains last_reset as ISO-formatted string.

        Fixtures Used:
            None - tests datetime serialization.
        """
        # Given: CacheStatistics with last_reset datetime object
        stats = CacheStatistics()
        assert stats.last_reset is not None, "Last reset should be set"
        assert isinstance(stats.last_reset, datetime), "Last reset should be a datetime object"

        # When: to_dict() is called
        result = stats.to_dict()

        # Then: Dictionary contains last_reset as ISO-formatted string
        assert "last_reset" in result, "Last reset should be in dictionary"
        assert isinstance(result["last_reset"], str), "Last reset should be serialized as string"

        # Verify it's a valid ISO format by trying to parse it back
        parsed_datetime = datetime.fromisoformat(result["last_reset"])
        assert parsed_datetime == stats.last_reset, "Serialized datetime should match original when parsed"
        assert parsed_datetime.tzinfo == UTC, "Parsed datetime should maintain UTC timezone"

    def test_to_dict_handles_none_last_reset_gracefully(self):
        """
        Test that to_dict() handles None value for last_reset without errors.

        Verifies:
            to_dict() gracefully handles None last_reset (if initialization failed)
            by including None in output per contract's Returns section.

        Business Impact:
            Prevents serialization errors in edge cases where statistics
            initialization may have encountered issues.

        Scenario:
            Given: CacheStatistics with last_reset set to None.
            When: to_dict() is called.
            Then: Dictionary contains last_reset as None without raising exceptions.

        Fixtures Used:
            None - tests None handling in serialization.
        """
        # Given: CacheStatistics with last_reset set to None
        stats = CacheStatistics()
        # Manually set last_reset to None to test error handling
        stats.last_reset = None

        # When: to_dict() is called
        result = stats.to_dict()

        # Then: Dictionary contains last_reset as None without raising exceptions
        assert "last_reset" in result, "Last reset field should still be present"
        assert result["last_reset"] is None, "Last reset should be None in serialized result"

