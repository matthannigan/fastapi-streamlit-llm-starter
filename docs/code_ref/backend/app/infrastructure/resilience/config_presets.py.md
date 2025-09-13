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

## EnvironmentRecommendation

Environment-based preset recommendation with confidence and reasoning.

## ResilienceStrategy

Resilience strategy enumeration defining optimized patterns for different operation criticality levels.

Provides predefined strategy configurations that automatically optimize retry attempts,
circuit breaker thresholds, and timeout values based on operation requirements and
acceptable latency/reliability trade-offs.

Values:
    AGGRESSIVE: Fast retries (3 attempts), low circuit breaker thresholds (3 failures)
               for user-facing operations requiring quick response
    BALANCED: Moderate retries (3 attempts), balanced thresholds (5 failures)
             for standard API operations and background processing
    CONSERVATIVE: Minimal retries (2 attempts), high thresholds (10 failures)
                 for resource-intensive operations and batch processing
    CRITICAL: Maximum retries (5 attempts), highest thresholds (15 failures)
             for mission-critical operations requiring highest reliability
             
Behavior:
    - String enum supporting serialization and direct comparison
    - Each strategy maps to specific retry and circuit breaker configurations
    - Strategies balance latency, reliability, and resource consumption
    - Enables consistent resilience patterns across different services
    
Examples:
    >>> strategy = ResilienceStrategy.BALANCED
    >>> config = DEFAULT_PRESETS[strategy]
    >>> print(f"Max attempts: {config.retry_config.max_attempts}")
    
    >>> # Strategy selection based on operation criticality
    >>> if operation_type == "user_facing":
    ...     strategy = ResilienceStrategy.AGGRESSIVE
    >>> elif operation_type == "critical":
    ...     strategy = ResilienceStrategy.CRITICAL
    >>> else:
    ...     strategy = ResilienceStrategy.BALANCED

## ResilienceConfig

Comprehensive resilience configuration with retry mechanisms, circuit breakers, and strategy management.

Provides complete configuration for resilience patterns including retry behavior,
circuit breaker policies, and feature toggles. Integrates with strategy-based presets
while supporting custom configuration overrides for specific requirements.

Attributes:
    strategy: ResilienceStrategy enum defining the overall resilience approach
    retry_config: RetryConfig with exponential backoff and jitter settings
    circuit_breaker_config: CircuitBreakerConfig with failure thresholds and recovery
    enable_circuit_breaker: bool to enable/disable circuit breaker functionality
    enable_retry: bool to enable/disable retry mechanisms
    
State Management:
    - Immutable configuration after creation for consistent behavior
    - Strategy-based defaults with override capabilities
    - Comprehensive validation ensuring configuration integrity
    - Thread-safe access for concurrent resilience operations
    
Usage:
    # Strategy-based configuration
    config = ResilienceConfig(strategy=ResilienceStrategy.CRITICAL)
    
    # Custom configuration with overrides
    config = ResilienceConfig(
        strategy=ResilienceStrategy.BALANCED,
        retry_config=RetryConfig(max_attempts=5),
        circuit_breaker_config=CircuitBreakerConfig(failure_threshold=3)
    )
    
    # Feature-specific configuration
    config = ResilienceConfig(
        strategy=ResilienceStrategy.CONSERVATIVE,
        enable_circuit_breaker=False,  # Retry-only mode
        enable_retry=True
    )
    
    # Integration with orchestrator
    orchestrator = AIServiceResilience()
    @orchestrator.with_resilience("ai_operation", custom_config=config)
    async def ai_operation():
        return await ai_service.process()

## ResiliencePreset

Predefined resilience configuration preset.

Encapsulates retry, circuit breaker, and strategy settings
for different deployment scenarios.

### to_dict()

```python
def to_dict(self) -> Dict[str, Any]:
```

Convert preset to dictionary for serialization.

### to_resilience_config()

```python
def to_resilience_config(self) -> ResilienceConfig:
```

Convert preset to resilience configuration object.

## PresetManager

Manager for resilience presets with validation and recommendation capabilities.

### __init__()

```python
def __init__(self):
```

Initialize preset manager with default presets.

### get_preset()

```python
def get_preset(self, name: str) -> ResiliencePreset:
```

Get preset by name with validation.

Args:
    name: Preset name (simple, development, production)
    
Returns:
    ResiliencePreset object
    
Raises:
    ValueError: If preset name is not found

### list_presets()

```python
def list_presets(self) -> List[str]:
```

Get list of available preset names.

Returns:
    List of preset names (e.g., ["simple", "development", "production"])

### get_preset_details()

```python
def get_preset_details(self, name: str) -> Dict[str, Any]:
```

Get detailed information about a specific preset.

Args:
    name: Preset name to get details for
    
Returns:
    Dictionary containing preset configuration details, description, and context

### validate_preset()

```python
def validate_preset(self, preset: ResiliencePreset) -> bool:
```

Validate preset configuration values.

Args:
    preset: Preset to validate
    
Returns:
    True if valid, False otherwise

### recommend_preset()

```python
def recommend_preset(self, environment: Optional[str] = None) -> str:
```

Recommend appropriate preset for given environment.

Args:
    environment: Environment name (dev, test, staging, prod, etc.)
    If None, will auto-detect from environment variables
    
Returns:
    Recommended preset name

### recommend_preset_with_details()

```python
def recommend_preset_with_details(self, environment: Optional[str] = None) -> EnvironmentRecommendation:
```

Get detailed environment-aware preset recommendation.

Args:
    environment: Environment name or None for auto-detection
    
Returns:
    EnvironmentRecommendation with preset, confidence, and reasoning

### get_all_presets_summary()

```python
def get_all_presets_summary(self) -> Dict[str, Dict[str, Any]]:
```

Get summary of all available presets with their detailed information.

Returns:
    Dictionary mapping preset names to their detailed configuration information

## get_default_presets()

```python
def get_default_presets() -> Dict[ResilienceStrategy, ResilienceConfig]:
```

Returns a dictionary of default resilience strategy configurations.

Creates pre-configured ResilienceConfig objects for each available strategy
(aggressive, balanced, conservative, critical) with optimized settings for
different operational requirements.

Returns:
    Dictionary mapping ResilienceStrategy enum values to configured ResilienceConfig objects
