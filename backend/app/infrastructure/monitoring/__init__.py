"""
Monitoring Infrastructure Service

Re-exports key monitoring and metrics collection components.
"""
from app.refactor import USE_REFACTORED_STRUCTURE

if USE_REFACTORED_STRUCTURE:
    pass
else:
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