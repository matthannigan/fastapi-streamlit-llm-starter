---
sidebar_label: validate_cache_config
---

# Cache Configuration Validation Script

  file_path: `backend/scripts/validate_cache_config.py`

Provides validation, inspection, and recommendation capabilities for the
cache configuration preset system, following the resilience configuration 
validation pattern.

Usage:
    python validate_cache_config.py --list-presets
    python validate_cache_config.py --show-preset development
    python validate_cache_config.py --validate-current
    python validate_cache_config.py --validate-preset production
    python validate_cache_config.py --recommend-preset staging
    python validate_cache_config.py --quiet --list-presets

## CacheConfigValidator

Main validator class for cache configuration operations.

### __init__()

```python
def __init__(self, quiet: bool = False):
```

Initialize the validator.

### list_presets()

```python
def list_presets(self) -> None:
```

List all available cache presets with descriptions.

### show_preset()

```python
def show_preset(self, preset_name: str) -> None:
```

Show detailed configuration for a specific preset.

### validate_preset()

```python
def validate_preset(self, preset_name: str) -> None:
```

Validate a specific preset configuration.

### validate_current()

```python
def validate_current(self) -> None:
```

Validate the current cache configuration from environment.

### recommend_preset()

```python
def recommend_preset(self, environment: Optional[str] = None) -> None:
```

Recommend appropriate preset for given or detected environment.

## main()

```python
def main():
```

Main CLI interface.
