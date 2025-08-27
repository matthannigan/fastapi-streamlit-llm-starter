---
sidebar_label: cache_presets
---

# Cache Configuration Presets and Strategy Management

  file_path: `backend/app/infrastructure/cache/cache_presets.py`

This module provides a comprehensive system for managing cache configurations
in AI service applications. It includes:

**Core Components:**
- CacheStrategy: Enum defining available cache strategies (fast, balanced, robust, ai_optimized)
- CacheConfig: Main configuration class combining Redis settings, performance tuning, and AI features
- CachePreset: Predefined configuration templates for different deployment scenarios
- CachePresetManager: Advanced manager with validation, environment detection, and recommendation capabilities

**Preset System:**
- Pre-defined presets for common scenarios (disabled, simple, development, production, ai-development, ai-production)
- Environment-aware preset recommendations with confidence scoring
- Automatic environment detection from system variables and indicators
- Pattern-based environment classification for complex deployment names

**Strategy Configurations:**
- Default strategy presets with optimized TTL, compression, and connection parameters
- AI-specific strategy configurations for text processing workloads
- Validation system for configuration integrity

**Key Features:**
- Simplified configuration through presets instead of 28+ environment variables
- Intelligent environment detection and preset recommendation
- Comprehensive validation with fallback to basic validation
- Pattern matching for complex environment naming schemes
- Extensible preset system for custom deployment scenarios

**Usage:**
- Use preset_manager.recommend_preset() for automatic environment-based selection
- Access predefined presets via CACHE_PRESETS dictionary or preset_manager.get_preset()
- Convert presets to full CacheConfig objects via to_cache_config()
- Leverage DEFAULT_PRESETS for direct strategy-based configuration access

This module serves as the central configuration hub for all cache-related
settings across the application, providing both simplified preset-based configuration
and advanced customization capabilities.
