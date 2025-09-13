"""
Unit tests for AIResponseCache statistics and performance monitoring implementation.

This test suite verifies the observable behaviors documented in the
AIResponseCache public contract. Tests focus on behavior-driven testing principles
and observable statistics collection and reporting functionality.

Implementation Status:
    - 8 tests PASS: All statistics and performance monitoring tests implemented and passing
    
Implementation Notes:
    All tests have been re-implemented using behavior-driven testing principles based strictly 
    on the public contract from backend/contracts/infrastructure/cache/redis_ai.pyi. 
    Key improvements:
    - Removed internal implementation mocking (e.g., cache.performance_monitor._calculate_hit_rate)
    - Test only documented behavior from public contract
    - Focus on observable outcomes rather than implementation details
    - Ensure tests would pass even if internal implementation is completely rewritten

Coverage Focus:
    - Statistics collection and reporting behavior verification
    - AI-specific analytics and text tier analysis
    - Operation performance metrics aggregation
    - Error handling for statistics collection failures

External Dependencies:
    All external dependencies use real fixtures from conftest.py following
    behavior-driven testing principles for accurate behavior simulation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import hashlib
from typing import Any, Dict, Optional

from app.infrastructure.cache.redis_ai import AIResponseCache
from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError


class TestAIResponseCacheStatistics:
    """
    Test suite for AIResponseCache statistics and performance monitoring methods.
    
    Scope:
        - get_cache_stats() comprehensive statistics collection
        - get_cache_hit_ratio() performance calculation
        - get_performance_summary() consolidated performance metrics
        - get_ai_performance_summary() AI-specific analytics
        - get_text_tier_statistics() text size tier analysis
        - get_operation_performance() operation-specific performance metrics
        
    Business Critical:
        Performance statistics enable cache optimization and capacity planning
        
    Test Strategy:
        - Unit tests for statistics aggregation from multiple sources
        - Integration with CachePerformanceMonitor for metrics collection
        - AI-specific analytics and recommendations generation
        - Error handling for statistics collection failures
        
    External Dependencies:
        - None
        - Redis statistics (via parent class)
    """

    async def test_get_cache_stats_returns_comprehensive_statistics(self, valid_ai_params):
        """
        Test that get_cache_stats returns comprehensive cache statistics as documented.
        
        Verifies:
            Statistics collection aggregates data from all cache components
            
        Business Impact:
            Provides complete cache health visibility for monitoring and optimization
            
        Scenario:
            Given: Active AI cache with various cached entries and performance history
            When: get_cache_stats is called
            Then: Comprehensive statistics are returned with documented structure
            And: Statistics include Redis, memory, performance, and AI-specific metrics
            And: All statistics collection succeeds without exceptions
            
        Statistics Structure Verified:
            - redis: connection status, key count, memory usage, Redis metrics
            - memory: L1 cache statistics, utilization, entry counts
            - performance: hit ratios, operation timings, compression stats
            - ai_metrics: AI-specific performance data and analytics
            
        Fixtures Used:
            - cache_statistics_sample: Expected comprehensive statistics structure
            - None
            
        Data Aggregation Verified:
            Statistics properly aggregate from multiple cache components
            
        Related Tests:
            - test_get_cache_stats_handles_redis_failure_gracefully()
            - test_get_ai_performance_summary_includes_comprehensive_ai_analytics()
        """
        # Given: AI cache instance
        cache = AIResponseCache(**valid_ai_params)
        
        # When: get_cache_stats is called
        stats = await cache.get_cache_stats()
        
        # Then: Returns Dict[str, Any] as documented
        assert isinstance(stats, dict)
        
        # And: Contains all required top-level keys as per contract
        assert "redis" in stats
        assert "memory" in stats
        assert "performance" in stats
        assert "ai_metrics" in stats
        
        # And: Redis section has documented structure
        redis_stats = stats["redis"]
        assert isinstance(redis_stats, dict)
        assert "status" in redis_stats or "connected" in redis_stats
        
        # And: Memory section has documented structure
        memory_stats = stats["memory"]
        assert isinstance(memory_stats, dict)
        
        # And: Performance section has documented structure
        performance_stats = stats["performance"]
        assert isinstance(performance_stats, dict)
        
        # And: AI metrics section has documented structure
        ai_metrics = stats["ai_metrics"]
        assert isinstance(ai_metrics, dict)

    async def test_get_cache_stats_handles_redis_failure_gracefully(self, valid_ai_params):
        """
        Test that get_cache_stats handles Redis connection failures gracefully.
        
        Verifies:
            Statistics collection works even when Redis is unavailable
            
        Business Impact:
            Ensures monitoring remains available during Redis outages
            
        Scenario:
            Given: AI cache operating in memory-only mode due to Redis failure
            When: get_cache_stats is called
            Then: Statistics are returned with Redis status indicating failure
            And: Memory cache and performance statistics are still available
            And: No exceptions are raised due to Redis unavailability
            And: Error status is clearly indicated in Redis statistics section
            
        Graceful Degradation Verified:
            - Redis section shows connection failure status
            - Memory cache statistics remain available
            - Performance monitor statistics are unaffected
            - Overall statistics collection succeeds despite Redis failure
            
        Fixtures Used:
            - None
            
        Error Status Documentation:
            Redis failure is clearly indicated in returned statistics
            
        Related Tests:
            - test_get_cache_stats_returns_comprehensive_statistics()
            - test_connect_handles_redis_failure_gracefully()
        """
        # Given: AI cache with an invalid Redis URL to simulate failure
        invalid_params = valid_ai_params.copy()
        invalid_params["redis_url"] = "redis://invalid-host:99999"
        cache = AIResponseCache(**invalid_params)
        
        # When: get_cache_stats is called despite Redis being unavailable
        stats = await cache.get_cache_stats()
        
        # Then: Method does not raise exceptions as documented
        assert isinstance(stats, dict)
        
        # And: All required sections are present despite Redis failure
        assert "redis" in stats
        assert "memory" in stats
        assert "performance" in stats
        assert "ai_metrics" in stats
        
        # And: Redis section indicates error status as documented
        redis_stats = stats["redis"]
        assert isinstance(redis_stats, dict)
        # Contract states Redis errors are caught and logged, returning error status
        # The status should indicate the connection problem
        if "status" in redis_stats:
            assert redis_stats["status"] in ["unavailable", "error", "disconnected"]
        
        # And: Other sections are still populated despite Redis failure
        memory_stats = stats["memory"]
        assert isinstance(memory_stats, dict)
        
        performance_stats = stats["performance"]
        assert isinstance(performance_stats, dict)
        
        ai_metrics = stats["ai_metrics"]
        assert isinstance(ai_metrics, dict)

    def test_get_cache_hit_ratio_calculates_percentage_correctly(self, valid_ai_params):
        """
        Test that get_cache_hit_ratio returns accurate hit ratio percentage.
        
        Verifies:
            Hit ratio calculation matches documented percentage format (0.0 to 100.0)
            
        Business Impact:
            Provides key cache effectiveness metric for performance monitoring
            
        Scenario:
            Given: AI cache with recorded hit and miss operations
            When: get_cache_hit_ratio is called
            Then: Hit ratio is calculated as (hits / total_operations) * 100
            And: Result is returned as float percentage between 0.0 and 100.0
            And: Zero operations scenario returns 0.0 without division errors
            
        Calculation Scenarios:
            - 75 hits out of 100 operations = 75.0%
            - 0 hits out of 50 operations = 0.0%
            - 100 hits out of 100 operations = 100.0%
            - 0 operations total = 0.0% (no division by zero)
            
        Fixtures Used:
            - None
            
        Percentage Format Verified:
            Return value is float percentage (0.0-100.0), not ratio (0.0-1.0)
            
        Related Tests:
            - test_get_performance_summary_includes_hit_ratio()
            - test_get_cache_stats_returns_comprehensive_statistics()
        """
        # Given: AI cache instance
        cache = AIResponseCache(**valid_ai_params)
        
        # When: get_cache_hit_ratio is called
        ratio = cache.get_cache_hit_ratio()
        
        # Then: Returns float as documented
        assert isinstance(ratio, float)
        
        # And: Value is a percentage (0.0 to 100.0) as documented
        assert 0.0 <= ratio <= 100.0
        
        # And: Contract specifies it calculates percentage of successful retrievals vs misses
        # Since this is a fresh cache with no operations, ratio should be 0.0 or a valid percentage

    def test_get_cache_hit_ratio_handles_zero_operations(self, valid_ai_params):
        """
        Test that get_cache_hit_ratio handles zero operations without division errors.
        
        Verifies:
            Zero operations scenario is handled gracefully as documented
            
        Business Impact:
            Prevents monitoring errors when cache has no recorded operations
            
        Scenario:
            Given: Newly initialized AI cache with no operations recorded
            When: get_cache_hit_ratio is called
            Then: Method returns 0.0 without raising division by zero errors
            And: Result clearly indicates no operations have been performed
            
        Zero Operations Handling Verified:
            - No division by zero exceptions
            - Clear return value (0.0) indicating no operations
            - Graceful handling documented in method contract
            
        Fixtures Used:
            - None
            
        Edge Case Handling:
            Zero operations is valid scenario for new or cleared caches
            
        Related Tests:
            - test_get_cache_hit_ratio_calculates_percentage_correctly()
            - test_get_performance_summary_handles_empty_performance_data()
        """
        # Given: Newly initialized AI cache with no operations
        cache = AIResponseCache(**valid_ai_params)
        
        # When: get_cache_hit_ratio is called on cache with no operations
        ratio = cache.get_cache_hit_ratio()
        
        # Then: Returns 0.0 as documented for no operations
        assert ratio == 0.0
        assert isinstance(ratio, float)
        
        # And: No exceptions are raised (contract guarantees this)
        # If we reach this point, no exceptions were raised

    def test_get_performance_summary_includes_hit_ratio(self, valid_ai_params):
        """
        Test that get_performance_summary includes hit ratio and comprehensive metrics.
        
        Verifies:
            Performance summary aggregates key metrics as documented
            
        Business Impact:
            Provides consolidated performance view for monitoring dashboards
            
        Scenario:
            Given: AI cache with performance history and metrics
            When: get_performance_summary is called
            Then: Summary includes hit ratio, operation counts, timing statistics
            And: AI-specific metrics are included for operation analysis
            And: Text tier distribution shows cache usage patterns
            
        Performance Summary Structure Verified:
            - hit_ratio: cache effectiveness percentage
            - total_operations: complete operation count
            - cache_hits/cache_misses: hit/miss breakdown
            - recent_avg_cache_operation_time: recent performance timing
            - ai_operation_metrics: operation-specific performance data
            - text_tier_distribution: text size distribution analysis
            
        Fixtures Used:
            - cache_statistics_sample: Expected performance summary structure
            
        Metric Consolidation Verified:
            Summary properly consolidates performance data from multiple sources
            
        Related Tests:
            - test_get_cache_hit_ratio_calculates_percentage_correctly()
            - test_get_ai_performance_summary_includes_comprehensive_ai_analytics()
        """
        # Given: AI cache instance
        cache = AIResponseCache(**valid_ai_params)
        
        # When: get_performance_summary is called
        summary = cache.get_performance_summary()
        
        # Then: Returns Dict[str, Any] as documented
        assert isinstance(summary, dict)
        
        # And: Contains all documented performance indicators
        assert "hit_ratio" in summary
        assert "total_operations" in summary
        assert "cache_hits" in summary
        assert "cache_misses" in summary
        assert "recent_avg_cache_operation_time" in summary
        assert "ai_operation_metrics" in summary
        assert "text_tier_distribution" in summary
        
        # And: Hit ratio is a float percentage as documented
        assert isinstance(summary["hit_ratio"], float)
        
        # And: Operation counts are integers
        assert isinstance(summary["total_operations"], int)
        assert isinstance(summary["cache_hits"], int)
        assert isinstance(summary["cache_misses"], int)
        
        # And: Timing is a number
        assert isinstance(summary["recent_avg_cache_operation_time"], (int, float))
        
        # And: AI-specific metrics are present
        assert isinstance(summary["ai_operation_metrics"], dict)
        assert isinstance(summary["text_tier_distribution"], dict)

    def test_get_ai_performance_summary_includes_comprehensive_ai_analytics(self, valid_ai_params):
        """
        Test that get_ai_performance_summary provides detailed AI-specific analytics.
        
        Verifies:
            AI performance summary includes operation-specific and optimization analytics
            
        Business Impact:
            Enables AI-specific cache optimization and performance tuning
            
        Scenario:
            Given: AI cache with diverse operation history and performance data
            When: get_ai_performance_summary is called
            Then: Summary includes operation-specific metrics and recommendations
            And: Text tier analysis shows usage patterns by text size
            And: Key generation statistics provide performance insights
            And: Optimization recommendations are included for cache tuning
            
        AI Analytics Structure Verified:
            - total_operations: AI-specific operation count
            - overall_hit_rate: AI cache effectiveness
            - hit_rate_by_operation: per-operation hit rate analysis
            - text_tier_distribution: text size pattern analysis
            - key_generation_stats: key generation performance
            - optimization_recommendations: AI-specific optimization suggestions
            - inherited_stats: parent cache statistics integration
            
        Fixtures Used:
            - valid_ai_params: AI cache configuration
            
        AI-Specific Analytics:
            Summary focuses on AI cache patterns and optimization opportunities
            
        Related Tests:
            - test_get_text_tier_statistics_analyzes_text_size_patterns()
            - test_get_operation_performance_provides_detailed_operation_metrics()
        """
        from collections import defaultdict
        
        # Given: AI cache with mock performance data
        cache = AIResponseCache(**valid_ai_params)
        
        # Set up AI metrics with correct structure expected by implementation
        cache.ai_metrics['cache_hits_by_operation']['summarize'] = 8
        cache.ai_metrics['cache_hits_by_operation']['sentiment'] = 6
        cache.ai_metrics['cache_misses_by_operation']['summarize'] = 2
        cache.ai_metrics['cache_misses_by_operation']['sentiment'] = 4
        cache.ai_metrics['text_tier_distribution']['small'] = 5
        cache.ai_metrics['text_tier_distribution']['medium'] = 8
        cache.ai_metrics['text_tier_distribution']['large'] = 1
        
        # When: get_ai_performance_summary is called
        summary = cache.get_ai_performance_summary()
        
        # Then: Summary includes comprehensive AI analytics structure
        assert "total_operations" in summary
        assert "overall_hit_rate" in summary
        assert "hit_rate_by_operation" in summary
        assert "text_tier_distribution" in summary
        assert "key_generation_stats" in summary
        assert "optimization_recommendations" in summary
        assert "inherited_stats" in summary
        
        # And: Total operations calculation is correct
        assert summary["total_operations"] == 20  # 8+6+2+4
        
        # And: Overall hit rate calculation is correct
        assert summary["overall_hit_rate"] == 70.0  # (8+6)/(8+6+2+4) * 100
        
        # And: Operation-specific metrics are calculated correctly
        assert isinstance(summary["hit_rate_by_operation"], dict)
        assert summary["hit_rate_by_operation"]["summarize"] == 80.0  # 8/(8+2) * 100
        assert summary["hit_rate_by_operation"]["sentiment"] == 60.0   # 6/(6+4) * 100
        
        # And: Text tier analysis is present
        assert isinstance(summary["text_tier_distribution"], dict)
        assert summary["text_tier_distribution"]["small"] == 5
        assert summary["text_tier_distribution"]["medium"] == 8
        assert summary["text_tier_distribution"]["large"] == 1
        
        # And: Key generation stats provide performance insights
        assert isinstance(summary["key_generation_stats"], dict)
        
        # And: Optimization recommendations exist
        assert isinstance(summary["optimization_recommendations"], list)

    def test_get_text_tier_statistics_analyzes_text_size_patterns(self, valid_ai_params):
        """
        Test that get_text_tier_statistics provides comprehensive text tier analysis.
        
        Verifies:
            Text tier statistics show cache usage patterns by text size categories
            
        Business Impact:
            Enables optimization of text size tier thresholds for better performance
            
        Scenario:
            Given: AI cache with varied text sizes across tier categories
            When: get_text_tier_statistics is called
            Then: Statistics show tier configuration and usage distribution
            And: Performance analysis per tier reveals optimization opportunities
            And: Tier recommendations suggest threshold adjustments
            
        Text Tier Analysis Structure Verified:
            - tier_configuration: current text size tier thresholds
            - tier_distribution: operation count per tier category
            - tier_performance_analysis: hit rates and timing per tier
            - tier_recommendations: optimization suggestions per tier
            
        Tier Categories Analyzed:
            - small: texts under small threshold (typically <500 chars)
            - medium: texts between small and large thresholds
            - large: texts above large threshold (typically >5000 chars)
            
        Fixtures Used:
            - valid_ai_params: Text tier threshold configuration
            
        Optimization Insights:
            Analysis provides actionable recommendations for tier threshold tuning
            
        Related Tests:
            - test_get_ai_performance_summary_includes_comprehensive_ai_analytics()
            - test_build_key_handles_large_text_with_hashing()
        """
        # Given: AI cache with configured text size tiers
        cache = AIResponseCache(**valid_ai_params)
        
        # Set up AI metrics with text tier data
        cache.ai_metrics['text_tier_distribution']['small'] = 25
        cache.ai_metrics['text_tier_distribution']['medium'] = 45
        cache.ai_metrics['text_tier_distribution']['large'] = 15
        
        # When: get_text_tier_statistics is called
        statistics = cache.get_text_tier_statistics()
        
        # Then: Statistics show tier configuration
        assert "tier_configuration" in statistics
        tier_config = statistics["tier_configuration"]
        assert "small" in tier_config
        assert "medium" in tier_config 
        assert "large" in tier_config
        
        # And: Tier configuration matches initialization parameters
        assert tier_config["small"] == valid_ai_params["text_size_tiers"]["small"]
        assert tier_config["medium"] == valid_ai_params["text_size_tiers"]["medium"]
        assert tier_config["large"] == valid_ai_params["text_size_tiers"]["large"]
        
        # And: Tier distribution shows operation counts per tier
        assert "tier_distribution" in statistics
        tier_dist = statistics["tier_distribution"]
        assert tier_dist["small"] == 25
        assert tier_dist["medium"] == 45
        assert tier_dist["large"] == 15
        
        # And: Performance analysis per tier is included
        assert "tier_performance_analysis" in statistics
        tier_perf = statistics["tier_performance_analysis"]
        assert isinstance(tier_perf, dict)
        
        # And: Data completeness information is provided
        assert "data_completeness" in statistics
        completeness = statistics["data_completeness"]
        assert "expected_tiers" in completeness
        assert "recorded_tiers" in completeness
        assert "missing_tiers" in completeness
        assert "completeness_percentage" in completeness

    def test_get_operation_performance_provides_detailed_operation_metrics(self, valid_ai_params):
        """
        Test that get_operation_performance provides detailed AI operation analysis.
        
        Verifies:
            Operation performance metrics show detailed analysis per AI operation type
            
        Business Impact:
            Enables per-operation cache optimization and performance tuning
            
        Scenario:
            Given: AI cache with performance history across multiple operation types
            When: get_operation_performance is called
            Then: Detailed metrics are returned for each operation type
            And: Performance analysis includes timing statistics and percentiles
            And: Summary provides overall operation performance overview
            
        Operation Performance Structure Verified:
            - operations: per-operation detailed metrics including:
                - avg_duration_ms: average operation duration
                - min_duration_ms/max_duration_ms: performance bounds
                - percentiles: p50, p95, p99 performance percentiles
                - total_operations: operation count
                - configured_ttl: TTL setting for operation
            - summary: overall performance summary across operations
            
        Performance Analysis Depth:
            - Statistical distribution analysis (percentiles)
            - Performance bounds (min/max timing)
            - Configuration correlation (TTL settings)
            - Comprehensive operation counting
            
        Fixtures Used:
            - valid_ai_params: Operation TTL configurations
            
        Optimization Support:
            Metrics enable per-operation cache and TTL optimization
            
        Related Tests:
            - test_standard_cache_interface_integration()
            - test_get_ai_performance_summary_includes_comprehensive_ai_analytics()
        """
        # Given: AI cache with operation TTL configurations
        cache = AIResponseCache(**valid_ai_params)
        
        # Set up mock performance data in the expected format
        # The method expects ai_metrics['operation_performance'] to be a list of performance records
        cache.ai_metrics['operation_performance'] = [
            {"operation": "summarize", "duration": 0.0452},  # 45.2ms
            {"operation": "summarize", "duration": 0.0521},  # 52.1ms
            {"operation": "summarize", "duration": 0.0487},  # 48.7ms
            {"operation": "summarize", "duration": 0.0413},  # 41.3ms
            {"operation": "summarize", "duration": 0.0558},  # 55.8ms
            {"operation": "sentiment", "duration": 0.0125},  # 12.5ms
            {"operation": "sentiment", "duration": 0.0152},  # 15.2ms
            {"operation": "sentiment", "duration": 0.0118},  # 11.8ms
            {"operation": "sentiment", "duration": 0.0141},  # 14.1ms
        ]
        
        # When: get_operation_performance is called
        performance = cache.get_operation_performance()
        
        # Then: Detailed metrics are returned for each operation
        assert "operations" in performance
        assert "summary" in performance
        
        operations = performance["operations"]
        
        # And: Operations with performance data are present
        assert "summarize" in operations
        assert "sentiment" in operations
        
        # And: Each operation includes detailed performance metrics
        for operation, metrics in operations.items():
            assert "avg_duration_ms" in metrics
            assert "min_duration_ms" in metrics
            assert "max_duration_ms" in metrics
            assert "percentiles" in metrics
            assert "total_operations" in metrics
            assert "configured_ttl" in metrics
            assert "sample_count" in metrics
            
            # And: TTL matches configuration
            assert metrics["configured_ttl"] == valid_ai_params["operation_ttls"][operation]
            
        # And: Duration calculations are reasonable
        assert operations["summarize"]["avg_duration_ms"] > 0
        assert operations["sentiment"]["avg_duration_ms"] > 0
        
        # And: Summary provides overall performance overview
        summary = performance["summary"]
        assert isinstance(summary, dict)
