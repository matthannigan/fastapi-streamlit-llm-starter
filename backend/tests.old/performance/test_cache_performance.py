"""
Performance tests for cache implementations.

These tests measure actual performance characteristics and validate that
cache implementations meet performance thresholds. Tests are marked as 'slow'
and require the --run-slow flag to execute.
"""

import pytest

from app.infrastructure.cache import (
    CachePerformanceBenchmark,
    InMemoryCache,
)


@pytest.mark.slow
class TestCachePerformance:
    """Test actual cache performance characteristics."""
    
    @pytest.fixture
    def benchmark(self):
        """Create a benchmark instance for performance testing."""
        return CachePerformanceBenchmark()
    
    @pytest.fixture
    def memory_cache(self):
        """Create an InMemoryCache for performance testing."""
        return InMemoryCache(default_ttl=3600, max_size=1000)
    
    @pytest.mark.asyncio
    async def test_memory_cache_performance_thresholds(self, benchmark, memory_cache):
        """Test that InMemoryCache meets performance thresholds."""
        result = await benchmark.benchmark_basic_operations(memory_cache, iterations=100)
        
        # Verify performance thresholds
        assert result.avg_duration_ms < 50.0, f"Average duration {result.avg_duration_ms}ms exceeds 50ms threshold"
        assert result.p95_duration_ms < 100.0, f"P95 duration {result.p95_duration_ms}ms exceeds 100ms threshold"
        assert result.operations_per_second > 20, f"Throughput {result.operations_per_second} ops/sec below 20 ops/sec threshold"
        assert result.success_rate >= 0.99, f"Success rate {result.success_rate} below 99% threshold"
        
        # Memory should be efficient
        assert result.memory_usage_mb < 100.0, f"Memory usage {result.memory_usage_mb}MB exceeds 100MB threshold"
    
    @pytest.mark.asyncio
    async def test_memory_cache_memory_performance(self, benchmark, memory_cache):
        """Test memory cache specific performance characteristics."""
        result = await benchmark.benchmark_memory_cache_performance(memory_cache, iterations=200)
        
        # Memory cache should be very fast
        assert result.avg_duration_ms < 5.0, f"Memory cache average duration {result.avg_duration_ms}ms exceeds 5ms threshold"
        assert result.operations_per_second > 100, f"Memory cache throughput {result.operations_per_second} ops/sec below 100 ops/sec threshold"
        
        # Should have good hit rates after warmup
        memory_hit_rate = result.metadata.get("memory_hit_rate", 0)
        assert memory_hit_rate > 50.0, f"Memory hit rate {memory_hit_rate}% below 50% threshold"
    
    @pytest.mark.asyncio
    async def test_comprehensive_benchmark_suite_performance(self, benchmark, memory_cache):
        """Test comprehensive benchmark suite meets performance requirements."""
        suite = await benchmark.run_comprehensive_benchmark_suite(memory_cache, include_compression=False)
        
        # Suite should complete successfully
        assert suite.pass_rate >= 0.9, f"Benchmark suite pass rate {suite.pass_rate} below 90%"
        assert suite.performance_grade in ["Excellent", "Good", "Acceptable"], f"Performance grade {suite.performance_grade} is poor"
        
        # All individual benchmarks should meet basic thresholds
        for result in suite.results:
            assert result.success_rate >= 0.95, f"{result.operation_type} success rate {result.success_rate} below 95%"
            assert result.avg_duration_ms < 100.0, f"{result.operation_type} average duration {result.avg_duration_ms}ms exceeds 100ms"
    
    @pytest.mark.asyncio
    async def test_benchmark_overhead_validation(self, benchmark, memory_cache):
        """Test that benchmarking itself has minimal overhead."""
        # Run a small benchmark
        start_time = __import__("time").time()
        result = await benchmark.benchmark_basic_operations(memory_cache, iterations=10)
        benchmark_duration = __import__("time").time() - start_time
        
        # Benchmark overhead should be reasonable
        # Total benchmark time should not be more than 10x the actual operation time
        expected_max_duration = result.duration_ms / 1000.0 * 10  # 10x the measured operation time
        assert benchmark_duration < expected_max_duration, f"Benchmark overhead too high: {benchmark_duration}s vs expected max {expected_max_duration}s"
        
        # Benchmark should not use excessive memory
        assert result.memory_usage_mb < 50.0, f"Benchmark memory usage {result.memory_usage_mb}MB too high"
    
    @pytest.mark.asyncio 
    async def test_performance_regression_detection_accuracy(self, benchmark, memory_cache):
        """Test that performance regression detection works accurately."""
        # Create a baseline
        baseline_result = await benchmark.benchmark_basic_operations(memory_cache, iterations=50)
        
        # Create a simulated slower cache (by adding artificial delay)
        class SlowCache:
            def __init__(self, base_cache, delay_factor=2.0):
                self.base_cache = base_cache
                self.delay_factor = delay_factor
            
            async def get(self, key):
                await __import__("asyncio").sleep(0.001 * self.delay_factor)  # Add delay
                return await self.base_cache.get(key)
            
            async def set(self, key, value, ttl=None):
                await __import__("asyncio").sleep(0.001 * self.delay_factor)  # Add delay
                return await self.base_cache.set(key, value, ttl)
            
            async def delete(self, key):
                await __import__("asyncio").sleep(0.001 * self.delay_factor)  # Add delay
                return await self.base_cache.delete(key)
            
            async def exists(self, key):
                await __import__("asyncio").sleep(0.001 * self.delay_factor)  # Add delay
                return await self.base_cache.exists(key)
            
            async def clear(self):
                await __import__("asyncio").sleep(0.001 * self.delay_factor)  # Add delay
                return await self.base_cache.clear()
        
        slow_cache = SlowCache(memory_cache, delay_factor=3.0)
        
        # Test comparison
        comparison = await benchmark.compare_before_after_refactoring(
            memory_cache, slow_cache, test_iterations=20
        )
        
        # Should detect regression
        assert comparison.regression_detected, "Failed to detect performance regression"
        assert comparison.performance_change_percent > 10, f"Should detect significant regression, got {comparison.performance_change_percent}%"
        assert len(comparison.degradation_areas) > 0, "Should identify degradation areas"
        assert "regression" in " ".join(comparison.recommendations).lower(), "Should recommend addressing regression"
    
    def test_performance_thresholds_realistic(self):
        """Test that performance thresholds are realistic and achievable."""
        from app.infrastructure.cache.benchmarks import CachePerformanceThresholds
        
        thresholds = CachePerformanceThresholds()
        
        # Basic operations should be achievable
        assert thresholds.BASIC_OPERATIONS_AVG_MS <= 50.0, "Basic operations threshold too strict"
        assert thresholds.BASIC_OPERATIONS_AVG_MS >= 1.0, "Basic operations threshold too lenient"
        
        # Memory cache should be faster than basic operations
        assert thresholds.MEMORY_CACHE_AVG_MS < thresholds.BASIC_OPERATIONS_AVG_MS, "Memory cache should be faster than basic operations"
        assert thresholds.MEMORY_CACHE_AVG_MS <= 5.0, "Memory cache threshold too strict"
        
        # Regression thresholds should be reasonable
        assert 5.0 <= thresholds.REGRESSION_WARNING_PERCENT <= 15.0, "Regression warning threshold should be 5-15%"
        assert 20.0 <= thresholds.REGRESSION_CRITICAL_PERCENT <= 50.0, "Regression critical threshold should be 20-50%"
    
    @pytest.mark.asyncio
    async def test_benchmark_scalability(self, benchmark, memory_cache):
        """Test benchmark performance with different iteration counts."""
        iteration_counts = [10, 50, 100]
        results = []
        
        for iterations in iteration_counts:
            result = await benchmark.benchmark_basic_operations(memory_cache, iterations=iterations)
            results.append((iterations, result))
        
        # Benchmark timing should scale roughly linearly with iterations
        for i in range(1, len(results)):
            prev_iterations, prev_result = results[i-1]
            curr_iterations, curr_result = results[i]
            
            # More iterations should take proportionally more time (within reason)
            time_ratio = curr_result.duration_ms / prev_result.duration_ms
            iteration_ratio = curr_iterations / prev_iterations
            
            # Allow for some overhead, but should be roughly proportional
            assert 0.8 * iteration_ratio <= time_ratio <= 2.0 * iteration_ratio, \
                f"Benchmark timing not scaling linearly: {time_ratio} vs expected ~{iteration_ratio}"
    
    @pytest.mark.asyncio
    async def test_data_generator_performance(self):
        """Test that test data generation is efficient."""
        from app.infrastructure.cache.benchmarks import CacheBenchmarkDataGenerator
        
        generator = CacheBenchmarkDataGenerator()
        
        # Test data generation timing
        start_time = __import__("time").time()
        
        basic_data = generator.generate_basic_operations_data(1000)
        memory_data = generator.generate_memory_pressure_data(10.0)  # 10MB
        concurrent_data = generator.generate_concurrent_access_patterns(10)
        compression_data = generator.generate_compression_test_data()
        
        generation_time = __import__("time").time() - start_time
        
        # Data generation should be fast
        assert generation_time < 5.0, f"Test data generation took {generation_time}s, should be under 5s"
        
        # Verify data quality
        assert len(basic_data) == 1000
        assert len(memory_data) > 0
        assert len(concurrent_data) == 10
        assert len(compression_data) >= 4
