---
sidebar_label: test_dependency_injection
---

# Test dependency injection in TextProcessorService.

  file_path: `backend/tests.old/unit/core/test_dependency_injection.py`

## TestTextProcessorDependencyInjection

Test that TextProcessorService correctly uses injected dependencies.

### test_constructor_uses_injected_settings()

```python
def test_constructor_uses_injected_settings(self):
```

Test that the constructor uses injected settings instance.

### test_agent_uses_injected_settings_model()

```python
def test_agent_uses_injected_settings_model(self):
```

Test that the AI agent is initialized with model from injected settings.

### test_batch_concurrency_uses_injected_settings()

```python
def test_batch_concurrency_uses_injected_settings(self):
```

Test that batch processing uses concurrency limit from injected settings.
