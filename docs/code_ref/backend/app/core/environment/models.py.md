---
sidebar_label: models
---

# Data models for environment detection.

  file_path: `backend/app/core/environment/models.py`

Contains dataclasses and data structures used in environment detection including
EnvironmentSignal, EnvironmentInfo, and DetectionConfig.

## EnvironmentSignal

Single environment detection signal with confidence scoring and reasoning.

Represents one piece of evidence used in environment detection, such as
an environment variable, system indicator, or hostname pattern match.
Each signal includes confidence scoring to enable weighted decision making.

Attributes:
    source: Detection mechanism that generated this signal (e.g., "env_var", "hostname_pattern")
    value: Raw value that triggered the detection (e.g., "production", "staging.example.com")
    environment: Environment classification this signal indicates
    confidence: Confidence score from 0.0-1.0 for this detection
    reasoning: Human-readable explanation of why this signal indicates the environment

Examples:
    >>> signal = EnvironmentSignal(
    ...     source="ENVIRONMENT",
    ...     value="production",
    ...     environment=Environment.PRODUCTION,
    ...     confidence=0.95,
    ...     reasoning="Explicit environment from ENVIRONMENT=production"
    ... )
    >>> assert signal.confidence > 0.9
    >>> assert signal.environment == Environment.PRODUCTION

## EnvironmentInfo

Comprehensive environment detection result with confidence scoring and metadata.

Contains the final environment determination along with confidence scoring,
reasoning, and supporting evidence. Includes feature-specific context and
metadata for advanced use cases like preset selection or security overrides.

Attributes:
    environment: Final determined environment classification
    confidence: Overall confidence score from 0.0-1.0 for the detection
    reasoning: Human-readable explanation of the detection decision
    detected_by: Primary detection mechanism that determined the environment
    feature_context: Feature-specific context used in detection
    additional_signals: All environment signals collected during detection
    metadata: Feature-specific metadata and configuration hints

Usage:
    # Basic environment checking
    env_info = detector.detect_environment()
    if env_info.environment == Environment.PRODUCTION and env_info.confidence > 0.8:
        enable_production_features()

    # Feature-aware detection
    ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)
    if 'ai_prefix' in ai_env.metadata:
        cache_key_prefix = ai_env.metadata['ai_prefix']

    # Debugging detection issues
    print(f"Environment: {env_info}")
    print(f"Reasoning: {env_info.reasoning}")
    for signal in env_info.additional_signals:
        print(f"  - {signal.source}: {signal.reasoning}")

### __str__()

```python
def __str__(self) -> str:
```

## DetectionConfig

Configuration for environment detection behavior and patterns.

Controls how the EnvironmentDetector identifies environments through
environment variables, patterns, indicators, and feature-specific overrides.
Allows customization of detection logic for different deployment scenarios.

Attributes:
    env_var_precedence: Environment variables checked in priority order
    development_patterns: Regex patterns indicating development environments
    staging_patterns: Regex patterns indicating staging environments
    production_patterns: Regex patterns indicating production environments
    development_indicators: System indicators suggesting development
    production_indicators: System indicators suggesting production
    feature_contexts: Feature-specific configuration overrides

Examples:
    # Custom configuration for specialized deployment
    config = DetectionConfig(
        env_var_precedence=['CUSTOM_ENV', 'ENVIRONMENT'],
        production_patterns=[r'.*live.*', r'.*prod.*']
    )
    detector = EnvironmentDetector(config)

    # Add custom feature context
    config.feature_contexts[FeatureContext.AI_ENABLED] = {
        'environment_var': 'ENABLE_AI_FEATURES',
        'true_values': ['true', '1', 'enabled']
    }
