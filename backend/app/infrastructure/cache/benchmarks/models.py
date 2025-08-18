"""
Cache Benchmarking Data Models

This module contains all data models used for cache performance benchmarking,
including result containers, comparison utilities, and suite aggregation.

Classes:
    BenchmarkResult: Individual benchmark measurement data
    ComparisonResult: Before/after performance comparison data  
    BenchmarkSuite: Collection of benchmark results with analysis

The data models support comprehensive performance analysis including timing,
memory usage, statistical analysis, and performance grading.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class BenchmarkResult:
    """
    Comprehensive result data for a single cache performance benchmark.
    
    This class captures all metrics from a benchmark run including timing,
    memory usage, success rates, and optional cache-specific metrics like
    hit rates and compression ratios.
    
    Attributes:
        operation_type: Type of cache operation (get, set, delete, etc.)
        duration_ms: Total duration in milliseconds
        memory_peak_mb: Peak memory usage during benchmark
        iterations: Number of iterations performed
        avg_duration_ms: Average duration per operation
        min_duration_ms: Minimum operation duration
        max_duration_ms: Maximum operation duration
        p95_duration_ms: 95th percentile duration
        p99_duration_ms: 99th percentile duration
        std_dev_ms: Standard deviation of operation times
        operations_per_second: Throughput metric
        success_rate: Percentage of successful operations (0-1)
        memory_usage_mb: Average memory usage
        cache_hit_rate: Cache hit rate if applicable (0-1)
        compression_ratio: Compression efficiency if applicable
        compression_savings_mb: Memory saved through compression
        median_duration_ms: Median operation duration
        error_count: Number of failed operations
        test_data_size_bytes: Size of test data used
        additional_metrics: Custom metrics dictionary
        metadata: Additional metadata about the benchmark
        timestamp: ISO format timestamp of benchmark execution
    
    Example:
        >>> result = BenchmarkResult(
        ...     operation_type="get",
        ...     duration_ms=125.5,
        ...     memory_peak_mb=45.2,
        ...     iterations=1000,
        ...     avg_duration_ms=0.125,
        ...     min_duration_ms=0.05,
        ...     max_duration_ms=2.1,
        ...     p95_duration_ms=0.8,
        ...     p99_duration_ms=1.5,
        ...     std_dev_ms=0.3,
        ...     operations_per_second=8000.0,
        ...     success_rate=1.0,
        ...     memory_usage_mb=42.1
        ... )
        >>> print(result.performance_grade())
        >>> print(result.meets_threshold(1.0))
    """
    
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
        """
        Convert benchmark result to dictionary for serialization.
        
        Returns:
            Dictionary representation of all benchmark data
        """
        return asdict(self)
    
    def meets_threshold(self, threshold_ms: float) -> bool:
        """
        Check if benchmark result meets performance threshold.
        
        Args:
            threshold_ms: Maximum acceptable average duration in milliseconds
            
        Returns:
            True if average duration is within threshold, False otherwise
        """
        return self.avg_duration_ms <= threshold_ms
    
    def performance_grade(self) -> str:
        """
        Calculate performance grade based on standard thresholds.
        
        Grade categories:
        - Excellent: ≤5ms average
        - Good: ≤25ms average  
        - Acceptable: ≤50ms average
        - Poor: ≤100ms average
        - Critical: >100ms average
        
        Returns:
            Performance grade as string
        """
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
    """
    Result data for comparing performance between cache implementations.
    
    This class provides comprehensive analysis when comparing two cache
    implementations, including performance deltas, regression detection,
    and improvement recommendations.
    
    Attributes:
        original_cache_results: Benchmark results from original implementation
        new_cache_results: Benchmark results from new implementation  
        performance_change_percent: Overall performance change percentage
        memory_change_percent: Memory usage change percentage
        operations_per_second_change: Throughput change
        baseline_cache_name: Name/description of original cache
        comparison_cache_name: Name/description of new cache
        operation_comparisons: Per-operation comparison details
        overall_performance_change: Weighted overall performance delta
        cache_hit_rate_change: Hit rate improvement/degradation
        compression_efficiency_change: Compression improvement
        regression_detected: Whether performance regression was detected
        significant_differences: List of metrics with significant changes
        improvement_areas: Areas where performance improved
        degradation_areas: Areas where performance degraded
        recommendation: Overall recommendation based on analysis
        recommendations: List of specific recommendations
        timestamp: ISO format timestamp of comparison
    
    Example:
        >>> comparison = ComparisonResult(
        ...     original_cache_results=old_result,
        ...     new_cache_results=new_result,
        ...     performance_change_percent=-15.2,  # 15.2% improvement
        ...     memory_change_percent=8.5,         # 8.5% more memory
        ...     operations_per_second_change=18.3  # 18.3% faster throughput
        ... )
        >>> print(comparison.summary())
        >>> print(f"Regression: {comparison.regression_detected}")
    """
    
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
    
    @property
    def is_regression(self) -> bool:
        """
        Check if this comparison indicates a performance regression.
        
        Returns:
            True if regression was detected, False otherwise
        """
        return self.regression_detected
    
    @property
    def operation_type(self) -> str:
        """
        Get the operation type being compared.
        
        Returns:
            The operation type from the new cache results
        """
        return self.new_cache_results.operation_type
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert comparison result to dictionary for serialization.
        
        Returns:
            Dictionary representation of all comparison data
        """
        return asdict(self)
    
    def summary(self) -> str:
        """
        Generate human-readable summary of comparison results.
        
        Returns:
            Concise summary string describing the performance comparison
        """
        direction = "improved" if self.performance_change_percent < 0 else "degraded"
        abs_change = abs(self.performance_change_percent)
        
        return (f"Performance {direction} by {abs_change:.1f}% "
                f"(Memory: {self.memory_change_percent:+.1f}%, "
                f"Throughput: {self.operations_per_second_change:+.1f}%)")
    
    def generate_recommendations(self) -> List[str]:
        """
        Generate performance recommendations based on comparison results.
        
        Returns:
            List of recommendation strings based on detected changes
        """
        recommendations = []
        
        # Performance recommendations
        if self.performance_change_percent > 20:
            recommendations.append("Consider optimizing algorithms for better performance")
        elif self.performance_change_percent < -20:
            recommendations.append("Excellent performance improvement achieved")
        
        # Memory recommendations  
        if self.memory_change_percent > 50:
            recommendations.append("Memory usage has increased significantly - investigate memory leaks")
        elif self.memory_change_percent > 20:
            recommendations.append("Monitor memory usage as it has increased")
        elif self.memory_change_percent < -20:
            recommendations.append("Good memory optimization achieved")
        
        # Throughput recommendations
        if self.operations_per_second_change < -20:
            recommendations.append("Throughput has decreased - review performance bottlenecks")
        elif self.operations_per_second_change > 20:
            recommendations.append("Throughput improvement is excellent")
        
        # Regression recommendations
        if self.regression_detected:
            recommendations.append("Address performance regressions before deployment")
        
        # Success rate recommendations
        if (hasattr(self.new_cache_results, 'success_rate') and 
            hasattr(self.original_cache_results, 'success_rate')):
            success_rate_change = self.new_cache_results.success_rate - self.original_cache_results.success_rate
            if success_rate_change < -0.1:  # 10% degradation
                recommendations.append("Success rate has decreased - investigate reliability issues")
        
        # Default recommendation if no specific issues found
        if not recommendations:
            if self.performance_change_percent < 5 and self.memory_change_percent < 10:
                recommendations.append("Performance changes are minimal - deployment ready")
            else:
                recommendations.append("Review performance changes before deployment")
        
        return recommendations


@dataclass
class BenchmarkSuite:
    """
    Collection of benchmark results with comprehensive analysis.
    
    This class aggregates multiple benchmark results into a cohesive
    analysis, providing overall performance grading, success rates,
    and suite-level metrics.
    
    Attributes:
        name: Descriptive name for the benchmark suite
        results: List of individual benchmark results
        total_duration_ms: Total time for all benchmarks
        pass_rate: Percentage of benchmarks that passed (0-1)
        failed_benchmarks: List of benchmark names that failed
        performance_grade: Overall performance grade for the suite
        memory_efficiency_grade: Overall memory efficiency grade
        timestamp: ISO format timestamp of suite execution
        environment_info: Information about test environment
    
    Example:
        >>> suite = BenchmarkSuite(
        ...     name="Redis Cache Performance",
        ...     results=[result1, result2, result3],
        ...     total_duration_ms=1250.5,
        ...     pass_rate=1.0,
        ...     failed_benchmarks=[],
        ...     performance_grade="Good",
        ...     memory_efficiency_grade="Excellent"
        ... )
        >>> score = suite.calculate_overall_score()
        >>> get_result = suite.get_operation_result("get")
    """
    
    name: str
    results: List[BenchmarkResult]
    total_duration_ms: float
    pass_rate: float
    failed_benchmarks: List[str]
    performance_grade: str
    memory_efficiency_grade: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    environment_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert benchmark suite to dictionary for serialization.
        
        Returns:
            Dictionary representation of all benchmark suite data
        """
        return asdict(self)
    
    def to_json(self) -> str:
        """
        Serialize benchmark suite to JSON string.
        
        Returns:
            JSON string representation of the entire benchmark suite
        """
        return json.dumps(asdict(self), indent=2)
    
    def get_operation_result(self, operation_type: str) -> Optional[BenchmarkResult]:
        """
        Get benchmark result for specific operation type.
        
        Args:
            operation_type: The operation type to search for (e.g., "get", "set")
            
        Returns:
            BenchmarkResult for the operation if found, None otherwise
        """
        for result in self.results:
            if result.operation_type == operation_type:
                return result
        return None
    
    def calculate_overall_score(self) -> float:
        """
        Calculate overall performance score (0-100).
        
        The score is a weighted combination of:
        - Timing performance (50% weight)
        - Success rate (30% weight)  
        - Memory efficiency (20% weight)
        
        Returns:
            Overall score from 0-100, where 100 is optimal performance
        """
        if not self.results:
            return 0.0
        
        # Weight different aspects of performance
        timing_score = min(100, max(0, 100 - sum(r.avg_duration_ms for r in self.results) / len(self.results)))
        success_score = self.pass_rate * 100
        memory_score = min(100, max(0, 100 - sum(r.memory_usage_mb for r in self.results) / len(self.results)))
        
        # Weighted average: timing 50%, success 30%, memory 20%
        return (timing_score * 0.5) + (success_score * 0.3) + (memory_score * 0.2)