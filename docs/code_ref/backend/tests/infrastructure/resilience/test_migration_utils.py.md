---
sidebar_label: test_migration_utils
---

# Unit tests for resilience configuration migration utilities.

  file_path: `backend/tests/infrastructure/resilience/test_migration_utils.py`

Tests the migration analysis, preset recommendation, and script generation
functionality for legacy-to-preset configuration migration.

## TestLegacyConfigAnalyzer

Test legacy configuration detection and analysis.

### test_detect_empty_legacy_configuration()

```python
def test_detect_empty_legacy_configuration(self):
```

Test detection when no legacy variables are present.

### test_detect_basic_legacy_configuration()

```python
def test_detect_basic_legacy_configuration(self):
```

Test detection of basic legacy configuration.

### test_detect_operation_specific_strategies()

```python
def test_detect_operation_specific_strategies(self):
```

Test detection of operation-specific strategy overrides.

### test_detect_advanced_retry_configuration()

```python
def test_detect_advanced_retry_configuration(self):
```

Test detection of advanced retry configuration parameters.

### test_detect_with_invalid_values()

```python
def test_detect_with_invalid_values(self):
```

Test detection handles invalid values gracefully.

### test_recommend_preset_no_legacy_config()

```python
def test_recommend_preset_no_legacy_config(self):
```

Test preset recommendation when no legacy config exists.

### test_recommend_preset_development_pattern()

```python
def test_recommend_preset_development_pattern(self):
```

Test recommendation for development-like configuration.

### test_recommend_preset_production_pattern()

```python
def test_recommend_preset_production_pattern(self):
```

Test recommendation for production-like configuration.

### test_recommend_preset_with_custom_overrides()

```python
def test_recommend_preset_with_custom_overrides(self):
```

Test recommendation generates custom overrides for non-standard values.

### test_generate_migration_warnings()

```python
def test_generate_migration_warnings(self):
```

Test generation of migration warnings for problematic configurations.

### test_generate_migration_steps()

```python
def test_generate_migration_steps(self):
```

Test generation of detailed migration steps.

### test_preset_scoring_calculation()

```python
def test_preset_scoring_calculation(self):
```

Test preset scoring calculation logic.

## TestConfigurationMigrator

Test configuration migration orchestration.

### test_analyze_current_environment()

```python
def test_analyze_current_environment(self):
```

Test analysis of current environment variables.

### test_generate_bash_migration_script()

```python
def test_generate_bash_migration_script(self):
```

Test generation of bash migration script.

### test_generate_env_file_migration()

```python
def test_generate_env_file_migration(self):
```

Test generation of .env file migration.

### test_generate_docker_migration()

```python
def test_generate_docker_migration(self):
```

Test generation of Docker environment migration.

### test_generate_invalid_format_raises_error()

```python
def test_generate_invalid_format_raises_error(self):
```

Test that invalid format raises appropriate error.

## TestMigrationIntegration

Test integration scenarios for migration utilities.

### test_full_migration_workflow_development()

```python
def test_full_migration_workflow_development(self):
```

Test complete migration workflow for development scenario.

### test_full_migration_workflow_production()

```python
def test_full_migration_workflow_production(self):
```

Test complete migration workflow for production scenario.

### test_migration_with_complex_custom_overrides()

```python
def test_migration_with_complex_custom_overrides(self):
```

Test migration with complex custom configuration requirements.

### test_global_migrator_instance()

```python
def test_global_migrator_instance(self, mock_environ):
```

Test the global migrator instance functionality.

### test_edge_case_empty_environment()

```python
def test_edge_case_empty_environment(self):
```

Test migration analysis with completely empty environment.

### test_edge_case_partial_configuration()

```python
def test_edge_case_partial_configuration(self):
```

Test migration with only partial legacy configuration.

## TestMigrationRecommendation

Test MigrationRecommendation data class.

### test_migration_recommendation_creation()

```python
def test_migration_recommendation_creation(self):
```

Test creation of migration recommendation.

### test_migration_recommendation_with_all_fields()

```python
def test_migration_recommendation_with_all_fields(self):
```

Test creation with all fields populated.
