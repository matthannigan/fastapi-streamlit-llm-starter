---
sidebar_label: test_domain_integration_helpers
---

# Helper utilities for tests that mix domain and infrastructure concerns.

  file_path: `backend/tests.old/unit/infrastructure/resilience/test_domain_integration_helpers.py`

This file provides utilities for tests that need to simulate domain service
registration with the resilience infrastructure. These are temporary helpers
until the domain/infrastructure test separation is fully implemented.

## MockDomainService

Mock domain service that registers operations.

Useful for testing how the infrastructure handles domain service integration.

### __init__()

```python
def __init__(self, resilience_service, operations = None):
```

### get_registered_operations()

```python
def get_registered_operations(self):
```

Get list of operations registered by this domain service.

## register_text_processing_operations()

```python
def register_text_processing_operations(resilience_service):
```

Register typical text processing operations with resilience service.

This simulates what TextProcessorService would do during initialization.
Used for tests that need to verify infrastructure behavior with registered operations.

## register_legacy_operation_names()

```python
def register_legacy_operation_names(resilience_service):
```

Register operations using legacy naming (for backward compatibility tests).

These match the old hardcoded operation names that were in the orchestrator.

## register_custom_operations()

```python
def register_custom_operations(resilience_service, operations_config):
```

Register custom operations for testing specific scenarios.

Args:
    resilience_service: The resilience service instance
    operations_config: Dict mapping operation names to ResilienceStrategy

Returns:
    List of registered operation names

## create_test_resilience_service_with_operations()

```python
def create_test_resilience_service_with_operations(settings = None, operation_type = 'text_processing'):
```

Create a resilience service with pre-registered operations for testing.

Args:
    settings: Optional settings object
    operation_type: Type of operations to register ("text_processing", "legacy", "custom")

Returns:
    Tuple of (resilience_service, registered_operations)
