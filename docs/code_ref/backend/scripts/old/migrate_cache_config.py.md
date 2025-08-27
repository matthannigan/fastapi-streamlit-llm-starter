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
