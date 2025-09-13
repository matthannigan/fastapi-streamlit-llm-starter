---
sidebar_label: migrate_cache_config
---

# CLI tool for migrating legacy cache configuration to preset-based system.

  file_path: `backend/scripts/old/migrate_cache_config.py`

This script analyzes your current environment variables and provides
recommendations for migrating from individual CACHE_* variables to the 
simplified preset-based configuration system.

Supports migration from Phase 3 cache configuration (28+ variables) to 
Phase 4 preset system (1 primary + 2-3 overrides).

## MigrationRecommendation

Recommendation for migrating to preset system.

## CacheConfigMigrator

Migrates legacy cache configuration to preset system.

### __init__()

```python
def __init__(self):
```

Initialize the migrator.

### detect_legacy_configuration()

```python
def detect_legacy_configuration(self, env_vars: Dict[str, str] = None) -> Dict[str, Any]:
```

Detect legacy cache configuration from environment variables.

Args:
    env_vars: Environment variables dict (defaults to os.environ)
    
Returns:
    Dictionary of detected legacy configuration

### find_best_preset_match()

```python
def find_best_preset_match(self, legacy_config: Dict[str, Any]) -> MigrationRecommendation:
```

Find the best preset match for legacy configuration.

Args:
    legacy_config: Detected legacy configuration
    
Returns:
    Migration recommendation with preset and overrides

## print_banner()

```python
def print_banner():
```

Print the CLI tool banner.

## print_preset_info()

```python
def print_preset_info():
```

Print information about available presets.

## analyze_configuration()

```python
def analyze_configuration(env_file: Optional[str] = None, quiet: bool = False) -> None:
```

Analyze current configuration and provide migration recommendations.

## main()

```python
def main():
```

Main CLI interface.
