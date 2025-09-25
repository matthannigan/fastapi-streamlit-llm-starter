---
sidebar_label: conftest
---

# Pytest fixtures for health monitoring integration tests.

  file_path: `backend/tests.new/integration/health/conftest.py`

This module provides fixtures for testing health monitoring system integration
with cache services, resilience patterns, AI services, and monitoring APIs.

## health_checker()

```python
def health_checker():
```

Create a basic HealthChecker instance for testing.

## health_checker_with_custom_timeouts()

```python
def health_checker_with_custom_timeouts():
```

Create a HealthChecker with custom component-specific timeouts.

## mock_cache_service()

```python
def mock_cache_service():
```

Mock AIResponseCache for health check testing.

## fake_redis_cache()

```python
def fake_redis_cache():
```

Create AIResponseCache with FakeStrictRedis for integration testing.

## mock_resilience_service()

```python
def mock_resilience_service():
```

Mock resilience service for health check testing.

## mock_unhealthy_resilience_service()

```python
def mock_unhealthy_resilience_service():
```

Mock resilience service with unhealthy status for testing.

## mock_ai_service()

```python
def mock_ai_service():
```

Mock AI service for health check testing.

## settings_with_gemini_key()

```python
def settings_with_gemini_key():
```

Settings instance with valid Gemini API key.

## settings_without_gemini_key()

```python
def settings_without_gemini_key():
```

Settings instance without Gemini API key.

## mock_database_connection()

```python
def mock_database_connection():
```

Mock database connection for health check testing.

## failing_health_check()

```python
def failing_health_check():
```

Health check function that always fails.

## timeout_health_check()

```python
def timeout_health_check():
```

Health check function that always times out.

## degraded_health_check()

```python
def degraded_health_check():
```

Health check function that returns degraded status.

## slow_health_check()

```python
def slow_health_check():
```

Health check function that takes time but succeeds.

## performance_monitor()

```python
def performance_monitor():
```

Create a CachePerformanceMonitor instance for testing.

## sample_health_check()

```python
def sample_health_check():
```

Sample health check function for testing registration.
