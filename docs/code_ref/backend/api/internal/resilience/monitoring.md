# Infrastructure Service: Resilience Configuration Monitoring API

🏗️ **STABLE API** - Changes affect all template users
📋 **Minimum test coverage**: 90%
🔧 **Configuration-driven behavior**

This module provides comprehensive REST API endpoints for monitoring resilience
configuration usage, performance metrics, alerts, and analytics. It includes
capabilities for tracking configuration usage patterns, analyzing performance
trends, managing alerts, and exporting monitoring data for external analysis.

The module implements sophisticated monitoring and analytics tools that provide
operational visibility into resilience system behavior, configuration usage
patterns, and performance characteristics across different time windows and
operational contexts.

## Endpoints

GET /internal/resilience/monitoring/usage-statistics: Configuration usage statistics and trends
GET /internal/resilience/monitoring/preset-trends/{preset_name}: Usage trends for specific presets
GET /internal/resilience/monitoring/performance-metrics: Performance metrics analysis
GET /internal/resilience/monitoring/alerts: Active configuration alerts and notifications
GET /internal/resilience/monitoring/session/{session_id}: Session-specific configuration metrics
GET /internal/resilience/monitoring/export: Export monitoring data in various formats
POST /internal/resilience/monitoring/cleanup: Clean up old metrics and monitoring data

## Monitoring Features

- Real-time configuration usage tracking and analysis
- Preset usage trends with time-series data
- Performance metrics collection and aggregation
- Alert management and notification systems
- Session-based metrics tracking and analysis
- Data export capabilities for external analysis

## Usage Analytics

- Total configuration loads and access patterns
- Preset usage frequency and popularity analysis
- Error rate monitoring and threshold alerting
- Load time performance tracking and optimization
- Custom vs. legacy configuration adoption rates
- Environment-specific usage pattern analysis

## Performance Monitoring

- Average and percentile load time analysis
- Error count tracking and trend analysis
- Performance threshold compliance monitoring
- P95 response time tracking for SLA compliance
- Memory usage monitoring and optimization
- Throughput analysis and capacity planning

## Alert Management

- Multi-level alert system (info, warning, error, critical)
- Configurable alert thresholds and triggers
- Alert categorization and priority management
- Real-time alert status monitoring
- Alert history and trend analysis
- Automated alert cleanup and management

## Data Export and Cleanup

- Multiple export formats (JSON, CSV, etc.)
- Configurable time window selection
- Automated data cleanup and retention management
- Session-based data export capabilities
- Performance-optimized bulk data operations

## Dependencies

- ConfigMetricsCollector: Core monitoring and metrics collection engine
- ConfigMonitoring: Real-time monitoring and alert management
- Analytics: Advanced analytics and trend analysis capabilities
- Security: API key verification for all monitoring endpoints

## Authentication

All monitoring endpoints require API key authentication to ensure
secure access to operational data and prevent unauthorized monitoring.

## Example

Get usage statistics for last 24 hours:
GET /internal/resilience/monitoring/usage-statistics?time_window_hours=24

Get performance metrics:
GET /internal/resilience/monitoring/performance-metrics?hours=48

Export monitoring data:
GET /internal/resilience/monitoring/export?format=json&time_window_hours=168

## Note

Monitoring data provides valuable operational insights but may include
sensitive configuration information. Regular cleanup helps maintain
system performance and data retention compliance.
