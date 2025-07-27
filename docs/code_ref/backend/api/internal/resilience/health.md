# Infrastructure Service: Resilience Health Monitoring API

🏗️ **STABLE API** - Changes affect all template users
📋 **Minimum test coverage**: 90%
🔧 **Configuration-driven behavior**

This module provides comprehensive FastAPI endpoints for monitoring and managing
the AI resilience service's health, configuration, and performance metrics. It
serves as the primary interface for internal monitoring, diagnostics, and
operational visibility into the resilience infrastructure.

The module implements endpoints for real-time health checks, configuration
retrieval, metrics collection, and dashboard-style monitoring views. All
endpoints support both legacy and modern resilience configurations with
automatic detection and appropriate response formatting.

## Endpoints

GET  /internal/resilience/health: Get service health status and circuit breaker states
GET  /internal/resilience/config: Retrieve current resilience configuration and strategies
GET  /internal/resilience/metrics: Get comprehensive resilience metrics for all operations
GET  /internal/resilience/metrics/{operation_name}: Get metrics for a specific operation
POST /internal/resilience/metrics/reset: Reset metrics for specific or all operations
GET  /internal/resilience/dashboard: Get dashboard-style summary for monitoring systems

## Configuration Management

- Automatic detection of legacy vs. modern configuration formats
- Environment variable override support for presets and custom configs
- Operation-specific strategy retrieval with fallback handling
- JSON parsing and validation for custom configuration overrides

## Health Monitoring

- Circuit breaker state tracking (open, closed, half-open)
- Overall service health assessment
- Operation-level health status reporting
- Real-time degradation detection

## Performance Metrics

- Success/failure rates by operation
- Retry attempt tracking and analysis
- Circuit breaker activation statistics
- Response time and throughput metrics
- Historical trend data for performance analysis

## Dependencies

- AIResilienceOrchestrator: Core resilience service for operations
- Settings: Configuration management and environment integration
- Security: API key verification for protected endpoints
- Pydantic Models: Structured response validation and documentation

## Authentication

Most endpoints require API key authentication via the verify_api_key
dependency. Some monitoring endpoints support optional authentication
for flexibility in different deployment scenarios.

## Example

To check overall resilience service health:
GET /internal/resilience/health

To get comprehensive metrics for monitoring:
GET /internal/resilience/dashboard

To reset metrics for a specific operation:
POST /internal/resilience/metrics/reset?operation_name=summarize

## Note

This module automatically handles both legacy and modern resilience
configurations, ensuring backward compatibility while supporting
new features. Metrics are computed in real-time and may include
brief processing delays for comprehensive statistics.
