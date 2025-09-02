---
sidebar_label: validate_docs
---

# Documentation validation script for FastAPI-Streamlit-LLM Starter.

  file_path: `scripts/validate_docs.py`

This script validates that documentation matches the actual implementation,
including file references, environment variables, code examples, and Docker commands.

## ValidationError

Custom exception for validation errors.

## DocumentationValidator

Main class for validating documentation against implementation.

### __init__()

```python
def __init__(self, project_root: Optional[Path] = None):
```

Initialize the validator with project root directory.

### validate_documentation()

```python
def validate_documentation(self):
```

Main validation function that runs all validation checks.

### validate_file_references()

```python
def validate_file_references(self):
```

Check that all referenced files exist.

### validate_environment_variables()

```python
def validate_environment_variables(self):
```

Verify environment variables match across all configuration files.

### validate_code_examples()

```python
def validate_code_examples(self):
```

Test that all code examples work.

### validate_docker_commands()

```python
def validate_docker_commands(self):
```

Validate Docker commands and configurations.

### validate_api_documentation()

```python
def validate_api_documentation(self):
```

Validate API documentation consistency.

### validate_integration()

```python
def validate_integration(self):
```

Test integration scenarios.

### report_results()

```python
def report_results(self):
```

Report validation results.

## validate_documentation()

```python
def validate_documentation():
```

Main validation function.
