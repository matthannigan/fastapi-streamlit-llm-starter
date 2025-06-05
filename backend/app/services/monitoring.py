import time
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from statistics import mean, median

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Data class for storing individual performance measurements."""
    duration: float
    text_length: int
    timestamp: float
    operation_type: str = ""
    additional_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


@dataclass
class CompressionMetric:
    """Data class for storing compression performance measurements."""
    original_size: int
    compressed_size: int
    compression_ratio: float
    compression_time: float
    timestamp: float
    operation_type: str = ""

    def __post_init__(self):
        if self.compression_ratio == 0 and self.original_size > 0:
            self.compression_ratio = self.compressed_size / self.original_size


class CachePerformanceMonitor:
    """
    Monitors and tracks cache performance metrics for optimization and debugging.
    
    This class tracks:
    - Key generation performance
    - Cache operation timing (get/set operations)
    - Compression ratios and efficiency
    - Recent measurements with automatic cleanup
    """
    
    def __init__(self, retention_hours: int = 1, max_measurements: int = 1000):
        """
        Initialize the cache performance monitor.
        
        Args:
            retention_hours: How long to keep measurements (default: 1 hour)
            max_measurements: Maximum number of measurements to store per metric type
        """
        self.retention_hours = retention_hours
        self.max_measurements = max_measurements
        
        # Storage for different types of measurements
        self.key_generation_times: List[PerformanceMetric] = []
        self.cache_operation_times: List[PerformanceMetric] = []
        self.compression_ratios: List[CompressionMetric] = []
        
        # Track overall cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_operations = 0
        
        # Performance thresholds for alerting
        self.key_generation_threshold = 0.1  # 100ms
        self.cache_operation_threshold = 0.05  # 50ms
        
    def record_key_generation_time(
        self, 
        duration: float, 
        text_length: int, 
        operation_type: str = "",
        additional_data: Dict[str, Any] = None
    ):
        """
        Record key generation performance metrics.
        
        Args:
            duration: Time taken to generate the cache key (in seconds)
            text_length: Length of the text being processed
            operation_type: Type of operation (summarize, sentiment, etc.)
            additional_data: Additional metadata to store with the metric
        """
        metric = PerformanceMetric(
            duration=duration,
            text_length=text_length,
            timestamp=time.time(),
            operation_type=operation_type,
            additional_data=additional_data or {}
        )
        
        self.key_generation_times.append(metric)
        self._cleanup_old_measurements(self.key_generation_times)
        
        # Log warning if performance is poor
        if duration > self.key_generation_threshold:
            logger.warning(
                f"Slow key generation: {duration:.3f}s for {text_length} chars "
                f"in {operation_type} operation"
            )
        
        logger.debug(
            f"Key generation time: {duration:.3f}s for {text_length} chars "
            f"({operation_type})"
        )
    
    def record_cache_operation_time(
        self, 
        operation: str, 
        duration: float, 
        cache_hit: bool,
        text_length: int = 0,
        additional_data: Dict[str, Any] = None
    ):
        """
        Record cache operation performance (get/set operations).
        
        Args:
            operation: Operation type ('get', 'set', 'delete', etc.)
            duration: Time taken for the operation (in seconds)
            cache_hit: Whether this was a cache hit (for get operations)
            text_length: Length of text being cached/retrieved
            additional_data: Additional metadata to store
        """
        metric = PerformanceMetric(
            duration=duration,
            text_length=text_length,
            timestamp=time.time(),
            operation_type=operation,
            additional_data=additional_data or {}
        )
        
        self.cache_operation_times.append(metric)
        self._cleanup_old_measurements(self.cache_operation_times)
        
        # Update cache hit/miss statistics
        self.total_operations += 1
        if operation == "get":
            if cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
        
        # Log warning if operation is slow
        if duration > self.cache_operation_threshold:
            logger.warning(
                f"Slow cache {operation}: {duration:.3f}s "
                f"(hit: {cache_hit}, text_length: {text_length})"
            )
        
        logger.debug(
            f"Cache {operation} time: {duration:.3f}s "
            f"(hit: {cache_hit}, text_length: {text_length})"
        )
    
    def record_compression_ratio(
        self, 
        original_size: int, 
        compressed_size: int, 
        compression_time: float,
        operation_type: str = ""
    ):
        """
        Record compression performance and efficiency metrics.
        
        Args:
            original_size: Size of data before compression (in bytes)
            compressed_size: Size of data after compression (in bytes)
            compression_time: Time taken to compress (in seconds)
            operation_type: Type of operation being compressed
        """
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        metric = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=compression_time,
            timestamp=time.time(),
            operation_type=operation_type
        )
        
        self.compression_ratios.append(metric)
        self._cleanup_old_measurements(self.compression_ratios)
        
        savings = original_size - compressed_size
        savings_percent = (savings / original_size * 100) if original_size > 0 else 0
        
        logger.debug(
            f"Compression: {original_size} -> {compressed_size} bytes "
            f"({savings_percent:.1f}% savings, {compression_time:.3f}s, {operation_type})"
        )
    
    def _cleanup_old_measurements(self, measurements: List):
        """
        Remove old measurements based on retention policy.
        
        Args:
            measurements: List of measurements to clean up
        """
        if not measurements:
            return
        
        # Calculate cutoff time
        cutoff_time = time.time() - (self.retention_hours * 3600)
        
        # Remove old measurements
        original_count = len(measurements)
        measurements[:] = [m for m in measurements if m.timestamp > cutoff_time]
        
        # Also enforce max measurements limit
        if len(measurements) > self.max_measurements:
            # Keep the most recent measurements
            measurements[:] = measurements[-self.max_measurements:]
        
        if len(measurements) < original_count:
            logger.debug(
                f"Cleaned up {original_count - len(measurements)} old measurements"
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache performance statistics.
        
        Returns:
            Dictionary containing performance metrics and statistics
        """
        # Clean up old measurements first
        self._cleanup_old_measurements(self.key_generation_times)
        self._cleanup_old_measurements(self.cache_operation_times)
        self._cleanup_old_measurements(self.compression_ratios)
        
        stats = {
            "timestamp": datetime.now().isoformat(),
            "retention_hours": self.retention_hours,
            "cache_hit_rate": self._calculate_hit_rate(),
            "total_cache_operations": self.total_operations,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses
        }
        
        # Key generation statistics
        if self.key_generation_times:
            key_gen_durations = [m.duration for m in self.key_generation_times]
            key_gen_text_lengths = [m.text_length for m in self.key_generation_times]
            
            stats["key_generation"] = {
                "total_operations": len(self.key_generation_times),
                "avg_duration": mean(key_gen_durations),
                "median_duration": median(key_gen_durations),
                "max_duration": max(key_gen_durations),
                "min_duration": min(key_gen_durations),
                "avg_text_length": mean(key_gen_text_lengths),
                "max_text_length": max(key_gen_text_lengths),
                "slow_operations": len([d for d in key_gen_durations if d > self.key_generation_threshold])
            }
        
        # Cache operation statistics
        if self.cache_operation_times:
            cache_op_durations = [m.duration for m in self.cache_operation_times]
            
            # Group by operation type
            ops_by_type = {}
            for metric in self.cache_operation_times:
                op_type = metric.operation_type
                if op_type not in ops_by_type:
                    ops_by_type[op_type] = []
                ops_by_type[op_type].append(metric.duration)
            
            stats["cache_operations"] = {
                "total_operations": len(self.cache_operation_times),
                "avg_duration": mean(cache_op_durations),
                "median_duration": median(cache_op_durations),
                "max_duration": max(cache_op_durations),
                "min_duration": min(cache_op_durations),
                "slow_operations": len([d for d in cache_op_durations if d > self.cache_operation_threshold]),
                "by_operation_type": {
                    op_type: {
                        "count": len(durations),
                        "avg_duration": mean(durations),
                        "max_duration": max(durations)
                    } for op_type, durations in ops_by_type.items()
                }
            }
        
        # Compression statistics
        if self.compression_ratios:
            ratios = [m.compression_ratio for m in self.compression_ratios]
            comp_times = [m.compression_time for m in self.compression_ratios]
            original_sizes = [m.original_size for m in self.compression_ratios]
            compressed_sizes = [m.compressed_size for m in self.compression_ratios]
            
            total_original = sum(original_sizes)
            total_compressed = sum(compressed_sizes)
            overall_savings = total_original - total_compressed
            overall_savings_percent = (overall_savings / total_original * 100) if total_original > 0 else 0
            
            stats["compression"] = {
                "total_operations": len(self.compression_ratios),
                "avg_compression_ratio": mean(ratios),
                "median_compression_ratio": median(ratios),
                "best_compression_ratio": min(ratios),
                "worst_compression_ratio": max(ratios),
                "avg_compression_time": mean(comp_times),
                "max_compression_time": max(comp_times),
                "total_bytes_processed": total_original,
                "total_bytes_saved": overall_savings,
                "overall_savings_percent": overall_savings_percent
            }
        
        return stats
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate as a percentage."""
        if self.total_operations == 0:
            return 0.0
        return (self.cache_hits / self.total_operations) * 100
    
    def get_recent_slow_operations(self, threshold_multiplier: float = 2.0) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get recent operations that were significantly slower than average.
        
        Args:
            threshold_multiplier: How many times the average to consider "slow"
            
        Returns:
            Dictionary with slow operations by category
        """
        slow_ops = {
            "key_generation": [],
            "cache_operations": [],
            "compression": []
        }
        
        # Analyze key generation times
        if self.key_generation_times:
            avg_duration = mean([m.duration for m in self.key_generation_times])
            threshold = avg_duration * threshold_multiplier
            
            for metric in self.key_generation_times:
                if metric.duration > threshold:
                    slow_ops["key_generation"].append({
                        "duration": metric.duration,
                        "text_length": metric.text_length,
                        "operation_type": metric.operation_type,
                        "timestamp": datetime.fromtimestamp(metric.timestamp).isoformat(),
                        "times_slower": metric.duration / avg_duration
                    })
        
        # Analyze cache operations
        if self.cache_operation_times:
            avg_duration = mean([m.duration for m in self.cache_operation_times])
            threshold = avg_duration * threshold_multiplier
            
            for metric in self.cache_operation_times:
                if metric.duration > threshold:
                    slow_ops["cache_operations"].append({
                        "duration": metric.duration,
                        "operation_type": metric.operation_type,
                        "text_length": metric.text_length,
                        "timestamp": datetime.fromtimestamp(metric.timestamp).isoformat(),
                        "times_slower": metric.duration / avg_duration
                    })
        
        # Analyze compression times
        if self.compression_ratios:
            avg_duration = mean([m.compression_time for m in self.compression_ratios])
            threshold = avg_duration * threshold_multiplier
            
            for metric in self.compression_ratios:
                if metric.compression_time > threshold:
                    slow_ops["compression"].append({
                        "compression_time": metric.compression_time,
                        "original_size": metric.original_size,
                        "compression_ratio": metric.compression_ratio,
                        "operation_type": metric.operation_type,
                        "timestamp": datetime.fromtimestamp(metric.timestamp).isoformat(),
                        "times_slower": metric.compression_time / avg_duration
                    })
        
        return slow_ops
    
    def reset_stats(self):
        """Reset all performance statistics and measurements."""
        self.key_generation_times.clear()
        self.cache_operation_times.clear()
        self.compression_ratios.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_operations = 0
        logger.info("Cache performance statistics reset")
    
    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all raw metrics data for external analysis.
        
        Returns:
            Dictionary containing all raw performance measurements
        """
        return {
            "key_generation_times": [asdict(m) for m in self.key_generation_times],
            "cache_operation_times": [asdict(m) for m in self.cache_operation_times],
            "compression_ratios": [asdict(m) for m in self.compression_ratios],
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_operations": self.total_operations,
            "export_timestamp": datetime.now().isoformat()
        } 