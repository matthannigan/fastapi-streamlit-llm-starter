"""
Comprehensive tests for cache performance benchmarking infrastructure.

This test suite validates the cache benchmarking system including timing accuracy,
memory measurement, regression detection, and comprehensive reporting capabilities.
The tests ensure the benchmarking infrastructure meets the >95% coverage requirement
for infrastructure components.
"""

import asyncio
import json
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.cache.benchmarks import (
    BenchmarkResult,
    BenchmarkSuite,
    CacheBenchmarkDataGenerator,
    CachePerformanceBenchmark,
    CachePerformanceThresholds,
    ComparisonResult,
    PerformanceRegressionDetector,
)
from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.memory import InMemoryCache


class MockCache(CacheInterface):
    """Mock cache implementation for testing."""
    
    def __init__(self, delay_ms: float = 1.0, failure_rate: float = 0.0):
        self.delay_ms = delay_ms
        self.failure_rate = failure_rate
        self.storage = {}
        self.operation_count = 0
        self._memory_cache = {}
        self.compression_threshold = 1000
        
    async def get(self, key: str):
        await self._simulate_delay()
        self._check_failure()
        return self.storage.get(key)
    
    async def set(self, key: str, value, ttl: int = None):
        await self._simulate_delay()
        self._check_failure()
        self.storage[key] = value
    
    async def delete(self, key: str):
        await self._simulate_delay()
        self._check_failure()
        self.storage.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        await self._simulate_delay()
        return key in self.storage
    
    async def clear(self):
        await self._simulate_delay()
        self.storage.clear()
    
    async def _simulate_delay(self):
        if self.delay_ms > 0:
            await asyncio.sleep(self.delay_ms / 1000.0)
        self.operation_count += 1
    
    def _check_failure(self):
        import random
        if random.random() < self.failure_rate:
            raise Exception("Simulated cache failure")


class TestBenchmarkDataStructures:
    """Test the benchmark data structures and their methods."""
    
    def test_benchmark_result_creation(self):
        """Test BenchmarkResult creation and methods."""
        result = BenchmarkResult(
            operation_type="test_operation",
            duration_ms=100.0,
            memory_peak_mb=10.0,
            iterations=50,
            avg_duration_ms=25.0,
            min_duration_ms=10.0,
            max_duration_ms=40.0,
            p95_duration_ms=35.0,
            p99_duration_ms=38.0,
            std_dev_ms=5.0,
            operations_per_second=40.0,
            success_rate=0.98,
            memory_usage_mb=5.0
        )
        
        assert result.operation_type == "test_operation"
        assert result.avg_duration_ms == 25.0
        assert result.success_rate == 0.98
        
        # Test threshold checking
        assert result.meets_threshold(50.0) is True
        assert result.meets_threshold(20.0) is False
        
        # Test performance grading
        assert result.performance_grade() in ["Excellent", "Good", "Acceptable", "Poor", "Critical"]
        
        # Test serialization
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["operation_type"] == "test_operation"
    
    def test_comparison_result_creation(self):
        """Test ComparisonResult creation and methods."""
        original_result = BenchmarkResult(
            operation_type="test",
            duration_ms=100.0,
            memory_peak_mb=10.0,
            iterations=50,
            avg_duration_ms=30.0,
            min_duration_ms=20.0,
            max_duration_ms=40.0,
            p95_duration_ms=35.0,
            p99_duration_ms=38.0,
            std_dev_ms=5.0,
            operations_per_second=33.0,
            success_rate=0.95,
            memory_usage_mb=8.0
        )
        
        new_result = BenchmarkResult(
            operation_type="test",
            duration_ms=90.0,
            memory_peak_mb=8.0,
            iterations=50,
            avg_duration_ms=25.0,
            min_duration_ms=18.0,
            max_duration_ms=35.0,
            p95_duration_ms=30.0,
            p99_duration_ms=33.0,
            std_dev_ms=4.0,
            operations_per_second=40.0,
            success_rate=0.98,
            memory_usage_mb=6.0
        )
        
        comparison = ComparisonResult(
            original_cache_results=original_result,
            new_cache_results=new_result,
            performance_change_percent=-16.7,  # 25/30 = 83.3%, so -16.7% improvement
            memory_change_percent=-25.0,       # 6/8 = 75%, so -25% improvement
            operations_per_second_change=21.2, # 40/33 = 121.2%, so +21.2% improvement
            regression_detected=False,
            improvement_areas=["Performance improved", "Memory improved"],
            degradation_areas=[],
            recommendations=["Monitor in production"]
        )
        
        assert comparison.regression_detected is False
        assert len(comparison.improvement_areas) == 2
        assert len(comparison.degradation_areas) == 0
        
        # Test summary generation
        summary = comparison.summary()
        assert "improved" in summary
        assert "16.7%" in summary  # Summary uses absolute value, not negative sign
        
        # Test serialization
        comparison_dict = comparison.to_dict()
        assert isinstance(comparison_dict, dict)
        assert comparison_dict["regression_detected"] is False
    
    def test_benchmark_suite_creation(self):
        """Test BenchmarkSuite creation and methods."""
        result1 = BenchmarkResult(
            operation_type="basic_operations",
            duration_ms=100.0,
            memory_peak_mb=10.0,
            iterations=50,
            avg_duration_ms=20.0,
            min_duration_ms=15.0,
            max_duration_ms=25.0,
            p95_duration_ms=24.0,
            p99_duration_ms=25.0,
            std_dev_ms=2.0,
            operations_per_second=50.0,
            success_rate=1.0,
            memory_usage_mb=5.0
        )
        
        result2 = BenchmarkResult(
            operation_type="memory_cache",
            duration_ms=50.0,
            memory_peak_mb=5.0,
            iterations=100,
            avg_duration_ms=2.0,
            min_duration_ms=1.0,
            max_duration_ms=5.0,
            p95_duration_ms=4.0,
            p99_duration_ms=5.0,
            std_dev_ms=1.0,
            operations_per_second=500.0,
            success_rate=1.0,
            memory_usage_mb=2.0
        )
        
        suite = BenchmarkSuite(
            name="Test Suite",
            results=[result1, result2],
            total_duration_ms=150.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            performance_grade="Excellent",
            memory_efficiency_grade="Good"
        )
        
        assert suite.name == "Test Suite"
        assert len(suite.results) == 2
        assert suite.pass_rate == 1.0
        
        # Test getting specific operation result
        basic_result = suite.get_operation_result("basic_operations")
        assert basic_result is not None
        assert basic_result.operation_type == "basic_operations"
        
        nonexistent_result = suite.get_operation_result("nonexistent")
        assert nonexistent_result is None
        
        # Test overall score calculation
        score = suite.calculate_overall_score()
        assert 0 <= score <= 100
        
        # Test JSON serialization
        json_str = suite.to_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["name"] == "Test Suite"


class TestCacheBenchmarkDataGenerator:
    """Test the benchmark data generator functionality."""
    
    def test_basic_operations_data_generation(self):
        """Test generation of basic operations test data."""
        generator = CacheBenchmarkDataGenerator()
        
        test_data = generator.generate_basic_operations_data(50)
        
        assert len(test_data) == 50
        
        for data in test_data:
            assert "key" in data
            assert "text" in data
            assert "operation" in data
            assert "options" in data
            assert "expected_size_bytes" in data
            assert "cache_ttl" in data
            
            assert data["operation"] in generator.operation_types
            assert isinstance(data["expected_size_bytes"], int)
            assert data["expected_size_bytes"] > 0
            assert 300 <= data["cache_ttl"] <= 3600
    
    def test_memory_pressure_data_generation(self):
        """Test generation of memory pressure test data."""
        generator = CacheBenchmarkDataGenerator()
        
        test_data = generator.generate_memory_pressure_data(1.0)  # 1MB
        
        assert len(test_data) > 0
        
        total_size = sum(data["size_bytes"] for data in test_data)
        target_size = 1.0 * 1024 * 1024  # 1MB in bytes
        
        # Should be approximately 1MB (within 20% tolerance)
        assert 0.8 * target_size <= total_size <= 1.2 * target_size
        
        for data in test_data:
            assert "key" in data
            assert "text" in data
            assert "operation" in data
            assert "size_bytes" in data
            assert "priority" in data
            
            assert data["priority"] in ["high", "medium", "low"]
    
    def test_concurrent_access_patterns_generation(self):
        """Test generation of concurrent access patterns."""
        generator = CacheBenchmarkDataGenerator()
        
        patterns = generator.generate_concurrent_access_patterns(5)
        
        assert len(patterns) == 5
        
        for pattern in patterns:
            assert "pattern_id" in pattern
            assert "operations" in pattern
            assert "concurrency_level" in pattern
            assert "duration_seconds" in pattern
            
            assert isinstance(pattern["operations"], list)
            assert len(pattern["operations"]) >= 50
            assert 5 <= pattern["concurrency_level"] <= 20
            assert 10 <= pattern["duration_seconds"] <= 60
            
            for operation in pattern["operations"][:5]:  # Check first 5
                assert "type" in operation
                assert "key" in operation
                assert "delay_ms" in operation
                assert operation["type"] in ["get", "set", "delete"]
    
    def test_compression_test_data_generation(self):
        """Test generation of compression test data."""
        generator = CacheBenchmarkDataGenerator()
        
        test_data = generator.generate_compression_test_data()
        
        assert len(test_data) >= 4  # Should have at least 4 different test types
        
        types_found = set()
        for data in test_data:
            assert "type" in data
            assert "text" in data
            assert "expected_compression_ratio" in data
            assert "description" in data
            
            types_found.add(data["type"])
            assert isinstance(data["text"], str)
            assert len(data["text"]) > 0
            assert 0.0 < data["expected_compression_ratio"] <= 1.0
        
        # Should have different compression types
        expected_types = {"highly_compressible", "moderately_compressible", "poorly_compressible", "structured_data"}
        assert types_found == expected_types


class TestPerformanceRegressionDetector:
    """Test the performance regression detection functionality."""
    
    def test_timing_regression_detection(self):
        """Test detection of timing-related regressions."""
        detector = PerformanceRegressionDetector(warning_threshold=10.0, critical_threshold=25.0)
        
        # Create baseline result
        old_result = BenchmarkResult(
            operation_type="test",
            duration_ms=100.0,
            memory_peak_mb=10.0,
            iterations=50,
            avg_duration_ms=20.0,
            min_duration_ms=15.0,
            max_duration_ms=25.0,
            p95_duration_ms=24.0,
            p99_duration_ms=25.0,
            std_dev_ms=2.0,
            operations_per_second=50.0,
            success_rate=1.0,
            memory_usage_mb=5.0
        )
        
        # Create degraded result (30% slower)
        new_result = BenchmarkResult(
            operation_type="test",
            duration_ms=130.0,
            memory_peak_mb=10.0,
            iterations=50,
            avg_duration_ms=26.0,  # 30% slower
            min_duration_ms=20.0,
            max_duration_ms=32.0,
            p95_duration_ms=31.0,  # 29% slower
            p99_duration_ms=32.0,
            std_dev_ms=3.0,
            operations_per_second=38.5,  # 23% slower
            success_rate=1.0,
            memory_usage_mb=5.0
        )
        
        regressions = detector.detect_timing_regressions(old_result, new_result)
        
        assert len(regressions) >= 2  # Should detect avg duration and throughput regressions
        
        # Check for average duration regression
        avg_regression = next((r for r in regressions if r["metric"] == "average_duration"), None)
        assert avg_regression is not None
        assert avg_regression["severity"] == "critical"  # 30% > 25% threshold
        assert avg_regression["change_percent"] == 30.0
        
        # Check for throughput regression
        throughput_regression = next((r for r in regressions if r["metric"] == "operations_per_second"), None)
        assert throughput_regression is not None
        assert throughput_regression["change_percent"] < -10.0  # Negative because it's a decrease
    
    def test_memory_regression_detection(self):
        """Test detection of memory-related regressions."""
        detector = PerformanceRegressionDetector(warning_threshold=15.0, critical_threshold=30.0)
        
        # Create baseline result
        old_result = BenchmarkResult(
            operation_type="test",
            duration_ms=100.0,
            memory_peak_mb=10.0,
            iterations=50,
            avg_duration_ms=20.0,
            min_duration_ms=15.0,
            max_duration_ms=25.0,
            p95_duration_ms=24.0,
            p99_duration_ms=25.0,
            std_dev_ms=2.0,
            operations_per_second=50.0,
            success_rate=1.0,
            memory_usage_mb=8.0
        )
        
        # Create result with memory regression (50% more memory)
        new_result = BenchmarkResult(
            operation_type="test",
            duration_ms=100.0,
            memory_peak_mb=15.0,  # 50% increase
            iterations=50,
            avg_duration_ms=20.0,
            min_duration_ms=15.0,
            max_duration_ms=25.0,
            p95_duration_ms=24.0,
            p99_duration_ms=25.0,
            std_dev_ms=2.0,
            operations_per_second=50.0,
            success_rate=1.0,
            memory_usage_mb=12.0  # 50% increase
        )
        
        regressions = detector.detect_memory_regressions(old_result, new_result)
        
        assert len(regressions) >= 1  # Should detect memory usage regression
        
        memory_regression = regressions[0]
        assert memory_regression["type"] == "memory_regression"
        assert memory_regression["severity"] == "critical"  # 50% > 30% threshold
        assert memory_regression["change_percent"] == 50.0
    
    def test_cache_hit_rate_validation(self):
        """Test cache hit rate validation."""
        detector = PerformanceRegressionDetector()
        
        # Create baseline result with good hit rate
        old_result = BenchmarkResult(
            operation_type="test",
            duration_ms=100.0,
            memory_peak_mb=10.0,
            iterations=50,
            avg_duration_ms=20.0,
            min_duration_ms=15.0,
            max_duration_ms=25.0,
            p95_duration_ms=24.0,
            p99_duration_ms=25.0,
            std_dev_ms=2.0,
            operations_per_second=50.0,
            success_rate=1.0,
            memory_usage_mb=8.0,
            cache_hit_rate=85.0
        )
        
        # Test with degraded hit rate
        new_result_bad = BenchmarkResult(
            operation_type="test",
            duration_ms=100.0,
            memory_peak_mb=10.0,
            iterations=50,
            avg_duration_ms=20.0,
            min_duration_ms=15.0,
            max_duration_ms=25.0,
            p95_duration_ms=24.0,
            p99_duration_ms=25.0,
            std_dev_ms=2.0,
            operations_per_second=50.0,
            success_rate=1.0,
            memory_usage_mb=8.0,
            cache_hit_rate=65.0  # 20% decrease
        )
        
        validation = detector.validate_cache_hit_rates(old_result, new_result_bad)
        assert validation["status"] == "regression_detected"
        assert validation["severity"] == "critical"  # >15% decrease
        
        # Test with maintained hit rate
        new_result_good = BenchmarkResult(
            operation_type="test",
            duration_ms=100.0,
            memory_peak_mb=10.0,
            iterations=50,
            avg_duration_ms=20.0,
            min_duration_ms=15.0,
            max_duration_ms=25.0,
            p95_duration_ms=24.0,
            p99_duration_ms=25.0,
            std_dev_ms=2.0,
            operations_per_second=50.0,
            success_rate=1.0,
            memory_usage_mb=8.0,
            cache_hit_rate=87.0  # 2% increase
        )
        
        validation = detector.validate_cache_hit_rates(old_result, new_result_good)
        assert validation["status"] == "passed"
        assert validation["change_percent"] == 2.0


class TestCachePerformanceBenchmark:
    """Test the main cache performance benchmark functionality."""
    
    @pytest.fixture
    def benchmark(self):
        """Create a benchmark instance for testing."""
        return CachePerformanceBenchmark()
    
    @pytest.fixture
    def fast_cache(self):
        """Create a fast mock cache for testing."""
        return MockCache(delay_ms=1.0, failure_rate=0.0)
    
    @pytest.fixture
    def slow_cache(self):
        """Create a slow mock cache for testing."""
        return MockCache(delay_ms=10.0, failure_rate=0.0)
    
    @pytest.fixture
    def unreliable_cache(self):
        """Create an unreliable mock cache for testing."""
        return MockCache(delay_ms=2.0, failure_rate=0.1)
    
    @pytest.mark.asyncio
    async def test_basic_operations_benchmark(self, benchmark, fast_cache):
        """Test basic operations benchmarking."""
        result = await benchmark.benchmark_basic_operations(fast_cache, iterations=10)
        
        assert result.operation_type == "basic_operations"
        assert result.iterations == 10
        assert result.avg_duration_ms > 0
        assert result.operations_per_second > 0
        assert result.success_rate > 0
        assert result.memory_usage_mb >= 0
        
        # Should be fast
        assert result.avg_duration_ms < 100  # Less than 100ms average
        assert result.success_rate >= 0.9   # At least 90% success rate
        
        # Check metadata
        assert "total_operations" in result.metadata
        assert "successful_operations" in result.metadata
        assert "warmup_iterations" in result.metadata
    
    @pytest.mark.asyncio
    async def test_memory_cache_performance_benchmark(self, benchmark, fast_cache):
        """Test memory cache performance benchmarking."""
        result = await benchmark.benchmark_memory_cache_performance(fast_cache, iterations=20)
        
        assert result.operation_type == "memory_cache_performance"
        assert result.avg_duration_ms > 0
        assert result.operations_per_second > 0
        assert result.success_rate > 0
        
        # Check metadata for memory cache specific metrics
        assert "memory_hits" in result.metadata
        assert "redis_hits" in result.metadata
        assert "cache_misses" in result.metadata
        assert "memory_hit_rate" in result.metadata
        assert "has_memory_cache" in result.metadata
    
    @pytest.mark.asyncio
    async def test_compression_efficiency_benchmark(self, benchmark, fast_cache):
        """Test compression efficiency benchmarking."""
        result = await benchmark.benchmark_compression_efficiency(fast_cache, iterations=5)
        
        assert result.operation_type == "compression_efficiency"
        assert result.avg_duration_ms > 0
        assert result.operations_per_second > 0
        assert result.success_rate > 0
        assert result.compression_ratio is not None
        assert result.compression_savings_mb is not None
        
        # Check metadata for compression specific metrics
        assert "has_compression" in result.metadata
        assert "total_original_bytes" in result.metadata
        assert "total_compressed_bytes" in result.metadata
        assert "compression_test_types" in result.metadata
    
    @pytest.mark.asyncio
    async def test_before_after_comparison(self, benchmark, fast_cache, slow_cache):
        """Test before/after refactoring comparison."""
        comparison = await benchmark.compare_before_after_refactoring(
            slow_cache, fast_cache, test_iterations=10
        )
        
        assert isinstance(comparison, ComparisonResult)
        assert comparison.original_cache_results.operation_type == "basic_operations"
        assert comparison.new_cache_results.operation_type == "basic_operations"
        
        # Fast cache should be better than slow cache
        assert comparison.performance_change_percent < 0  # Negative = improvement
        assert len(comparison.recommendations) > 0
        
        # Should detect improvement
        assert len(comparison.improvement_areas) > 0 or not comparison.regression_detected
    
    @pytest.mark.asyncio
    async def test_comprehensive_benchmark_suite(self, benchmark, fast_cache):
        """Test comprehensive benchmark suite execution."""
        suite = await benchmark.run_comprehensive_benchmark_suite(fast_cache, include_compression=True)
        
        assert isinstance(suite, BenchmarkSuite)
        assert suite.name == "Comprehensive Cache Performance Benchmark"
        assert len(suite.results) >= 2  # At least basic ops and memory cache
        assert suite.pass_rate > 0
        assert suite.performance_grade in ["Excellent", "Good", "Acceptable", "Poor", "Critical"]
        assert suite.memory_efficiency_grade in ["Excellent", "Good", "Acceptable", "Poor", "Critical"]
        
        # Should have environment info
        assert "platform" in suite.environment_info
        assert "python_version" in suite.environment_info
    
    def test_performance_report_generation(self, benchmark):
        """Test performance report generation."""
        # Create mock suite
        result = BenchmarkResult(
            operation_type="basic_operations",
            duration_ms=100.0,
            memory_peak_mb=10.0,
            iterations=50,
            avg_duration_ms=20.0,
            min_duration_ms=15.0,
            max_duration_ms=25.0,
            p95_duration_ms=24.0,
            p99_duration_ms=25.0,
            std_dev_ms=2.0,
            operations_per_second=50.0,
            success_rate=1.0,
            memory_usage_mb=5.0,
            metadata={"total_operations": 50}
        )
        
        suite = BenchmarkSuite(
            name="Test Suite",
            results=[result],
            total_duration_ms=150.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            performance_grade="Good",
            memory_efficiency_grade="Excellent",
            environment_info={"platform": "Test Platform"}
        )
        
        report = benchmark.generate_performance_report(suite)
        
        assert isinstance(report, str)
        assert "CACHE PERFORMANCE BENCHMARK REPORT" in report
        assert "Test Suite" in report
        assert "BASIC_OPERATIONS" in report
        assert "Good" in report
        assert "Test Platform" in report
    
    def test_performance_trends_analysis(self, benchmark):
        """Test performance trends analysis."""
        # Create historical results
        historical_suites = []
        
        for i in range(3):
            result = BenchmarkResult(
                operation_type="basic_operations",
                duration_ms=100.0 + (i * 10),  # Getting slower
                memory_peak_mb=10.0,
                iterations=50,
                avg_duration_ms=20.0 + (i * 2),  # Getting slower
                min_duration_ms=15.0,
                max_duration_ms=25.0,
                p95_duration_ms=24.0,
                p99_duration_ms=25.0,
                std_dev_ms=2.0,
                operations_per_second=50.0 - (i * 5),  # Getting slower
                success_rate=1.0,
                memory_usage_mb=5.0 + i,  # Using more memory
                timestamp=f"2024-01-0{i+1}T12:00:00"
            )
            
            suite = BenchmarkSuite(
                name=f"Suite {i}",
                results=[result],
                total_duration_ms=150.0,
                pass_rate=1.0,
                failed_benchmarks=[],
                performance_grade="Good",
                memory_efficiency_grade="Good"
            )
            historical_suites.append(suite)
        
        trends = benchmark.analyze_performance_trends(historical_suites)
        
        assert "basic_operations" in trends
        trend = trends["basic_operations"]
        assert trend["trend_direction"] == "degrading"
        assert trend["duration_change_percent"] > 0  # Getting slower
        assert trend["sample_count"] == 3
    
    @pytest.mark.asyncio
    async def test_benchmark_with_failures(self, benchmark, unreliable_cache):
        """Test benchmarking with cache failures."""
        result = await benchmark.benchmark_basic_operations(unreliable_cache, iterations=20)
        
        assert result.operation_type == "basic_operations"
        assert result.success_rate < 1.0  # Should have some failures
        assert result.success_rate > 0.5  # But not total failure
        
        # Should still provide meaningful metrics
        assert result.avg_duration_ms > 0
        assert result.operations_per_second > 0
    
    def test_threshold_validation(self):
        """Test performance threshold validation."""
        thresholds = CachePerformanceThresholds()
        
        # Test all thresholds are reasonable
        assert thresholds.BASIC_OPERATIONS_AVG_MS > 0
        assert thresholds.BASIC_OPERATIONS_AVG_MS < 1000  # Less than 1 second
        assert thresholds.MEMORY_CACHE_AVG_MS < thresholds.BASIC_OPERATIONS_AVG_MS
        assert thresholds.REGRESSION_WARNING_PERCENT > 0
        assert thresholds.REGRESSION_CRITICAL_PERCENT > thresholds.REGRESSION_WARNING_PERCENT
    
    def test_environment_info_collection(self, benchmark):
        """Test environment information collection."""
        env_info = benchmark._collect_environment_info()
        
        assert "platform" in env_info
        assert "python_version" in env_info
        assert "processor" in env_info
        assert "cpu_count" in env_info
        assert "environment_variables" in env_info
        
        env_vars = env_info["environment_variables"]
        assert isinstance(env_vars, dict)
        # Should mask sensitive variables
        if "API_KEY" in env_vars and env_vars["API_KEY"] != "not_set":
            assert env_vars["API_KEY"] == "***MASKED***"


class TestBenchmarkIntegration:
    """Test integration between benchmarking components."""
    
    @pytest.mark.asyncio
    async def test_benchmark_with_real_memory_cache(self):
        """Test benchmarking with real InMemoryCache."""
        cache = InMemoryCache(default_ttl=3600, max_size=100)
        benchmark = CachePerformanceBenchmark()
        
        result = await benchmark.benchmark_basic_operations(cache, iterations=10)
        
        assert result.operation_type == "basic_operations"
        assert result.success_rate == 1.0  # InMemoryCache should be very reliable
        assert result.avg_duration_ms < 50   # Should be fast
        assert result.operations_per_second > 10
    
    @pytest.mark.asyncio
    async def test_benchmark_suite_with_real_cache(self):
        """Test full benchmark suite with real cache."""
        cache = InMemoryCache(default_ttl=3600, max_size=100)
        benchmark = CachePerformanceBenchmark()
        
        suite = await benchmark.run_comprehensive_benchmark_suite(cache, include_compression=False)
        
        assert len(suite.results) >= 2
        assert suite.pass_rate == 1.0  # All benchmarks should pass
        assert all(r.success_rate >= 0.9 for r in suite.results)
        
        # Generate report to ensure it works end-to-end
        report = benchmark.generate_performance_report(suite)
        assert len(report) > 100  # Should be a substantial report
    
    def test_data_generator_integration(self):
        """Test data generator produces valid data for benchmarks."""
        generator = CacheBenchmarkDataGenerator()
        
        # Test that generated data works with our mock cache
        basic_data = generator.generate_basic_operations_data(5)
        assert len(basic_data) == 5
        
        for data in basic_data:
            # Verify the data has all required fields
            assert all(key in data for key in ["key", "text", "operation", "options"])
            
            # Verify data types
            assert isinstance(data["key"], str)
            assert isinstance(data["text"], str)
            assert isinstance(data["operation"], str)
            assert isinstance(data["options"], dict)
    
    @pytest.mark.asyncio
    async def test_regression_detection_integration(self):
        """Test regression detection with real benchmark results."""
        fast_cache = MockCache(delay_ms=1.0)
        slow_cache = MockCache(delay_ms=20.0)  # 20x slower
        
        benchmark = CachePerformanceBenchmark()
        
        # Run benchmarks
        fast_result = await benchmark.benchmark_basic_operations(fast_cache, iterations=10)
        slow_result = await benchmark.benchmark_basic_operations(slow_cache, iterations=10)
        
        # Test regression detection
        detector = PerformanceRegressionDetector()
        regressions = detector.detect_timing_regressions(fast_result, slow_result)
        
        # Should detect significant performance regression
        assert len(regressions) > 0
        timing_regression = next((r for r in regressions if "duration" in r["metric"]), None)
        assert timing_regression is not None
        assert timing_regression["severity"] in ["warning", "critical"]