"""
Monitoring Infrastructure Service

Centralized monitoring and observability for application infrastructure. Exposes
performance monitoring, configuration metrics, and standardized health checks.

Components:
- Cache Performance Monitoring: hit rates, timings, compression, memory
- Configuration Monitoring: resilience configuration metrics and changes
- Health Checks: async-first component and system health monitoring
- Metrics Collection: application-wide metrics (extensible)

Usage:
```python
from app.infrastructure.monitoring import (
    CachePerformanceMonitor,
    config_metrics_collector,
    HealthChecker,
    check_ai_model_health,
)

checker = HealthChecker()
checker.register_check("ai_model", check_ai_model_health)
```
"""

from app.infrastructure.cache.monitoring import CachePerformanceMonitor, PerformanceMetric, CompressionMetric
from app.infrastructure.resilience.config_monitoring import config_metrics_collector, ConfigurationMetric
from app.infrastructure.monitoring.health import (
    HealthStatus,
    ComponentStatus,
    SystemHealthStatus,
    HealthChecker,
    check_ai_model_health,
    check_cache_health,
    check_resilience_health,
    check_database_health,
)

__all__ = [
    "CachePerformanceMonitor",
    "PerformanceMetric",
    "CompressionMetric",
    "config_metrics_collector",
    "ConfigurationMetric",
    # Health infrastructure exports
    "HealthStatus",
    "ComponentStatus",
    "SystemHealthStatus",
    "HealthChecker",
    "check_ai_model_health",
    "check_cache_health",
    "check_resilience_health",
    "check_database_health",
]