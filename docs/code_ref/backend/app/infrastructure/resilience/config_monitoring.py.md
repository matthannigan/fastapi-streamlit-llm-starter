---
sidebar_label: config_monitoring
---

# Configuration monitoring and metrics collection for preset usage tracking.

  file_path: `backend/app/infrastructure/resilience/config_monitoring.py`

This module provides comprehensive monitoring capabilities for resilience
configuration including usage patterns, performance metrics, and change auditing.

## MetricType

Types of configuration metrics.

## AlertLevel

Alert severity levels.

## ConfigurationMetric

Individual configuration metric event.

### to_dict()

```python
def to_dict(self) -> Dict[str, Any]:
```

Convert metric to dictionary for serialization.

## ConfigurationAlert

Configuration monitoring alert.

### to_dict()

```python
def to_dict(self) -> Dict[str, Any]:
```

Convert alert to dictionary for serialization.

## ConfigurationUsageStats

Configuration usage statistics.

## ConfigurationMetricsCollector

Collects and aggregates configuration metrics.

Provides real-time monitoring of configuration usage patterns,
performance metrics, and operational health.

### __init__()

```python
def __init__(self, max_events: int = 10000, retention_hours: int = 24):
```

Initialize metrics collector.

Args:
    max_events: Maximum number of events to keep in memory
    retention_hours: Hours to retain metrics data

### track_config_operation()

```python
def track_config_operation(self, operation: str, preset_name: str = 'unknown', session_id: Optional[str] = None, user_context: Optional[str] = None):
```

Context manager for tracking configuration operations.

Args:
    operation: Name of the operation being tracked
    preset_name: Configuration preset being used
    session_id: Optional session identifier
    user_context: Optional user context information

### record_preset_usage()

```python
def record_preset_usage(self, preset_name: str, operation: str = 'load', session_id: Optional[str] = None, user_context: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
```

Record usage of a specific preset.

Args:
    preset_name: Name of the preset used
    operation: Operation performed
    session_id: Optional session identifier
    user_context: Optional user context
    metadata: Additional metadata about the usage

### record_config_load()

```python
def record_config_load(self, preset_name: str, operation: str, duration_ms: float, session_id: Optional[str] = None, user_context: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
```

Record configuration loading performance.

Args:
    preset_name: Name of the preset loaded
    operation: Operation performed
    duration_ms: Load time in milliseconds
    session_id: Optional session identifier
    user_context: Optional user context
    metadata: Additional metadata about the load

### record_config_error()

```python
def record_config_error(self, preset_name: str, operation: str, error_message: str, session_id: Optional[str] = None, user_context: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
```

Record configuration error.

Args:
    preset_name: Name of the preset that caused error
    operation: Operation that failed
    error_message: Error message
    session_id: Optional session identifier
    user_context: Optional user context
    metadata: Additional error metadata

### record_config_change()

```python
def record_config_change(self, old_preset: str, new_preset: str, operation: str = 'change', session_id: Optional[str] = None, user_context: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
```

Record configuration change event.

Args:
    old_preset: Previous preset name
    new_preset: New preset name
    operation: Type of change operation
    session_id: Optional session identifier
    user_context: Optional user context
    metadata: Additional change metadata

### record_validation_event()

```python
def record_validation_event(self, preset_name: str, is_valid: bool, operation: str = 'validate', session_id: Optional[str] = None, user_context: Optional[str] = None, validation_errors: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
```

Record configuration validation event.

Args:
    preset_name: Name of the preset validated
    is_valid: Whether validation passed
    operation: Validation operation type
    session_id: Optional session identifier
    user_context: Optional user context
    validation_errors: List of validation errors if any
    metadata: Additional validation metadata

### get_usage_statistics()

```python
def get_usage_statistics(self, time_window_hours: Optional[int] = None) -> ConfigurationUsageStats:
```

Get configuration usage statistics.

Args:
    time_window_hours: Time window for statistics (None for all time)
    
Returns:
    Configuration usage statistics

### get_preset_usage_trend()

```python
def get_preset_usage_trend(self, preset_name: str, hours: int = 24) -> List[Dict[str, Any]]:
```

Get usage trend for a specific preset over time.

Args:
    preset_name: Name of the preset
    hours: Number of hours to analyze
    
Returns:
    List of hourly usage counts

### get_performance_metrics()

```python
def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
```

Get performance metrics for configuration operations.

Args:
    hours: Number of hours to analyze
    
Returns:
    Performance metrics summary

### get_active_alerts()

```python
def get_active_alerts(self, max_alerts: int = 50) -> List[Dict[str, Any]]:
```

Get active configuration alerts.

Args:
    max_alerts: Maximum number of alerts to return
    
Returns:
    List of active alerts

### get_session_metrics()

```python
def get_session_metrics(self, session_id: str) -> List[Dict[str, Any]]:
```

Get metrics for a specific session.

Args:
    session_id: Session identifier
    
Returns:
    List of metrics for the session

### clear_old_metrics()

```python
def clear_old_metrics(self, hours: int = 24):
```

Clear metrics older than specified hours.

Args:
    hours: Hours threshold for clearing old metrics

### export_metrics()

```python
def export_metrics(self, format: str = 'json', time_window_hours: Optional[int] = None) -> str:
```

Export metrics in specified format.

Args:
    format: Export format ('json' or 'csv')
    time_window_hours: Time window for export (None for all)
    
Returns:
    Exported metrics as string
