"""
Monitoring Infrastructure Service Package

This package provides comprehensive monitoring and observability infrastructure for the FastAPI
application. It delivers centralized performance monitoring, health checking, metrics collection,
and configuration tracking across all infrastructure services.

## Package Architecture

The monitoring system follows a layered observability approach:
- **Metrics Layer**: Real-time performance and operational metrics collection
- **Health Layer**: Component and system health monitoring with async-first design
- **Configuration Layer**: Configuration change tracking and validation monitoring
- **Alerting Layer**: Threshold-based alerting and notification system (future)

## Core Components

### Cache Performance Monitoring
Comprehensive cache performance tracking and analytics:
- **Performance Metrics**: Hit rates, miss rates, response times, throughput
- **Memory Analytics**: Memory usage patterns, peak detection, efficiency tracking
- **Compression Monitoring**: Compression ratios, efficiency metrics, size analysis
- **Invalidation Tracking**: Cache invalidation patterns and frequency analysis
- **Threshold Alerting**: Automatic alerting when performance degrades

### Health Checking System
Robust health monitoring with async-first design:
- **Component Health**: Individual service health monitoring (AI, cache, database)
- **System Health**: Overall system health aggregation and status reporting
- **Custom Checks**: Extensible health check registration system
- **Timeout Management**: Configurable timeouts with graceful degradation
- **Health History**: Historical health data tracking and trend analysis

### Configuration Monitoring
Dynamic configuration tracking and validation:
- **Configuration Metrics**: Preset usage tracking and performance correlation
- **Change Auditing**: Configuration change history and impact analysis
- **Validation Monitoring**: Configuration validation success rates and errors
- **Usage Analytics**: Feature usage patterns and optimization opportunities

### Metrics Collection Framework
Extensible metrics collection with standardized interfaces:
- **Custom Metrics**: Easy registration of application-specific metrics
- **Metric Aggregation**: Automatic aggregation and statistical analysis
- **Export Integration**: Compatible with external monitoring systems
- **Historical Data**: Time-series data storage and retrieval

## Performance Characteristics

- **Metrics Collection**: < 1ms overhead per metric collection
- **Health Checks**: Configurable timeouts (default: 2-5 seconds per component)
- **Memory Efficient**: Minimal memory footprint with circular buffer storage
- **High Throughput**: Supports high-frequency metric collection (1000+ ops/sec)
- **Non-blocking**: Async-first design prevents monitoring from blocking operations

## Usage Patterns

### Basic Health Monitoring
```python
from app.infrastructure.monitoring import HealthChecker, check_ai_model_health

# Create health checker with standard checks
checker = HealthChecker()
checker.register_check("ai_model", check_ai_model_health)

# Perform health checks
health_status = await checker.check_all()
print(f"System healthy: {health_status.is_healthy}")
```

### Cache Performance Monitoring
```python
from app.infrastructure.monitoring import CachePerformanceMonitor

# Initialize performance monitor
monitor = CachePerformanceMonitor()

# Track cache operations
await monitor.record_hit("user_cache", response_time_ms=15.2)
await monitor.record_miss("user_cache")

# Get performance metrics
metrics = monitor.get_metrics("user_cache")
print(f"Hit rate: {metrics.hit_rate:.2%}")
```

### Configuration Monitoring
```python
from app.infrastructure.monitoring import config_metrics_collector

# Metrics are collected automatically
stats = config_metrics_collector.get_usage_stats()
alerts = config_metrics_collector.get_active_alerts()

# Track configuration changes
config_metrics_collector.record_config_change(
    "resilience_preset", old_value="development", new_value="production"
)
```

### Custom Health Checks
```python
from app.infrastructure.monitoring import HealthChecker, HealthStatus

async def check_external_service_health() -> HealthStatus:
    try:
        # Your health check logic
        response = await external_service.ping()
        return HealthStatus.healthy("External service responding")
    except Exception as e:
        return HealthStatus.unhealthy(f"External service failed: {e}")

# Register custom check
checker.register_check("external_service", check_external_service_health)
```

## Integration with Other Infrastructure

The monitoring system integrates with all infrastructure services:
- **Cache System**: Automatic performance tracking and health monitoring
- **Resilience System**: Configuration monitoring and performance correlation
- **AI System**: Model health checks and performance tracking
- **Security System**: Authentication monitoring and audit logging

## Configuration

Monitoring behavior is controlled through environment variables:

```bash
# Health Check Configuration
HEALTH_CHECK_TIMEOUT_MS=2000           # Default health check timeout
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=1000  # AI model specific timeout
HEALTH_CHECK_CACHE_TIMEOUT_MS=3000     # Cache specific timeout
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=1500 # Resilience specific timeout
HEALTH_CHECK_RETRY_COUNT=2             # Number of retries for failed checks

# Performance Monitoring Configuration
CACHE_METRICS_RETENTION_HOURS=24       # How long to retain cache metrics
METRICS_COLLECTION_INTERVAL_MS=1000    # Metrics collection frequency
PERFORMANCE_ALERT_THRESHOLDS={}        # Custom alert thresholds

# Configuration Monitoring
CONFIG_MONITORING_ENABLED=true         # Enable configuration monitoring
CONFIG_CHANGE_RETENTION_DAYS=30        # Configuration change history retention
```

## Monitoring Capabilities

### Real-time Metrics
- **Cache Performance**: Hit/miss rates, response times, memory usage
- **System Health**: Component status, error rates, availability
- **Configuration**: Preset usage, validation success rates, change frequency
- **Request Metrics**: Request counts, error rates, response times

### Historical Analytics
- **Trend Analysis**: Performance trends over time
- **Capacity Planning**: Resource usage forecasting
- **Error Correlation**: Error pattern analysis and root cause identification
- **Configuration Impact**: Performance impact of configuration changes

### Alerting (Future Enhancement)
- **Threshold Alerts**: Automatic alerts when metrics exceed thresholds
- **Anomaly Detection**: ML-based anomaly detection for unusual patterns
- **Escalation Policies**: Configurable alert escalation and notification
- **Alert Correlation**: Intelligent alert grouping and root cause analysis

## Testing Support

The monitoring system includes comprehensive testing utilities:
- **Mock Monitors**: Configurable mock implementations for testing
- **Test Metrics**: Pre-defined metrics for test scenarios
- **Health Check Mocks**: Controllable health check responses
- **Performance Simulation**: Synthetic load generation for testing

## Thread Safety

All monitoring components are designed for concurrent access:
- **Thread-Safe Metrics**: All metric operations are atomic and thread-safe
- **Concurrent Health Checks**: Health checks run concurrently without interference
- **Lock-Free Designs**: Most operations use lock-free algorithms for performance
- **Immutable Data**: Metric snapshots use immutable data structures
"""

from app.infrastructure.cache.monitoring import CachePerformanceMonitor, PerformanceMetric, CompressionMetric
from app.infrastructure.resilience.config_monitoring import config_metrics_collector, ConfigurationMetric
from app.infrastructure.monitoring.health import HealthStatus, ComponentStatus, SystemHealthStatus, HealthChecker, check_ai_model_health, check_cache_health, check_resilience_health, check_database_health

__all__ = ['CachePerformanceMonitor', 'PerformanceMetric', 'CompressionMetric', 'config_metrics_collector', 'ConfigurationMetric', 'HealthStatus', 'ComponentStatus', 'SystemHealthStatus', 'HealthChecker', 'check_ai_model_health', 'check_cache_health', 'check_resilience_health', 'check_database_health']
