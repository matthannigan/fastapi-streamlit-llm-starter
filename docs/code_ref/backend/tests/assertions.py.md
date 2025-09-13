---
sidebar_label: assertions
---

# Custom test assertions for enhanced testing.

  file_path: `backend/tests/assertions.py`

This module provides custom assertion helpers that extend pytest
capabilities for domain-specific testing scenarios.

## assert_valid_response_structure()

```python
def assert_valid_response_structure(response_data: Dict[str, Any], required_fields: List[str]):
```

Assert that a response has the required structure.

## assert_cache_hit_rate()

```python
def assert_cache_hit_rate(hits: int, total: int, min_rate: float = 0.8):
```

Assert that cache hit rate meets minimum threshold.

## assert_response_time_within_limits()

```python
def assert_response_time_within_limits(duration: float, max_duration: float = 1.0):
```

Assert that response time is within acceptable limits.

## assert_valid_api_key_format()

```python
def assert_valid_api_key_format(api_key: str):
```

Assert that API key has valid format.
