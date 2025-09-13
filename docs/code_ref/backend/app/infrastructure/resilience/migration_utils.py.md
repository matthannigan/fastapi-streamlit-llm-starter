---
sidebar_label: migration_utils
---

# Configuration migration utilities for legacy-to-preset migration.

  file_path: `backend/app/infrastructure/resilience/migration_utils.py`

This module provides tools to analyze legacy resilience configurations
and recommend appropriate preset replacements with migration guidance.

## MigrationConfidence

Confidence levels for migration recommendations.

## MigrationRecommendation

Recommendation for migrating from legacy to preset configuration.

### __post_init__()

```python
def __post_init__(self):
```

## LegacyConfigAnalyzer

Analyzer for legacy resilience configuration patterns.

### __init__()

```python
def __init__(self):
```

Initialize the legacy configuration analyzer.

### detect_legacy_configuration()

```python
def detect_legacy_configuration(self, env_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
```

Detect legacy resilience configuration from environment variables.

Args:
    env_vars: Environment variables to analyze (if None, uses os.environ)
    
Returns:
    Dictionary of detected legacy configuration values

### recommend_preset()

```python
def recommend_preset(self, legacy_config: Dict[str, Any]) -> MigrationRecommendation:
```

Recommend appropriate preset based on legacy configuration analysis.

Args:
    legacy_config: Detected legacy configuration
    
Returns:
    Migration recommendation with preset, confidence, and guidance

## ConfigurationMigrator

Tool for performing automated configuration migrations.

### __init__()

```python
def __init__(self):
```

Initialize the configuration migrator.

### analyze_current_environment()

```python
def analyze_current_environment(self) -> MigrationRecommendation:
```

Analyze current environment and provide migration recommendation.

### generate_migration_script()

```python
def generate_migration_script(self, recommendation: MigrationRecommendation, output_format: str = 'bash') -> str:
```

Generate migration script in specified format.

Args:
    recommendation: Migration recommendation to implement
    output_format: Script format ('bash', 'env', 'docker')
    
Returns:
    Generated migration script content
