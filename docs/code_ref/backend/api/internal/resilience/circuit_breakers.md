# Resilience circuit breaker management and monitoring REST API endpoints.

This module provides REST API endpoints for monitoring and managing circuit
breakers within the resilience infrastructure. Circuit breakers are critical
components that protect services from cascading failures by detecting and
isolating failing operations, providing real-time status monitoring and
administrative control capabilities.

The module implements comprehensive circuit breaker management with real-time
status monitoring, detailed state analysis, and administrative reset
capabilities. All endpoints provide extensive information about circuit
breaker health and operational status.

## Endpoints

GET /resilience/circuit-breakers: Get status of all circuit breakers
GET /resilience/circuit-breakers/{breaker_name}: Get detailed information for specific breaker
POST /resilience/circuit-breakers/{breaker_name}/reset: Reset circuit breaker to closed state

## Circuit Breaker Management Features

- Real-time circuit breaker status monitoring
- Detailed state analysis (open, closed, half-open)
- Failure count tracking and threshold management
- Last failure time monitoring and analysis
- Administrative reset capabilities for operational control
- Comprehensive metrics collection and reporting

## Circuit Breaker States

- Closed: Normal operation, requests pass through
- Open: Failure threshold exceeded, requests blocked
- Half-Open: Testing phase, limited requests allowed
- State transition monitoring and logging
- Automatic state management based on configured thresholds

## Monitoring Capabilities

- Current failure counts and success rates
- Last failure timestamps and error patterns
- Recovery timeout configuration and status
- Threshold configuration and compliance monitoring
- Historical metrics and trend analysis
- Performance impact assessment

## Administrative Operations

- Manual circuit breaker reset for emergency recovery
- State manipulation for testing and maintenance
- Configuration validation and compliance checking
- Operational control for service maintenance
- Emergency override capabilities for critical situations

## Dependencies

- AIResilienceOrchestrator: Core circuit breaker management and orchestration
- CircuitBreaker: Individual circuit breaker instances with state management
- Metrics: Circuit breaker performance and operational metrics
- Security: API key verification for all circuit breaker endpoints

## Authentication

All circuit breaker endpoints require API key authentication to ensure
secure access to critical infrastructure components and prevent
unauthorized manipulation of circuit breaker states.

## Example

Get all circuit breaker statuses:
GET /api/internal/resilience/circuit-breakers

Get specific circuit breaker details:
GET /api/internal/resilience/circuit-breakers/text_processing_service

Reset a circuit breaker:
POST /api/internal/resilience/circuit-breakers/text_processing_service/reset

## Note

Circuit breakers are critical safety components that protect against
cascading failures. Manual resets should be used carefully and only
when the underlying issues have been resolved to prevent immediate
re-opening of the circuit breaker.
