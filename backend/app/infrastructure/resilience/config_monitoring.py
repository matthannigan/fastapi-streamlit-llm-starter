"""
Configuration monitoring and metrics collection for preset usage tracking.

This module provides comprehensive monitoring capabilities for resilience
configuration including usage patterns, performance metrics, and change auditing.
"""

import time
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of configuration metrics."""
    PRESET_USAGE = "preset_usage"
    CONFIG_LOAD = "config_load"
    CONFIG_ERROR = "config_error"
    CONFIG_CHANGE = "config_change"
    VALIDATION_EVENT = "validation_event"
    PERFORMANCE_EVENT = "performance_event"


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ConfigurationMetric:
    """Individual configuration metric event."""
    timestamp: datetime
    metric_type: MetricType
    preset_name: str
    operation: str
    value: float
    metadata: Dict[str, Any]
    session_id: Optional[str] = None
    user_context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary for serialization."""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'metric_type': self.metric_type.value
        }


@dataclass
class ConfigurationAlert:
    """Configuration monitoring alert."""
    timestamp: datetime
    level: AlertLevel
    title: str
    description: str
    preset_name: str
    metric_type: MetricType
    threshold_value: float
    actual_value: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for serialization."""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'metric_type': self.metric_type.value
        }


class ConfigurationUsageStats(NamedTuple):
    """Configuration usage statistics."""
    total_loads: int
    preset_usage_count: Dict[str, int]
    error_rate: float
    avg_load_time_ms: float
    most_used_preset: str
    least_used_preset: str
    custom_config_usage_rate: float
    legacy_config_usage_rate: float


class ConfigurationMetricsCollector:
    """
    Collects and aggregates configuration metrics.
    
    Provides real-time monitoring of configuration usage patterns,
    performance metrics, and operational health.
    """
    
    def __init__(self, max_events: int = 10000, retention_hours: int = 24):
        """
        Initialize metrics collector.
        
        Args:
            max_events: Maximum number of events to keep in memory
            retention_hours: Hours to retain metrics data
        """
        self.max_events = max_events
        self.retention_hours = retention_hours
        self.metrics: deque = deque(maxlen=max_events)
        self.alerts: List[ConfigurationAlert] = []
        self.session_metrics: Dict[str, List[ConfigurationMetric]] = defaultdict(list)
        
        # Threading for concurrent access
        self._lock = threading.RLock()
        
        # Aggregated statistics cache
        self._stats_cache: Optional[ConfigurationUsageStats] = None
        self._stats_cache_time: Optional[datetime] = None
        self._cache_ttl_seconds = 60  # 1 minute cache
        
        # Alert thresholds
        self.alert_thresholds = {
            'error_rate_threshold': 0.05,  # 5% error rate
            'load_time_threshold_ms': 100.0,  # 100ms load time
            'config_change_frequency_threshold': 10,  # 10 changes per hour
            'validation_failure_threshold': 0.10,  # 10% validation failures
        }
        
        logger.info("ConfigurationMetricsCollector initialized")
    
    @contextmanager
    def track_config_operation(self, operation: str, preset_name: str = "unknown", 
                              session_id: Optional[str] = None, user_context: Optional[str] = None):
        """
        Context manager for tracking configuration operations.
        
        Args:
            operation: Name of the operation being tracked
            preset_name: Configuration preset being used
            session_id: Optional session identifier
            user_context: Optional user context information
        """
        start_time = time.perf_counter()
        error_occurred = False
        
        try:
            yield
        except Exception as e:
            error_occurred = True
            self.record_config_error(preset_name, operation, str(e), session_id, user_context)
            raise
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            if not error_occurred:
                self.record_config_load(preset_name, operation, duration_ms, session_id, user_context)
    
    def record_preset_usage(self, preset_name: str, operation: str = "load", 
                           session_id: Optional[str] = None, user_context: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None):
        """
        Record usage of a specific preset.
        
        Args:
            preset_name: Name of the preset used
            operation: Operation performed
            session_id: Optional session identifier
            user_context: Optional user context
            metadata: Additional metadata about the usage
        """
        metric = ConfigurationMetric(
            timestamp=datetime.utcnow(),
            metric_type=MetricType.PRESET_USAGE,
            preset_name=preset_name,
            operation=operation,
            value=1.0,
            metadata=metadata or {},
            session_id=session_id,
            user_context=user_context
        )
        
        self._record_metric(metric)
        logger.debug(f"Recorded preset usage: {preset_name} - {operation}")
    
    def record_config_load(self, preset_name: str, operation: str, duration_ms: float,
                          session_id: Optional[str] = None, user_context: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None):
        """
        Record configuration loading performance.
        
        Args:
            preset_name: Name of the preset loaded
            operation: Operation performed
            duration_ms: Load time in milliseconds
            session_id: Optional session identifier
            user_context: Optional user context
            metadata: Additional metadata about the load
        """
        metric = ConfigurationMetric(
            timestamp=datetime.utcnow(),
            metric_type=MetricType.CONFIG_LOAD,
            preset_name=preset_name,
            operation=operation,
            value=duration_ms,
            metadata=metadata or {},
            session_id=session_id,
            user_context=user_context
        )
        
        self._record_metric(metric)
        
        # Check performance threshold
        if duration_ms > self.alert_thresholds['load_time_threshold_ms']:
            self._create_performance_alert(preset_name, duration_ms)
        
        logger.debug(f"Recorded config load: {preset_name} - {duration_ms:.2f}ms")
    
    def record_config_error(self, preset_name: str, operation: str, error_message: str,
                           session_id: Optional[str] = None, user_context: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None):
        """
        Record configuration error.
        
        Args:
            preset_name: Name of the preset that caused error
            operation: Operation that failed
            error_message: Error message
            session_id: Optional session identifier
            user_context: Optional user context
            metadata: Additional error metadata
        """
        error_metadata = {
            'error_message': error_message,
            **(metadata or {})
        }
        
        metric = ConfigurationMetric(
            timestamp=datetime.utcnow(),
            metric_type=MetricType.CONFIG_ERROR,
            preset_name=preset_name,
            operation=operation,
            value=1.0,
            metadata=error_metadata,
            session_id=session_id,
            user_context=user_context
        )
        
        self._record_metric(metric)
        self._create_error_alert(preset_name, operation, error_message)
        logger.warning(f"Recorded config error: {preset_name} - {operation}: {error_message}")
    
    def record_config_change(self, old_preset: str, new_preset: str, operation: str = "change",
                            session_id: Optional[str] = None, user_context: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None):
        """
        Record configuration change event.
        
        Args:
            old_preset: Previous preset name
            new_preset: New preset name
            operation: Type of change operation
            session_id: Optional session identifier
            user_context: Optional user context
            metadata: Additional change metadata
        """
        change_metadata = {
            'old_preset': old_preset,
            'new_preset': new_preset,
            **(metadata or {})
        }
        
        metric = ConfigurationMetric(
            timestamp=datetime.utcnow(),
            metric_type=MetricType.CONFIG_CHANGE,
            preset_name=new_preset,
            operation=operation,
            value=1.0,
            metadata=change_metadata,
            session_id=session_id,
            user_context=user_context
        )
        
        self._record_metric(metric)
        logger.info(f"Recorded config change: {old_preset} -> {new_preset}")
    
    def record_validation_event(self, preset_name: str, is_valid: bool, operation: str = "validate",
                               session_id: Optional[str] = None, user_context: Optional[str] = None,
                               validation_errors: Optional[List[str]] = None,
                               metadata: Optional[Dict[str, Any]] = None):
        """
        Record configuration validation event.
        
        Args:
            preset_name: Name of the preset validated
            is_valid: Whether validation passed
            operation: Validation operation type
            session_id: Optional session identifier
            user_context: Optional user context
            validation_errors: List of validation errors if any
            metadata: Additional validation metadata
        """
        validation_metadata = {
            'is_valid': is_valid,
            'validation_errors': validation_errors or [],
            **(metadata or {})
        }
        
        metric = ConfigurationMetric(
            timestamp=datetime.utcnow(),
            metric_type=MetricType.VALIDATION_EVENT,
            preset_name=preset_name,
            operation=operation,
            value=1.0 if is_valid else 0.0,
            metadata=validation_metadata,
            session_id=session_id,
            user_context=user_context
        )
        
        self._record_metric(metric)
        logger.debug(f"Recorded validation event: {preset_name} - {'valid' if is_valid else 'invalid'}")
    
    def get_usage_statistics(self, time_window_hours: Optional[int] = None) -> ConfigurationUsageStats:
        """
        Get configuration usage statistics.
        
        Args:
            time_window_hours: Time window for statistics (None for all time)
            
        Returns:
            Configuration usage statistics
        """
        # Check cache first
        if (self._stats_cache and self._stats_cache_time and 
            (datetime.utcnow() - self._stats_cache_time).seconds < self._cache_ttl_seconds):
            return self._stats_cache
        
        with self._lock:
            # Filter metrics by time window
            cutoff_time = None
            if time_window_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
            
            relevant_metrics = [
                m for m in self.metrics 
                if not cutoff_time or m.timestamp >= cutoff_time
            ]
            
            if not relevant_metrics:
                return ConfigurationUsageStats(
                    total_loads=0,
                    preset_usage_count={},
                    error_rate=0.0,
                    avg_load_time_ms=0.0,
                    most_used_preset="none",
                    least_used_preset="none",
                    custom_config_usage_rate=0.0,
                    legacy_config_usage_rate=0.0
                )
            
            # Calculate statistics
            preset_counts = defaultdict(int)
            load_times = []
            error_count = 0
            total_loads = 0
            custom_config_count = 0
            legacy_config_count = 0
            
            for metric in relevant_metrics:
                if metric.metric_type == MetricType.PRESET_USAGE:
                    preset_counts[metric.preset_name] += 1
                elif metric.metric_type == MetricType.CONFIG_LOAD:
                    load_times.append(metric.value)
                    total_loads += 1
                elif metric.metric_type == MetricType.CONFIG_ERROR:
                    error_count += 1
                
                # Check for custom/legacy config usage
                if metric.metadata.get('config_type') == 'custom':
                    custom_config_count += 1
                elif metric.metadata.get('config_type') == 'legacy':
                    legacy_config_count += 1
            
            # Calculate derived statistics
            error_rate = error_count / max(total_loads, 1)
            avg_load_time = sum(load_times) / max(len(load_times), 1)
            
            most_used = max(preset_counts.items(), key=lambda x: x[1], default=("none", 0))[0]
            least_used = min(preset_counts.items(), key=lambda x: x[1], default=("none", 0))[0]
            
            total_operations = len(relevant_metrics)
            custom_rate = custom_config_count / max(total_operations, 1)
            legacy_rate = legacy_config_count / max(total_operations, 1)
            
            stats = ConfigurationUsageStats(
                total_loads=total_loads,
                preset_usage_count=dict(preset_counts),
                error_rate=error_rate,
                avg_load_time_ms=avg_load_time,
                most_used_preset=most_used,
                least_used_preset=least_used,
                custom_config_usage_rate=custom_rate,
                legacy_config_usage_rate=legacy_rate
            )
            
            # Cache the results
            self._stats_cache = stats
            self._stats_cache_time = datetime.utcnow()
            
            return stats
    
    def get_preset_usage_trend(self, preset_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get usage trend for a specific preset over time.
        
        Args:
            preset_name: Name of the preset
            hours: Number of hours to analyze
            
        Returns:
            List of hourly usage counts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Create hourly buckets
        hourly_usage = defaultdict(int)
        
        with self._lock:
            for metric in self.metrics:
                if (metric.timestamp >= cutoff_time and 
                    metric.preset_name == preset_name and
                    metric.metric_type == MetricType.PRESET_USAGE):
                    
                    hour_bucket = metric.timestamp.replace(minute=0, second=0, microsecond=0)
                    hourly_usage[hour_bucket] += 1
        
        # Convert to list format
        trend_data = []
        for hour in range(hours):
            bucket_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=hour)
            usage_count = hourly_usage.get(bucket_time, 0)
            trend_data.append({
                'timestamp': bucket_time.isoformat(),
                'usage_count': usage_count
            })
        
        return sorted(trend_data, key=lambda x: x['timestamp'])
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance metrics for configuration operations.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Performance metrics summary
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        load_times = []
        error_times = []
        preset_performance = defaultdict(list)
        
        with self._lock:
            for metric in self.metrics:
                if metric.timestamp >= cutoff_time:
                    if metric.metric_type == MetricType.CONFIG_LOAD:
                        load_times.append(metric.value)
                        preset_performance[metric.preset_name].append(metric.value)
                    elif metric.metric_type == MetricType.CONFIG_ERROR:
                        error_times.append(metric.timestamp)
        
        if not load_times:
            return {
                'avg_load_time_ms': 0.0,
                'min_load_time_ms': 0.0,
                'max_load_time_ms': 0.0,
                'p95_load_time_ms': 0.0,
                'error_count': 0,
                'preset_performance': {}
            }
        
        # Calculate percentiles
        sorted_times = sorted(load_times)
        p95_index = int(len(sorted_times) * 0.95)
        
        # Calculate per-preset performance
        preset_stats = {}
        for preset, times in preset_performance.items():
            if times:
                preset_stats[preset] = {
                    'avg_load_time_ms': sum(times) / len(times),
                    'min_load_time_ms': min(times),
                    'max_load_time_ms': max(times),
                    'sample_count': len(times)
                }
        
        return {
            'avg_load_time_ms': sum(load_times) / len(load_times),
            'min_load_time_ms': min(load_times),
            'max_load_time_ms': max(load_times),
            'p95_load_time_ms': sorted_times[p95_index] if sorted_times else 0.0,
            'error_count': len(error_times),
            'total_samples': len(load_times),
            'preset_performance': preset_stats
        }
    
    def get_active_alerts(self, max_alerts: int = 50) -> List[Dict[str, Any]]:
        """
        Get active configuration alerts.
        
        Args:
            max_alerts: Maximum number of alerts to return
            
        Returns:
            List of active alerts
        """
        # Filter recent alerts (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_alerts = [
            alert for alert in self.alerts[-max_alerts:]
            if alert.timestamp >= cutoff_time
        ]
        
        return [alert.to_dict() for alert in recent_alerts]
    
    def get_session_metrics(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get metrics for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of metrics for the session
        """
        session_metrics = self.session_metrics.get(session_id, [])
        return [metric.to_dict() for metric in session_metrics]
    
    def clear_old_metrics(self, hours: int = 24):
        """
        Clear metrics older than specified hours.
        
        Args:
            hours: Hours threshold for clearing old metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self._lock:
            # Filter metrics
            self.metrics = deque(
                (m for m in self.metrics if m.timestamp >= cutoff_time),
                maxlen=self.max_events
            )
            
            # Filter alerts
            self.alerts = [
                alert for alert in self.alerts
                if alert.timestamp >= cutoff_time
            ]
            
            # Clear old session metrics
            for session_id, metrics_list in list(self.session_metrics.items()):
                filtered_metrics = [
                    m for m in metrics_list if m.timestamp >= cutoff_time
                ]
                if filtered_metrics:
                    self.session_metrics[session_id] = filtered_metrics
                else:
                    del self.session_metrics[session_id]
        
        logger.info(f"Cleared metrics older than {hours} hours")
    
    def export_metrics(self, format: str = "json", time_window_hours: Optional[int] = None) -> str:
        """
        Export metrics in specified format.
        
        Args:
            format: Export format ('json' or 'csv')
            time_window_hours: Time window for export (None for all)
            
        Returns:
            Exported metrics as string
        """
        cutoff_time = None
        if time_window_hours:
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        relevant_metrics = [
            m for m in self.metrics 
            if not cutoff_time or m.timestamp >= cutoff_time
        ]
        
        if format.lower() == "json":
            return json.dumps([metric.to_dict() for metric in relevant_metrics], indent=2)
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if relevant_metrics:
                writer = csv.DictWriter(output, fieldnames=relevant_metrics[0].to_dict().keys())
                writer.writeheader()
                for metric in relevant_metrics:
                    writer.writerow(metric.to_dict())
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _record_metric(self, metric: ConfigurationMetric):
        """
        Record a metric internally.
        
        Args:
            metric: Metric to record
        """
        with self._lock:
            self.metrics.append(metric)
            
            # Add to session metrics if session_id provided
            if metric.session_id:
                self.session_metrics[metric.session_id].append(metric)
            
            # Invalidate stats cache
            self._stats_cache = None
            self._stats_cache_time = None
    
    def _create_error_alert(self, preset_name: str, operation: str, error_message: str):
        """
        Create an error alert.
        
        Args:
            preset_name: Preset that caused the error
            operation: Operation that failed
            error_message: Error message
        """
        alert = ConfigurationAlert(
            timestamp=datetime.utcnow(),
            level=AlertLevel.ERROR,
            title=f"Configuration Error: {preset_name}",
            description=f"Error in {operation}: {error_message}",
            preset_name=preset_name,
            metric_type=MetricType.CONFIG_ERROR,
            threshold_value=0.0,
            actual_value=1.0,
            metadata={'operation': operation, 'error_message': error_message}
        )
        
        self.alerts.append(alert)
        logger.warning(f"Created error alert for {preset_name}: {error_message}")
    
    def _create_performance_alert(self, preset_name: str, load_time_ms: float):
        """
        Create a performance alert.
        
        Args:
            preset_name: Preset with performance issue
            load_time_ms: Actual load time
        """
        threshold = self.alert_thresholds['load_time_threshold_ms']
        
        alert = ConfigurationAlert(
            timestamp=datetime.utcnow(),
            level=AlertLevel.WARNING,
            title=f"Slow Configuration Load: {preset_name}",
            description=f"Configuration load time ({load_time_ms:.2f}ms) exceeds threshold ({threshold}ms)",
            preset_name=preset_name,
            metric_type=MetricType.PERFORMANCE_EVENT,
            threshold_value=threshold,
            actual_value=load_time_ms,
            metadata={'load_time_ms': load_time_ms}
        )
        
        self.alerts.append(alert)
        logger.warning(f"Created performance alert for {preset_name}: {load_time_ms:.2f}ms")


# Global metrics collector instance
config_metrics_collector = ConfigurationMetricsCollector()