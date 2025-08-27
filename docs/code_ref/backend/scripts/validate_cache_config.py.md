---
sidebar_label: validate_cache_config
---

# Cache Configuration Validation Script

  file_path: `backend/scripts/validate_cache_config.py`

Provides validation, inspection, and recommendation capabilities for the
cache configuration preset system, following the resilience configuration
validation pattern.

## Usage

python validate_cache_config.py --list-presets
python validate_cache_config.py --show-preset development
python validate_cache_config.py --validate-current
python validate_cache_config.py --validate-preset production
python validate_cache_config.py --recommend-preset staging
python validate_cache_config.py --quiet --list-presets
