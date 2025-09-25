---
sidebar_label: conftest
---

# Conftest file for pytest.

  file_path: `backend/tests.old/conftest.py`

TODO: Split this file into fixtures.py and mocks.py

## event_loop()

```python
def event_loop():
```

Create an instance of the default event loop for the test session.

## client()

```python
def client():
```

Create a test client for the FastAPI app.

## async_client()

```python
async def async_client():
```

Create an async test client.

## auth_headers()

```python
def auth_headers():
```

Headers with authentication for protected endpoints.

## authenticated_client()

```python
def authenticated_client(client, auth_headers):
```

Test client with authentication headers pre-configured.

## test_settings()

```python
def test_settings():
```

Test Settings instance with all required fields including GEMINI_API_KEY.

## sample_text()

```python
def sample_text():
```

Sample text for testing.

## sample_request()

```python
def sample_request(sample_text):
```

Sample request for testing.

## mock_ai_response()

```python
def mock_ai_response():
```

Mock AI response for testing.

## sample_response()

```python
def sample_response():
```

Sample AI response for cache tests.

## sample_options()

```python
def sample_options():
```

Sample operation options for cache tests.

## mock_processor()

```python
def mock_processor():
```

Mock TextProcessorService for testing.

## mock_cache_service()

```python
def mock_cache_service():
```

Mock AIResponseCache for testing.

## mock_performance_monitor()

```python
def mock_performance_monitor():
```

Mock CachePerformanceMonitor for testing.

## performance_monitor()

```python
def performance_monitor():
```

Create a mock performance monitor (shared fixture name for infra tests).

## ai_cache()

```python
async def ai_cache(performance_monitor):
```

Provide an AIResponseCache instance for infra tests across modules.

## cache_performance_monitor()

```python
def cache_performance_monitor():
```

Real CachePerformanceMonitor instance for testing.

## app_with_mock_performance_monitor()

```python
def app_with_mock_performance_monitor(mock_performance_monitor):
```

FastAPI app with mock performance monitor dependency override.

## client_with_mock_monitor()

```python
def client_with_mock_monitor(app_with_mock_performance_monitor):
```

Test client with mocked performance monitor.

## mock_ai_agent()

```python
def mock_ai_agent():
```

Mock the AI agent to avoid actual API calls during testing.

## pytest_addoption()

```python
def pytest_addoption(parser):
```

Add custom command line options.

## pytest_configure()

```python
def pytest_configure(config):
```

Configure pytest based on command line options.

## pytest_collection_modifyitems()

```python
def pytest_collection_modifyitems(config, items):
```

Modify test collection based on command line options.
