---
sidebar_label: mocks
---

# Common mock objects for testing.

  file_path: `backend/tests/mocks.py`

This module contains mock implementations and helper utilities
for creating test doubles across the test suite.

## MockAIClient

Mock AI client for testing.

### __init__()

```python
def __init__(self):
```

## MockCacheClient

Mock cache client for testing.

### __init__()

```python
def __init__(self):
```

### get()

```python
async def get(self, key):
```

### set()

```python
async def set(self, key, value, ttl = None):
```

### delete()

```python
async def delete(self, key):
```

### clear()

```python
async def clear(self):
```

## MockAuthenticator

Mock authenticator for testing.

### __init__()

```python
def __init__(self):
```

## mock_ai_client()

```python
def mock_ai_client():
```

Fixture providing a mock AI client.

## mock_cache_client()

```python
def mock_cache_client():
```

Fixture providing a mock cache client.

## mock_authenticator()

```python
def mock_authenticator():
```

Fixture providing a mock authenticator.
