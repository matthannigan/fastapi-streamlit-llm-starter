---
sidebar_label: test_resilience_integration1
---

# Tests for resilience integration.

  file_path: `backend/tests/integration/test_resilience_integration1.py`
Need to combine old test_resilience_endpoints.py and test_preset_resilience_integration.py

This file currently only contains tests that were in test_resilience_endpoints.py

Comprehensive tests for resilience endpoints.
Tests all endpoints in app/resilience_endpoints.py

## TestResilienceHealthEndpoint

Test the resilience health endpoint.

### test_resilience_health_success()

```python
def test_resilience_health_success(self, client, mock_resilience_service):
```

Test successful health check.

### test_resilience_health_error()

```python
def test_resilience_health_error(self, client, mock_resilience_service):
```

Test health check with service error.

## TestResilienceConfigEndpoint

Test the resilience configuration endpoint.

### test_get_resilience_config_success()

```python
def test_get_resilience_config_success(self, client, auth_headers, mock_resilience_service):
```

Test successful configuration retrieval.

## TestResilienceMetricsEndpoints

Test resilience metrics endpoints.

### test_get_all_metrics_success()

```python
def test_get_all_metrics_success(self, client, auth_headers, mock_resilience_service):
```

Test getting all operation metrics.

### test_get_all_metrics_unauthorized()

```python
def test_get_all_metrics_unauthorized(self, client, mock_resilience_service):
```

Test metrics endpoint without authentication.

### test_get_operation_metrics_error()

```python
def test_get_operation_metrics_error(self, client, auth_headers, mock_resilience_service):
```

Test operation metrics with service error.

### test_reset_metrics_all_operations()

```python
def test_reset_metrics_all_operations(self, client, auth_headers, mock_resilience_service):
```

Test resetting all metrics.

### test_reset_metrics_specific_operation()

```python
def test_reset_metrics_specific_operation(self, client, auth_headers, mock_resilience_service):
```

Test resetting metrics for specific operation.

## TestCircuitBreakerEndpoints

Test circuit breaker management endpoints.

### test_get_circuit_breaker_status()

```python
def test_get_circuit_breaker_status(self, client, auth_headers, mock_resilience_service):
```

Test getting circuit breaker status.

### test_get_circuit_breaker_details_success()

```python
def test_get_circuit_breaker_details_success(self, client, auth_headers, mock_resilience_service):
```

Test getting specific circuit breaker details.

### test_reset_circuit_breaker_success()

```python
def test_reset_circuit_breaker_success(self, client, auth_headers, mock_resilience_service):
```

Test resetting a circuit breaker.

## TestResilienceDashboardEndpoint

Test the resilience dashboard endpoint.

### test_dashboard_success()

```python
def test_dashboard_success(self, client, mock_resilience_service):
```

Test successful dashboard retrieval.

### test_dashboard_with_alerts()

```python
def test_dashboard_with_alerts(self, client, mock_resilience_service):
```

Test dashboard with alerts.

### test_dashboard_error_handling()

```python
def test_dashboard_error_handling(self, client, mock_resilience_service):
```

Test dashboard error handling.

## TestAuthenticationProtection

Test authentication requirements for protected endpoints.

### test_protected_endpoints_require_auth()

```python
def test_protected_endpoints_require_auth(self, client, endpoint):
```

Test that protected endpoints require authentication.

### test_protected_post_endpoints_require_auth()

```python
def test_protected_post_endpoints_require_auth(self, client, endpoint):
```

Test that protected POST endpoints require authentication.

### test_optional_auth_endpoints_work_without_auth()

```python
def test_optional_auth_endpoints_work_without_auth(self, client, mock_resilience_service, mock_text_processor):
```

Test that optional auth endpoints work without authentication.

## TestErrorHandling

Test error handling and edge cases.

### test_invalid_operation_name_in_metrics()

```python
def test_invalid_operation_name_in_metrics(self, client, auth_headers, mock_resilience_service):
```

Test handling of invalid operation names.

### test_service_unavailable_scenarios()

```python
def test_service_unavailable_scenarios(self, client, auth_headers, mock_resilience_service):
```

Test scenarios where resilience service is unavailable.

### test_circuit_breaker_reset_error()

```python
def test_circuit_breaker_reset_error(self, client, auth_headers, mock_resilience_service):
```

Test error handling in circuit breaker reset.

### test_malformed_auth_header()

```python
def test_malformed_auth_header(self, client, mock_resilience_service):
```

Test handling of malformed authorization headers.

### test_empty_metrics_response()

```python
def test_empty_metrics_response(self, client, mock_resilience_service):
```

Test dashboard with empty metrics.

## mock_resilience_service()

```python
def mock_resilience_service():
```

Mock the resilience service for all tests in this module.

## client()

```python
def client():
```

Test client for making requests.

## auth_headers()

```python
def auth_headers():
```

Authorization headers for authenticated requests - using established pattern.

## mock_text_processor()

```python
def mock_text_processor():
```

Mock the text processor service.

## mock_api_key_auth()

```python
def mock_api_key_auth():
```

Mock API key authentication to allow test API keys.
