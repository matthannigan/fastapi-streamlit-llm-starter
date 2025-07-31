---
sidebar_label: config_presets
---

# Resilience Configuration Presets and Strategy Management

  file_path: `backend/app/infrastructure/resilience/config_presets.py`

This module provides a comprehensive system for managing resilience configurations
in AI service applications. It includes:

**Core Components:**
- ResilienceStrategy: Enum defining available resilience strategies (aggressive, balanced, conservative, critical)
- ResilienceConfig: Main configuration class combining retry, circuit breaker, and strategy settings
- ResiliencePreset: Predefined configuration templates for different deployment scenarios
- PresetManager: Advanced manager with validation, environment detection, and recommendation capabilities

**Preset System:**
- Pre-defined presets for common scenarios (simple, development, production)
- Environment-aware preset recommendations with confidence scoring
- Automatic environment detection from system variables and indicators
- Pattern-based environment classification for complex deployment names

**Strategy Configurations:**
- Default strategy presets with optimized retry and circuit breaker parameters
- Operation-specific strategy overrides for fine-grained control
- Validation system for configuration integrity

**Key Features:**
- Simplified configuration through presets instead of manual environment variables
- Intelligent environment detection and preset recommendation
- Comprehensive validation with fallback to basic validation
- Pattern matching for complex environment naming schemes
- Extensible preset system for custom deployment scenarios

**Usage:**
- Use preset_manager.recommend_preset() for automatic environment-based selection
- Access predefined presets via PRESETS dictionary or preset_manager.get_preset()
- Convert presets to full ResilienceConfig objects via to_resilience_config()
- Leverage DEFAULT_PRESETS for direct strategy-based configuration access

This module serves as the central configuration hub for all resilience-related
settings across the application, providing both simplified preset-based configuration
and advanced customization capabilities.
