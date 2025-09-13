---
sidebar_label: cache_presets
---

# Cache configuration presets and strategy management system.

  file_path: `backend/app/infrastructure/cache/cache_presets.py`

This module provides a comprehensive preset system for managing cache configurations
across different deployment environments, reducing complexity by replacing dozens of
individual environment variables with simple preset selections.

## Core Components

- **CacheStrategy**: Enum defining cache strategies (fast, balanced, robust, ai_optimized)
- **CacheConfig**: Main configuration combining Redis settings and AI features
- **CachePreset**: Predefined configuration templates for deployment scenarios
- **CachePresetManager**: Advanced manager with validation and environment detection

## Preset System

- **Predefined Presets**: Common scenarios (disabled, development, production, ai-production)
- **Environment Detection**: Automatic environment detection and recommendations
- **Confidence Scoring**: Environment-aware preset recommendations with confidence levels
- **Pattern Matching**: Intelligent environment classification for complex deployments

## Strategy Configurations

- **Optimized Defaults**: Strategy presets with optimal TTL, compression, and connection settings
- **AI Optimizations**: Specialized configurations for text processing and AI workloads
- **Validation**: Comprehensive configuration integrity validation

## Key Features

- **Simplified Setup**: Single preset replaces 28+ individual environment variables
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

## EnvironmentRecommendation

Environment-based preset recommendation with confidence and reasoning.

## CacheStrategy

Cache strategy enumeration defining optimized configurations for different deployment scenarios.

Provides predefined strategy types that automatically configure TTL values, compression settings,
and performance parameters for common deployment patterns. Each strategy balances performance,
reliability, and resource usage for specific use cases.

Values:
    FAST: Development and testing strategy with minimal TTLs (60-300s) and fast access
    BALANCED: Production default with moderate TTLs (3600-7200s) and balanced performance
    ROBUST: High-reliability strategy with extended TTLs (7200-86400s) for stability
    AI_OPTIMIZED: AI workload strategy with text hashing and intelligent caching (1800-14400s)

Behavior:
    - String enum supporting direct comparison and serialization
    - Each strategy maps to specific configuration parameters in DEFAULT_PRESETS
    - Provides consistent configuration across different deployment environments
    - Enables easy strategy switching without manual parameter tuning

Examples:
    >>> strategy = CacheStrategy.BALANCED
    >>> print(f"Using {strategy} strategy")
    Using balanced strategy

    >>> # Strategy-based configuration
    >>> config = DEFAULT_PRESETS[CacheStrategy.AI_OPTIMIZED]
    >>> print(f"Default TTL: {config.default_ttl}s")

    >>> # Environment-based strategy selection
    >>> if is_production():
    ...     strategy = CacheStrategy.ROBUST
    ... else:
    ...     strategy = CacheStrategy.FAST

## CacheConfig

Comprehensive cache configuration with Redis settings, performance tuning, and AI optimizations.

Provides complete configuration management for cache systems with validation, environment
integration, and strategy-based presets. Supports both simple Redis caching and advanced
AI-optimized configurations with text processing capabilities.

Attributes:
    strategy: CacheStrategy enum defining the caching approach and default parameters
    redis_url: Optional[str] Redis connection URL (redis://, rediss://, unix://)
    redis_password: Optional[str] Redis authentication password
    use_tls: bool enable TLS encryption for Redis connections
    tls_cert_path: Optional[str] path to TLS certificate file
    default_ttl: int default time-to-live in seconds (60-86400)
    enable_compression: bool enable automatic data compression
    compression_threshold: int bytes threshold for triggering compression (1024-65536)
    max_connections: int maximum Redis connection pool size (1-100)
    connection_timeout: int connection timeout in seconds (1-30)
    enable_ai_features: bool enable AI-specific caching optimizations
    text_hash_threshold: int character threshold for text hashing (500-10000)
    operation_specific_ttls: Dict[str, int] TTL overrides per operation type

State Management:
    - Immutable configuration after creation for consistent behavior
    - Validation methods ensure configuration integrity
    - Strategy-based defaults provide production-ready configurations
    - Environment integration supports deployment-specific customization

Usage:
    # Strategy-based configuration
    config = CacheConfig(strategy=CacheStrategy.AI_OPTIMIZED)

    # Custom configuration with overrides
    config = CacheConfig(
        strategy=CacheStrategy.BALANCED,
        redis_url="redis://cache-cluster:6379",
        default_ttl=7200,
        enable_ai_features=True
    )

    # Production configuration with security
    config = CacheConfig(
        strategy=CacheStrategy.ROBUST,
        use_tls=True,
        tls_cert_path="/etc/ssl/redis.crt",
        redis_password=os.environ["REDIS_PASSWORD"]
    )

### to_dict()

```python
def to_dict(self) -> Dict[str, Any]:
```

Convert configuration to dictionary for factory usage.

### validate()

```python
def validate(self):
```

Validate cache configuration settings.

Returns:
    ValidationResult with any errors or warnings found

## CachePreset

Predefined cache configuration preset with validation and environment-specific optimization.

Encapsulates complete cache configuration including Redis settings, performance parameters,
and AI-specific features for streamlined deployment across different environments.
Provides validation, conversion methods, and intelligent defaults.

Attributes:
    name: str unique preset identifier for reference and logging
    description: str human-readable preset description for documentation
    strategy: CacheStrategy base strategy defining performance characteristics
    redis_settings: Dict[str, Any] Redis connection and performance parameters
    performance_settings: Dict[str, Any] caching performance and optimization settings
    ai_settings: Dict[str, Any] AI-specific configuration for text processing

Public Methods:
    to_cache_config(): Convert preset to full CacheConfig instance
    validate(): Validate preset configuration integrity
    merge_with(): Merge with another preset for configuration inheritance

State Management:
    - Immutable preset configuration after initialization
    - Comprehensive validation with detailed error reporting
    - Environment-specific parameter optimization
    - Strategy-based intelligent defaults

Usage:
    # Access predefined presets
    preset = CACHE_PRESETS['production']
    config = preset.to_cache_config()

    # Custom preset creation
    custom_preset = CachePreset(
        name="high_performance",
        description="High-performance caching for real-time applications",
        strategy=CacheStrategy.FAST,
        redis_settings={
            "max_connections": 50,
            "connection_timeout": 5
        }
    )

    # Preset validation and conversion
    if custom_preset.validate():
        cache_config = custom_preset.to_cache_config()
        cache = initialize_cache(cache_config)

### to_dict()

```python
def to_dict(self) -> Dict[str, Any]:
```

Convert preset to dictionary for serialization.

### to_cache_config()

```python
def to_cache_config(self):
```

Convert preset to cache configuration object compatible with config.py CacheConfig.

## CachePresetManager

Manager for cache presets with validation and recommendation capabilities.

### __init__()

```python
def __init__(self):
```

Initialize preset manager with default presets.

### get_preset()

```python
def get_preset(self, name: str) -> CachePreset:
```

Get preset by name with validation.

Args:
    name: Preset name (disabled, simple, development, production, ai-development, ai-production)

Returns:
    CachePreset object

Raises:
    ValueError: If preset name is not found

### list_presets()

```python
def list_presets(self) -> List[str]:
```

Get list of available preset names.

### get_preset_details()

```python
def get_preset_details(self, name: str) -> Dict[str, Any]:
```

Get detailed information about a preset.

### validate_preset()

```python
def validate_preset(self, preset: CachePreset) -> bool:
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

Get summary of all available presets.

## get_default_presets()

```python
def get_default_presets() -> Dict[CacheStrategy, CacheConfig]:
```

Returns a dictionary of default cache strategy configurations.
