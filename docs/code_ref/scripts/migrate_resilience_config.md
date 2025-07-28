# Resilience Configuration Migration Script

  file_path: `scripts/migrate_resilience_config.py`

This script helps migrate from legacy resilience configuration (47+ environment variables)
to the simplified preset-based configuration system.

## Usage

python scripts/migrate_resilience_config.py [options]

## Options

--analyze         Analyze current configuration and suggest preset
--migrate         Generate migration commands
--dry-run         Show what would be done without making changes
--output FILE     Save migration to file
--help            Show this help message
