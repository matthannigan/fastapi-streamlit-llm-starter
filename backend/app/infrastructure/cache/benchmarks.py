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
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .base import CacheInterface
from .monitoring import CachePerformanceMonitor

# Import factory and config classes if available
try:
    from .factory import CacheFactory
    FACTORY_AVAILABLE = True
except ImportError:
    FACTORY_AVAILABLE = False
    CacheFactory = None

try:
    from .config import CacheConfigBuilder, EnvironmentPresets
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    CacheConfigBuilder = EnvironmentPresets = None

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
    # Additional statistical fields for Phase 3
    median_duration_ms: float = 0.0
    error_count: int = 0
    test_data_size_bytes: int = 0
    additional_metrics: Dict[str, Any] = field(default_factory=dict)
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
    performance_change_percent: float = 0.0
    memory_change_percent: float = 0.0
    operations_per_second_change: float = 0.0
    baseline_cache_name: str = "Original Cache"
    comparison_cache_name: str = "New Cache"
    operation_comparisons: Dict[str, Dict[str, float]] = field(default_factory=dict)
    overall_performance_change: float = 0.0
    cache_hit_rate_change: Optional[float] = None
    compression_efficiency_change: Optional[float] = None
    regression_detected: bool = False
    significant_differences: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    degradation_areas: List[str] = field(default_factory=list)
    recommendation: str = ""
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
    
    def _generate_test_data_sets(self, test_operations: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """Generate varied test data sets for comprehensive benchmarking."""
        import random
        
        # Small data set (simple key-value pairs)
        small_data = []
        for i in range(min(25, test_operations // 4)):
            small_data.append({
                "key": f"small_key_{i}",
                "text": "Short text for basic testing.",
                "operation": random.choice(self.operation_types),
                "options": {"length": "short"},
                "expected_size_bytes": 30,
                "cache_ttl": 300
            })
        
        # Medium data set (100x repetitions)
        medium_data = []
        for i in range(min(50, test_operations // 2)):
            text = self.text_samples[1] * random.randint(1, 3)
            medium_data.append({
                "key": f"medium_key_{i}",
                "text": text,
                "operation": random.choice(self.operation_types),
                "options": {"length": "medium", "detail_level": "detailed"},
                "expected_size_bytes": len(text.encode('utf-8')),
                "cache_ttl": random.randint(600, 1800)
            })
        
        # Large data set (1000x repetitions with lists)
        large_data = []
        for i in range(min(20, test_operations // 5)):
            base_text = self.text_samples[2]
            text_with_lists = base_text + "\n" + "\n".join([f"Item {j}: {base_text[:50]}" for j in range(random.randint(5, 15))])
            large_data.append({
                "key": f"large_key_{i}",
                "text": text_with_lists,
                "operation": random.choice(self.operation_types),
                "options": {"length": "long", "detail_level": "comprehensive"},
                "expected_size_bytes": len(text_with_lists.encode('utf-8')),
                "cache_ttl": random.randint(1800, 3600)
            })
        
        # JSON data set (complex objects)
        json_data = []
        for i in range(min(30, test_operations // 3)):
            complex_obj = {
                "user_id": random.randint(1, 10000),
                "content": random.choice(self.text_samples),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "tags": [f"tag_{j}" for j in range(random.randint(1, 5))],
                    "scores": {op: random.uniform(0.1, 1.0) for op in self.operation_types}
                },
                "processing_history": [{
                    "operation": random.choice(self.operation_types),
                    "timestamp": datetime.now().isoformat(),
                    "duration_ms": random.randint(10, 500)
                } for _ in range(random.randint(1, 3))]
            }
            json_text = json.dumps(complex_obj)
            json_data.append({
                "key": f"json_key_{i}",
                "text": json_text,
                "operation": "qa",  # More complex operation for JSON data
                "options": {"format": "json", "detail_level": "comprehensive"},
                "expected_size_bytes": len(json_text.encode('utf-8')),
                "cache_ttl": random.randint(900, 2700)
            })
        
        # Realistic data generation using sentence-like patterns
        realistic_data = []
        sentence_templates = [
            "The {adjective} {noun} {verb} {adverb} in the {location}.",
            "During {time_period}, we observed that {subject} {action} {object} with {result}.",
            "Analysis of {data_type} reveals {finding} which {implication} for {domain}."
        ]
        
        vocab = {
            "adjective": ["complex", "efficient", "robust", "scalable", "innovative"],
            "noun": ["system", "algorithm", "process", "framework", "solution"],
            "verb": ["processes", "analyzes", "transforms", "optimizes", "manages"],
            "adverb": ["effectively", "rapidly", "consistently", "accurately", "reliably"],
            "location": ["production environment", "test suite", "cache layer", "data pipeline"],
            "time_period": ["Q1 2024", "the past month", "recent testing", "initial deployment"],
            "subject": ["the cache system", "our algorithm", "the benchmark suite"],
            "action": ["improved performance by", "reduced latency to", "achieved throughput of"],
            "object": ["25% over baseline", "sub-millisecond levels", "1000+ requests/second"],
            "result": ["significant improvements", "optimal efficiency", "enhanced reliability"],
            "data_type": ["performance metrics", "cache statistics", "response times"],
            "finding": ["consistent patterns", "notable improvements", "optimal configurations"],
            "implication": ["suggests optimization opportunities", "indicates successful refactoring"],
            "domain": ["AI applications", "web services", "data processing"]
        }
        
        for i in range(min(25, test_operations // 4)):
            template = random.choice(sentence_templates)
            # Generate varied, sentence-like text
            filled_template = template
            for placeholder, options in vocab.items():
                if f"{{{placeholder}}}" in filled_template:
                    filled_template = filled_template.replace(f"{{{placeholder}}}", random.choice(options))
            
            # Create multiple sentences for more realistic content
            realistic_text = " ".join([filled_template for _ in range(random.randint(2, 5))])
            
            realistic_data.append({
                "key": f"realistic_key_{i}",
                "text": realistic_text,
                "operation": random.choice(self.operation_types),
                "options": {k: random.choice(v) for k, v in self.sample_options.items()},
                "expected_size_bytes": len(realistic_text.encode('utf-8')),
                "cache_ttl": random.randint(300, 3600)
            })
        
        return {
            "small": small_data,
            "medium": medium_data,
            "large": large_data,
            "json": json_data,
            "realistic": realistic_data
        }

    def generate_basic_operations_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate test data for basic cache operations."""
        import random
        
        # Use the new varied data generation but flatten for backward compatibility
        data_sets = self._generate_test_data_sets(count)
        
        # Combine all data sets and shuffle
        all_data = []
        for data_set in data_sets.values():
            all_data.extend(data_set)
        
        random.shuffle(all_data)
        
        # Return the requested count
        return all_data[:count]
    
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
        
        # Add operation_types for backward compatibility
        self.operation_types = ["summarize", "sentiment", "key_points", "questions", "qa"]
        
    async def benchmark_basic_operations(self, cache: CacheInterface, iterations: Optional[int] = None) -> BenchmarkResult:
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
                
                # Test exists operation (if available)
                if hasattr(cache, 'exists'):
                    await cache.exists(data["key"])
                else:
                    _ = result is not None
                
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
        
        # Calculate statistics with enhanced metrics
        if durations:
            avg_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            median_duration = statistics.median(durations)
            std_dev = self._calculate_standard_deviation(durations)
            p95_duration = self._percentile(durations, 95)
            p99_duration = self._percentile(durations, 99)
            
            # Detect outliers
            outlier_analysis = self._detect_outliers(durations)
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(durations)
        else:
            avg_duration = min_duration = max_duration = median_duration = std_dev = p95_duration = p99_duration = 0.0
            outlier_analysis = {"outlier_count": 0}
            confidence_intervals = {"margin_of_error": 0.0}
        
        # Calculate performance metrics
        success_rate = successful_operations / iterations if iterations > 0 else 0.0
        operations_per_second = successful_operations / total_duration if total_duration > 0 else 0.0
        cache_hit_rate = (cache_hits / (cache_hits + cache_misses)) * 100 if (cache_hits + cache_misses) > 0 else None
        
        # Calculate test data size
        total_data_size = sum(len(data["text"].encode('utf-8')) for data in test_data)
        
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
            median_duration_ms=median_duration,
            std_dev_ms=std_dev,
            operations_per_second=operations_per_second,
            success_rate=success_rate,
            memory_usage_mb=peak_memory - initial_memory,
            cache_hit_rate=cache_hit_rate,
            error_count=iterations - successful_operations,
            test_data_size_bytes=total_data_size,
            additional_metrics={
                "outlier_count": outlier_analysis.get("outlier_count", 0),
                "confidence_interval_95": confidence_intervals,
                "data_variety_score": len(set(data["operation"] for data in test_data)) / len(self.operation_types),
                "avg_text_size_bytes": total_data_size / len(test_data) if test_data else 0
            },
            metadata={
                "total_operations": iterations,
                "successful_operations": successful_operations,
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "warmup_iterations": self.warmup_iterations,
                "outlier_analysis": outlier_analysis,
                "statistical_confidence": "95%" if len(durations) >= 30 else "estimated"
            }
        )
        
        logger.info(f"Basic operations benchmark completed: {avg_duration:.2f}ms avg, {operations_per_second:.0f} ops/sec")
        return result

    async def benchmark_memory_cache_performance(self, cache, iterations: Optional[int] = None) -> BenchmarkResult:
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

    async def benchmark_compression_efficiency(self, cache, iterations: Optional[int] = None) -> BenchmarkResult:
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
        iterations = iterations or max(1, self.default_iterations // 2)  # Fewer iterations for compression testing
        
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
                            except Exception:
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
                                             test_iterations: Optional[int] = None) -> ComparisonResult:
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
            # Ensure both caches are in clean state (if clear method is available)
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
            
            # Create detailed operation comparisons
            operation_comparisons = {
                "avg_duration": {
                    "baseline_ms": original_result.avg_duration_ms,
                    "comparison_ms": new_result.avg_duration_ms,
                    "change_percent": performance_change
                },
                "throughput": {
                    "baseline_ops_sec": original_result.operations_per_second,
                    "comparison_ops_sec": new_result.operations_per_second,
                    "change_percent": ops_change
                },
                "memory_usage": {
                    "baseline_mb": original_result.memory_usage_mb,
                    "comparison_mb": new_result.memory_usage_mb,
                    "change_percent": memory_change
                }
            }
            
            # Determine overall performance change
            overall_change = (performance_change + (-ops_change) + memory_change) / 3  # Average of key metrics
            
            # Identify significant differences
            significant_differences = []
            if abs(performance_change) > 15:
                significant_differences.append(f"Response time changed by {performance_change:+.1f}%")
            if abs(ops_change) > 15:
                significant_differences.append(f"Throughput changed by {ops_change:+.1f}%")
            if abs(memory_change) > 25:
                significant_differences.append(f"Memory usage changed by {memory_change:+.1f}%")
            
            # Generate primary recommendation
            if regression_detected:
                recommendation = "Performance regression detected - investigate before deployment"
            elif overall_change < -10:
                recommendation = "Significant performance improvement - deploy with confidence"
            elif overall_change > 10:
                recommendation = "Performance degradation detected - optimization needed"
            else:
                recommendation = "Performance characteristics are similar - refactoring successful"
            
            comparison_result = ComparisonResult(
                baseline_cache_name=getattr(original_cache.__class__, '__name__', 'Original Cache'),
                comparison_cache_name=getattr(new_cache.__class__, '__name__', 'New Cache'),
                original_cache_results=original_result,
                new_cache_results=new_result,
                operation_comparisons=operation_comparisons,
                overall_performance_change=overall_change,
                performance_change_percent=performance_change,
                memory_change_percent=memory_change,
                operations_per_second_change=ops_change,
                cache_hit_rate_change=hit_rate_change,
                regression_detected=regression_detected,
                significant_differences=significant_differences,
                improvement_areas=improvement_areas,
                degradation_areas=degradation_areas,
                recommendation=recommendation,
                recommendations=recommendations
            )
            
            logger.info(f"Cache comparison completed: {performance_change:+.1f}% performance change, regression: {regression_detected}")
            return comparison_result
            
        except Exception as e:
            logger.error(f"Cache comparison failed: {e}")
            raise

    async def compare_caches(self, caches: Dict[str, CacheInterface], test_iterations: Optional[int] = None) -> Dict[str, Any]:
        """
        Compare performance between multiple cache implementations.
        
        This method runs identical benchmarks on all provided cache implementations
        and provides a comprehensive comparison matrix with performance rankings.
        
        Args:
            caches: Dictionary of cache name -> cache implementation
            test_iterations: Number of test iterations for comparison (default: 100)
        
        Returns:
            Dict containing comparison matrix, rankings, and recommendations
        """
        test_iterations = test_iterations or self.default_iterations
        
        if len(caches) < 2:
            raise ValueError("Need at least 2 caches for comparison")
        
        logger.info(f"Starting multi-cache comparison with {len(caches)} caches, {test_iterations} iterations each")
        
        # Benchmark all caches
        cache_results = {}
        
        for cache_name, cache in caches.items():
            try:
                logger.info(f"Benchmarking {cache_name}...")
                
                # Ensure cache is in clean state (if clear method is available)
                if hasattr(cache, 'clear'):
                    await cache.clear()
                
                result = await self.benchmark_basic_operations(cache, test_iterations)
                cache_results[cache_name] = result
                
                # Wait between benchmarks to avoid interference
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Benchmarking {cache_name} failed: {e}")
                continue
        
        if len(cache_results) < 2:
            raise RuntimeError("Not enough successful cache benchmarks for comparison")
        
        # Create comparison matrix
        comparison_matrix = {}
        
        for metric in ["avg_duration_ms", "operations_per_second", "memory_usage_mb", "success_rate"]:
            comparison_matrix[metric] = {}
            
            for cache_name, result in cache_results.items():
                comparison_matrix[metric][cache_name] = getattr(result, metric)
        
        # Calculate performance rankings
        rankings = {
            "fastest_response": min(cache_results.items(), key=lambda x: x[1].avg_duration_ms),
            "highest_throughput": max(cache_results.items(), key=lambda x: x[1].operations_per_second),
            "most_memory_efficient": min(cache_results.items(), key=lambda x: x[1].memory_usage_mb),
            "most_reliable": max(cache_results.items(), key=lambda x: x[1].success_rate)
        }
        
        # Calculate relative performance scores
        baseline_name, baseline_result = min(cache_results.items(), key=lambda x: x[1].avg_duration_ms)
        
        relative_performance = {}
        for cache_name, result in cache_results.items():
            score = 0
            
            # Response time score (lower is better)
            response_ratio = baseline_result.avg_duration_ms / result.avg_duration_ms
            score += response_ratio * 40  # 40% weight
            
            # Throughput score (higher is better) 
            throughput_ratio = result.operations_per_second / baseline_result.operations_per_second
            score += throughput_ratio * 30  # 30% weight
            
            # Memory efficiency score (lower is better)
            if baseline_result.memory_usage_mb > 0:
                memory_ratio = baseline_result.memory_usage_mb / max(result.memory_usage_mb, 0.1)
                score += memory_ratio * 20  # 20% weight
            else:
                score += 20  # Full score if no memory usage
            
            # Reliability score
            reliability_ratio = result.success_rate / baseline_result.success_rate
            score += reliability_ratio * 10  # 10% weight
            
            relative_performance[cache_name] = {
                "overall_score": score,
                "response_time_vs_fastest": (result.avg_duration_ms / baseline_result.avg_duration_ms - 1) * 100,
                "throughput_vs_fastest": (result.operations_per_second / baseline_result.operations_per_second - 1) * 100
            }
        
        # Generate recommendations
        recommendations = []
        
        # Best overall performer
        best_overall = max(relative_performance.items(), key=lambda x: x[1]["overall_score"])
        recommendations.append(f"Best overall performance: {best_overall[0]} (score: {best_overall[1]['overall_score']:.1f})")
        
        # Specific use case recommendations
        if rankings["fastest_response"][0] != rankings["highest_throughput"][0]:
            recommendations.append(
                f"For low latency: use {rankings['fastest_response'][0]} "
                f"({rankings['fastest_response'][1].avg_duration_ms:.2f}ms avg)"
            )
            recommendations.append(
                f"For high throughput: use {rankings['highest_throughput'][0]} "
                f"({rankings['highest_throughput'][1].operations_per_second:.0f} ops/sec)"
            )
        
        # Memory efficiency recommendation
        if rankings["most_memory_efficient"][1].memory_usage_mb < 10:
            recommendations.append(
                f"For memory-constrained environments: use {rankings['most_memory_efficient'][0]} "
                f"({rankings['most_memory_efficient'][1].memory_usage_mb:.2f}MB)"
            )
        
        # Detect significant performance differences
        performance_spread = max(r.avg_duration_ms for r in cache_results.values()) / min(r.avg_duration_ms for r in cache_results.values())
        if performance_spread > 2:
            recommendations.append(f"Significant performance variation detected (spread: {performance_spread:.1f}x) - choose carefully")
        
        return {
            "cache_results": {name: result.to_dict() for name, result in cache_results.items()},
            "comparison_matrix": comparison_matrix,
            "rankings": {
                k: {"cache_name": v[0], "value": getattr(v[1], k.split("_")[-1] if "_" in k else "avg_duration_ms")}
                for k, v in rankings.items()
            },
            "relative_performance": relative_performance,
            "recommendations": recommendations,
            "baseline_cache": baseline_name,
            "test_config": {
                "iterations_per_cache": test_iterations,
                "caches_tested": list(caches.keys()),
                "total_operations": test_iterations * len(caches)
            }
        }

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile for a list of values."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (percentile / 100.0)
        f = int(k)
        c = k - f
        
        if f == len(sorted_data) - 1:
            return sorted_data[f]
        else:
            return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get comprehensive memory usage information."""
        memory_info = {"process_mb": 0.0, "available_mb": 0.0, "total_mb": 0.0}
        
        try:
            import psutil
            
            # Process memory
            process = psutil.Process()
            memory_info["process_mb"] = process.memory_info().rss / 1024 / 1024
            
            # System memory
            vm = psutil.virtual_memory()
            memory_info["available_mb"] = vm.available / 1024 / 1024
            memory_info["total_mb"] = vm.total / 1024 / 1024
            memory_info["percent_used"] = vm.percent
            
        except ImportError:
            # Fallback for process memory only
            memory_info["process_mb"] = self._get_process_memory_mb()
        except Exception as e:
            logger.debug(f"Could not get comprehensive memory usage: {e}")
        
        return memory_info
    
    def _calculate_standard_deviation(self, data: List[float]) -> float:
        """Calculate standard deviation with outlier detection."""
        if len(data) < 2:
            return 0.0
        
        try:
            return statistics.stdev(data)
        except statistics.StatisticsError:
            return 0.0
    
    def _detect_outliers(self, data: List[float]) -> Dict[str, Any]:
        """Detect outliers using IQR method."""
        if len(data) < 4:
            return {"outliers": [], "outlier_count": 0, "clean_data": data}
        
        sorted_data = sorted(data)
        q1 = self._percentile(sorted_data, 25)
        q3 = self._percentile(sorted_data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = [x for x in data if x < lower_bound or x > upper_bound]
        clean_data = [x for x in data if lower_bound <= x <= upper_bound]
        
        return {
            "outliers": outliers,
            "outlier_count": len(outliers),
            "clean_data": clean_data,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "iqr": iqr
        }
    
    def _calculate_confidence_intervals(self, data: List[float], confidence: float = 0.95) -> Dict[str, float]:
        """Calculate confidence intervals for mean."""
        if len(data) < 2:
            return {"lower": 0.0, "upper": 0.0, "margin_of_error": 0.0}
        
        try:
            import math
            
            mean = statistics.mean(data)
            stdev = statistics.stdev(data)
            n = len(data)
            
            # Use t-distribution for small samples, normal for large
            if n >= 30:
                # Normal distribution (z-score)
                z_score = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
                margin_of_error = z_score * (stdev / math.sqrt(n))
            else:
                # t-distribution (simplified - using approximation)
                t_score = 2.0 + (0.3 / n)  # Rough approximation for small samples
                margin_of_error = t_score * (stdev / math.sqrt(n))
            
            return {
                "lower": mean - margin_of_error,
                "upper": mean + margin_of_error,
                "margin_of_error": margin_of_error
            }
        except Exception as e:
            logger.debug(f"Could not calculate confidence intervals: {e}")
            return {"lower": 0.0, "upper": 0.0, "margin_of_error": 0.0}

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

    async def benchmark_factory_creation(self, iterations: int = 50) -> BenchmarkResult:
        """
        Benchmark factory method performance for cache creation.
        
        Tests the performance of different CacheFactory methods to ensure
        factory overhead is minimal and creation times are acceptable.
        
        Args:
            iterations: Number of cache creation iterations per factory method
        
        Returns:
            BenchmarkResult: Factory creation performance metrics
        """
        logger.info(f"Starting factory creation benchmark with {iterations} iterations per method")
        
        # Create factory instance
        factory = CacheFactory()
        
        # Track memory usage
        initial_memory = self._get_process_memory_mb()
        peak_memory = initial_memory
        
        # Performance tracking
        durations = []
        successful_operations = 0
        factory_methods_tested = []
        
        start_time = time.time()
        
        # Test for_web_app() factory performance
        logger.debug("Testing for_web_app() factory method...")
        for i in range(iterations):
            operation_start = time.perf_counter()
            
            try:
                if factory:
                    cache = await factory.for_web_app(
                        fail_on_connection_error=False
                    )
                else:
                    raise AttributeError("CacheFactory not available")
                
                operation_end = time.perf_counter()
                operation_duration = (operation_end - operation_start) * 1000
                durations.append(operation_duration)
                successful_operations += 1
                
                # Clean up
                if hasattr(cache, 'disconnect'):
                    await cache.disconnect()
                
                # Track memory usage
                current_memory = self._get_process_memory_mb()
                peak_memory = max(peak_memory, current_memory)
                
            except Exception as e:
                logger.warning(f"for_web_app() creation {i} failed: {e}")
                operation_end = time.perf_counter()
                durations.append((operation_end - operation_start) * 1000)
        
        factory_methods_tested.append("for_web_app")
        
        # Test for_ai_app() factory performance
        logger.debug("Testing for_ai_app() factory method...")
        for i in range(iterations):
            operation_start = time.perf_counter()
            
            try:
                if factory:
                    cache = await factory.for_ai_app(
                        fail_on_connection_error=False
                    )
                else:
                    raise AttributeError("CacheFactory not available")
                
                operation_end = time.perf_counter()
                operation_duration = (operation_end - operation_start) * 1000
                durations.append(operation_duration)
                successful_operations += 1
                
                # Clean up
                if hasattr(cache, 'disconnect'):
                    await cache.disconnect()
                
                # Track memory usage
                current_memory = self._get_process_memory_mb()
                peak_memory = max(peak_memory, current_memory)
                
            except Exception as e:
                logger.warning(f"for_ai_app() creation {i} failed: {e}")
                operation_end = time.perf_counter()
                durations.append((operation_end - operation_start) * 1000)
        
        factory_methods_tested.append("for_ai_app")
        
        # Test for_testing() factory performance
        logger.debug("Testing for_testing() factory method...")
        for i in range(iterations):
            operation_start = time.perf_counter()
            
            try:
                if factory:
                    cache = await factory.for_testing(use_memory_cache=True)
                else:
                    raise AttributeError("CacheFactory not available")
                
                operation_end = time.perf_counter()
                operation_duration = (operation_end - operation_start) * 1000
                durations.append(operation_duration)
                successful_operations += 1
                
                # Clean up
                if hasattr(cache, 'disconnect'):
                    await cache.disconnect()
                
                # Track memory usage
                current_memory = self._get_process_memory_mb()
                peak_memory = max(peak_memory, current_memory)
                
            except Exception as e:
                logger.warning(f"for_testing() creation {i} failed: {e}")
                operation_end = time.perf_counter()
                durations.append((operation_end - operation_start) * 1000)
        
        factory_methods_tested.append("for_testing")
        
        # Test create_cache_from_config() factory performance
        logger.debug("Testing create_cache_from_config() factory method...")
        for i in range(iterations):
            operation_start = time.perf_counter()
            
            try:
                # Create a simple config for testing
                if CacheConfigBuilder and factory:
                    config = CacheConfigBuilder().for_environment("testing").build()
                    cache = await factory.create_cache_from_config(
                        config.to_dict(),
                        fail_on_connection_error=False
                    )
                else:
                    raise AttributeError("Config or Factory classes not available")
                
                operation_end = time.perf_counter()
                operation_duration = (operation_end - operation_start) * 1000
                durations.append(operation_duration)
                successful_operations += 1
                
                # Clean up
                if hasattr(cache, 'disconnect'):
                    await cache.disconnect()
                
                # Track memory usage
                current_memory = self._get_process_memory_mb()
                peak_memory = max(peak_memory, current_memory)
                
            except Exception as e:
                logger.warning(f"create_cache_from_config() creation {i} failed: {e}")
                operation_end = time.perf_counter()
                durations.append((operation_end - operation_start) * 1000)
        
        factory_methods_tested.append("create_cache_from_config")
        
        total_duration = time.time() - start_time
        
        # Calculate statistics
        if durations:
            avg_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            median_duration = statistics.median(durations)
            std_dev = self._calculate_standard_deviation(durations)
            p95_duration = self._percentile(durations, 95)
            p99_duration = self._percentile(durations, 99)
        else:
            avg_duration = min_duration = max_duration = median_duration = std_dev = p95_duration = p99_duration = 0.0
        
        # Calculate performance metrics
        total_iterations = iterations * len(factory_methods_tested)
        success_rate = successful_operations / total_iterations if total_iterations > 0 else 0.0
        operations_per_second = successful_operations / total_duration if total_duration > 0 else 0.0
        
        result = BenchmarkResult(
            operation_type="factory_creation",
            duration_ms=total_duration * 1000,
            memory_peak_mb=peak_memory,
            iterations=total_iterations,
            avg_duration_ms=avg_duration,
            min_duration_ms=min_duration,
            max_duration_ms=max_duration,
            p95_duration_ms=p95_duration,
            p99_duration_ms=p99_duration,
            median_duration_ms=median_duration,
            std_dev_ms=std_dev,
            operations_per_second=operations_per_second,
            success_rate=success_rate,
            memory_usage_mb=peak_memory - initial_memory,
            error_count=total_iterations - successful_operations,
            test_data_size_bytes=0,  # No data size for factory creation
            additional_metrics={
                "factory_methods_tested": factory_methods_tested,
                "iterations_per_method": iterations,
                "creation_overhead_acceptable": avg_duration < 10.0  # Less than 10ms is acceptable
            },
            metadata={
                "factory_methods": factory_methods_tested,
                "successful_operations": successful_operations,
                "total_iterations": total_iterations,
                "avg_creation_time_per_method": avg_duration
            }
        )
        
        logger.info(f"Factory creation benchmark completed: {avg_duration:.2f}ms avg creation time")
        return result

    async def run_environment_benchmarks(self, test_iterations: int = 50) -> Dict[str, BenchmarkResult]:
        """
        Run benchmarks across different environment configurations.
        
        Tests cache performance using different environment presets to validate
        configuration impact on performance and help with environment tuning.
        
        Args:
            test_iterations: Number of iterations for each environment test
        
        Returns:
            Dict[str, BenchmarkResult]: Environment-specific benchmark results
        """
        logger.info(f"Starting environment benchmarks with {test_iterations} iterations each")
        
        # Create factory instance
        factory = CacheFactory()
        
        environment_results = {}
        
        # Test development environment
        try:
            logger.info("Testing development environment configuration...")
            if EnvironmentPresets and factory:
                dev_config = EnvironmentPresets.development()
                dev_cache = await factory.create_cache_from_config(dev_config.to_dict(), fail_on_connection_error=False)
            else:
                raise AttributeError("EnvironmentPresets or CacheFactory not available")
            
            dev_result = await self.benchmark_basic_operations(dev_cache, test_iterations)
            dev_result.operation_type = "development_environment"
            dev_result.metadata.update({
                "environment": "development",
                "preset_used": "EnvironmentPresets.development()",
                "config_summary": {
                    "default_ttl": dev_config.default_ttl,
                    "memory_cache_size": dev_config.memory_cache_size,
                    "compression_threshold": dev_config.compression_threshold
                }
            })
            environment_results["development"] = dev_result
            
            # Clean up
            if hasattr(dev_cache, 'disconnect'):
                await dev_cache.disconnect()
            
        except Exception as e:
            logger.error(f"Development environment benchmark failed: {e}")
        
        # Test testing environment
        try:
            logger.info("Testing testing environment configuration...")
            if EnvironmentPresets and factory:
                test_config = EnvironmentPresets.testing()
                test_cache = await factory.create_cache_from_config(test_config.to_dict(), fail_on_connection_error=False)
            else:
                raise AttributeError("EnvironmentPresets or CacheFactory not available")
            
            test_result = await self.benchmark_basic_operations(test_cache, test_iterations)
            test_result.operation_type = "testing_environment"
            test_result.metadata.update({
                "environment": "testing",
                "preset_used": "EnvironmentPresets.testing()",
                "config_summary": {
                    "default_ttl": test_config.default_ttl,
                    "memory_cache_size": test_config.memory_cache_size,
                    "compression_threshold": test_config.compression_threshold
                }
            })
            environment_results["testing"] = test_result
            
            # Clean up
            if hasattr(test_cache, 'disconnect'):
                await test_cache.disconnect()
            
        except Exception as e:
            logger.error(f"Testing environment benchmark failed: {e}")
        
        # Test production environment
        try:
            logger.info("Testing production environment configuration...")
            if EnvironmentPresets and factory:
                prod_config = EnvironmentPresets.production()
                prod_cache = await factory.create_cache_from_config(prod_config.to_dict(), fail_on_connection_error=False)
            else:
                raise AttributeError("EnvironmentPresets or CacheFactory not available")
            
            prod_result = await self.benchmark_basic_operations(prod_cache, test_iterations)
            prod_result.operation_type = "production_environment"
            prod_result.metadata.update({
                "environment": "production",
                "preset_used": "EnvironmentPresets.production()",
                "config_summary": {
                    "default_ttl": prod_config.default_ttl,
                    "memory_cache_size": prod_config.memory_cache_size,
                    "compression_threshold": prod_config.compression_threshold
                }
            })
            environment_results["production"] = prod_result
            
            # Clean up
            if hasattr(prod_cache, 'disconnect'):
                await prod_cache.disconnect()
            
        except Exception as e:
            logger.error(f"Production environment benchmark failed: {e}")
        
        # Test AI development environment
        try:
            logger.info("Testing AI development environment configuration...")
            if EnvironmentPresets and factory:
                ai_dev_config = EnvironmentPresets.ai_development()
                ai_dev_cache = await factory.create_cache_from_config(ai_dev_config.to_dict(), fail_on_connection_error=False)
            else:
                raise AttributeError("EnvironmentPresets or CacheFactory not available")
            
            ai_dev_result = await self.benchmark_basic_operations(ai_dev_cache, test_iterations)
            ai_dev_result.operation_type = "ai_development_environment"
            ai_dev_result.metadata.update({
                "environment": "ai_development",
                "preset_used": "EnvironmentPresets.ai_development()",
                "has_ai_config": ai_dev_config.ai_config is not None,
                "config_summary": {
                    "default_ttl": ai_dev_config.default_ttl,
                    "memory_cache_size": ai_dev_config.memory_cache_size,
                    "compression_threshold": ai_dev_config.compression_threshold
                }
            })
            environment_results["ai_development"] = ai_dev_result
            
            # Clean up
            if hasattr(ai_dev_cache, 'disconnect'):
                await ai_dev_cache.disconnect()
            
        except Exception as e:
            logger.error(f"AI development environment benchmark failed: {e}")
        
        # Test AI production environment
        try:
            logger.info("Testing AI production environment configuration...")
            if EnvironmentPresets and factory:
                ai_prod_config = EnvironmentPresets.ai_production()
                ai_prod_cache = await factory.create_cache_from_config(ai_prod_config.to_dict(), fail_on_connection_error=False)
            else:
                raise AttributeError("EnvironmentPresets or CacheFactory not available")
            
            ai_prod_result = await self.benchmark_basic_operations(ai_prod_cache, test_iterations)
            ai_prod_result.operation_type = "ai_production_environment"
            ai_prod_result.metadata.update({
                "environment": "ai_production",
                "preset_used": "EnvironmentPresets.ai_production()",
                "has_ai_config": ai_prod_config.ai_config is not None,
                "config_summary": {
                    "default_ttl": ai_prod_config.default_ttl,
                    "memory_cache_size": ai_prod_config.memory_cache_size,
                    "compression_threshold": ai_prod_config.compression_threshold
                }
            })
            environment_results["ai_production"] = ai_prod_result
            
            # Clean up
            if hasattr(ai_prod_cache, 'disconnect'):
                await ai_prod_cache.disconnect()
            
        except Exception as e:
            logger.error(f"AI production environment benchmark failed: {e}")
        
        logger.info(f"Environment benchmarks completed: {len(environment_results)} environments tested")
        return environment_results

    def compare_environment_performance(self, environment_results: Dict[str, BenchmarkResult]) -> Dict[str, Any]:
        """
        Compare performance across different environment configurations.
        
        Args:
            environment_results: Results from run_environment_benchmarks()
        
        Returns:
            Dict containing environment performance comparison and recommendations
        """
        if len(environment_results) < 2:
            return {"error": "Need at least 2 environment results for comparison"}
        
        # Find best and worst performing environments
        best_env = min(environment_results.items(), key=lambda x: x[1].avg_duration_ms)
        worst_env = max(environment_results.items(), key=lambda x: x[1].avg_duration_ms)
        
        # Calculate relative performance
        performance_comparison = {}
        baseline = best_env[1].avg_duration_ms
        
        for env_name, result in environment_results.items():
            performance_comparison[env_name] = {
                "avg_duration_ms": result.avg_duration_ms,
                "relative_performance": ((result.avg_duration_ms - baseline) / baseline) * 100 if baseline > 0 else 0,
                "operations_per_second": result.operations_per_second,
                "memory_usage_mb": result.memory_usage_mb,
                "success_rate": result.success_rate
            }
        
        # Generate recommendations
        recommendations = []
        
        if best_env[0] in ["production", "ai_production"]:
            recommendations.append(f"Production environment ({best_env[0]}) shows optimal performance - good configuration")
        else:
            recommendations.append(f"Consider adopting {best_env[0]} configuration settings for better performance")
        
        if worst_env[1].avg_duration_ms > best_env[1].avg_duration_ms * 2:
            recommendations.append(f"{worst_env[0]} environment shows significant performance degradation - review configuration")
        
        # Check for memory efficiency
        memory_efficient = min(environment_results.items(), key=lambda x: x[1].memory_usage_mb)
        if memory_efficient[1].memory_usage_mb < 10:
            recommendations.append(f"{memory_efficient[0]} environment is most memory efficient")
        
        return {
            "best_performance": {
                "environment": best_env[0],
                "avg_duration_ms": best_env[1].avg_duration_ms,
                "operations_per_second": best_env[1].operations_per_second
            },
            "worst_performance": {
                "environment": worst_env[0],
                "avg_duration_ms": worst_env[1].avg_duration_ms,
                "operations_per_second": worst_env[1].operations_per_second
            },
            "performance_comparison": performance_comparison,
            "recommendations": recommendations
        }

    def generate_report(self, results: Union[BenchmarkResult, BenchmarkSuite, List[BenchmarkResult]]) -> str:
        """
        Generate comprehensive performance report from benchmark results.
        
        Args:
            results: Single result, suite, or list of results to report on
        
        Returns:
            str: Formatted performance report with charts data and recommendations
        """
        if isinstance(results, BenchmarkResult):
            return self._generate_single_result_report(results)
        elif isinstance(results, BenchmarkSuite):
            return self.generate_performance_report(results)
        elif isinstance(results, list):
            return self._generate_multi_result_report(results)
        else:
            return "Invalid results type for report generation"
    
    def _generate_single_result_report(self, result: BenchmarkResult) -> str:
        """Generate report for a single benchmark result."""
        report_lines = []
        
        report_lines.append("=" * 60)
        report_lines.append(f"SINGLE BENCHMARK REPORT: {result.operation_type.upper()}")
        report_lines.append("=" * 60)
        report_lines.append(f"Timestamp: {result.timestamp}")
        report_lines.append(f"Performance Grade: {result.performance_grade()}")
        report_lines.append("")
        
        # Core metrics
        report_lines.append("CORE METRICS")
        report_lines.append("-" * 30)
        report_lines.append(f"Average Duration: {result.avg_duration_ms:.2f}ms")
        report_lines.append(f"Median Duration: {result.median_duration_ms:.2f}ms")
        report_lines.append(f"P95 Duration: {result.p95_duration_ms:.2f}ms")
        report_lines.append(f"P99 Duration: {result.p99_duration_ms:.2f}ms")
        report_lines.append(f"Operations/sec: {result.operations_per_second:.0f}")
        report_lines.append(f"Success Rate: {result.success_rate * 100:.1f}%")
        report_lines.append(f"Memory Usage: {result.memory_usage_mb:.2f}MB")
        
        if result.error_count > 0:
            report_lines.append(f"Errors: {result.error_count}")
        
        if result.cache_hit_rate is not None:
            report_lines.append(f"Cache Hit Rate: {result.cache_hit_rate:.1f}%")
        
        # Additional metrics
        if result.additional_metrics:
            report_lines.append("\nADDITIONAL METRICS")
            report_lines.append("-" * 30)
            for key, value in result.additional_metrics.items():
                report_lines.append(f"{key}: {value}")
        
        report_lines.append("\n" + "=" * 60)
        
        return "\n".join(report_lines)
    
    def _generate_multi_result_report(self, results: List[BenchmarkResult]) -> str:
        """Generate comparative report for multiple benchmark results."""
        report_lines = []
        
        report_lines.append("=" * 80)
        report_lines.append("MULTI-BENCHMARK COMPARISON REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Number of Benchmarks: {len(results)}")
        report_lines.append("")
        
        # Summary table
        report_lines.append("PERFORMANCE SUMMARY")
        report_lines.append("-" * 80)
        report_lines.append(f"{'Operation':<25} {'Avg Duration':<15} {'Ops/Sec':<12} {'Success Rate':<12} {'Grade':<10}")
        report_lines.append("-" * 80)
        
        for result in results:
            report_lines.append(
                f"{result.operation_type:<25} "
                f"{result.avg_duration_ms:<15.2f} "
                f"{result.operations_per_second:<12.0f} "
                f"{result.success_rate * 100:<12.1f}% "
                f"{result.performance_grade():<10}"
            )
        
        # Best and worst performers
        best = min(results, key=lambda x: x.avg_duration_ms)
        worst = max(results, key=lambda x: x.avg_duration_ms)
        
        report_lines.append("\nPERFORMANCE HIGHLIGHTS")
        report_lines.append("-" * 40)
        report_lines.append(f"Best Performance: {best.operation_type} ({best.avg_duration_ms:.2f}ms)")
        report_lines.append(f"Worst Performance: {worst.operation_type} ({worst.avg_duration_ms:.2f}ms)")
        
        # Overall statistics
        valid_durations = [r.avg_duration_ms for r in results if r.avg_duration_ms is not None]
        valid_ops = [r.operations_per_second for r in results if r.operations_per_second is not None]
        valid_rates = [r.success_rate for r in results if r.success_rate is not None]
        
        avg_duration = sum(valid_durations) / len(valid_durations) if valid_durations else 0.0
        avg_ops_per_sec = sum(valid_ops) / len(valid_ops) if valid_ops else 0.0
        avg_success_rate = (sum(valid_rates) / len(valid_rates) * 100) if valid_rates else 0.0
        
        report_lines.append("\nOVERALL AVERAGES")
        report_lines.append("-" * 40)
        report_lines.append(f"Average Duration: {avg_duration:.2f}ms")
        report_lines.append(f"Average Throughput: {avg_ops_per_sec:.0f} ops/sec")
        report_lines.append(f"Average Success Rate: {avg_success_rate:.1f}%")
        
        report_lines.append("\n" + "=" * 80)
        
        return "\n".join(report_lines)

    def save_results_to_file(self, results: Union[BenchmarkResult, BenchmarkSuite], filename: str) -> None:
        """Save benchmark results to JSON file."""
        try:
            import os
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Convert to dict for serialization
            if isinstance(results, BenchmarkSuite):
                data = results.to_dict() if hasattr(results, 'to_dict') else asdict(results)
            else:
                data = results.to_dict() if hasattr(results, 'to_dict') else asdict(results)
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Benchmark results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save results to {filename}: {e}")

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

    def create_benchmark_ci_workflow(self) -> Dict[str, Any]:
        """
        Generate CI/CD workflow configuration for automated benchmarking.
        
        Returns:
            Dict containing workflow configuration and performance thresholds
        """
        workflow_config = {
            "name": "Cache Performance Benchmarks",
            "triggers": [
                "pull_request",
                "push_to_main",
                "schedule_nightly"
            ],
            "jobs": {
                "benchmark_cache_performance": {
                    "steps": [
                        "checkout_code",
                        "setup_python",
                        "install_dependencies", 
                        "setup_redis_test_instance",
                        "run_benchmark_suite",
                        "analyze_performance_regression",
                        "upload_benchmark_artifacts",
                        "post_performance_summary"
                    ],
                    "performance_thresholds": {
                        "max_avg_duration_ms": self.thresholds.BASIC_OPERATIONS_AVG_MS,
                        "min_operations_per_second": 100,
                        "max_memory_usage_mb": self.thresholds.MEMORY_USAGE_WARNING_MB,
                        "min_success_rate_percent": self.thresholds.SUCCESS_RATE_WARNING,
                        "max_regression_percent": self.thresholds.REGRESSION_WARNING_PERCENT
                    },
                    "benchmark_commands": [
                        "python -m pytest tests/infrastructure/cache/test_benchmarks.py::test_ci_benchmark_suite -v",
                        "python -c 'from app.infrastructure.cache.benchmarks import CachePerformanceBenchmark; import asyncio; asyncio.run(CachePerformanceBenchmark().run_ci_benchmark_suite())'"
                    ]
                }
            },
            "artifacts": {
                "benchmark_results": "benchmark_results.json",
                "performance_report": "performance_report.md",
                "performance_charts": "performance_charts/"
            },
            "notifications": {
                "on_regression": "team_channel",
                "on_improvement": "team_channel",
                "on_failure": "oncall_engineer"
            }
        }
        
        return workflow_config

    async def run_ci_benchmark_suite(self) -> Dict[str, Any]:
        """
        Run optimized benchmark suite for CI/CD environments.
        
        This method runs a subset of benchmarks optimized for CI execution time
        while still providing meaningful performance validation.
        
        Returns:
            Dict containing CI-specific benchmark results and pass/fail status
        """
        logger.info("Starting CI benchmark suite (optimized for speed)")
        
        # Create factory instance
        factory = CacheFactory()
        
        ci_results = {
            "overall_status": "PASS",
            "benchmark_results": {},
            "performance_checks": {},
            "recommendations": [],
            "execution_time_seconds": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        try:
            # 1. Quick factory creation benchmark
            logger.info("Running factory creation benchmark...")
            factory_result = await self.benchmark_factory_creation(iterations=10)  # Reduced for CI
            ci_results["benchmark_results"]["factory_creation"] = factory_result.to_dict()
            
            # Check factory creation threshold
            if factory_result.avg_duration_ms > 10.0:  # 10ms threshold for CI
                ci_results["performance_checks"]["factory_creation"] = "FAIL"
                ci_results["overall_status"] = "FAIL"
                ci_results["recommendations"].append("Factory creation is too slow for production use")
            else:
                ci_results["performance_checks"]["factory_creation"] = "PASS"
            
            # 2. Quick basic operations test
            logger.info("Running basic operations benchmark...")
            if FACTORY_AVAILABLE and factory:
                test_cache = await factory.for_testing(use_memory_cache=True)
            else:
                from .memory import InMemoryCache
                test_cache = InMemoryCache(default_ttl=60, max_size=100)
            basic_result = await self.benchmark_basic_operations(test_cache, iterations=25)  # Reduced for CI
            ci_results["benchmark_results"]["basic_operations"] = basic_result.to_dict()
            
            # Check basic operations thresholds
            if basic_result.avg_duration_ms > self.thresholds.BASIC_OPERATIONS_AVG_MS:
                ci_results["performance_checks"]["basic_operations_speed"] = "FAIL"
                ci_results["overall_status"] = "FAIL"
                ci_results["recommendations"].append(f"Basic operations exceed {self.thresholds.BASIC_OPERATIONS_AVG_MS}ms threshold")
            else:
                ci_results["performance_checks"]["basic_operations_speed"] = "PASS"
            
            if basic_result.success_rate < 0.95:
                ci_results["performance_checks"]["basic_operations_reliability"] = "FAIL"
                ci_results["overall_status"] = "FAIL"
                ci_results["recommendations"].append("Basic operations reliability below 95%")
            else:
                ci_results["performance_checks"]["basic_operations_reliability"] = "PASS"
            
            # 3. Quick environment comparison
            logger.info("Running environment comparison...")
            env_results = await self.run_environment_benchmarks(test_iterations=10)  # Reduced for CI
            ci_results["benchmark_results"]["environments"] = {k: v.to_dict() for k, v in env_results.items()}
            
            # Check environment consistency
            if len(env_results) >= 2:
                durations = [r.avg_duration_ms for r in env_results.values()]
                max_duration = max(durations)
                min_duration = min(durations)
                variation = (max_duration - min_duration) / min_duration * 100 if min_duration > 0 else 0
                
                if variation > 50:  # More than 50% variation between environments
                    ci_results["performance_checks"]["environment_consistency"] = "WARN"
                    ci_results["recommendations"].append(f"High variation between environments ({variation:.1f}%)")
                else:
                    ci_results["performance_checks"]["environment_consistency"] = "PASS"
            
            # Clean up
            if hasattr(test_cache, 'disconnect'):
                await test_cache.disconnect()
            
        except Exception as e:
            logger.error(f"CI benchmark suite failed: {e}")
            ci_results["overall_status"] = "ERROR"
            ci_results["error"] = str(e)
            ci_results["recommendations"].append("Benchmark execution failed - investigate test environment")
        
        ci_results["execution_time_seconds"] = time.time() - start_time
        
        # Final recommendations based on overall status
        if ci_results["overall_status"] == "PASS":
            ci_results["recommendations"].append("All performance checks passed - safe to deploy")
        elif ci_results["overall_status"] == "FAIL":
            ci_results["recommendations"].insert(0, "Performance regression detected - review before deployment")
        
        logger.info(f"CI benchmark suite completed: {ci_results['overall_status']} ({ci_results['execution_time_seconds']:.1f}s)")
        
        # Save results for CI artifacts
        try:
            import os
            results_file = os.path.join(os.getcwd(), "benchmark_results.json")
            with open(results_file, 'w') as f:
                json.dump(ci_results, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Could not save CI results to file: {e}")
        
        return ci_results

    def create_performance_badges(self, results: Union[BenchmarkResult, BenchmarkSuite]) -> Dict[str, str]:
        """
        Generate performance badge data for README/documentation.
        
        Args:
            results: Benchmark results to create badges from
        
        Returns:
            Dict containing badge configurations for various metrics
        """
        badges = {}
        
        if isinstance(results, BenchmarkResult):
            # Single result badges
            badges["response_time"] = {
                "label": "Response Time",
                "message": f"{results.avg_duration_ms:.1f}ms",
                "color": "green" if results.avg_duration_ms < 25 else "yellow" if results.avg_duration_ms < 50 else "red"
            }
            
            badges["throughput"] = {
                "label": "Throughput", 
                "message": f"{results.operations_per_second:.0f} ops/sec",
                "color": "green" if results.operations_per_second > 500 else "yellow" if results.operations_per_second > 100 else "red"
            }
            
            badges["reliability"] = {
                "label": "Reliability",
                "message": f"{results.success_rate * 100:.1f}%",
                "color": "green" if results.success_rate >= 0.99 else "yellow" if results.success_rate >= 0.95 else "red"
            }
            
        elif isinstance(results, BenchmarkSuite):
            # Suite-level badges
            _ = sum(r.avg_duration_ms for r in results.results) / len(results.results) if results.results else 0
            _ = sum(r.operations_per_second for r in results.results) / len(results.results) if results.results else 0
            
            badges["performance_grade"] = {
                "label": "Performance",
                "message": results.performance_grade,
                "color": "green" if results.performance_grade in ["Excellent", "Good"] else "yellow" if results.performance_grade == "Acceptable" else "red"
            }
            
            badges["test_coverage"] = {
                "label": "Tests",
                "message": f"{len(results.results)} benchmarks",
                "color": "green" if len(results.results) >= 3 else "yellow"
            }
            
            badges["pass_rate"] = {
                "label": "Pass Rate",
                "message": f"{results.pass_rate * 100:.0f}%",
                "color": "green" if results.pass_rate >= 0.9 else "yellow" if results.pass_rate >= 0.7 else "red"
            }
        
        # Convert to shields.io format
        shield_badges = {}
        for badge_name, config in badges.items():
            shield_url = f"https://img.shields.io/badge/{config['label']}-{config['message'].replace(' ', '%20')}-{config['color']}"
            shield_badges[badge_name] = {
                "url": shield_url,
                "markdown": f"![{config['label']}]({shield_url})",
                "html": f'<img src="{shield_url}" alt="{config["label"]} Badge"/>'
            }
        
        return shield_badges

    def set_performance_thresholds(self, **thresholds) -> None:
        """
        Update performance thresholds for CI/CD validation.
        
        Args:
            **thresholds: Threshold values to update (e.g., max_avg_duration_ms=30)
        """
        threshold_mapping = {
            "max_avg_duration_ms": "BASIC_OPERATIONS_AVG_MS",
            "max_p95_duration_ms": "BASIC_OPERATIONS_P95_MS", 
            "max_memory_usage_mb": "MEMORY_USAGE_WARNING_MB",
            "max_regression_percent": "REGRESSION_WARNING_PERCENT",
            "min_success_rate": "SUCCESS_RATE_WARNING"
        }
        
        for threshold_name, value in thresholds.items():
            if threshold_name in threshold_mapping:
                attr_name = threshold_mapping[threshold_name]
                setattr(self.thresholds, attr_name, value)
                logger.info(f"Updated threshold {attr_name} to {value}")
            else:
                logger.warning(f"Unknown threshold: {threshold_name}")

    def generate_performance_summary_for_ci(self, ci_results: Dict[str, Any]) -> str:
        """
        Generate a markdown performance summary for CI/CD posting.
        
        Args:
            ci_results: Results from run_ci_benchmark_suite()
        
        Returns:
            str: Markdown formatted summary for CI posting
        """
        status_emoji = "✅" if ci_results["overall_status"] == "PASS" else "❌" if ci_results["overall_status"] == "FAIL" else "⚠️"
        
        summary = []
        summary.append(f"## {status_emoji} Cache Performance Benchmark Results")
        summary.append(f"**Status:** {ci_results['overall_status']}")
        summary.append(f"**Execution Time:** {ci_results['execution_time_seconds']:.1f}s")
        summary.append(f"**Timestamp:** {ci_results['timestamp']}")
        summary.append("")
        
        # Performance checks summary
        summary.append("### Performance Checks")
        summary.append("| Check | Status |")
        summary.append("|-------|--------|") 
        
        for check_name, status in ci_results.get("performance_checks", {}).items():
            check_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            summary.append(f"| {check_name.replace('_', ' ').title()} | {check_emoji} {status} |")
        
        summary.append("")
        
        # Key metrics
        if "basic_operations" in ci_results.get("benchmark_results", {}):
            basic_ops = ci_results["benchmark_results"]["basic_operations"]
            summary.append("### Key Metrics")
            summary.append(f"- **Average Response Time:** {basic_ops.get('avg_duration_ms', 0):.2f}ms")
            summary.append(f"- **Throughput:** {basic_ops.get('operations_per_second', 0):.0f} ops/sec")
            summary.append(f"- **Success Rate:** {basic_ops.get('success_rate', 0) * 100:.1f}%")
            summary.append(f"- **Memory Usage:** {basic_ops.get('memory_usage_mb', 0):.2f}MB")
            summary.append("")
        
        # Recommendations
        if ci_results.get("recommendations"):
            summary.append("### Recommendations")
            for rec in ci_results["recommendations"]:
                summary.append(f"- {rec}")
            summary.append("")
        
        # Environment results summary
        if "environments" in ci_results.get("benchmark_results", {}):
            summary.append("### Environment Performance")
            summary.append("| Environment | Avg Duration (ms) | Throughput (ops/sec) |")
            summary.append("|-------------|-------------------|----------------------|") 
            
            for env_name, env_result in ci_results["benchmark_results"]["environments"].items():
                summary.append(
                    f"| {env_name.title()} | {env_result.get('avg_duration_ms', 0):.2f} | "
                    f"{env_result.get('operations_per_second', 0):.0f} |"
                )
            summary.append("")
        
        # Link to full results
        summary.append("---")
        summary.append("📊 [View detailed benchmark results](./benchmark_results.json)")
        
        return "\n".join(summary)

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