---
sidebar_label: migrate_resilience_config
---

# Resilience Configuration Migration Script

  file_path: `scripts/migrate_resilience_config.py`

This script helps migrate from legacy resilience configuration (47+ environment variables)
to the simplified preset-based configuration system.

Usage:
    python scripts/migrate_resilience_config.py [options]

Options:
    --analyze         Analyze current configuration and suggest preset
    --migrate         Generate migration commands
    --dry-run         Show what would be done without making changes
    --output FILE     Save migration to file
    --help            Show this help message

## ResilienceConfigMigrator

Migrate legacy resilience configuration to preset-based system.

### __init__()

```python
def __init__(self):
```

### analyze_current_config()

```python
def analyze_current_config(self) -> Dict[str, any]:
```

Analyze current configuration and provide recommendations.

### generate_migration_commands()

```python
def generate_migration_commands(self, target_preset: Optional[str] = None) -> List[str]:
```

Generate shell commands for migration.

## main()

```python
def main():
```

Main migration script entry point.
