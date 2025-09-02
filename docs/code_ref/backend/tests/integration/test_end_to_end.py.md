---
sidebar_label: test_end_to_end
---

# Comprehensive backward compatibility integration tests.

  file_path: `backend/tests/integration/test_end_to_end.py`

This module provides end-to-end integration tests for backward compatibility,
covering real-world migration scenarios, API compatibility, and system integration.

## TestEndToEndBackwardCompatibility

End-to-end tests for backward compatibility.

### test_legacy_api_endpoint_compatibility()

```python
def test_legacy_api_endpoint_compatibility(self, client, mock_resilience_service):
```

Test that legacy API endpoints still work.

### test_configuration_migration_scenario()

```python
def test_configuration_migration_scenario(self, client, auth_headers, mock_resilience_service):
```

Test configuration migration from old to new format.

### test_metrics_backward_compatibility()

```python
def test_metrics_backward_compatibility(self, client, auth_headers, mock_resilience_service):
```

Test metrics API backward compatibility.

### test_circuit_breaker_backward_compatibility()

```python
def test_circuit_breaker_backward_compatibility(self, client, auth_headers, mock_resilience_service):
```

Test circuit breaker API backward compatibility.

### test_error_handling_consistency()

```python
def test_error_handling_consistency(self, client, mock_resilience_service):
```

Test that error handling is consistent across versions.

### test_data_format_consistency()

```python
def test_data_format_consistency(self, client, mock_resilience_service):
```

Test that data formats remain consistent.

### test_performance_regression_prevention()

```python
def test_performance_regression_prevention(self, client, auth_headers, mock_resilience_service):
```

Test that performance hasn't regressed.

### test_concurrent_request_handling()

```python
def test_concurrent_request_handling(self, client, auth_headers, mock_resilience_service):
```

Test handling of concurrent requests.

## TestRealWorldScenarios

Tests simulating real-world deployment scenarios.

### test_kubernetes_deployment_scenario()

```python
def test_kubernetes_deployment_scenario(self, client, mock_resilience_service):
```

Test scenario simulating Kubernetes deployment.

### test_docker_compose_environment_scenario()

```python
def test_docker_compose_environment_scenario(self, client, auth_headers, mock_resilience_service):
```

Test scenario simulating Docker Compose environment.

### test_cloud_deployment_scenario()

```python
def test_cloud_deployment_scenario(self, client, mock_resilience_service):
```

Test scenario simulating cloud deployment.

## TestDataIntegrity

Tests for data integrity across versions.

### test_configuration_data_integrity()

```python
def test_configuration_data_integrity(self, client, auth_headers, mock_resilience_service):
```

Test that configuration data maintains integrity.

### test_metrics_data_integrity()

```python
def test_metrics_data_integrity(self, client, auth_headers, mock_resilience_service):
```

Test that metrics data maintains integrity.

### test_health_data_consistency()

```python
def test_health_data_consistency(self, client, mock_resilience_service):
```

Test that health data is consistent.

## client()

```python
def client():
```

Test client.

## auth_headers()

```python
def auth_headers():
```

Auth headers for protected endpoints.

## mock_resilience_service()

```python
def mock_resilience_service():
```

Mock resilience service.

## mock_api_key_auth()

```python
def mock_api_key_auth():
```

Mock API key authentication to allow test API keys.
