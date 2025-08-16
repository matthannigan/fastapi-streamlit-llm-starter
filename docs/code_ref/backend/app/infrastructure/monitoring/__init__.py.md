---
sidebar_label: __init__
---

# Monitoring Infrastructure Service

  file_path: `backend/app/infrastructure/monitoring/__init__.py`

Centralized monitoring and observability for application infrastructure. Exposes
performance monitoring, configuration metrics, and standardized health checks.

## Components

- Cache Performance Monitoring: hit rates, timings, compression, memory
- Configuration Monitoring: resilience configuration metrics and changes
- Health Checks: async-first component and system health monitoring
- Metrics Collection: application-wide metrics (extensible)

## Usage

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
