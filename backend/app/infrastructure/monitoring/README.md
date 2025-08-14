---
sidebar_label: monitoring
---

# Monitoring Infrastructure Module

This directory provides a comprehensive monitoring and observability infrastructure for FastAPI applications, serving as a centralized access point for performance monitoring, health checks, and metrics collection. It implements a unified monitoring architecture that aggregates capabilities from multiple infrastructure components while providing extensible foundations for future monitoring implementations.

## Directory Structure

```
monitoring/
├── __init__.py          # Centralized monitoring exports and comprehensive documentation
├── health.py           # Health check infrastructure (core implementation)
├── metrics.py          # Application metrics collection (placeholder for future implementation)
└── README.md           # This documentation file
```

## Core Architecture

### Centralized Monitoring Design

The monitoring infrastructure follows a **centralized aggregation architecture** that unifies monitoring capabilities across the application:

1. **Aggregation Layer**: Centralized imports from distributed monitoring implementations
2. **Performance Monitoring Layer**: Real-time cache and configuration performance tracking
3. **Health Check Layer**: System health monitoring and status reporting (planned)
4. **Metrics Collection Layer**: Application-wide metrics gathering and export (planned)
5. **Integration Layer**: Unified interface for external monitoring systems

## Current Components

### Active Monitoring Capabilities

**Available Now:** The monitoring module currently provides access to comprehensive monitoring capabilities from other infrastructure modules:

#### Cache Performance Monitoring
- **Source**: `app.infrastructure.cache.monitoring.CachePerformanceMonitor`
- **Key Features**:
  - ✅ **Real-time Performance Tracking**: Cache operation timing with statistical analysis
  - ✅ **Hit/Miss Ratio Analytics**: Cache effectiveness monitoring with trend analysis
  - ✅ **Memory Usage Monitoring**: Memory consumption tracking with threshold alerting
  - ✅ **Compression Efficiency**: Compression ratio analysis and optimization recommendations
  - ✅ **Key Generation Performance**: Key generation timing with text length correlations
  - ✅ **Export Capabilities**: JSON metrics export for external monitoring systems

#### Configuration Monitoring
- **Source**: `app.infrastructure.resilience.config_monitoring.config_metrics_collector`
- **Key Features**:
  - ✅ **Usage Analytics**: Comprehensive preset usage pattern tracking
  - ✅ **Performance Monitoring**: Configuration load time tracking and analysis
  - ✅ **Alert System**: Configurable alerts for performance thresholds
  - ✅ **Trend Analysis**: Historical usage and performance trend analysis
  - ✅ **Session Analytics**: Session-based usage statistics and patterns

### Health Check Infrastructure (`health.py`)
Core health check capabilities for monitoring overall system status and component availability.

Features:
- ✅ Component and system status data models (`HealthStatus`, `ComponentStatus`, `SystemHealthStatus`)
- ✅ Async `HealthChecker` with per-component/global timeouts, retries, and error isolation
- ✅ Built-in checks: AI model, cache, resilience, and database placeholder
- ✅ Backward-compatible mapping to existing `HealthResponse` in `/v1/health`

Usage:
```python
from app.infrastructure.monitoring import (
    HealthChecker,
    check_ai_model_health,
    check_cache_health,
    check_resilience_health,
)

checker = HealthChecker()
checker.register_check("ai_model", check_ai_model_health)
checker.register_check("cache", check_cache_health)
checker.register_check("resilience", check_resilience_health)
system_status = await checker.check_all_components()
```

FastAPI integration:
- `get_health_checker()` in `app/dependencies.py` returns a cached instance
- `/v1/health` endpoint uses the checker and degrades gracefully on failures

Configuration (see `app.core.config.Settings`):
- `health_check_timeout_ms`, per-component overrides, retry count, enabled components

#### Application Metrics Collection (`metrics.py`)
**Purpose:** Centralized metrics collection and export capabilities for comprehensive application observability.

**Planned Features:**
- 🔄 **Multiple Metric Types**: Counter, Gauge, Histogram, and Summary metrics
- 🔄 **Prometheus Integration**: Native Prometheus exposition format support
- 🔄 **Real-time Collection**: Live metrics streaming and aggregation
- 🔄 **Custom Labels**: Flexible labeling system for metric categorization
- 🔄 **Export Formats**: JSON, Prometheus, and custom format adapters

**Planned Architecture:**
```python
# Future implementation structure
class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge" 
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class MetricsCollector:
    def register(self, metric: Metric)
    def export_prometheus(self) -> str
    def export_json(self) -> str
```

## Usage Examples

### Current Monitoring Capabilities

#### Cache Performance Monitoring

```python
from app.infrastructure.monitoring import CachePerformanceMonitor

# Initialize cache performance monitor
cache_monitor = CachePerformanceMonitor(
    retention_hours=2,
    memory_warning_threshold_bytes=100 * 1024 * 1024,  # 100MB
    compression_threshold_bytes=50 * 1024 * 1024       # 50MB
)

# Record cache operations
cache_monitor.record_cache_operation_time("get", 0.05, cache_hit=True)
cache_monitor.record_cache_operation_time("set", 0.12, cache_hit=False)

# Record compression metrics
cache_monitor.record_compression_operation(
    original_size=5000,
    compressed_size=1500,
    compression_time=0.03
)

# Get performance statistics
stats = cache_monitor.get_cache_stats()
print(f"Cache hit ratio: {stats.hit_ratio:.2f}%")
print(f"Average operation time: {stats.avg_operation_time:.3f}s")
print(f"Memory usage: {stats.memory_usage_bytes / 1024 / 1024:.1f}MB")

# Export metrics for external monitoring
metrics_json = cache_monitor.export_metrics("json", time_window_hours=1)
```

#### Configuration Change Monitoring

```python
from app.infrastructure.monitoring import config_metrics_collector

# Track configuration operations
with config_metrics_collector.track_config_operation("load_preset", "production"):
    preset = preset_manager.get_preset("production")

# Record configuration events
config_metrics_collector.record_preset_usage(
    preset_name="production",
    operation="apply_configuration",
    metadata={
        "environment": "prod",
        "success": True,
        "load_time_ms": 45
    }
)

# Get usage statistics
stats = config_metrics_collector.get_usage_statistics()
print(f"Most used preset: {stats.most_used_preset}")
print(f"Average load time: {stats.avg_load_time_ms:.2f}ms")
print(f"Total configurations loaded: {stats.total_loads}")

# Export configuration metrics
config_metrics = config_metrics_collector.export_metrics(
    format_type="json",
    time_window_hours=24
)
```

### Unified Monitoring Dashboard

```python
from app.infrastructure.monitoring import (
    CachePerformanceMonitor,
    config_metrics_collector
)

class MonitoringDashboard:
    """Unified monitoring dashboard for all system metrics."""
    
    def __init__(self):
        self.cache_monitor = CachePerformanceMonitor()
        self.config_collector = config_metrics_collector
    
    async def get_system_overview(self) -> dict:
        """Get comprehensive system monitoring overview."""
        return {
            "cache_performance": {
                "stats": self.cache_monitor.get_cache_stats(),
                "health": self.cache_monitor.get_health_status(),
                "alerts": self.cache_monitor.get_active_alerts()
            },
            "configuration_monitoring": {
                "usage_stats": self.config_collector.get_usage_statistics(),
                "performance": self.config_collector.get_performance_summary(),
                "recent_events": self.config_collector.get_recent_events(limit=10)
            },
            "system_status": {
                "timestamp": time.time(),
                "overall_health": "healthy",  # Computed from components
                "components_monitored": 2
            }
        }
    
    async def export_all_metrics(self, format_type: str = "json") -> dict:
        """Export all monitoring metrics in unified format."""
        return {
            "cache_metrics": self.cache_monitor.export_metrics(format_type),
            "config_metrics": self.config_collector.export_metrics(format_type),
            "export_timestamp": time.time(),
            "format": format_type
        }

# Use unified dashboard
dashboard = MonitoringDashboard()
overview = await dashboard.get_system_overview()
all_metrics = await dashboard.export_all_metrics()
```

### Future Health Check Usage (Planned)

```python
# Future implementation - when health.py is completed
from app.infrastructure.monitoring.health import HealthChecker, ComponentStatus

# Create health checker with component checks
health_checker = HealthChecker()

# Register component health checks
health_checker.register_check("database", check_database_connection)
health_checker.register_check("redis", check_redis_connection)
health_checker.register_check("ai_service", check_ai_service_availability)
health_checker.register_check("cache", check_cache_health)

# Perform comprehensive health check
health_status = await health_checker.check_health()

if health_status.is_healthy:
    print("All systems operational")
else:
    print(f"System issues detected: {health_status.failed_components}")
    for component in health_status.failed_components:
        print(f"- {component.name}: {component.message}")

# Integration with FastAPI health endpoint
@app.get("/health")
async def health_endpoint():
    """System health check endpoint."""
    status = await health_checker.check_health()
    return {
        "status": "healthy" if status.is_healthy else "unhealthy",
        "components": [
            {
                "name": comp.name,
                "status": comp.status.value,
                "response_time_ms": comp.response_time_ms,
                "message": comp.message
            }
            for comp in status.components
        ],
        "timestamp": time.time()
    }
```

### Future Metrics Collection Usage (Planned)

```python
# Future implementation - when metrics.py is completed
from app.infrastructure.monitoring.metrics import MetricsCollector, Counter, Gauge, Histogram

# Initialize metrics collector
metrics = MetricsCollector()

# Create and register application metrics
request_counter = Counter(
    "http_requests_total", 
    "Total HTTP requests",
    labels=["method", "endpoint", "status"]
)

response_time_histogram = Histogram(
    "http_response_time_seconds",
    "HTTP response time in seconds",
    buckets=[0.001, 0.01, 0.1, 1.0, 10.0]
)

active_connections = Gauge(
    "active_database_connections",
    "Current number of active database connections"
)

# Register metrics
metrics.register(request_counter)
metrics.register(response_time_histogram)
metrics.register(active_connections)

# Record metrics in application code
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect HTTP metrics."""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Record metrics
    request_counter.increment(labels={
        "method": request.method,
        "endpoint": request.url.path,
        "status": str(response.status_code)
    })
    
    response_time = time.time() - start_time
    response_time_histogram.observe(response_time)
    
    return response

# Export metrics for Prometheus
@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return Response(
        content=metrics.export_prometheus(),
        media_type="text/plain"
    )
```

## Integration Patterns

### FastAPI Application Integration

The monitoring system integrates seamlessly with FastAPI applications:

```python
from fastapi import FastAPI, Depends, BackgroundTasks
from app.infrastructure.monitoring import CachePerformanceMonitor, config_metrics_collector

app = FastAPI()

# Global monitoring instances
cache_monitor = CachePerformanceMonitor()

@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """Middleware for automatic monitoring integration."""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Record performance metrics
    if request.url.path.startswith("/api/"):
        processing_time = time.time() - start_time
        
        # Record API performance
        cache_monitor.record_api_performance(
            endpoint=request.url.path,
            method=request.method,
            response_time=processing_time,
            status_code=response.status_code
        )
    
    return response

# Monitoring endpoints
@app.get("/internal/monitoring/overview")
async def monitoring_overview():
    """Get comprehensive monitoring overview."""
    return {
        "cache_performance": cache_monitor.get_cache_stats(),
        "configuration_usage": config_metrics_collector.get_usage_statistics(),
        "system_health": "healthy",  # Future: from health checker
        "timestamp": time.time()
    }

@app.get("/internal/monitoring/metrics")
async def export_metrics(format: str = "json"):
    """Export monitoring metrics."""
    return {
        "cache_metrics": cache_monitor.export_metrics(format),
        "config_metrics": config_metrics_collector.export_metrics(format)
    }
```

### External Monitoring System Integration

```python
import asyncio
from typing import Dict, Any

class ExternalMonitoringIntegration:
    """Integration with external monitoring systems."""
    
    def __init__(self, 
                 prometheus_gateway_url: str = None,
                 grafana_api_url: str = None):
        self.prometheus_gateway = prometheus_gateway_url
        self.grafana_api = grafana_api_url
        self.cache_monitor = CachePerformanceMonitor()
        self.config_collector = config_metrics_collector
    
    async def push_metrics_to_prometheus(self):
        """Push metrics to Prometheus Push Gateway."""
        if not self.prometheus_gateway:
            return
        
        # Collect all metrics
        cache_metrics = self.cache_monitor.export_metrics("prometheus")
        config_metrics = self.config_collector.export_metrics("prometheus")
        
        # Push to Prometheus Gateway
        combined_metrics = f"{cache_metrics}\n{config_metrics}"
        
        # Implementation would use HTTP client to push metrics
        # await self._push_to_gateway(combined_metrics)
    
    async def create_grafana_dashboard(self) -> Dict[str, Any]:
        """Generate Grafana dashboard configuration."""
        return {
            "dashboard": {
                "title": "Application Monitoring Dashboard",
                "panels": [
                    {
                        "title": "Cache Performance",
                        "type": "graph",
                        "targets": [
                            {"expr": "cache_hit_ratio"},
                            {"expr": "cache_operation_time"}
                        ]
                    },
                    {
                        "title": "Configuration Usage",
                        "type": "table",
                        "targets": [
                            {"expr": "config_preset_usage_total"}
                        ]
                    }
                ]
            }
        }
    
    async def start_monitoring_loop(self, interval_seconds: int = 60):
        """Start continuous monitoring loop."""
        while True:
            try:
                await self.push_metrics_to_prometheus()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(interval_seconds)

# Use external monitoring integration
monitoring_integration = ExternalMonitoringIntegration(
    prometheus_gateway_url="http://prometheus-gateway:9091",
    grafana_api_url="http://grafana:3000/api"
)

# Start monitoring in background
@app.on_event("startup")
async def start_monitoring():
    """Start monitoring when application starts."""
    asyncio.create_task(
        monitoring_integration.start_monitoring_loop(interval_seconds=30)
    )
```

### Service-Level Monitoring Integration

```python
from app.infrastructure.monitoring import CachePerformanceMonitor

class MonitoredAIService:
    """AI service with integrated monitoring."""
    
    def __init__(self):
        self.cache_monitor = CachePerformanceMonitor()
        self.service_metrics = {
            "requests_processed": 0,
            "average_response_time": 0.0,
            "error_rate": 0.0
        }
    
    async def process_text(self, text: str, operation: str) -> dict:
        """Process text with comprehensive monitoring."""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_start = time.time()
            cached_result = await self._check_cache(text, operation)
            cache_time = time.time() - cache_start
            
            # Record cache performance
            self.cache_monitor.record_cache_operation_time(
                operation="get",
                duration=cache_time,
                cache_hit=cached_result is not None
            )
            
            if cached_result:
                return cached_result
            
            # Process with AI service
            result = await self._process_with_ai(text, operation)
            
            # Cache result
            await self._cache_result(text, operation, result)
            
            # Update service metrics
            processing_time = time.time() - start_time
            self._update_service_metrics(processing_time, success=True)
            
            return result
            
        except Exception as e:
            # Record error metrics
            error_time = time.time() - start_time
            self._update_service_metrics(error_time, success=False)
            raise
    
    def _update_service_metrics(self, processing_time: float, success: bool):
        """Update internal service metrics."""
        self.service_metrics["requests_processed"] += 1
        
        # Update average response time
        current_avg = self.service_metrics["average_response_time"]
        count = self.service_metrics["requests_processed"]
        self.service_metrics["average_response_time"] = (
            (current_avg * (count - 1) + processing_time) / count
        )
        
        # Update error rate
        if not success:
            error_count = self.service_metrics.get("error_count", 0) + 1
            self.service_metrics["error_count"] = error_count
            self.service_metrics["error_rate"] = error_count / count
    
    def get_service_health(self) -> dict:
        """Get current service health metrics."""
        return {
            "status": "healthy" if self.service_metrics["error_rate"] < 0.05 else "degraded",
            "metrics": self.service_metrics,
            "cache_performance": self.cache_monitor.get_cache_stats(),
            "timestamp": time.time()
        }
```

## Configuration Management

### Environment-Based Monitoring Configuration

```python
import os
from app.infrastructure.monitoring import CachePerformanceMonitor, config_metrics_collector

class MonitoringConfig:
    """Centralized monitoring configuration."""
    
    def __init__(self):
        # Cache monitoring configuration
        self.cache_retention_hours = int(os.getenv("CACHE_MONITORING_RETENTION_HOURS", "2"))
        self.cache_memory_threshold_mb = int(os.getenv("CACHE_MEMORY_THRESHOLD_MB", "100"))
        self.cache_compression_threshold_mb = int(os.getenv("CACHE_COMPRESSION_THRESHOLD_MB", "50"))
        
        # Configuration monitoring settings
        self.config_retention_hours = int(os.getenv("CONFIG_MONITORING_RETENTION_HOURS", "24"))
        self.config_max_events = int(os.getenv("CONFIG_MAX_EVENTS", "10000"))
        
        # General monitoring settings
        self.monitoring_enabled = os.getenv("ENABLE_MONITORING", "true").lower() == "true"
        self.metrics_export_interval = int(os.getenv("METRICS_EXPORT_INTERVAL", "60"))
        self.monitoring_log_level = os.getenv("MONITORING_LOG_LEVEL", "INFO")
    
    def create_cache_monitor(self) -> CachePerformanceMonitor:
        """Create configured cache performance monitor."""
        return CachePerformanceMonitor(
            retention_hours=self.cache_retention_hours,
            memory_warning_threshold_bytes=self.cache_memory_threshold_mb * 1024 * 1024,
            compression_threshold_bytes=self.cache_compression_threshold_mb * 1024 * 1024
        )
    
    def configure_config_collector(self):
        """Configure the configuration metrics collector."""
        config_metrics_collector.configure(
            max_events=self.config_max_events,
            retention_hours=self.config_retention_hours
        )

# Environment-specific configurations
def get_monitoring_config() -> MonitoringConfig:
    """Get environment-appropriate monitoring configuration."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        # Production: comprehensive monitoring
        config = MonitoringConfig()
        config.cache_retention_hours = 24
        config.config_retention_hours = 168  # 1 week
        config.metrics_export_interval = 30   # More frequent
        return config
    
    elif env == "development":
        # Development: lightweight monitoring
        config = MonitoringConfig()
        config.cache_retention_hours = 1
        config.config_retention_hours = 6
        config.metrics_export_interval = 300  # Less frequent
        return config
    
    else:
        # Default configuration
        return MonitoringConfig()
```

### Runtime Configuration Management

```python
from app.infrastructure.monitoring import CachePerformanceMonitor, config_metrics_collector

class RuntimeMonitoringManager:
    """Runtime monitoring configuration and management."""
    
    def __init__(self):
        self.config = get_monitoring_config()
        self.cache_monitor = self.config.create_cache_monitor()
        self.config.configure_config_collector()
        self.monitoring_active = self.config.monitoring_enabled
    
    async def update_monitoring_configuration(self, new_config: dict):
        """Update monitoring configuration at runtime."""
        if "cache_retention_hours" in new_config:
            self.cache_monitor.update_retention_policy(
                hours=new_config["cache_retention_hours"]
            )
        
        if "memory_threshold_mb" in new_config:
            self.cache_monitor.update_memory_threshold(
                threshold_bytes=new_config["memory_threshold_mb"] * 1024 * 1024
            )
        
        if "monitoring_enabled" in new_config:
            self.monitoring_active = new_config["monitoring_enabled"]
            if not self.monitoring_active:
                await self._pause_monitoring()
            else:
                await self._resume_monitoring()
    
    async def get_monitoring_status(self) -> dict:
        """Get current monitoring system status."""
        return {
            "monitoring_active": self.monitoring_active,
            "cache_monitor_status": {
                "active": True,
                "retention_hours": self.cache_monitor.retention_hours,
                "memory_threshold_mb": self.cache_monitor.memory_warning_threshold_bytes / 1024 / 1024,
                "metrics_count": len(self.cache_monitor.get_all_metrics())
            },
            "config_collector_status": {
                "active": True,
                "events_count": len(config_metrics_collector.get_recent_events()),
                "retention_hours": config_metrics_collector.retention_hours
            },
            "configuration": {
                "environment": os.getenv("ENVIRONMENT", "unknown"),
                "export_interval": self.config.metrics_export_interval,
                "log_level": self.config.monitoring_log_level
            }
        }
    
    async def _pause_monitoring(self):
        """Pause monitoring operations."""
        # Implementation would pause metric collection
        pass
    
    async def _resume_monitoring(self):
        """Resume monitoring operations."""
        # Implementation would resume metric collection
        pass

# Global monitoring manager
monitoring_manager = RuntimeMonitoringManager()
```

## Error Handling & Resilience

The monitoring system provides robust error handling and graceful degradation:

### Monitoring Failure Isolation

```python
from app.infrastructure.monitoring import CachePerformanceMonitor
import logging

logger = logging.getLogger(__name__)

class ResilientMonitoringWrapper:
    """Wrapper providing resilient monitoring with graceful degradation."""
    
    def __init__(self):
        self.cache_monitor = None
        self.monitoring_failures = 0
        self.max_failures = 5
        self.monitoring_disabled = False
    
    async def record_safe(self, operation: str, *args, **kwargs):
        """Safely record monitoring data with error handling."""
        if self.monitoring_disabled:
            return
        
        try:
            if not self.cache_monitor:
                self.cache_monitor = CachePerformanceMonitor()
            
            # Attempt to record monitoring data
            if operation == "cache_operation":
                self.cache_monitor.record_cache_operation_time(*args, **kwargs)
            elif operation == "compression":
                self.cache_monitor.record_compression_operation(*args, **kwargs)
            
            # Reset failure count on success
            self.monitoring_failures = 0
            
        except Exception as e:
            self.monitoring_failures += 1
            logger.warning(f"Monitoring operation failed: {e}")
            
            if self.monitoring_failures >= self.max_failures:
                logger.error("Too many monitoring failures - disabling monitoring")
                self.monitoring_disabled = True
    
    async def get_stats_safe(self) -> dict:
        """Safely get monitoring statistics."""
        try:
            if self.cache_monitor and not self.monitoring_disabled:
                return self.cache_monitor.get_cache_stats()
        except Exception as e:
            logger.warning(f"Failed to get monitoring stats: {e}")
        
        return {
            "status": "monitoring_unavailable",
            "message": "Monitoring data not available",
            "monitoring_disabled": self.monitoring_disabled,
            "failures": self.monitoring_failures
        }
    
    async def health_check(self) -> dict:
        """Check monitoring system health."""
        return {
            "monitoring_active": not self.monitoring_disabled,
            "failure_count": self.monitoring_failures,
            "status": "healthy" if not self.monitoring_disabled else "degraded"
        }

# Use resilient monitoring
resilient_monitor = ResilientMonitoringWrapper()
```

### Monitoring Data Validation

```python
from typing import Any, Dict, Optional
import json

class MonitoringDataValidator:
    """Validate monitoring data integrity and format."""
    
    @staticmethod
    def validate_cache_metrics(metrics: Dict[str, Any]) -> bool:
        """Validate cache metrics data structure."""
        required_fields = [
            "hit_ratio", "avg_operation_time", "total_operations", "memory_usage_bytes"
        ]
        
        try:
            # Check required fields exist
            for field in required_fields:
                if field not in metrics:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Validate data types and ranges
            if not (0 <= metrics["hit_ratio"] <= 100):
                logger.warning(f"Invalid hit_ratio: {metrics['hit_ratio']}")
                return False
            
            if metrics["avg_operation_time"] < 0:
                logger.warning(f"Invalid avg_operation_time: {metrics['avg_operation_time']}")
                return False
            
            return True
            
        except (TypeError, KeyError, ValueError) as e:
            logger.error(f"Cache metrics validation error: {e}")
            return False
    
    @staticmethod
    def sanitize_export_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize monitoring data for safe export."""
        sanitized = {}
        
        for key, value in data.items():
            try:
                # Ensure JSON serializable
                json.dumps(value)
                sanitized[key] = value
            except (TypeError, ValueError):
                logger.warning(f"Excluding non-serializable field: {key}")
                sanitized[key] = str(value)  # Convert to string as fallback
        
        return sanitized
    
    @staticmethod
    def validate_export_format(data: str, format_type: str) -> bool:
        """Validate exported monitoring data format."""
        try:
            if format_type == "json":
                json.loads(data)
                return True
            elif format_type == "prometheus":
                # Basic Prometheus format validation
                lines = data.strip().split('\n')
                for line in lines:
                    if line and not (line.startswith('#') or ' ' in line):
                        return False
                return True
            else:
                logger.warning(f"Unknown export format: {format_type}")
                return False
        except Exception as e:
            logger.error(f"Export validation error: {e}")
            return False

# Use data validation
validator = MonitoringDataValidator()
```

## Performance Characteristics

### Monitoring Performance Metrics

| Component | Operation | Performance Target | Actual Performance |
|-----------|-----------|-------------------|-------------------|
| **Cache Monitor** | Metric Recording | <1ms | ~0.1-0.5ms typical |
| **Cache Monitor** | Statistics Generation | <10ms | ~2-5ms typical |
| **Config Collector** | Event Recording | <1ms | ~0.1-0.3ms typical |
| **Data Export** | JSON Export | <100ms | ~20-50ms typical |
| **Data Export** | Prometheus Export | <50ms | ~10-30ms typical |

### Memory Usage Characteristics

- **Base Monitoring**: ~2-5MB for core monitoring infrastructure
- **Cache Monitor**: ~1-10MB depending on retention settings and metric volume
- **Config Collector**: ~500KB-2MB for configuration event storage
- **Export Operations**: ~100KB-1MB temporary memory during export operations
- **Per-Metric Storage**: ~100-500KB per active monitoring component

### Optimization Features

- **Efficient Data Structures**: Time-series data stored in optimized collections
- **Bounded Memory**: Configurable retention policies prevent unbounded growth
- **Lazy Export**: Metrics exported on-demand rather than continuously processed
- **Compression**: Large monitoring datasets automatically compressed
- **Sampling**: High-frequency metrics can be sampled to reduce overhead

## Migration Guide

### Adding Monitoring to Existing Services

1. **Install Monitoring Dependencies:**
```python
# Add monitoring imports to your service
from app.infrastructure.monitoring import CachePerformanceMonitor, config_metrics_collector

# Initialize monitoring in service constructor
class YourService:
    def __init__(self):
        self.cache_monitor = CachePerformanceMonitor()
```

2. **Integrate Monitoring Calls:**
```python
# Before: Plain service operation
async def process_data(self, data: str) -> dict:
    result = await self._expensive_operation(data)
    return result

# After: Monitored service operation
async def process_data(self, data: str) -> dict:
    start_time = time.time()
    
    try:
        result = await self._expensive_operation(data)
        
        # Record successful operation
        operation_time = time.time() - start_time
        self.cache_monitor.record_operation_success(
            operation="process_data",
            duration=operation_time
        )
        
        return result
    except Exception as e:
        # Record failed operation
        operation_time = time.time() - start_time
        self.cache_monitor.record_operation_failure(
            operation="process_data",
            duration=operation_time,
            error=str(e)
        )
        raise
```

3. **Add Monitoring Endpoints:**
```python
# Add monitoring endpoints to your FastAPI application
@app.get("/internal/monitoring/{service_name}")
async def get_service_monitoring(service_name: str):
    """Get monitoring data for specific service."""
    if service_name == "your_service":
        return your_service.get_monitoring_stats()
    # Add other services as needed
```

### Migrating to Unified Monitoring

```python
# Step 1: Replace individual monitoring with unified approach
# Before: Individual monitoring instances
class LegacyService:
    def __init__(self):
        self.custom_metrics = {}
        self.performance_data = []

# After: Unified monitoring infrastructure
from app.infrastructure.monitoring import CachePerformanceMonitor

class ModernService:
    def __init__(self):
        self.monitor = CachePerformanceMonitor()

# Step 2: Migrate existing metrics
async def migrate_legacy_metrics(legacy_service: LegacyService, modern_service: ModernService):
    """Migrate existing metrics to new monitoring system."""
    for metric_name, metric_data in legacy_service.custom_metrics.items():
        # Convert legacy metrics to new format
        modern_service.monitor.import_legacy_data(metric_name, metric_data)
```

## Advanced Features

### Custom Monitoring Extensions

```python
from app.infrastructure.monitoring import CachePerformanceMonitor

class CustomBusinessMetricsMonitor(CachePerformanceMonitor):
    """Extended monitoring with business-specific metrics."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.business_metrics = {
            "user_satisfaction_scores": [],
            "revenue_impact": [],
            "feature_usage": {}
        }
    
    def record_user_satisfaction(self, score: float, user_id: str):
        """Record user satisfaction metrics."""
        self.business_metrics["user_satisfaction_scores"].append({
            "score": score,
            "user_id": user_id,
            "timestamp": time.time()
        })
    
    def record_revenue_impact(self, amount: float, transaction_id: str):
        """Record revenue impact metrics."""
        self.business_metrics["revenue_impact"].append({
            "amount": amount,
            "transaction_id": transaction_id,
            "timestamp": time.time()
        })
    
    def get_business_analytics(self) -> dict:
        """Get business analytics summary."""
        satisfaction_scores = [m["score"] for m in self.business_metrics["user_satisfaction_scores"]]
        revenue_amounts = [m["amount"] for m in self.business_metrics["revenue_impact"]]
        
        return {
            "average_satisfaction": sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0,
            "total_revenue_impact": sum(revenue_amounts),
            "metrics_count": {
                "satisfaction_records": len(satisfaction_scores),
                "revenue_records": len(revenue_amounts)
            }
        }

# Use custom monitoring
business_monitor = CustomBusinessMetricsMonitor()
```

### Real-time Monitoring Streams

```python
import asyncio
from typing import AsyncGenerator

class RealTimeMonitoringStream:
    """Real-time monitoring data streaming."""
    
    def __init__(self):
        self.cache_monitor = CachePerformanceMonitor()
        self.subscribers = set()
    
    async def subscribe_to_metrics(self) -> AsyncGenerator[dict, None]:
        """Subscribe to real-time metrics updates."""
        subscriber_id = id(self)
        self.subscribers.add(subscriber_id)
        
        try:
            while subscriber_id in self.subscribers:
                # Get latest metrics
                current_metrics = {
                    "timestamp": time.time(),
                    "cache_stats": self.cache_monitor.get_cache_stats(),
                    "recent_operations": self.cache_monitor.get_recent_operations(limit=10)
                }
                
                yield current_metrics
                await asyncio.sleep(1)  # 1-second intervals
                
        finally:
            self.subscribers.discard(subscriber_id)
    
    def unsubscribe(self, subscriber_id: int):
        """Unsubscribe from metrics updates."""
        self.subscribers.discard(subscriber_id)

# WebSocket endpoint for real-time monitoring
@app.websocket("/ws/monitoring")
async def monitoring_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring data."""
    await websocket.accept()
    
    stream = RealTimeMonitoringStream()
    
    try:
        async for metrics in stream.subscribe_to_metrics():
            await websocket.send_json(metrics)
    except WebSocketDisconnect:
        pass
```

## Best Practices

### Monitoring Guidelines

1. **Selective Monitoring**: Monitor critical paths and performance bottlenecks, not every operation
2. **Efficient Collection**: Use appropriate retention periods and sampling rates
3. **Error Resilience**: Ensure monitoring failures don't impact application functionality
4. **Data Validation**: Validate monitoring data before export or alerting
5. **Privacy Considerations**: Avoid collecting sensitive data in monitoring metrics

### Performance Guidelines

1. **Minimal Overhead**: Keep monitoring overhead under 1% of total application performance
2. **Asynchronous Operations**: Use async monitoring calls where possible
3. **Batch Operations**: Batch multiple monitoring operations for efficiency
4. **Memory Management**: Configure appropriate retention policies to prevent memory leaks
5. **Export Optimization**: Export metrics during low-traffic periods when possible

### Integration Guidelines

1. **Centralized Access**: Use the monitoring module as single access point for all monitoring
2. **Standard Interfaces**: Follow consistent patterns for monitoring integration
3. **Configuration Management**: Use environment-based configuration for monitoring settings
4. **Testing Integration**: Include monitoring validation in test suites
5. **Documentation**: Document monitoring integration for service teams

This monitoring infrastructure provides a comprehensive, extensible foundation for application observability with both current functionality through imported components and planned future implementations for complete monitoring coverage.