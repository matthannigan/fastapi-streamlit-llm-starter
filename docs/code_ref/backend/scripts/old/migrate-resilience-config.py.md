---
sidebar_label: migrate-resilience-config
---

# CLI tool for migrating legacy resilience configuration to preset-based system.

  file_path: `backend/scripts/old/migrate-resilience-config.py`

This script analyzes your current environment variables and provides
recommendations for migrating to the simplified preset-based configuration.

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
def analyze_configuration(env_file: Optional[str] = None) -> None:
```

Analyze current configuration and provide recommendations.

## generate_migration_files()

```python
def generate_migration_files(output_dir: str, format_type: str = 'all') -> None:
```

Generate migration files in specified format.

## interactive_migration()

```python
def interactive_migration() -> None:
```

Interactive migration wizard.

## main()

```python
def main():
```

Main CLI entry point.
