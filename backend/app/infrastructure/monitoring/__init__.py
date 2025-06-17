"""
Monitoring Infrastructure Service

Re-exports key monitoring and metrics collection components.
"""
# Bridge from old monitoring locations.
from ...services.monitoring import CachePerformanceMonitor, PerformanceMetric, CompressionMetric
from ...config_monitoring import config_metrics_collector, ConfigurationMetric

__all__ = [
    "CachePerformanceMonitor",
    "PerformanceMetric",
    "CompressionMetric",
    "config_metrics_collector",
    "ConfigurationMetric"
]