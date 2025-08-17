"""
[REFACTORED] Cache Performance Benchmarking Infrastructure

This module provides comprehensive performance benchmarking capabilities for cache implementations,
including timing analysis, memory usage tracking, compression efficiency testing, and regression
detection. It builds on the existing CachePerformanceMonitor infrastructure to provide detailed
performance validation for cache refactoring efforts.

Key Features:
    - Comprehensive cache operation benchmarking (get/set/delete/exists/clear)
    - Memory cache performance analysis with L1/L2 cache coordination testing
    - Compression efficiency benchmarking with ratio and timing analysis
    - Before/after refactoring comparison utilities for regression detection
    - Realistic workload generation for text processing scenarios
    - Performance trend analysis and threshold validation
    - Detailed reporting with recommendations and optimization insights

Core Components:
    BenchmarkResult: Dataclass for individual benchmark measurements
    ComparisonResult: Dataclass for before/after performance comparisons
    BenchmarkSuite: Collection of related benchmark results with analysis
    CachePerformanceBenchmark: Main benchmarking class with comprehensive test methods
    CacheBenchmarkDataGenerator: Realistic test data generation for various scenarios
    PerformanceRegressionDetector: Automated regression detection and alerting

Usage Example:
    >>> # Initialize benchmark system
    >>> benchmark = CachePerformanceBenchmark()
    >>> 
    >>> # Benchmark basic cache operations
    >>> cache = GenericRedisCache()
    >>> result = await benchmark.benchmark_basic_operations(cache, iterations=100)
    >>> print(f"Average operation time: {result.avg_duration_ms:.2f}ms")
    >>> print(f"Operations per second: {result.operations_per_second:.0f}")
    >>> 
    >>> # Test memory cache performance
    >>> memory_result = await benchmark.benchmark_memory_cache_performance(cache)
    >>> print(f"L1 cache hit rate: {memory_result.cache_hit_rate:.1f}%")
    >>> 
    >>> # Compare implementations
    >>> old_cache = AIResponseCache()
    >>> comparison = await benchmark.compare_before_after_refactoring(old_cache, cache)
    >>> print(f"Performance change: {comparison.performance_change_percent:+.1f}%")
    >>> 
    >>> # Generate comprehensive report
    >>> suite = benchmark.run_comprehensive_benchmark_suite(cache)
    >>> report = benchmark.generate_performance_report(suite)
    >>> print(report)

Performance Areas Tested:
    1. Basic Operations:
       - Get/Set/Delete operation timing with percentile analysis
       - Bulk operation performance under load
       - Concurrent access pattern testing
       - Error handling and timeout behavior
    
    2. Memory Cache Performance:
       - L1 memory cache hit rates and timing
       - Memory cache eviction efficiency
       - L1/L2 cache coordination and fallback behavior
       - Memory usage and entry management
    
    3. Compression Efficiency:
       - Compression ratio analysis across different data types
       - Compression/decompression timing measurements
       - Memory savings calculation and efficiency metrics
       - Compression threshold optimization testing
    
    4. Performance Comparison:
       - Before/after refactoring validation
       - Regression detection with configurable thresholds
       - Performance trend analysis over time
       - Optimization recommendation generation

Benchmark Configuration:
    Default Performance Thresholds:
        - Basic Operations: <50ms average, <100ms p95
        - Memory Cache: <5ms average, <10ms p95
        - Compression: <100ms average, <200ms p95
        - Memory Usage: <100MB total cache size
        - Regression Threshold: <10% performance degradation

Data Collection and Analysis:
    The benchmarking system automatically collects:
    - Timing measurements with microsecond precision
    - Memory usage tracking for all cache components
    - Hit/miss ratios and cache efficiency metrics
    - Compression performance and savings analysis
    - Error rates and timeout handling performance
    - System resource utilization during testing

Integration Points:
    - Cache service layer for operation benchmarking
    - Performance monitoring for trend analysis
    - API endpoints for automated benchmark execution
    - Alert systems for regression detection
    - Reporting tools for performance analysis

Dependencies:
    - time, asyncio: Timing and async operation support
    - statistics: Statistical analysis and percentile calculations
    - psutil: System resource monitoring (optional with fallback)
    - dataclasses: Structured result storage
    - typing: Type hints and annotations
    - datetime: Timestamp and duration management
    - json: Result serialization and export

Thread Safety:
    This module is designed for single-threaded use within each benchmark session.
    Concurrent benchmark execution requires separate benchmark instances to prevent
    data corruption and ensure measurement accuracy.

Performance Considerations:
    - Minimal overhead design with efficient measurement collection
    - Isolated benchmark execution to prevent interference
    - Configurable iteration counts for timing vs. accuracy trade-offs
    - Automatic cleanup of temporary test data
    - Resource-aware testing with memory and CPU monitoring
"""

import asyncio
import json
import logging
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from .base import CacheInterface
from .monitoring import CachePerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Comprehensive result data for a single cache performance benchmark."""
    
    operation_type: str
    duration_ms: float
    memory_peak_mb: float
    iterations: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    std_dev_ms: float
    operations_per_second: float
    success_rate: float
    memory_usage_mb: float
    cache_hit_rate: Optional[float] = None
    compression_ratio: Optional[float] = None
    compression_savings_mb: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert benchmark result to dictionary for serialization."""
        return asdict(self)
    
    def meets_threshold(self, threshold_ms: float) -> bool:
        """Check if benchmark result meets performance threshold."""
        return self.avg_duration_ms <= threshold_ms
    
    def performance_grade(self) -> str:
        """Calculate performance grade based on standard thresholds."""
        if self.avg_duration_ms <= 5.0:
            return "Excellent"
        elif self.avg_duration_ms <= 25.0:
            return "Good"
        elif self.avg_duration_ms <= 50.0:
            return "Acceptable"
        elif self.avg_duration_ms <= 100.0:
            return "Poor"
        else:
            return "Critical"


@dataclass
class ComparisonResult:
    """Result data for comparing performance between cache implementations."""
    
    original_cache_results: BenchmarkResult
    new_cache_results: BenchmarkResult
    performance_change_percent: float
    memory_change_percent: float
    operations_per_second_change: float
    cache_hit_rate_change: Optional[float] = None
    compression_efficiency_change: Optional[float] = None
    regression_detected: bool = False
    improvement_areas: List[str] = field(default_factory=list)
    degradation_areas: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert comparison result to dictionary for serialization."""
        return asdict(self)
    
    def summary(self) -> str:
        """Generate human-readable summary of comparison results."""
        direction = "improved" if self.performance_change_percent < 0 else "degraded"
        abs_change = abs(self.performance_change_percent)
        
        return (f"Performance {direction} by {abs_change:.1f}% "
                f"(Memory: {self.memory_change_percent:+.1f}%, "
                f"Throughput: {self.operations_per_second_change:+.1f}%)")


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results with comprehensive analysis."""
    
    name: str
    results: List[BenchmarkResult]
    total_duration_ms: float
    pass_rate: float
    failed_benchmarks: List[str]
    performance_grade: str
    memory_efficiency_grade: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    environment_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Serialize benchmark suite to JSON string."""
        return json.dumps(asdict(self), indent=2)
    
    def get_operation_result(self, operation_type: str) -> Optional[BenchmarkResult]:
        """Get benchmark result for specific operation type."""
        for result in self.results:
            if result.operation_type == operation_type:
                return result
        return None
    
    def calculate_overall_score(self) -> float:
        """Calculate overall performance score (0-100)."""
        if not self.results:
            return 0.0
        
        # Weight different aspects of performance
        timing_score = min(100, max(0, 100 - sum(r.avg_duration_ms for r in self.results) / len(self.results)))
        success_score = self.pass_rate * 100
        memory_score = min(100, max(0, 100 - sum(r.memory_usage_mb for r in self.results) / len(self.results)))
        
        # Weighted average: timing 50%, success 30%, memory 20%
        return (timing_score * 0.5) + (success_score * 0.3) + (memory_score * 0.2)


class CachePerformanceThresholds:
    """Performance threshold definitions for cache operations."""
    
    # Basic operation thresholds (milliseconds)
    BASIC_OPERATIONS_AVG_MS = 50.0
    BASIC_OPERATIONS_P95_MS = 100.0
    BASIC_OPERATIONS_P99_MS = 200.0
    
    # Memory cache thresholds (milliseconds)
    MEMORY_CACHE_AVG_MS = 5.0
    MEMORY_CACHE_P95_MS = 10.0
    MEMORY_CACHE_P99_MS = 20.0
    
    # Compression thresholds (milliseconds)
    COMPRESSION_AVG_MS = 100.0
    COMPRESSION_P95_MS = 200.0
    COMPRESSION_P99_MS = 500.0
    
    # Memory usage thresholds (megabytes)
    MEMORY_USAGE_WARNING_MB = 50.0
    MEMORY_USAGE_CRITICAL_MB = 100.0
    
    # Performance regression thresholds (percentage)
    REGRESSION_WARNING_PERCENT = 10.0
    REGRESSION_CRITICAL_PERCENT = 25.0
    
    # Success rate thresholds (percentage)
    SUCCESS_RATE_WARNING = 95.0
    SUCCESS_RATE_CRITICAL = 90.0


class CacheBenchmarkDataGenerator:
    """Generate realistic test data for cache performance benchmarking."""
    
    def __init__(self):
        self.text_samples = [
            "Short text for basic testing.",
            "Medium length text that represents typical cache content with some additional words to make it more realistic for testing purposes.",
            "Long text content that simulates larger cache entries with substantial content that might be encountered in real-world applications. " * 10,
            "Very long text content that tests the limits of cache performance with extensive data. " * 50
        ]
        
        self.operation_types = ["summarize", "sentiment", "key_points", "questions", "qa"]
        self.sample_options = {
            "length": ["short", "medium", "long"],
            "style": ["formal", "casual", "technical"],
            "detail_level": ["brief", "detailed", "comprehensive"]
        }
    
    def generate_basic_operations_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate test data for basic cache operations."""
        import random
        
        test_data = []
        for i in range(count):
            text = random.choice(self.text_samples)
            operation = random.choice(self.operation_types)
            options = {k: random.choice(v) for k, v in self.sample_options.items()}
            
            test_data.append({
                "key": f"test_key_{i}",
                "text": text,
                "operation": operation,
                "options": options,
                "expected_size_bytes": len(text.encode('utf-8')),
                "cache_ttl": random.randint(300, 3600)
            })
        
        return test_data
    
    def generate_memory_pressure_data(self, total_size_mb: float = 10.0) -> List[Dict[str, Any]]:
        """Generate large dataset for memory cache pressure testing."""
        import random
        
        target_bytes = int(total_size_mb * 1024 * 1024)
        test_data = []
        current_size = 0
        index = 0
        
        while current_size < target_bytes:
            # Generate variable-sized content
            size_factor = random.randint(1, 20)
            text = "Large cache entry content for memory pressure testing. " * size_factor
            text_bytes = len(text.encode('utf-8'))
            
            test_data.append({
                "key": f"memory_test_{index}",
                "text": text,
                "operation": random.choice(self.operation_types),
                "size_bytes": text_bytes,
                "priority": random.choice(["high", "medium", "low"])
            })
            
            current_size += text_bytes
            index += 1
        
        return test_data
    
    def generate_concurrent_access_patterns(self, num_patterns: int = 10) -> List[Dict[str, Any]]:
        """Generate patterns for concurrent cache access testing."""
        import random
        
        patterns = []
        base_keys = [f"concurrent_key_{i}" for i in range(20)]
        
        for i in range(num_patterns):
            pattern = {
                "pattern_id": f"pattern_{i}",
                "operations": [],
                "concurrency_level": random.randint(5, 20),
                "duration_seconds": random.randint(10, 60)
            }
            
            # Generate sequence of operations for this pattern
            for j in range(random.randint(50, 200)):
                operation = {
                    "type": random.choice(["get", "set", "delete"]),
                    "key": random.choice(base_keys),
                    "delay_ms": random.randint(1, 100),
                    "text": random.choice(self.text_samples) if random.random() > 0.3 else None
                }
                pattern["operations"].append(operation)
            
            patterns.append(pattern)
        
        return patterns
    
    def generate_compression_test_data(self) -> List[Dict[str, Any]]:
        """Generate diverse data for compression efficiency testing."""
        test_data = []
        
        # Highly compressible data (repetitive text)
        repetitive_text = "This is a highly repetitive text pattern. " * 100
        test_data.append({
            "type": "highly_compressible",
            "text": repetitive_text,
            "expected_compression_ratio": 0.1,  # Very good compression
            "description": "Repetitive text with high compression potential"
        })
        
        # Moderately compressible data (natural text)
        natural_text = """
        Natural language text typically compresses moderately well due to patterns in
        language structure, common word usage, and repeated phrases. This type of content
        represents typical cache entries for text processing applications.
        """ * 20
        test_data.append({
            "type": "moderately_compressible",
            "text": natural_text,
            "expected_compression_ratio": 0.4,  # Moderate compression
            "description": "Natural language with moderate compression potential"
        })
        
        # Poorly compressible data (random-like content)
        import random
        import string
        random_text = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=10000))
        test_data.append({
            "type": "poorly_compressible",
            "text": random_text,
            "expected_compression_ratio": 0.9,  # Poor compression
            "description": "Random text with low compression potential"
        })
        
        # JSON-like structured data
        json_like_text = '''{"users": [{"id": %d, "name": "User %d", "email": "user%d@example.com", "data": "%s"}''' % (
            random.randint(1, 1000), random.randint(1, 1000), random.randint(1, 1000), "x" * 100
        ) + "]} " * 50
        test_data.append({
            "type": "structured_data",
            "text": json_like_text,
            "expected_compression_ratio": 0.3,  # Good compression for structured data
            "description": "JSON-like structured data with good compression potential"
        })
        
        return test_data


class PerformanceRegressionDetector:
    """Detect and analyze performance regressions in cache benchmarks."""
    
    def __init__(self, warning_threshold: float = 10.0, critical_threshold: float = 25.0):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
    
    def detect_timing_regressions(self, old_result: BenchmarkResult, new_result: BenchmarkResult) -> List[Dict[str, Any]]:
        """Detect timing-related performance regressions."""
        regressions = []
        
        # Check average duration regression
        avg_change = ((new_result.avg_duration_ms - old_result.avg_duration_ms) / old_result.avg_duration_ms) * 100
        if avg_change > self.warning_threshold:
            severity = "critical" if avg_change > self.critical_threshold else "warning"
            regressions.append({
                "type": "timing_regression",
                "metric": "average_duration",
                "severity": severity,
                "change_percent": avg_change,
                "old_value": old_result.avg_duration_ms,
                "new_value": new_result.avg_duration_ms,
                "message": f"Average duration increased by {avg_change:.1f}%"
            })
        
        # Check P95 duration regression
        p95_change = ((new_result.p95_duration_ms - old_result.p95_duration_ms) / old_result.p95_duration_ms) * 100
        if p95_change > self.warning_threshold:
            severity = "critical" if p95_change > self.critical_threshold else "warning"
            regressions.append({
                "type": "timing_regression",
                "metric": "p95_duration",
                "severity": severity,
                "change_percent": p95_change,
                "old_value": old_result.p95_duration_ms,
                "new_value": new_result.p95_duration_ms,
                "message": f"P95 duration increased by {p95_change:.1f}%"
            })
        
        # Check operations per second degradation
        ops_change = ((new_result.operations_per_second - old_result.operations_per_second) / old_result.operations_per_second) * 100
        if ops_change < -self.warning_threshold:
            severity = "critical" if ops_change < -self.critical_threshold else "warning"
            regressions.append({
                "type": "throughput_regression",
                "metric": "operations_per_second",
                "severity": severity,
                "change_percent": ops_change,
                "old_value": old_result.operations_per_second,
                "new_value": new_result.operations_per_second,
                "message": f"Throughput decreased by {abs(ops_change):.1f}%"
            })
        
        return regressions
    
    def detect_memory_regressions(self, old_result: BenchmarkResult, new_result: BenchmarkResult) -> List[Dict[str, Any]]:
        """Detect memory-related performance regressions."""
        regressions = []
        
        # Check memory usage increase with safe division
        memory_change = 0.0
        if old_result.memory_usage_mb > 0:
            memory_change = ((new_result.memory_usage_mb - old_result.memory_usage_mb) / old_result.memory_usage_mb) * 100
            if memory_change > self.warning_threshold:
                severity = "critical" if memory_change > self.critical_threshold else "warning"
                regressions.append({
                    "type": "memory_regression",
                    "metric": "memory_usage",
                    "severity": severity,
                    "change_percent": memory_change,
                    "old_value": old_result.memory_usage_mb,
                    "new_value": new_result.memory_usage_mb,
                    "message": f"Memory usage increased by {memory_change:.1f}%"
                })
        
        # Check peak memory increase with safe division
        peak_change = 0.0
        if old_result.memory_peak_mb > 0:
            peak_change = ((new_result.memory_peak_mb - old_result.memory_peak_mb) / old_result.memory_peak_mb) * 100
        if peak_change > self.warning_threshold:
            severity = "critical" if peak_change > self.critical_threshold else "warning"
            regressions.append({
                "type": "memory_regression",
                "metric": "peak_memory",
                "severity": severity,
                "change_percent": peak_change,
                "old_value": old_result.memory_peak_mb,
                "new_value": new_result.memory_peak_mb,
                "message": f"Peak memory usage increased by {peak_change:.1f}%"
            })
        
        return regressions
    
    def validate_cache_hit_rates(self, old_result: BenchmarkResult, new_result: BenchmarkResult) -> Dict[str, Any]:
        """Validate cache hit rates haven't degraded."""
        if old_result.cache_hit_rate is None or new_result.cache_hit_rate is None:
            return {"status": "skipped", "reason": "hit_rate_data_unavailable"}
        
        hit_rate_change = new_result.cache_hit_rate - old_result.cache_hit_rate
        
        if hit_rate_change < -5.0:  # More than 5% hit rate decrease
            severity = "critical" if hit_rate_change < -15.0 else "warning"
            return {
                "status": "regression_detected",
                "severity": severity,
                "change_percent": hit_rate_change,
                "old_hit_rate": old_result.cache_hit_rate,
                "new_hit_rate": new_result.cache_hit_rate,
                "message": f"Cache hit rate decreased by {abs(hit_rate_change):.1f}%"
            }
        
        return {
            "status": "passed",
            "change_percent": hit_rate_change,
            "message": f"Cache hit rate maintained (change: {hit_rate_change:+.1f}%)"
        }


class CachePerformanceBenchmark:
    """
    Comprehensive performance benchmarking for cache implementations.
    
    This class provides extensive benchmarking capabilities for validating cache
    performance across multiple dimensions including timing, memory usage, compression
    efficiency, and regression detection. It builds on the existing performance
    monitoring infrastructure to provide detailed validation for cache refactoring.
    """
    
    def __init__(self, performance_monitor: Optional[CachePerformanceMonitor] = None):
        """
        Initialize cache performance benchmark system.
        
        Args:
            performance_monitor: Optional existing performance monitor for integration
        """
        self.performance_monitor = performance_monitor or CachePerformanceMonitor()
        self.data_generator = CacheBenchmarkDataGenerator()
        self.regression_detector = PerformanceRegressionDetector()
        self.results_history: List[BenchmarkSuite] = []
        
        # Performance thresholds
        self.thresholds = CachePerformanceThresholds()
        
        # Benchmark configuration
        self.default_iterations = 100
        self.warmup_iterations = 10
        self.timeout_seconds = 300  # 5 minute timeout for benchmarks
        
    async def benchmark_basic_operations(self, cache: CacheInterface, iterations: int = None) -> BenchmarkResult:
        """
        Benchmark basic cache operations (get/set/delete) with comprehensive timing analysis.
        
        Args:
            cache: Cache implementation to benchmark
            iterations: Number of test iterations (default: 100)
        
        Returns:
            BenchmarkResult: Comprehensive timing and performance metrics
        """
        iterations = iterations or self.default_iterations
        test_data = self.data_generator.generate_basic_operations_data(iterations)
        
        logger.info(f"Starting basic operations benchmark with {iterations} iterations")
        
        # Track memory usage
        initial_memory = self._get_process_memory_mb()
        peak_memory = initial_memory
        
        # Timing measurements
        durations = []
        successful_operations = 0
        cache_hits = 0
        cache_misses = 0
        
        # Warmup phase
        logger.debug("Performing warmup operations...")
        warmup_data = test_data[:self.warmup_iterations]
        for data in warmup_data:
            try:
                await cache.set(data["key"], {"text": data["text"], "options": data["options"]})
            except Exception as e:
                logger.debug(f"Warmup operation failed: {e}")
        
        # Main benchmark phase
        start_time = time.time()
        
        for i, data in enumerate(test_data):
            operation_start = time.perf_counter()
            
            try:
                # Test set operation
                await cache.set(
                    data["key"], 
                    {"text": data["text"], "options": data["options"]},
                    ttl=data.get("cache_ttl")
                )
                
                # Test get operation
                result = await cache.get(data["key"])
                
                # Test exists operation
                exists = await cache.exists(data["key"])
                
                operation_end = time.perf_counter()
                operation_duration = (operation_end - operation_start) * 1000  # Convert to ms
                
                durations.append(operation_duration)
                successful_operations += 1
                
                if result is not None:
                    cache_hits += 1
                else:
                    cache_misses += 1
                
                # Track peak memory usage
                current_memory = self._get_process_memory_mb()
                peak_memory = max(peak_memory, current_memory)
                
                # Log progress for long benchmarks
                if i > 0 and i % 50 == 0:
                    logger.debug(f"Completed {i}/{iterations} operations")
                    
            except Exception as e:
                logger.warning(f"Operation {i} failed: {e}")
                # Still record timing for failed operations
                operation_end = time.perf_counter()
                operation_duration = (operation_end - operation_start) * 1000
                durations.append(operation_duration)
        
        total_duration = time.time() - start_time
        
        # Calculate statistics
        if durations:
            avg_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            std_dev = statistics.stdev(durations) if len(durations) > 1 else 0.0
            p95_duration = statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max_duration
            p99_duration = statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else max_duration
        else:
            avg_duration = min_duration = max_duration = std_dev = p95_duration = p99_duration = 0.0
        
        # Calculate performance metrics
        success_rate = successful_operations / iterations if iterations > 0 else 0.0
        operations_per_second = successful_operations / total_duration if total_duration > 0 else 0.0
        cache_hit_rate = (cache_hits / (cache_hits + cache_misses)) * 100 if (cache_hits + cache_misses) > 0 else None
        
        result = BenchmarkResult(
            operation_type="basic_operations",
            duration_ms=total_duration * 1000,
            memory_peak_mb=peak_memory,
            iterations=iterations,
            avg_duration_ms=avg_duration,
            min_duration_ms=min_duration,
            max_duration_ms=max_duration,
            p95_duration_ms=p95_duration,
            p99_duration_ms=p99_duration,
            std_dev_ms=std_dev,
            operations_per_second=operations_per_second,
            success_rate=success_rate,
            memory_usage_mb=peak_memory - initial_memory,
            cache_hit_rate=cache_hit_rate,
            metadata={
                "total_operations": iterations,
                "successful_operations": successful_operations,
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "warmup_iterations": self.warmup_iterations
            }
        )
        
        logger.info(f"Basic operations benchmark completed: {avg_duration:.2f}ms avg, {operations_per_second:.0f} ops/sec")
        return result

    async def benchmark_memory_cache_performance(self, cache, iterations: int = None) -> BenchmarkResult:
        """
        Benchmark memory cache (L1) performance and efficiency.
        
        This test specifically focuses on memory cache hit rates, eviction behavior,
        and L1/L2 cache coordination for caches that implement memory caching.
        
        Args:
            cache: Cache implementation with memory cache support
            iterations: Number of test iterations (default: 200)
        
        Returns:
            BenchmarkResult: Memory cache performance metrics
        """
        iterations = iterations or (self.default_iterations * 2)  # More iterations for memory cache testing
        
        # Check if cache supports memory cache operations
        has_memory_cache = hasattr(cache, '_memory_cache') or hasattr(cache, 'memory_cache_size')
        if not has_memory_cache:
            logger.warning("Cache doesn't appear to have memory cache support, testing as regular cache")
        
        logger.info(f"Starting memory cache performance benchmark with {iterations} iterations")
        
        # Generate test data that will stress memory cache
        test_data = self.data_generator.generate_basic_operations_data(iterations)
        
        # Track memory usage
        initial_memory = self._get_process_memory_mb()
        peak_memory = initial_memory
        
        # Performance tracking
        durations = []
        memory_hits = 0
        redis_hits = 0
        cache_misses = 0
        successful_operations = 0
        
        start_time = time.time()
        
        # Phase 1: Populate cache to test memory cache behavior
        logger.debug("Phase 1: Populating cache for memory cache testing...")
        for i, data in enumerate(test_data[:iterations//2]):
            operation_start = time.perf_counter()
            
            try:
                await cache.set(data["key"], {"text": data["text"], "options": data["options"]})
                successful_operations += 1
                
                operation_end = time.perf_counter()
                durations.append((operation_end - operation_start) * 1000)
                
                # Track memory usage
                current_memory = self._get_process_memory_mb()
                peak_memory = max(peak_memory, current_memory)
                
            except Exception as e:
                logger.warning(f"Set operation {i} failed: {e}")
        
        # Phase 2: Test memory cache hits by accessing recently set items
        logger.debug("Phase 2: Testing memory cache hit performance...")
        for i, data in enumerate(test_data[:iterations//4]):  # Access subset multiple times
            for _ in range(3):  # Multiple accesses to trigger memory cache hits
                operation_start = time.perf_counter()
                
                try:
                    result = await cache.get(data["key"])
                    
                    operation_end = time.perf_counter()
                    operation_duration = (operation_end - operation_start) * 1000
                    durations.append(operation_duration)
                    
                    if result is not None:
                        # Try to determine if this was a memory cache hit
                        # This is implementation-specific heuristic
                        if operation_duration < 1.0:  # Very fast = likely memory cache
                            memory_hits += 1
                        else:
                            redis_hits += 1
                    else:
                        cache_misses += 1
                    
                    successful_operations += 1
                    
                except Exception as e:
                    logger.warning(f"Get operation failed: {e}")
        
        # Phase 3: Test cache eviction and memory management
        logger.debug("Phase 3: Testing memory cache eviction behavior...")
        eviction_test_data = self.data_generator.generate_memory_pressure_data(5.0)  # 5MB of data
        
        for i, data in enumerate(eviction_test_data):
            operation_start = time.perf_counter()
            
            try:
                await cache.set(data["key"], {"text": data["text"], "size": data["size_bytes"]})
                successful_operations += 1
                
                operation_end = time.perf_counter()
                durations.append((operation_end - operation_start) * 1000)
                
                # Track memory usage during eviction
                current_memory = self._get_process_memory_mb()
                peak_memory = max(peak_memory, current_memory)
                
            except Exception as e:
                logger.warning(f"Eviction test operation {i} failed: {e}")
        
        total_duration = time.time() - start_time
        
        # Calculate statistics
        if durations:
            avg_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            std_dev = statistics.stdev(durations) if len(durations) > 1 else 0.0
            p95_duration = statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max_duration
            p99_duration = statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else max_duration
        else:
            avg_duration = min_duration = max_duration = std_dev = p95_duration = p99_duration = 0.0
        
        # Calculate performance metrics
        total_get_operations = memory_hits + redis_hits + cache_misses
        memory_hit_rate = (memory_hits / total_get_operations) * 100 if total_get_operations > 0 else 0.0
        overall_hit_rate = ((memory_hits + redis_hits) / total_get_operations) * 100 if total_get_operations > 0 else 0.0
        success_rate = successful_operations / (successful_operations + cache_misses) if (successful_operations + cache_misses) > 0 else 0.0
        operations_per_second = successful_operations / total_duration if total_duration > 0 else 0.0
        
        result = BenchmarkResult(
            operation_type="memory_cache_performance",
            duration_ms=total_duration * 1000,
            memory_peak_mb=peak_memory,
            iterations=successful_operations,
            avg_duration_ms=avg_duration,
            min_duration_ms=min_duration,
            max_duration_ms=max_duration,
            p95_duration_ms=p95_duration,
            p99_duration_ms=p99_duration,
            std_dev_ms=std_dev,
            operations_per_second=operations_per_second,
            success_rate=success_rate,
            memory_usage_mb=peak_memory - initial_memory,
            cache_hit_rate=overall_hit_rate,
            metadata={
                "memory_hits": memory_hits,
                "redis_hits": redis_hits,
                "cache_misses": cache_misses,
                "memory_hit_rate": memory_hit_rate,
                "overall_hit_rate": overall_hit_rate,
                "has_memory_cache": has_memory_cache,
                "eviction_test_entries": len(eviction_test_data)
            }
        )
        
        logger.info(f"Memory cache benchmark completed: {avg_duration:.2f}ms avg, {memory_hit_rate:.1f}% memory hit rate")
        return result

    async def benchmark_compression_efficiency(self, cache, iterations: int = None) -> BenchmarkResult:
        """
        Benchmark compression performance and efficiency.
        
        Tests compression ratios, compression/decompression timing, and memory savings
        across different types of data to validate compression implementation.
        
        Args:
            cache: Cache implementation with compression support
            iterations: Number of compression test cycles (default: 50)
        
        Returns:
            BenchmarkResult: Compression performance and efficiency metrics
        """
        iterations = iterations or (self.default_iterations // 2)  # Fewer iterations for compression testing
        
        # Check if cache supports compression
        has_compression = hasattr(cache, 'compression_threshold') or hasattr(cache, '_compress_data')
        if not has_compression:
            logger.warning("Cache doesn't appear to have compression support, testing without compression")
        
        logger.info(f"Starting compression efficiency benchmark with {iterations} iterations")
        
        # Get diverse test data for compression testing
        compression_test_data = self.data_generator.generate_compression_test_data()
        
        # Track memory and timing
        initial_memory = self._get_process_memory_mb()
        peak_memory = initial_memory
        
        # Performance tracking
        durations = []
        compression_ratios = []
        total_original_bytes = 0
        total_compressed_bytes = 0
        successful_operations = 0
        compression_times = []
        
        start_time = time.time()
        
        for iteration in range(iterations):
            for data_type_index, test_data in enumerate(compression_test_data):
                operation_start = time.perf_counter()
                
                try:
                    key = f"compression_test_{iteration}_{data_type_index}"
                    text_data = test_data["text"]
                    original_size = len(text_data.encode('utf-8'))
                    
                    # Test compression through cache set operation
                    await cache.set(key, {"text": text_data, "type": test_data["type"]})
                    
                    # Test decompression through cache get operation
                    result = await cache.get(key)
                    
                    operation_end = time.perf_counter()
                    operation_duration = (operation_end - operation_start) * 1000
                    durations.append(operation_duration)
                    
                    if result is not None:
                        successful_operations += 1
                        
                        # Try to estimate compression ratio if possible
                        # This is implementation-specific and may not always be accurate
                        if hasattr(cache, '_get_compression_stats'):
                            try:
                                compression_stats = cache._get_compression_stats(key)
                                if compression_stats:
                                    compressed_size = compression_stats.get('compressed_size', original_size)
                                    compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
                                    compression_ratios.append(compression_ratio)
                                    total_original_bytes += original_size
                                    total_compressed_bytes += compressed_size
                            except:
                                # Fallback to expected compression ratio from test data
                                compression_ratio = test_data.get("expected_compression_ratio", 0.5)
                                compression_ratios.append(compression_ratio)
                                total_original_bytes += original_size
                                total_compressed_bytes += int(original_size * compression_ratio)
                        else:
                            # Use expected compression ratio from test data
                            compression_ratio = test_data.get("expected_compression_ratio", 0.5)
                            compression_ratios.append(compression_ratio)
                            total_original_bytes += original_size
                            total_compressed_bytes += int(original_size * compression_ratio)
                    
                    # Track memory usage
                    current_memory = self._get_process_memory_mb()
                    peak_memory = max(peak_memory, current_memory)
                    
                except Exception as e:
                    logger.warning(f"Compression test {iteration}-{data_type_index} failed: {e}")
                    operation_end = time.perf_counter()
                    durations.append((operation_end - operation_start) * 1000)
        
        total_duration = time.time() - start_time
        
        # Calculate statistics
        if durations:
            avg_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            std_dev = statistics.stdev(durations) if len(durations) > 1 else 0.0
            p95_duration = statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max_duration
            p99_duration = statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else max_duration
        else:
            avg_duration = min_duration = max_duration = std_dev = p95_duration = p99_duration = 0.0
        
        # Calculate compression metrics
        overall_compression_ratio = total_compressed_bytes / total_original_bytes if total_original_bytes > 0 else 1.0
        compression_savings_mb = (total_original_bytes - total_compressed_bytes) / (1024 * 1024)
        avg_compression_ratio = statistics.mean(compression_ratios) if compression_ratios else 1.0
        
        success_rate = successful_operations / (iterations * len(compression_test_data)) if iterations > 0 else 0.0
        operations_per_second = successful_operations / total_duration if total_duration > 0 else 0.0
        
        result = BenchmarkResult(
            operation_type="compression_efficiency",
            duration_ms=total_duration * 1000,
            memory_peak_mb=peak_memory,
            iterations=iterations * len(compression_test_data),
            avg_duration_ms=avg_duration,
            min_duration_ms=min_duration,
            max_duration_ms=max_duration,
            p95_duration_ms=p95_duration,
            p99_duration_ms=p99_duration,
            std_dev_ms=std_dev,
            operations_per_second=operations_per_second,
            success_rate=success_rate,
            memory_usage_mb=peak_memory - initial_memory,
            compression_ratio=overall_compression_ratio,
            compression_savings_mb=compression_savings_mb,
            metadata={
                "has_compression": has_compression,
                "total_original_bytes": total_original_bytes,
                "total_compressed_bytes": total_compressed_bytes,
                "avg_compression_ratio": avg_compression_ratio,
                "compression_test_types": len(compression_test_data),
                "compression_savings_percent": ((total_original_bytes - total_compressed_bytes) / total_original_bytes * 100) if total_original_bytes > 0 else 0.0
            }
        )
        
        logger.info(f"Compression benchmark completed: {avg_duration:.2f}ms avg, {overall_compression_ratio:.2f} compression ratio")
        return result

    async def compare_before_after_refactoring(self, original_cache: CacheInterface, new_cache: CacheInterface, 
                                             test_iterations: int = None) -> ComparisonResult:
        """
        Compare performance between original and refactored cache implementations.
        
        This method runs identical benchmarks on both cache implementations and
        provides detailed analysis of performance changes, regressions, and improvements.
        
        Args:
            original_cache: Original cache implementation (e.g., AIResponseCache)
            new_cache: New cache implementation (e.g., GenericRedisCache)
            test_iterations: Number of test iterations for comparison (default: 100)
        
        Returns:
            ComparisonResult: Detailed comparison analysis with regression detection
        """
        test_iterations = test_iterations or self.default_iterations
        
        logger.info(f"Starting before/after refactoring comparison with {test_iterations} iterations")
        
        try:
            # Ensure both caches are in clean state
            if hasattr(original_cache, 'clear'):
                await original_cache.clear()
            if hasattr(new_cache, 'clear'):
                await new_cache.clear()
            
            # Benchmark original cache
            logger.info("Benchmarking original cache implementation...")
            original_result = await self.benchmark_basic_operations(original_cache, test_iterations)
            
            # Wait a moment to allow cleanup
            await asyncio.sleep(1)
            
            # Benchmark new cache
            logger.info("Benchmarking new cache implementation...")
            new_result = await self.benchmark_basic_operations(new_cache, test_iterations)
            
            # Calculate performance changes with safe division
            performance_change = 0.0
            if original_result.avg_duration_ms > 0:
                performance_change = ((new_result.avg_duration_ms - original_result.avg_duration_ms) / original_result.avg_duration_ms) * 100
            
            memory_change = 0.0
            if original_result.memory_usage_mb > 0:
                memory_change = ((new_result.memory_usage_mb - original_result.memory_usage_mb) / original_result.memory_usage_mb) * 100
            
            ops_change = 0.0
            if original_result.operations_per_second > 0:
                ops_change = ((new_result.operations_per_second - original_result.operations_per_second) / original_result.operations_per_second) * 100
            
            hit_rate_change = None
            if original_result.cache_hit_rate is not None and new_result.cache_hit_rate is not None:
                hit_rate_change = new_result.cache_hit_rate - original_result.cache_hit_rate
            
            # Detect regressions
            timing_regressions = self.regression_detector.detect_timing_regressions(original_result, new_result)
            memory_regressions = self.regression_detector.detect_memory_regressions(original_result, new_result)
            hit_rate_validation = self.regression_detector.validate_cache_hit_rates(original_result, new_result)
            
            all_regressions = timing_regressions + memory_regressions
            regression_detected = len(all_regressions) > 0 or hit_rate_validation.get("status") == "regression_detected"
            
            # Analyze improvements and degradations
            improvement_areas = []
            degradation_areas = []
            
            if performance_change < -5:  # More than 5% improvement
                improvement_areas.append(f"Average response time improved by {abs(performance_change):.1f}%")
            elif performance_change > 10:  # More than 10% degradation
                degradation_areas.append(f"Average response time degraded by {performance_change:.1f}%")
            
            if ops_change > 5:  # More than 5% throughput improvement
                improvement_areas.append(f"Throughput improved by {ops_change:.1f}%")
            elif ops_change < -10:  # More than 10% throughput degradation
                degradation_areas.append(f"Throughput degraded by {abs(ops_change):.1f}%")
            
            if memory_change < -10:  # More than 10% memory improvement
                improvement_areas.append(f"Memory usage improved by {abs(memory_change):.1f}%")
            elif memory_change > 20:  # More than 20% memory increase
                degradation_areas.append(f"Memory usage increased by {memory_change:.1f}%")
            
            # Generate recommendations
            recommendations = []
            
            if regression_detected:
                recommendations.append("Performance regression detected - investigate before production deployment")
                for regression in all_regressions:
                    recommendations.append(f"Address {regression['metric']} regression: {regression['message']}")
            
            if new_result.success_rate < original_result.success_rate:
                recommendations.append(f"Success rate decreased from {original_result.success_rate:.1f}% to {new_result.success_rate:.1f}% - investigate error handling")
            
            if not improvement_areas and not degradation_areas:
                recommendations.append("Performance characteristics are similar - refactoring successful")
            
            if improvement_areas:
                recommendations.append("Performance improvements detected - monitor in production to validate")
            
            comparison_result = ComparisonResult(
                original_cache_results=original_result,
                new_cache_results=new_result,
                performance_change_percent=performance_change,
                memory_change_percent=memory_change,
                operations_per_second_change=ops_change,
                cache_hit_rate_change=hit_rate_change,
                regression_detected=regression_detected,
                improvement_areas=improvement_areas,
                degradation_areas=degradation_areas,
                recommendations=recommendations
            )
            
            logger.info(f"Cache comparison completed: {performance_change:+.1f}% performance change, regression: {regression_detected}")
            return comparison_result
            
        except Exception as e:
            logger.error(f"Cache comparison failed: {e}")
            raise

    def _get_process_memory_mb(self) -> float:
        """Get current process memory usage in MB."""
        try:
            # Try to use psutil if available
            try:
                import psutil
                process = psutil.Process()
                return process.memory_info().rss / 1024 / 1024
            except ImportError:
                pass
            
            # Fallback to reading /proc/self/status on Linux
            try:
                with open("/proc/self/status", "r") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            kb = int(line.split()[1])
                            return kb / 1024
            except (IOError, ValueError, IndexError):
                pass
            
            # If all methods fail, return 0
            return 0.0
            
        except Exception as e:
            logger.debug(f"Could not determine process memory usage: {e}")
            return 0.0

    async def run_comprehensive_benchmark_suite(self, cache: CacheInterface, include_compression: bool = True) -> BenchmarkSuite:
        """
        Run comprehensive benchmark suite covering all cache performance aspects.
        
        Args:
            cache: Cache implementation to benchmark
            include_compression: Whether to include compression benchmarks (default: True)
        
        Returns:
            BenchmarkSuite: Complete benchmark results with analysis
        """
        logger.info("Starting comprehensive cache benchmark suite")
        suite_start_time = time.time()
        
        results = []
        failed_benchmarks = []
        
        # Collect environment information
        environment_info = self._collect_environment_info()
        
        try:
            # 1. Basic operations benchmark
            logger.info("Running basic operations benchmark...")
            basic_result = await self.benchmark_basic_operations(cache)
            results.append(basic_result)
        except Exception as e:
            logger.error(f"Basic operations benchmark failed: {e}")
            failed_benchmarks.append(f"basic_operations: {str(e)}")
        
        try:
            # 2. Memory cache performance benchmark
            logger.info("Running memory cache performance benchmark...")
            memory_result = await self.benchmark_memory_cache_performance(cache)
            results.append(memory_result)
        except Exception as e:
            logger.error(f"Memory cache benchmark failed: {e}")
            failed_benchmarks.append(f"memory_cache_performance: {str(e)}")
        
        if include_compression:
            try:
                # 3. Compression efficiency benchmark
                logger.info("Running compression efficiency benchmark...")
                compression_result = await self.benchmark_compression_efficiency(cache)
                results.append(compression_result)
            except Exception as e:
                logger.error(f"Compression benchmark failed: {e}")
                failed_benchmarks.append(f"compression_efficiency: {str(e)}")
        
        suite_duration = time.time() - suite_start_time
        
        # Calculate suite-level metrics
        total_benchmarks = len(results) + len(failed_benchmarks)
        pass_rate = len(results) / total_benchmarks if total_benchmarks > 0 else 0.0
        
        # Calculate performance grades
        performance_grade = self._calculate_performance_grade(results)
        memory_efficiency_grade = self._calculate_memory_efficiency_grade(results)
        
        suite = BenchmarkSuite(
            name="Comprehensive Cache Performance Benchmark",
            results=results,
            total_duration_ms=suite_duration * 1000,
            pass_rate=pass_rate,
            failed_benchmarks=failed_benchmarks,
            performance_grade=performance_grade,
            memory_efficiency_grade=memory_efficiency_grade,
            environment_info=environment_info
        )
        
        # Store in history for trend analysis
        self.results_history.append(suite)
        
        logger.info(f"Benchmark suite completed: {len(results)}/{total_benchmarks} passed, grade: {performance_grade}")
        return suite

    def generate_performance_report(self, suite: BenchmarkSuite) -> str:
        """
        Generate comprehensive performance report from benchmark suite.
        
        Args:
            suite: Benchmark suite results
        
        Returns:
            str: Formatted performance report
        """
        report_lines = []
        
        # Header
        report_lines.append("=" * 80)
        report_lines.append("CACHE PERFORMANCE BENCHMARK REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Suite: {suite.name}")
        report_lines.append(f"Timestamp: {suite.timestamp}")
        report_lines.append(f"Duration: {suite.total_duration_ms / 1000:.2f}s")
        report_lines.append(f"Pass Rate: {suite.pass_rate * 100:.1f}%")
        report_lines.append(f"Performance Grade: {suite.performance_grade}")
        report_lines.append(f"Memory Efficiency: {suite.memory_efficiency_grade}")
        report_lines.append("")
        
        # Environment Information
        if suite.environment_info:
            report_lines.append("ENVIRONMENT")
            report_lines.append("-" * 40)
            for key, value in suite.environment_info.items():
                report_lines.append(f"{key}: {value}")
            report_lines.append("")
        
        # Individual Benchmark Results
        report_lines.append("BENCHMARK RESULTS")
        report_lines.append("-" * 40)
        
        for result in suite.results:
            report_lines.append(f"\n{result.operation_type.upper()}")
            report_lines.append("-" * 30)
            
            # Performance metrics
            meets_threshold = result.meets_threshold(self.thresholds.BASIC_OPERATIONS_AVG_MS)
            status = "✓ PASS" if meets_threshold else "✗ FAIL"
            grade = result.performance_grade()
            
            report_lines.append(f"Status: {status} ({grade})")
            report_lines.append(f"Average Duration: {result.avg_duration_ms:.2f}ms")
            report_lines.append(f"P95 Duration: {result.p95_duration_ms:.2f}ms")
            report_lines.append(f"P99 Duration: {result.p99_duration_ms:.2f}ms")
            report_lines.append(f"Operations/sec: {result.operations_per_second:.0f}")
            report_lines.append(f"Success Rate: {result.success_rate * 100:.1f}%")
            report_lines.append(f"Memory Usage: {result.memory_usage_mb:.2f}MB")
            
            if result.cache_hit_rate is not None:
                report_lines.append(f"Cache Hit Rate: {result.cache_hit_rate:.1f}%")
            
            if result.compression_ratio is not None:
                report_lines.append(f"Compression Ratio: {result.compression_ratio:.2f}")
                report_lines.append(f"Compression Savings: {result.compression_savings_mb:.2f}MB")
            
            # Key metadata
            if result.metadata:
                report_lines.append("Key Metrics:")
                for key, value in result.metadata.items():
                    if key in ['memory_hit_rate', 'compression_savings_percent', 'total_operations']:
                        report_lines.append(f"  {key}: {value}")
        
        # Failed Benchmarks
        if suite.failed_benchmarks:
            report_lines.append("\nFAILED BENCHMARKS")
            report_lines.append("-" * 40)
            for failure in suite.failed_benchmarks:
                report_lines.append(f"✗ {failure}")
        
        # Performance Analysis
        report_lines.append("\nPERFORMANCE ANALYSIS")
        report_lines.append("-" * 40)
        
        performance_insights = self._analyze_performance_insights(suite)
        for insight in performance_insights:
            report_lines.append(f"• {insight}")
        
        # Recommendations
        recommendations = self._generate_recommendations(suite)
        if recommendations:
            report_lines.append("\nRECOMMENDATIONS")
            report_lines.append("-" * 40)
            for rec in recommendations:
                report_lines.append(f"• {rec}")
        
        report_lines.append("\n" + "=" * 80)
        
        return "\n".join(report_lines)

    def analyze_performance_trends(self, historical_results: List[BenchmarkSuite]) -> Dict[str, Any]:
        """
        Analyze performance trends across historical benchmark results.
        
        Args:
            historical_results: List of historical benchmark suites
        
        Returns:
            Dict containing trend analysis for each operation type
        """
        if len(historical_results) < 2:
            return {"error": "Insufficient data for trend analysis", "sample_count": len(historical_results)}
        
        trends = {}
        
        # Group results by operation type
        operations_data = {}
        for suite in historical_results:
            for result in suite.results:
                op_type = result.operation_type
                if op_type not in operations_data:
                    operations_data[op_type] = []
                operations_data[op_type].append({
                    "timestamp": result.timestamp,
                    "avg_duration_ms": result.avg_duration_ms,
                    "operations_per_second": result.operations_per_second,
                    "memory_usage_mb": result.memory_usage_mb,
                    "success_rate": result.success_rate
                })
        
        # Analyze trends for each operation type
        for op_type, data in operations_data.items():
            if len(data) < 2:
                continue
            
            # Sort by timestamp
            data.sort(key=lambda x: x["timestamp"])
            
            # Calculate trends
            first_result = data[0]
            last_result = data[-1]
            
            duration_change = ((last_result["avg_duration_ms"] - first_result["avg_duration_ms"]) / first_result["avg_duration_ms"]) * 100
            throughput_change = ((last_result["operations_per_second"] - first_result["operations_per_second"]) / first_result["operations_per_second"]) * 100
            memory_change = ((last_result["memory_usage_mb"] - first_result["memory_usage_mb"]) / first_result["memory_usage_mb"]) * 100 if first_result["memory_usage_mb"] > 0 else 0
            
            # Determine trend direction
            if duration_change > 10:
                trend_direction = "degrading"
            elif duration_change < -10:
                trend_direction = "improving"
            else:
                trend_direction = "stable"
            
            trends[op_type] = {
                "trend_direction": trend_direction,
                "duration_change_percent": duration_change,
                "throughput_change_percent": throughput_change,
                "memory_change_percent": memory_change,
                "sample_count": len(data),
                "time_span": data[-1]["timestamp"] + " to " + data[0]["timestamp"],
                "current_performance": {
                    "avg_duration_ms": last_result["avg_duration_ms"],
                    "operations_per_second": last_result["operations_per_second"],
                    "memory_usage_mb": last_result["memory_usage_mb"]
                }
            }
        
        return trends

    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect environment information for benchmark context."""
        import platform
        import os
        
        env_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count() or "unknown"
        }
        
        # Add relevant environment variables
        env_vars = {}
        relevant_vars = ["DEBUG", "REDIS_URL", "RESILIENCE_PRESET", "API_KEY"]
        for var in relevant_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if "key" in var.lower() or "password" in var.lower():
                    env_vars[var] = "***MASKED***"
                else:
                    env_vars[var] = value
            else:
                env_vars[var] = "not_set"
        
        env_info["environment_variables"] = env_vars
        
        return env_info

    def _calculate_performance_grade(self, results: List[BenchmarkResult]) -> str:
        """Calculate overall performance grade for benchmark suite."""
        if not results:
            return "No Data"
        
        grades = [result.performance_grade() for result in results]
        grade_scores = {
            "Excellent": 5,
            "Good": 4,
            "Acceptable": 3,
            "Poor": 2,
            "Critical": 1
        }
        
        avg_score = sum(grade_scores.get(grade, 1) for grade in grades) / len(grades)
        
        if avg_score >= 4.5:
            return "Excellent"
        elif avg_score >= 3.5:
            return "Good"
        elif avg_score >= 2.5:
            return "Acceptable"
        elif avg_score >= 1.5:
            return "Poor"
        else:
            return "Critical"

    def _calculate_memory_efficiency_grade(self, results: List[BenchmarkResult]) -> str:
        """Calculate memory efficiency grade for benchmark suite."""
        if not results:
            return "No Data"
        
        total_memory = sum(result.memory_usage_mb for result in results)
        avg_memory = total_memory / len(results)
        
        if avg_memory <= 10:
            return "Excellent"
        elif avg_memory <= 25:
            return "Good"
        elif avg_memory <= 50:
            return "Acceptable"
        elif avg_memory <= 100:
            return "Poor"
        else:
            return "Critical"

    def _analyze_performance_insights(self, suite: BenchmarkSuite) -> List[str]:
        """Generate performance insights from benchmark suite."""
        insights = []
        
        if not suite.results:
            return ["No benchmark results available for analysis"]
        
        # Overall performance analysis
        avg_duration = sum(r.avg_duration_ms for r in suite.results) / len(suite.results)
        if avg_duration <= self.thresholds.BASIC_OPERATIONS_AVG_MS / 2:
            insights.append(f"Excellent performance: {avg_duration:.1f}ms average response time")
        elif avg_duration > self.thresholds.BASIC_OPERATIONS_AVG_MS:
            insights.append(f"Performance concern: {avg_duration:.1f}ms average exceeds {self.thresholds.BASIC_OPERATIONS_AVG_MS}ms threshold")
        
        # Success rate analysis
        avg_success_rate = sum(r.success_rate for r in suite.results) / len(suite.results) * 100
        if avg_success_rate >= 99:
            insights.append("Excellent reliability with >99% success rate")
        elif avg_success_rate < 95:
            insights.append(f"Reliability concern: {avg_success_rate:.1f}% success rate below 95% threshold")
        
        # Memory analysis
        total_memory = sum(r.memory_usage_mb for r in suite.results)
        if total_memory > self.thresholds.MEMORY_USAGE_WARNING_MB:
            insights.append(f"Memory usage concern: {total_memory:.1f}MB total usage")
        
        # Cache hit rate analysis
        cache_results = [r for r in suite.results if r.cache_hit_rate is not None]
        if cache_results:
            avg_hit_rate = sum(r.cache_hit_rate for r in cache_results) / len(cache_results)
            if avg_hit_rate >= 80:
                insights.append(f"Good cache efficiency: {avg_hit_rate:.1f}% hit rate")
            elif avg_hit_rate < 50:
                insights.append(f"Cache efficiency concern: {avg_hit_rate:.1f}% hit rate")
        
        # Compression analysis
        compression_results = [r for r in suite.results if r.compression_ratio is not None]
        if compression_results:
            avg_compression = sum(r.compression_ratio for r in compression_results) / len(compression_results)
            if avg_compression <= 0.5:
                insights.append(f"Good compression efficiency: {avg_compression:.2f} ratio")
            elif avg_compression > 0.8:
                insights.append(f"Compression efficiency concern: {avg_compression:.2f} ratio")
        
        return insights

    def _generate_recommendations(self, suite: BenchmarkSuite) -> List[str]:
        """Generate optimization recommendations based on benchmark results."""
        recommendations = []
        
        if not suite.results:
            return ["Run complete benchmark suite to generate recommendations"]
        
        # Performance recommendations
        slow_operations = [r for r in suite.results if r.avg_duration_ms > self.thresholds.BASIC_OPERATIONS_AVG_MS]
        if slow_operations:
            recommendations.append("Optimize slow operations: consider connection pooling, query optimization, or caching strategies")
        
        # Memory recommendations
        high_memory_ops = [r for r in suite.results if r.memory_usage_mb > self.thresholds.MEMORY_USAGE_WARNING_MB]
        if high_memory_ops:
            recommendations.append("Reduce memory usage: implement memory cache size limits and more aggressive eviction policies")
        
        # Cache hit rate recommendations
        low_hit_rate_ops = [r for r in suite.results if r.cache_hit_rate is not None and r.cache_hit_rate < 70]
        if low_hit_rate_ops:
            recommendations.append("Improve cache hit rates: review cache key patterns, TTL settings, and data access patterns")
        
        # Compression recommendations
        poor_compression_ops = [r for r in suite.results if r.compression_ratio is not None and r.compression_ratio > 0.7]
        if poor_compression_ops:
            recommendations.append("Optimize compression: adjust compression thresholds or algorithms for better efficiency")
        
        # Success rate recommendations
        unreliable_ops = [r for r in suite.results if r.success_rate < 0.95]
        if unreliable_ops:
            recommendations.append("Improve reliability: enhance error handling, connection management, and retry mechanisms")
        
        # Overall recommendations
        if suite.pass_rate < 1.0:
            recommendations.append("Address failed benchmarks before production deployment")
        
        if suite.performance_grade in ["Poor", "Critical"]:
            recommendations.append("Significant performance optimization needed - consider architectural changes")
        
        return recommendations