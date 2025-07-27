# Monitoring Infrastructure Service

This module provides comprehensive monitoring and observability capabilities for the
application infrastructure. It centralizes access to performance monitoring, health
checks, and metrics collection components.

## Components

- **Cache Performance Monitoring**: Real-time cache performance tracking with hit rates,
timing statistics, compression efficiency, and memory usage monitoring
- **Configuration Monitoring**: Tracking of resilience configuration changes and validation
- **Health Checks**: System health monitoring and status reporting (placeholder)
- **Metrics Collection**: Application-wide metrics gathering and export (placeholder)

## Key Features

- Real-time performance metrics collection
- Cache operation timing and efficiency tracking
- Memory usage monitoring with threshold alerting
- Configuration change tracking and validation
- Comprehensive statistics and trend analysis
- Exportable metrics for external monitoring systems

## Usage

```python
from app.infrastructure.monitoring import (
CachePerformanceMonitor,
config_metrics_collector
)

# Monitor cache performance
cache_monitor = CachePerformanceMonitor(
retention_hours=2,
memory_warning_threshold_bytes=100 * 1024 * 1024
)

# Record cache operations
cache_monitor.record_cache_operation_time("get", 0.05, True)

# Track configuration changes
config_metrics_collector.record_config_change("preset_applied", "production")
```

## Integration

The monitoring system integrates with:
- Cache services for performance tracking
- Resilience services for configuration monitoring
- Health check endpoints for system status
- External monitoring tools for metrics export
