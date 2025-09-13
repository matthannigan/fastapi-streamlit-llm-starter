---
sidebar_label: circuit_breakers
---

# Infrastructure Service: Resilience Circuit Breaker Management API

  file_path: `backend/app/api/internal/resilience/circuit_breakers.py`

🏗️ **STABLE API** - Changes affect all template users  
📋 **Minimum test coverage**: 90%  
🔧 **Configuration-driven behavior**

This module provides REST API endpoints for monitoring and managing circuit
breakers within the resilience infrastructure. Circuit breakers are critical
infrastructure components that protect services from cascading failures by detecting and
isolating failing operations, providing real-time status monitoring and
administrative control capabilities.

The module implements comprehensive circuit breaker management with real-time
status monitoring, detailed state analysis, and administrative reset
capabilities. All endpoints provide extensive information about circuit
breaker health and operational status.

Endpoints:
    GET /internal/resilience/circuit-breakers: Get status of all circuit breakers
    GET /internal/resilience/circuit-breakers/{breaker_name}: Get detailed information for specific breaker
    POST /internal/resilience/circuit-breakers/{breaker_name}/reset: Reset circuit breaker to closed state

Circuit Breaker Management Features:
    - Real-time circuit breaker status monitoring
    - Detailed state analysis (open, closed, half-open)
    - Failure count tracking and threshold management
    - Last failure time monitoring and analysis
    - Administrative reset capabilities for operational control
    - Comprehensive metrics collection and reporting

Circuit Breaker States:
    - Closed: Normal operation, requests pass through
    - Open: Failure threshold exceeded, requests blocked
    - Half-Open: Testing phase, limited requests allowed
    - State transition monitoring and logging
    - Automatic state management based on configured thresholds

Monitoring Capabilities:
    - Current failure counts and success rates
    - Last failure timestamps and error patterns
    - Recovery timeout configuration and status
    - Threshold configuration and compliance monitoring
    - Historical metrics and trend analysis
    - Performance impact assessment

Administrative Operations:
    - Manual circuit breaker reset for emergency recovery
    - State manipulation for testing and maintenance
    - Configuration validation and compliance checking
    - Operational control for service maintenance
    - Emergency override capabilities for critical situations

Dependencies:
    - AIResilienceOrchestrator: Core circuit breaker management and orchestration
    - CircuitBreaker: Individual circuit breaker instances with state management
    - Metrics: Circuit breaker performance and operational metrics
    - Security: API key verification for all circuit breaker endpoints

Authentication:
    All circuit breaker endpoints require API key authentication to ensure
    secure access to critical infrastructure components and prevent
    unauthorized manipulation of circuit breaker states.

Example:
    Get all circuit breaker statuses:
        GET /internal/resilience/circuit-breakers
        
    Get specific circuit breaker details:
        GET /internal/resilience/circuit-breakers/text_processing_service
        
    Reset a circuit breaker:
        POST /internal/resilience/circuit-breakers/text_processing_service/reset

Note:
    Circuit breakers are critical safety components that protect against
    cascading failures. Manual resets should be used carefully and only
    when the underlying issues have been resolved to prevent immediate
    re-opening of the circuit breaker.

## get_circuit_breaker_status()

```python
async def get_circuit_breaker_status(api_key: str = Depends(verify_api_key)):
```

Get comprehensive status information for all circuit breakers.

This endpoint provides detailed monitoring information for all circuit breakers
in the resilience system, including current states, failure statistics, and
operational metrics for each circuit breaker instance.

Args:
    api_key: API key for authentication (injected via dependency)
    
Returns:
    Dict[str, Any]: Circuit breaker status data containing:
        - Dictionary mapping circuit breaker names to their status information
        - Each circuit breaker includes:
            - Current state (open, closed, half-open)
            - Failure counts and thresholds
            - Last failure timestamps
            - Recovery timeout configuration
            - Performance metrics and statistics
        
Raises:
    HTTPException: 500 Internal Server Error if circuit breaker status retrieval fails
    
Example:
    >>> response = await get_circuit_breaker_status()
    >>> {
    ...     "text_processing_service": {
    ...         "state": "closed",
    ...         "failure_count": 2,
    ...         "failure_threshold": 5,
    ...         "last_failure_time": "2023-12-01T10:15:00Z"
    ...     },
    ...     "ai_summarization": {
    ...         "state": "open",
    ...         "failure_count": 5,
    ...         "failure_threshold": 5
    ...     }
    ... }

## get_circuit_breaker_details()

```python
async def get_circuit_breaker_details(breaker_name: str, api_key: str = Depends(verify_api_key)):
```

Get detailed information about a specific circuit breaker.

This endpoint provides comprehensive details for a single circuit breaker,
including its current state, configuration parameters, failure statistics,
and operational metrics for detailed monitoring and diagnostics.

Args:
    breaker_name: Name of the specific circuit breaker to retrieve details for
    api_key: API key for authentication (injected via dependency)
    
Returns:
    Dict[str, Any]: Detailed circuit breaker information containing:
        - name: Circuit breaker name
        - state: Current state (open, closed, half-open)
        - failure_count: Current number of consecutive failures
        - failure_threshold: Maximum failures before opening
        - recovery_timeout: Time before attempting half-open state
        - last_failure_time: Timestamp of most recent failure
        - metrics: Additional performance and operational metrics
        
Raises:
    HTTPException: 404 Not Found if circuit breaker doesn't exist
    HTTPException: 500 Internal Server Error if details retrieval fails
    
Example:
    >>> response = await get_circuit_breaker_details("text_processing_service")
    >>> {
    ...     "name": "text_processing_service",
    ...     "state": "closed",
    ...     "failure_count": 2,
    ...     "failure_threshold": 5,
    ...     "recovery_timeout": 60,
    ...     "last_failure_time": "2023-12-01T10:15:00Z",
    ...     "metrics": {...}
    ... }

## reset_circuit_breaker()

```python
async def reset_circuit_breaker(breaker_name: str, api_key: str = Depends(verify_api_key)):
```

Reset a specific circuit breaker to closed state for emergency recovery.

This administrative endpoint resets a circuit breaker to its closed state,
clearing failure counts and allowing normal operation to resume. Use with
caution and only after resolving underlying issues that caused the failures.

Args:
    breaker_name: Name of the specific circuit breaker to reset
    api_key: API key for authentication (injected via dependency)
    
Returns:
    Dict[str, str]: Reset confirmation containing:
        - message: Human-readable confirmation message
        - name: Name of the circuit breaker that was reset
        - new_state: New state of the circuit breaker (should be "closed")
        
Raises:
    HTTPException: 404 Not Found if circuit breaker doesn't exist
    HTTPException: 500 Internal Server Error if reset operation fails
    
Warning:
    Circuit breakers are critical safety components that protect against
    cascading failures. Manual resets should be used carefully and only
    when the underlying issues have been resolved to prevent immediate
    re-opening of the circuit breaker.
    
Example:
    >>> response = await reset_circuit_breaker("text_processing_service")
    >>> {
    ...     "message": "Circuit breaker 'text_processing_service' has been reset",
    ...     "name": "text_processing_service",
    ...     "new_state": "closed"
    ... }
