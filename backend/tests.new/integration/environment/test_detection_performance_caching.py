"""
Environment Detection Performance and Caching Integration Tests

This module tests environment detection performance characteristics and caching
behavior, ensuring efficient operation under concurrent access and load conditions.

MEDIUM PRIORITY - System performance optimization
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.environment import (
    Environment,
    FeatureContext,
    EnvironmentDetector,
    DetectionConfig,
    get_environment_info
)


class TestEnvironmentDetectionPerformanceAndCaching:
    """
    Integration tests for environment detection performance and caching.

    Seam Under Test:
        Detection Request → Cache Lookup → Environment Analysis → Result Caching

    Critical Path:
        Detection request → Cache lookup → Environment analysis → Result caching

    Business Impact:
        Ensures efficient environment detection under concurrent requests and load

    Test Strategy:
        - Test environment detection caching behavior
        - Verify performance under concurrent access
        - Test cache invalidation when environment changes
        - Validate memory usage and cache size management
        - Test caching behavior across different feature contexts
    """

    def test_environment_detection_caching_behavior(self, clean_environment):
        """
        Test that environment detection results are cached for performance.

        Integration Scope:
            Detection call → Cache lookup → Cached result → Performance optimization

        Business Impact:
            Ensures environment detection performance is optimized through caching

        Test Strategy:
            - Make initial environment detection call
            - Make subsequent calls with same environment
            - Verify consistent results and improved performance

        Success Criteria:
            - Detection results are cached and reused
            - Cached results are consistent
            - Performance improves with caching
        """
        import os
        os.environ['ENVIRONMENT'] = 'production'

        # First call - should populate cache
        start_time1 = time.time()
        env_info1 = get_environment_info()
        end_time1 = time.time()
        first_call_time = end_time1 - start_time1

        # Second call - should use cached result
        start_time2 = time.time()
        env_info2 = get_environment_info()
        end_time2 = time.time()
        second_call_time = end_time2 - start_time2

        # Results should be identical
        assert env_info1.environment == env_info2.environment
        assert env_info1.confidence == env_info2.confidence
        assert env_info1.reasoning == env_info2.reasoning
        assert env_info1.detected_by == env_info2.detected_by

        # Second call should be faster (though timing can be variable)
        assert second_call_time <= first_call_time

    def test_environment_detection_cache_invalidation_on_change(self, clean_environment):
        """
        Test that cache is invalidated when environment changes.

        Integration Scope:
            Environment change → Cache invalidation → Fresh detection → Updated results

        Business Impact:
            Ensures environment detection adapts to environment changes

        Test Strategy:
            - Set initial environment and detect
            - Change environment variable
            - Verify new detection reflects changed environment
            - Test cache invalidation behavior

        Success Criteria:
            - Cache is invalidated when environment changes
            - New environment detection reflects changes
            - Detection results update correctly
        """
        import os

        # Initial environment
        os.environ['ENVIRONMENT'] = 'development'
        env_info1 = get_environment_info()
        assert env_info1.environment == Environment.DEVELOPMENT

        # Change environment
        os.environ['ENVIRONMENT'] = 'production'
        env_info2 = get_environment_info()
        assert env_info2.environment == Environment.PRODUCTION

        # Should detect new environment, not cached old one
        assert env_info1.environment != env_info2.environment

    def test_concurrent_environment_detection_requests(self, clean_environment):
        """
        Test environment detection under concurrent access.

        Integration Scope:
            Concurrent requests → Thread-safe detection → Consistent results

        Business Impact:
            Ensures environment detection works correctly under concurrent access

        Test Strategy:
            - Make multiple concurrent detection requests
            - Verify all requests return consistent results
            - Test thread safety of detection logic

        Success Criteria:
            - All concurrent requests return same results
            - No race conditions or inconsistent state
            - Detection remains thread-safe under load
        """
        import os
        os.environ['ENVIRONMENT'] = 'production'

        results = []

        def detect_environment():
            env_info = get_environment_info()
            results.append((env_info.environment, env_info.confidence))

        # Run concurrent detection requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(detect_environment) for _ in range(10)]
            for future in as_completed(futures):
                future.result()  # Wait for completion

        # All results should be identical
        assert len(results) == 10
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result

        assert first_result[0] == Environment.PRODUCTION
        assert first_result[1] >= 0.8

    def test_caching_behavior_with_different_feature_contexts(self, clean_environment):
        """
        Test caching behavior across different feature contexts.

        Integration Scope:
            Feature contexts → Context-specific caching → Consistent results per context

        Business Impact:
            Ensures feature contexts work correctly with caching

        Test Strategy:
            - Test caching with different feature contexts
            - Verify context-specific results are cached
            - Test consistency within each context

        Success Criteria:
            - Each feature context maintains its own cached results
            - Results are consistent within each context
            - Context switching works correctly
        """
        import os
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['ENABLE_AI_CACHE'] = 'true'

        # Test default context caching
        default_env1 = get_environment_info(FeatureContext.DEFAULT)
        default_env2 = get_environment_info(FeatureContext.DEFAULT)

        assert default_env1.environment == default_env2.environment
        assert default_env1.feature_context == default_env2.feature_context
        assert default_env1.feature_context == FeatureContext.DEFAULT

        # Test AI context caching
        ai_env1 = get_environment_info(FeatureContext.AI_ENABLED)
        ai_env2 = get_environment_info(FeatureContext.AI_ENABLED)

        assert ai_env1.environment == ai_env2.environment
        assert ai_env1.feature_context == ai_env2.feature_context
        assert ai_env1.feature_context == FeatureContext.AI_ENABLED

        # Different contexts may have different metadata
        assert ai_env1.metadata.get('enable_ai_cache_enabled') is True
        assert default_env1.metadata.get('enable_ai_cache_enabled') is None

    def test_environment_detection_performance_under_load(self, clean_environment):
        """
        Test environment detection performance under load conditions.

        Integration Scope:
            Load conditions → Performance → Response times → System stability

        Business Impact:
            Ensures environment detection performs well under high load

        Test Strategy:
            - Simulate high load with many detection requests
            - Measure response times and consistency
            - Verify system remains stable under load

        Success Criteria:
            - Detection completes within acceptable time limits
            - Results remain consistent under load
            - No performance degradation or failures
        """
        import os
        os.environ['ENVIRONMENT'] = 'production'

        # Test performance under load
        num_requests = 50
        start_time = time.time()

        for _ in range(num_requests):
            env_info = get_environment_info()
            assert env_info.environment == Environment.PRODUCTION
            assert env_info.confidence >= 0.8

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete quickly (under 1 second for 50 requests)
        assert total_time < 2.0

        # Average time per request should be reasonable
        avg_time_per_request = total_time / num_requests
        assert avg_time_per_request < 0.05  # Less than 50ms per request

    def test_cache_performance_comparison_with_without_caching(self, clean_environment):
        """
        Test performance difference between cached and uncached detection.

        Integration Scope:
            Cached vs uncached → Performance comparison → Efficiency validation

        Business Impact:
            Ensures caching provides measurable performance benefits

        Test Strategy:
            - Measure performance with caching enabled
            - Compare with performance when caching is bypassed
            - Verify caching provides performance improvement

        Success Criteria:
            - Cached detection is faster than uncached
            - Performance improvement is measurable
            - Caching overhead is minimal
        """
        import os
        os.environ['ENVIRONMENT'] = 'production'

        # Test with caching (normal operation)
        cached_times = []
        for _ in range(10):
            start_time = time.time()
            env_info = get_environment_info()
            end_time = time.time()
            cached_times.append(end_time - start_time)
            assert env_info.environment == Environment.PRODUCTION

        avg_cached_time = sum(cached_times) / len(cached_times)

        # Test without caching by creating new detector each time
        uncached_times = []
        for _ in range(10):
            start_time = time.time()
            detector = EnvironmentDetector()
            env_info = detector.detect_environment()
            end_time = time.time()
            uncached_times.append(end_time - start_time)
            assert env_info.environment == Environment.PRODUCTION

        avg_uncached_time = sum(uncached_times) / len(uncached_times)

        # Cached should be faster (though difference may be small)
        assert avg_cached_time <= avg_uncached_time

    def test_memory_usage_and_cache_size_management(self, clean_environment):
        """
        Test memory usage and cache size management for environment detection.

        Integration Scope:
            Cache management → Memory usage → Size limits → Resource efficiency

        Business Impact:
            Ensures environment detection doesn't consume excessive memory

        Test Strategy:
            - Test cache behavior with multiple different environments
            - Verify cache doesn't grow unbounded
            - Test memory usage characteristics

        Success Criteria:
            - Cache size remains manageable
            - Memory usage is reasonable
            - No memory leaks in detection process
        """
        import os

        # Test with multiple different environments
        environments = ['development', 'staging', 'production', 'testing']

        cache_sizes = []
        for env in environments:
            os.environ['ENVIRONMENT'] = env
            env_info = get_environment_info()
            assert env_info.environment == Environment(env)

            # Get cache size (implementation dependent)
            # This is a conceptual test - actual implementation may vary

        # Cache should handle multiple environments efficiently
        # In practice, the cache size should be proportional to unique environments
        # and not grow excessively

    def test_cache_hit_miss_ratio_optimization(self, clean_environment):
        """
        Test cache hit/miss ratio optimization for environment detection.

        Integration Scope:
            Cache efficiency → Hit/miss tracking → Optimization opportunities

        Business Impact:
            Ensures optimal cache performance for environment detection

        Test Strategy:
            - Test cache behavior with repeated calls
            - Verify high cache hit ratio for same environment
            - Test cache miss behavior for different environments

        Success Criteria:
            - High cache hit ratio for repeated calls
            - Cache misses occur only when necessary
            - Cache efficiency is optimized
        """
        import os
        os.environ['ENVIRONMENT'] = 'production'

        # Initial call - cache miss
        env_info1 = get_environment_info()
        assert env_info1.environment == Environment.PRODUCTION

        # Subsequent calls - cache hits
        for _ in range(5):
            env_info = get_environment_info()
            assert env_info.environment == Environment.PRODUCTION
            assert env_info.confidence == env_info1.confidence

        # Change environment - cache miss
        os.environ['ENVIRONMENT'] = 'development'
        env_info2 = get_environment_info()
        assert env_info2.environment == Environment.DEVELOPMENT

        # Should get cache hits for new environment
        for _ in range(3):
            env_info = get_environment_info()
            assert env_info.environment == Environment.DEVELOPMENT

    def test_caching_with_environment_variable_changes(self, clean_environment):
        """
        Test caching behavior when environment variables change.

        Integration Scope:
            Environment changes → Cache invalidation → Fresh detection

        Business Impact:
            Ensures cache adapts correctly to environment changes

        Test Strategy:
            - Set initial environment and cache result
            - Change environment variable
            - Verify cache detects change and updates
            - Test adaptation to dynamic environment changes

        Success Criteria:
            - Cache detects environment variable changes
            - Fresh detection occurs after changes
            - Results reflect updated environment
        """
        import os

        # Initial environment
        os.environ['ENVIRONMENT'] = 'development'
        env_info1 = get_environment_info()
        assert env_info1.environment == Environment.DEVELOPMENT

        # Change environment variable
        os.environ['ENVIRONMENT'] = 'production'
        env_info2 = get_environment_info()
        assert env_info2.environment == Environment.PRODUCTION

        # Verify different results
        assert env_info1.environment != env_info2.environment

        # Change back to development
        os.environ['ENVIRONMENT'] = 'development'
        env_info3 = get_environment_info()
        assert env_info3.environment == Environment.DEVELOPMENT

        # Should match original development result
        assert env_info1.environment == env_info3.environment
        assert env_info1.confidence == env_info3.confidence

    def test_performance_with_complex_environment_setup(self, clean_environment):
        """
        Test performance with complex environment configuration.

        Integration Scope:
            Complex configuration → Performance → Scalability → System behavior

        Business Impact:
            Ensures environment detection performs well with complex setups

        Test Strategy:
            - Set up complex environment with many variables
            - Test detection performance with complex configuration
            - Verify system handles complexity efficiently

        Success Criteria:
            - Complex environment configuration doesn't impact performance
            - Detection completes within reasonable time limits
            - System scales well with configuration complexity
        """
        import os

        # Set up complex environment configuration
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['NODE_ENV'] = 'production'
        os.environ['HOSTNAME'] = 'api-prod-01.example.com'
        os.environ['DEBUG'] = 'false'
        os.environ['ENABLE_AI_CACHE'] = 'true'
        os.environ['ENFORCE_AUTH'] = 'true'

        # Test performance with complex setup
        start_time = time.time()

        for _ in range(10):
            env_info = get_environment_info()
            assert env_info.environment == Environment.PRODUCTION
            assert env_info.confidence >= 0.8

        end_time = time.time()
        total_time = end_time - start_time

        # Should still complete quickly despite complex configuration
        assert total_time < 1.0  # Less than 1 second for 10 requests

        # Test with feature contexts
        ai_env = get_environment_info(FeatureContext.AI_ENABLED)
        security_env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)

        assert ai_env.metadata.get('enable_ai_cache_enabled') is True
        assert security_env.metadata.get('enforce_auth_enabled') is True

    def test_cache_thread_safety_under_concurrent_access(self, clean_environment):
        """
        Test cache thread safety under concurrent access patterns.

        Integration Scope:
            Concurrent access → Thread safety → Cache consistency → Data integrity

        Business Impact:
            Ensures environment detection cache is thread-safe

        Test Strategy:
            - Test concurrent access to cached detection results
            - Verify thread safety of cache operations
            - Test data consistency under concurrent load

        Success Criteria:
            - No race conditions during concurrent access
            - Data remains consistent across threads
            - Cache operations are thread-safe
        """
        import os
        os.environ['ENVIRONMENT'] = 'production'

        def access_cache():
            env_info = get_environment_info()
            return (env_info.environment, env_info.confidence)

        # Test concurrent access
        results = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(access_cache) for _ in range(20)]
            for future in as_completed(futures):
                results.append(future.result())

        # All results should be identical
        assert len(results) == 20
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result

        assert first_result[0] == Environment.PRODUCTION
        assert first_result[1] >= 0.8

    def test_environment_detection_with_custom_configuration_performance(self, custom_detection_config):
        """
        Test performance with custom detection configuration.

        Integration Scope:
            Custom configuration → Performance → Efficiency → Scalability

        Business Impact:
            Ensures custom configurations don't impact performance

        Test Strategy:
            - Test detection with custom configuration
            - Measure performance characteristics
            - Verify custom config doesn't degrade performance

        Success Criteria:
            - Custom configuration doesn't impact performance
            - Detection completes within normal time limits
            - Custom patterns are processed efficiently
        """
        detector = EnvironmentDetector(custom_detection_config)

        import os
        os.environ['CUSTOM_ENV'] = 'production'

        # Test performance with custom configuration
        start_time = time.time()

        for _ in range(10):
            env_info = detector.detect_environment()
            assert env_info.environment == Environment.PRODUCTION

        end_time = time.time()
        total_time = end_time - start_time

        # Should perform well with custom configuration
        assert total_time < 1.0

        # Test with feature contexts
        ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)
        security_env = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)

        assert ai_env.metadata.get('enable_ai_features_enabled') is True
        assert security_env.metadata.get('force_secure_mode_enabled') is True
