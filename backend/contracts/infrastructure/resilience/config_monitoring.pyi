"""
Configuration monitoring and metrics collection for preset usage tracking.

This module provides comprehensive monitoring capabilities for resilience
configuration including usage patterns, performance metrics, and change auditing.
"""

import time
import json
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
from contextlib import contextmanager


class MetricType(Enum):
    """
    Enumeration of configuration metric types for comprehensive monitoring and analysis.
    
    Defines the categories of metrics that can be collected for resilience configuration
    monitoring, enabling detailed analysis of usage patterns, performance characteristics,
    and operational health.
    
    Values:
        PRESET_USAGE: Tracks usage of specific configuration presets
        CONFIG_LOAD: Monitors configuration loading performance and timing
        CONFIG_ERROR: Records configuration errors and failure patterns
        CONFIG_CHANGE: Logs configuration changes and modifications
        VALIDATION_EVENT: Tracks configuration validation results
        PERFORMANCE_EVENT: Monitors performance-related configuration events
    
    Usage:
        # Select metric type for recording
        metric_type = MetricType.PRESET_USAGE
    
        # Use in metric creation
        metric = ConfigurationMetric(
            timestamp=datetime.now(),
            metric_type=MetricType.CONFIG_LOAD,
            preset_name="production",
            operation="load",
            value=150.0,
            metadata={}
        )
    """

    ...


class AlertLevel(Enum):
    """
    Enumeration of alert severity levels for configuration monitoring notifications.
    
    Defines the severity classification for configuration-related alerts, enabling
    appropriate prioritization and response strategies for different types of
    configuration events and issues.
    
    Values:
        INFO: Informational alerts for routine configuration events
        WARNING: Warning alerts for potential issues that may need attention
        ERROR: Error alerts for configuration problems requiring investigation
        CRITICAL: Critical alerts for severe configuration issues needing immediate action
    
    Usage:
        # Determine alert severity based on conditions
        if load_time_ms > threshold:
            level = AlertLevel.WARNING
        elif validation_failed:
            level = AlertLevel.ERROR
    
        # Create alert with appropriate severity
        alert = ConfigurationAlert(
            timestamp=datetime.now(),
            level=AlertLevel.WARNING,
            title="Slow Configuration Load",
            description=f"Load time {load_time_ms}ms exceeds threshold",
            preset_name="production",
            metric_type=MetricType.CONFIG_LOAD,
            threshold_value=100.0,
            actual_value=load_time_ms,
            metadata={}
        )
    """

    ...


@dataclass
class ConfigurationMetric:
    """
    Individual configuration metric event for tracking and analysis.
    
    Encapsulates a single metric event from configuration operations including
    timing information, usage patterns, error conditions, and performance data.
    Provides comprehensive context for operational monitoring and analysis.
    
    Attributes:
        timestamp: UTC timestamp when the metric event occurred
        metric_type: Type of metric (usage, load, error, change, validation, performance)
        preset_name: Name of the configuration preset involved in the event
        operation: Specific operation being performed (load, validate, change, etc.)
        value: Numerical value associated with the metric (timing, count, percentage)
        metadata: Additional contextual data about the metric event
        session_id: Optional session identifier for grouping related events
        user_context: Optional user context for attribution and access patterns
    
    Public Methods:
        to_dict(): Convert metric to dictionary for JSON serialization and export
    
    State Management:
        - Immutable dataclass ensuring metric integrity after creation
        - Automatic conversion of enum values for serialization
        - ISO 8601 timestamp formatting for consistent time representation
        - Thread-safe access for concurrent monitoring scenarios
    
    Usage:
        # Create a performance metric
        metric = ConfigurationMetric(
            timestamp=datetime.now(timezone.utc),
            metric_type=MetricType.CONFIG_LOAD,
            preset_name="production",
            operation="load",
            value=150.5,  # milliseconds
            metadata={"cache_hit": False, "config_size": 2048},
            session_id="session_123",
            user_context="admin_user"
        )
    
        # Export for monitoring systems
        serialized = metric.to_dict()
        monitoring_system.send_metric(serialized)
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metric to dictionary for JSON serialization and export.
        
        Returns:
            Dict[str, Any]: Dictionary representation with:
            - All original fields from the metric dataclass
            - ISO 8601 formatted timestamp string
            - Metric type as string value instead of enum
            - Maintained metadata structure for context
            - Optional fields included as None if not set
        
        Behavior:
            - Converts datetime to ISO 8601 string format
            - Converts MetricType enum to string value
            - Preserves all metadata for analysis
            - Maintains original field names for compatibility
            - Returns shallow copy safe for modification
        
        Examples:
            >>> metric = ConfigurationMetric(
            ...     timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ...     metric_type=MetricType.CONFIG_LOAD,
            ...     preset_name="production",
            ...     operation="load",
            ...     value=100.0,
            ...     metadata={"test": True}
            ... )
            >>> result = metric.to_dict()
            >>> result['timestamp']
            '2023-01-01T12:00:00+00:00'
            >>> result['metric_type']
            'config_load'
            >>> result['preset_name']
            'production'
        """
        ...


@dataclass
class ConfigurationAlert:
    """
    Configuration monitoring alert for threshold violations and operational issues.
    
    Represents an alert condition triggered by configuration metrics exceeding
    defined thresholds or encountering problematic conditions. Provides comprehensive
    context for incident response and operational monitoring.
    
    Attributes:
        timestamp: UTC timestamp when the alert was generated
        level: Severity level of the alert (INFO, WARNING, ERROR, CRITICAL)
        title: Brief, descriptive title for the alert
        description: Detailed description of the alert condition and impact
        preset_name: Name of the configuration preset associated with the alert
        metric_type: Type of metric that triggered the alert
        threshold_value: Threshold value that was exceeded or violated
        actual_value: Actual value that triggered the alert
        metadata: Additional context about the alert condition
    
    Public Methods:
        to_dict(): Convert alert to dictionary for JSON serialization and export
    
    State Management:
        - Immutable dataclass ensuring alert integrity after creation
        - Automatic conversion of enum values for serialization
        - ISO 8601 timestamp formatting for consistent time representation
        - Structured data suitable for monitoring system integration
    
    Usage:
        # Create performance alert
        alert = ConfigurationAlert(
            timestamp=datetime.now(timezone.utc),
            level=AlertLevel.WARNING,
            title="Slow Configuration Load",
            description="Configuration load time exceeded threshold",
            preset_name="production",
            metric_type=MetricType.CONFIG_LOAD,
            threshold_value=100.0,
            actual_value=250.5,
            metadata={"environment": "prod", "server": "web-01"}
        )
    
        # Export for alerting systems
        serialized = alert.to_dict()
        alert_manager.send_alert(serialized)
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert alert to dictionary for JSON serialization and export.
        
        Returns:
            Dict[str, Any]: Dictionary representation with:
            - All original fields from the alert dataclass
            - ISO 8601 formatted timestamp string
            - Alert level as string value instead of enum
            - Metric type as string value instead of enum
            - Maintained metadata structure for context
            - Optional fields included as None if not set
        
        Behavior:
            - Converts datetime to ISO 8601 string format
            - Converts AlertLevel enum to string value
            - Converts MetricType enum to string value
            - Preserves all metadata for analysis
            - Maintains original field names for compatibility
            - Returns shallow copy safe for modification
        
        Examples:
            >>> alert = ConfigurationAlert(
            ...     timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ...     level=AlertLevel.WARNING,
            ...     title="Test Alert",
            ...     description="Test description",
            ...     preset_name="test",
            ...     metric_type=MetricType.CONFIG_LOAD,
            ...     threshold_value=100.0,
            ...     actual_value=150.0,
            ...     metadata={}
            ... )
            >>> result = alert.to_dict()
            >>> result['timestamp']
            '2023-01-01T12:00:00+00:00'
            >>> result['level']
            'warning'
            >>> result['metric_type']
            'config_load'
        """
        ...


class ConfigurationUsageStats(NamedTuple):
    """
    Aggregated configuration usage statistics for operational monitoring and analysis.
    
    Provides comprehensive usage metrics derived from collected configuration events,
    enabling insights into usage patterns, performance characteristics, and operational
    health of the resilience configuration system.
    
    Attributes:
        total_loads: Total number of configuration load operations performed
        preset_usage_count: Dictionary mapping preset names to usage counts
        error_rate: Error rate as percentage (0.0-1.0) of failed operations
        avg_load_time_ms: Average configuration loading time in milliseconds
        most_used_preset: Name of the most frequently used preset
        least_used_preset: Name of the least frequently used preset
        custom_config_usage_rate: Rate of custom configuration usage (0.0-1.0)
        legacy_config_usage_rate: Rate of legacy configuration usage (0.0-1.0)
    
    State Management:
        - Immutable NamedTuple ensuring data integrity
        - Derived from aggregated metric collection over time window
        - Calculated values reflect current operational state
        - Used for monitoring dashboards and alerting thresholds
    
    Usage:
        # Access individual statistics
        stats = collector.get_usage_statistics()
        print(f"Total loads: {stats.total_loads}")
        print(f"Error rate: {stats.error_rate:.2%}")
        print(f"Average load time: {stats.avg_load_time_ms:.2f}ms")
    
        # Analyze preset usage patterns
        for preset, count in stats.preset_usage_count.items():
            print(f"{preset}: {count} uses")
    
        # Health assessment
        if stats.error_rate > 0.05:
            alert_manager.trigger_alert("High configuration error rate")
    """

    ...


class ConfigurationMetricsCollector:
    """
    Comprehensive configuration metrics collection and analysis system.
    
    Provides real-time monitoring of configuration usage patterns, performance metrics,
    and operational health for resilience configuration management. Enables detailed
    analysis of configuration behavior, trend identification, and proactive alerting.
    
    Attributes:
        max_events: Maximum number of metric events to retain in memory
        retention_hours: Hours to retain metrics data before automatic cleanup
        metrics: Thread-safe deque storing collected metric events
        alerts: List of generated configuration alerts
        session_metrics: Dictionary mapping session IDs to their metric events
        alert_thresholds: Configuration for triggering alerts based on metric values
    
    Public Methods:
        track_config_operation(): Context manager for automatic operation tracking
        record_preset_usage(): Record usage of specific configuration preset
        record_config_load(): Record configuration loading performance
        record_config_error(): Record configuration error events
        record_config_change(): Record configuration modification events
        record_validation_event(): Record configuration validation results
        get_usage_statistics(): Get aggregated usage statistics
        get_preset_usage_trend(): Analyze usage trends over time
        get_performance_metrics(): Get performance analysis
        get_active_alerts(): Retrieve active configuration alerts
        get_session_metrics(): Get metrics for specific session
        clear_old_metrics(): Clean up old metric data
        export_metrics(): Export metrics in various formats
    
    State Management:
        - Thread-safe operations using reentrant locks for concurrent access
        - Automatic memory management with configurable retention policies
        - Real-time statistics calculation with caching for performance
        - Alert generation based on configurable thresholds
        - Session-based metric grouping for request tracking
    
    Usage:
        # Initialize collector with custom configuration
        collector = ConfigurationMetricsCollector(
            max_events=5000,
            retention_hours=12
        )
    
        # Track operations with context manager
        with collector.track_config_operation("load_preset", "production"):
            config = load_resilience_config("production")
    
        # Manual metric recording
        collector.record_preset_usage("development", operation="load")
        collector.record_config_load("production", "load", 125.5)
    
        # Analyze metrics
        stats = collector.get_usage_statistics()
        trends = collector.get_preset_usage_trend("production", hours=24)
        performance = collector.get_performance_metrics()
    
        # Alert management
        alerts = collector.get_active_alerts()
        for alert in alerts:
            if alert.level == AlertLevel.CRITICAL:
                incident_manager.create_ticket(alert)
    
        # Export for external monitoring
        json_data = collector.export_metrics("json", time_window_hours=1)
        monitoring_system.send_metrics(json_data)
    """

    def __init__(self, max_events: int = 10000, retention_hours: int = 24):
        """
        Initialize comprehensive configuration metrics collector.
        
        Args:
            max_events: Maximum number of events to retain in memory (1000-100000).
                       Must be positive integer. Default: 10000
            retention_hours: Hours to retain metrics data before cleanup (1-168).
                            Must be positive integer. Default: 24
        
        Raises:
            ValueError: If max_events or retention_hours are not positive integers
        
        Behavior:
            - Initializes thread-safe storage for metrics and alerts
            - Sets up configurable retention policies and thresholds
            - Creates session tracking for request-level monitoring
            - Establishes performance caching for statistics calculations
            - Configures alert thresholds for automated monitoring
            - Prepares memory management structures for high-volume operation
        
        Examples:
            # Default configuration
            collector = ConfigurationMetricsCollector()
        
            # Custom configuration for high-volume environment
            collector = ConfigurationMetricsCollector(
                max_events=50000,
                retention_hours=48
            )
        
            # Lightweight configuration for testing
            collector = ConfigurationMetricsCollector(
                max_events=1000,
                retention_hours=1
            )
        """
        ...

    @contextmanager
    def track_config_operation(self, operation: str, preset_name: str = 'unknown', session_id: Optional[str] = None, user_context: Optional[str] = None):
        """
        Context manager for automatic configuration operation tracking with timing and error handling.
        
        Args:
            operation: Name of the operation being tracked (load, validate, change, etc.).
                      Must be non-empty string. Typical values: "load", "validate", "change", "save"
            preset_name: Configuration preset being used (unknown if not specified).
                        Should match actual preset name when available. Default: "unknown"
            session_id: Optional session identifier for grouping related operations.
                        Useful for request-level tracking and debugging. Default: None
            user_context: Optional user context information for attribution and access patterns.
                         Can include user ID, role, or other contextual data. Default: None
        
        Yields:
            None: Control is yielded to the wrapped operation
        
        Raises:
            ValueError: If operation is empty or None
            Exception: Any exception from the wrapped operation (re-raised after logging)
        
        Behavior:
            - Automatically measures operation execution time in milliseconds
            - Records successful operations as CONFIG_LOAD metrics with timing
            - Records failed operations as CONFIG_ERROR metrics with error details
            - Captures exception information for error analysis and debugging
            - Associates metrics with session and user context when provided
            - Thread-safe recording suitable for concurrent operation tracking
            - Automatic cleanup and metric recording even when exceptions occur
        
        Side Effects:
            - Records CONFIG_LOAD metric on successful operation completion
            - Records CONFIG_ERROR metric on operation failure
            - May generate performance alerts if operation exceeds thresholds
            - Updates session metrics when session_id is provided
            - Affects aggregated statistics and trend calculations
        
        Examples:
            # Basic usage
            with collector.track_config_operation("load_preset", "production"):
                config = load_resilience_config("production")
        
            # With session tracking
            with collector.track_config_operation(
                "validate_config",
                "custom_config",
                session_id="req_12345",
                user_context="admin_user"
            ):
                validate_configuration(config)
        
            # Error handling (automatic)
            try:
                with collector.track_config_operation("save_config", "production"):
                    save_configuration(config, "production")
            except Exception as e:
                # Error already recorded in metrics
                print(f"Operation failed: {e}")
        """
        ...

    def record_preset_usage(self, preset_name: str, operation: str = 'load', session_id: Optional[str] = None, user_context: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Record usage of a specific preset.
        
        Args:
            preset_name: Name of the preset used
            operation: Operation performed
            session_id: Optional session identifier
            user_context: Optional user context
            metadata: Additional metadata about the usage
        """
        ...

    def record_config_load(self, preset_name: str, operation: str, duration_ms: float, session_id: Optional[str] = None, user_context: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
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
        ...

    def record_config_error(self, preset_name: str, operation: str, error_message: str, session_id: Optional[str] = None, user_context: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
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
        ...

    def record_config_change(self, old_preset: str, new_preset: str, operation: str = 'change', session_id: Optional[str] = None, user_context: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
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
        ...

    def record_validation_event(self, preset_name: str, is_valid: bool, operation: str = 'validate', session_id: Optional[str] = None, user_context: Optional[str] = None, validation_errors: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
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
        ...

    def get_usage_statistics(self, time_window_hours: Optional[int] = None) -> ConfigurationUsageStats:
        """
        Get configuration usage statistics.
        
        Args:
            time_window_hours: Time window for statistics (None for all time)
            
        Returns:
            Configuration usage statistics
        """
        ...

    def get_preset_usage_trend(self, preset_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get usage trend for a specific preset over time.
        
        Args:
            preset_name: Name of the preset
            hours: Number of hours to analyze
            
        Returns:
            List of hourly usage counts
        """
        ...

    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance metrics for configuration operations.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Performance metrics summary
        """
        ...

    def get_active_alerts(self, max_alerts: int = 50) -> List[Dict[str, Any]]:
        """
        Get active configuration alerts.
        
        Args:
            max_alerts: Maximum number of alerts to return
            
        Returns:
            List of active alerts
        """
        ...

    def get_session_metrics(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get metrics for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of metrics for the session
        """
        ...

    def clear_old_metrics(self, hours: int = 24):
        """
        Clear metrics older than specified hours.
        
        Args:
            hours: Hours threshold for clearing old metrics
        """
        ...

    def export_metrics(self, format: str = 'json', time_window_hours: Optional[int] = None) -> str:
        """
        Export metrics in specified format.
        
        Args:
            format: Export format ('json' or 'csv')
            time_window_hours: Time window for export (None for all)
            
        Returns:
            Exported metrics as string
        """
        ...
