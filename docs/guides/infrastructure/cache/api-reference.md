---
sidebar_label: API Reference
---

# Cache Infrastructure API Reference

This document provides comprehensive API reference documentation for all public APIs and interfaces in the cache infrastructure. The cache infrastructure provides production-ready caching capabilities with Redis backend support, automatic fallback to memory cache, performance monitoring, and comprehensive configuration management.

## Table of Contents

1. [CacheFactory API](#cachefactory-api)
2. [Configuration APIs](#configuration-apis)
3. [CacheInterface Contract](#cacheinterface-contract)
4. [Dependency Injection Functions](#dependency-injection-functions)
5. [Benchmark APIs](#benchmark-apis)
6. [Callback System](#callback-system)
7. [Exception Types](#exception-types)
8. [Usage Examples](#usage-examples)

---

## CacheFactory API

The `CacheFactory` class provides explicit cache instantiation with environment-optimized defaults and comprehensive error handling.

### Class: CacheFactory

```python
from app.infrastructure.cache.factory import CacheFactory
```

#### Constructor

```python
def __init__(self) -> None
```

Initializes the CacheFactory with default configuration and optional performance monitoring.

**Example:**
```python
factory = CacheFactory()
```

#### Core Factory Methods

##### for_web_app()

```python
async def for_web_app(
    self,
    redis_url: str = "redis://redis:6379",
    default_ttl: int = 1800,
    enable_l1_cache: bool = True,
    l1_cache_size: int = 200,
    compression_threshold: int = 2000,
    compression_level: int = 6,
    fail_on_connection_error: bool = False,
    **kwargs
) -> CacheInterface
```

Creates a cache optimized for web applications with balanced performance.

> **💡 For practical examples**: See the [Cache Usage Guide](./usage-guide.md#web-application-patterns) for complete web application caching patterns.

**Parameters:**
- `redis_url` (str): Redis server URL. Default: "redis://redis:6379"
- `default_ttl` (int): Default time-to-live in seconds. Default: 1800 (30 minutes)
- `enable_l1_cache` (bool): Enable in-memory L1 cache. Default: True
- `l1_cache_size` (int): Maximum L1 cache entries. Default: 200
- `compression_threshold` (int): Compress data above this size in bytes. Default: 2000
- `compression_level` (int): Zlib compression level 1-9. Default: 6
- `fail_on_connection_error` (bool): Raise error if Redis unavailable. Default: False
- `**kwargs`: Additional parameters passed to GenericRedisCache

**Returns:**
- `CacheInterface`: Configured cache instance (GenericRedisCache or InMemoryCache fallback)

**Raises:**
- `ValidationError`: Invalid parameter values or combinations
- `ConfigurationError`: Configuration conflicts or missing requirements
- `InfrastructureError`: Redis connection failed and fail_on_connection_error=True

**Example:**
```python
# Basic web application cache
cache = await factory.for_web_app()

# Production web cache with custom settings
cache = await factory.for_web_app(
    redis_url="redis://production:6379",
    default_ttl=3600,  # 1 hour
    fail_on_connection_error=True
)
```

##### for_ai_app()

```python
async def for_ai_app(
    self,
    redis_url: str = "redis://redis:6379",
    default_ttl: int = 3600,
    enable_l1_cache: bool = True,
    l1_cache_size: int = 100,
    compression_threshold: int = 1000,
    compression_level: int = 6,
    text_hash_threshold: int = 500,
    memory_cache_size: Optional[int] = None,
    operation_ttls: Optional[Dict[str, int]] = None,
    fail_on_connection_error: bool = False,
    **kwargs
) -> CacheInterface
```

Creates a cache optimized for AI applications with enhanced storage and compression.

> **💡 For practical examples**: See the [Cache Usage Guide](./usage-guide.md#ai-response-caching-patterns) for comprehensive AI response caching strategies.

**Parameters:**
- `redis_url` (str): Redis server URL. Default: "redis://redis:6379"
- `default_ttl` (int): Default time-to-live in seconds. Default: 3600 (1 hour)
- `enable_l1_cache` (bool): Enable in-memory L1 cache. Default: True
- `l1_cache_size` (int): Maximum L1 cache entries. Default: 100
- `compression_threshold` (int): Compress data above this size in bytes. Default: 1000
- `compression_level` (int): Zlib compression level 1-9. Default: 6
- `text_hash_threshold` (int): Hash text above this length for keys. Default: 500
- `memory_cache_size` (Optional[int]): Override l1_cache_size if provided
- `operation_ttls` (Optional[Dict[str, int]]): Custom TTLs per AI operation type
- `fail_on_connection_error` (bool): Raise error if Redis unavailable. Default: False
- `**kwargs`: Additional parameters passed to AIResponseCache

**Returns:**
- `CacheInterface`: Configured AIResponseCache or InMemoryCache fallback

**Raises:**
- `ValidationError`: Invalid parameter values or combinations
- `ConfigurationError`: Configuration conflicts or missing requirements
- `InfrastructureError`: Redis connection failed and fail_on_connection_error=True

**Example:**
```python
# Basic AI application cache
cache = await factory.for_ai_app()

# Production AI cache with custom operation TTLs
cache = await factory.for_ai_app(
    redis_url="redis://ai-production:6379",
    default_ttl=7200,  # 2 hours
    operation_ttls={
        "summarize": 1800,  # 30 minutes
        "sentiment": 3600,  # 1 hour
        "translate": 7200   # 2 hours
    }
)
```

##### for_testing()

```python
async def for_testing(
    self,
    redis_url: str = "redis://redis:6379/15",
    default_ttl: int = 60,
    enable_l1_cache: bool = False,
    l1_cache_size: int = 50,
    compression_threshold: int = 1000,
    compression_level: int = 1,
    fail_on_connection_error: bool = False,
    use_memory_cache: bool = False,
    **kwargs
) -> CacheInterface
```

Creates a cache optimized for testing environments with short TTLs and fast operations.

**Parameters:**
- `redis_url` (str): Redis server URL with test DB. Default: "redis://redis:6379/15"
- `default_ttl` (int): Default time-to-live in seconds. Default: 60 (1 minute)
- `enable_l1_cache` (bool): Enable in-memory L1 cache. Default: False
- `l1_cache_size` (int): Maximum L1 cache entries. Default: 50
- `compression_threshold` (int): Compress data above this size in bytes. Default: 1000
- `compression_level` (int): Zlib compression level 1-9. Default: 1
- `fail_on_connection_error` (bool): Raise error if Redis unavailable. Default: False
- `use_memory_cache` (bool): Force InMemoryCache usage. Default: False
- `**kwargs`: Additional parameters passed to cache implementation

**Returns:**
- `CacheInterface`: Configured cache instance optimized for testing

**Example:**
```python
# Basic testing cache
cache = await factory.for_testing()

# Memory-only testing cache
cache = await factory.for_testing(use_memory_cache=True)
```

##### create_cache_from_config()

```python
async def create_cache_from_config(
    self,
    config: Dict[str, Any],
    fail_on_connection_error: bool = False
) -> CacheInterface
```

Creates a cache instance from a configuration dictionary with flexible parameter support.

**Parameters:**
- `config` (Dict[str, Any]): Configuration dictionary with cache parameters
- `fail_on_connection_error` (bool): Raise error if Redis unavailable. Default: False

**Required Configuration Keys:**
- `redis_url` (str): Redis server URL

**Optional Configuration Keys:**
- `default_ttl` (int): Default time-to-live in seconds
- `enable_l1_cache` (bool): Enable in-memory L1 cache
- `l1_cache_size` (int): Maximum L1 cache entries
- `compression_threshold` (int): Compress data above this size
- `compression_level` (int): Zlib compression level 1-9
- `text_hash_threshold` (int): Hash text above this length (triggers AIResponseCache)
- `operation_ttls` (Dict[str, int]): Custom TTLs per operation (triggers AIResponseCache)
- `memory_cache_size` (int): Override l1_cache_size (triggers AIResponseCache)

**Returns:**
- `CacheInterface`: Configured cache instance based on configuration

**Example:**
```python
config = {
    "redis_url": "redis://localhost:6379",
    "default_ttl": 3600,
    "enable_l1_cache": True,
    "compression_threshold": 2000
}
cache = await factory.create_cache_from_config(config)
```

#### Private Validation Method

##### _validate_factory_inputs()

```python
def _validate_factory_inputs(
    self,
    redis_url: Optional[str] = None,
    default_ttl: Optional[int] = None,
    fail_on_connection_error: bool = False,
    **kwargs
) -> None
```

Validates common factory method inputs with comprehensive error checking.

**Parameters:**
- `redis_url` (Optional[str]): Redis connection URL to validate
- `default_ttl` (Optional[int]): Time-to-live value to validate
- `fail_on_connection_error` (bool): Whether to fail on connection errors
- `**kwargs`: Additional parameters for extensibility

**Raises:**
- `ValidationError`: When required parameters are missing or invalid
- `ConfigurationError`: When parameter combinations are incompatible

---

## Configuration APIs

### Class: CacheConfig

Main configuration dataclass with comprehensive cache settings.

```python
from app.infrastructure.cache.config import CacheConfig
```

#### Attributes

```python
@dataclass
class CacheConfig:
    # Redis configuration
    redis_url: Optional[str] = None
    redis_password: Optional[str] = None
    use_tls: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    
    # Cache configuration
    default_ttl: int = 3600  # 1 hour
    memory_cache_size: int = 100
    compression_threshold: int = 1000
    compression_level: int = 6
    
    # Environment configuration
    environment: str = "development"
    
    # AI-specific configuration
    ai_config: Optional[AICacheConfig] = None
```

#### Methods

##### validate()

```python
def validate(self) -> ValidationResult
```

Validates the configuration settings.

**Returns:**
- `ValidationResult`: Validation results with errors and warnings

**Example:**
```python
config = CacheConfig(redis_url="redis://localhost:6379")
result = config.validate()
if not result.is_valid:
    print(f"Validation errors: {result.errors}")
```

##### to_dict()

```python
def to_dict(self) -> Dict[str, Any]
```

Converts configuration to dictionary representation.

**Returns:**
- `Dict[str, Any]`: Dictionary representation of the configuration

### Class: AICacheConfig

AI-specific cache configuration settings.

```python
from app.infrastructure.cache.config import AICacheConfig
```

#### Attributes

```python
@dataclass
class AICacheConfig:
    text_hash_threshold: int = 1000
    hash_algorithm: str = "sha256"
    text_size_tiers: Dict[str, int] = field(default_factory=lambda: {
        "small": 1000,
        "medium": 10000,
        "large": 100000
    })
    operation_ttls: Dict[str, int] = field(default_factory=lambda: {
        "summarize": 7200,  # 2 hours
        "sentiment": 3600,  # 1 hour
        "key_points": 5400, # 1.5 hours
        "questions": 4800,  # 1.33 hours
        "qa": 3600         # 1 hour
    })
    enable_smart_promotion: bool = True
    max_text_length: int = 100000
```

#### Methods

##### validate()

```python
def validate(self) -> ValidationResult
```

Validates AI configuration settings.

**Returns:**
- `ValidationResult`: Validation results with AI-specific errors and warnings

### Class: CacheConfigBuilder

Builder pattern implementation for flexible configuration construction.

> **💡 Configuration patterns**: See the [Cache Usage Guide](./usage-guide.md#configuration-patterns) for step-by-step configuration examples using the builder pattern.

```python
from app.infrastructure.cache.config import CacheConfigBuilder
```

#### Constructor

```python
def __init__(self) -> None
```

Initializes the builder with an empty configuration.

#### Fluent Interface Methods

##### for_environment()

```python
def for_environment(self, environment: str) -> 'CacheConfigBuilder'
```

Sets configuration for a specific environment with optimized defaults.

**Parameters:**
- `environment` (str): Environment name ("development", "testing", "production")

**Returns:**
- `CacheConfigBuilder`: Self for method chaining

**Raises:**
- `ValidationError`: If environment is not supported

##### with_redis()

```python
def with_redis(
    self,
    redis_url: str,
    password: Optional[str] = None,
    use_tls: bool = False
) -> 'CacheConfigBuilder'
```

Configures Redis connection settings.

**Parameters:**
- `redis_url` (str): Redis connection URL
- `password` (Optional[str]): Redis password
- `use_tls` (bool): Enable TLS for connection

**Returns:**
- `CacheConfigBuilder`: Self for method chaining

##### with_security()

```python
def with_security(
    self,
    tls_cert_path: Optional[str] = None,
    tls_key_path: Optional[str] = None
) -> 'CacheConfigBuilder'
```

Configures TLS security settings.

**Parameters:**
- `tls_cert_path` (Optional[str]): Path to TLS certificate file
- `tls_key_path` (Optional[str]): Path to TLS private key file

**Returns:**
- `CacheConfigBuilder`: Self for method chaining

##### with_compression()

```python
def with_compression(
    self,
    threshold: int = 1000,
    level: int = 6
) -> 'CacheConfigBuilder'
```

Configures compression settings.

**Parameters:**
- `threshold` (int): Size threshold for enabling compression
- `level` (int): Compression level (1-9)

**Returns:**
- `CacheConfigBuilder`: Self for method chaining

##### with_memory_cache()

```python
def with_memory_cache(self, size: int) -> 'CacheConfigBuilder'
```

Configures memory cache settings.

**Parameters:**
- `size` (int): Maximum size of memory cache

**Returns:**
- `CacheConfigBuilder`: Self for method chaining

##### with_ai_features()

```python
def with_ai_features(self, **ai_options) -> 'CacheConfigBuilder'
```

Enables and configures AI-specific features.

**Parameters:**
- `**ai_options`: AI configuration options (text_hash_threshold, hash_algorithm, operation_ttls, etc.)

**Returns:**
- `CacheConfigBuilder`: Self for method chaining

**Raises:**
- `ValidationError`: If unknown AI configuration options are provided

##### from_file()

```python
def from_file(self, file_path: Union[str, Path]) -> 'CacheConfigBuilder'
```

Loads configuration from a JSON file.

**Parameters:**
- `file_path` (Union[str, Path]): Path to JSON configuration file

**Returns:**
- `CacheConfigBuilder`: Self for method chaining

**Raises:**
- `ConfigurationError`: If file cannot be read or parsed

##### from_environment()

```python
def from_environment(self) -> 'CacheConfigBuilder'
```

Loads configuration from environment variables.

**Returns:**
- `CacheConfigBuilder`: Self for method chaining

#### Build and Validation Methods

##### validate()

```python
def validate(self) -> ValidationResult
```

Validates the current configuration without building.

**Returns:**
- `ValidationResult`: Validation results with errors and warnings

##### build()

```python
def build(self) -> CacheConfig
```

Builds and validates the final configuration.

**Returns:**
- `CacheConfig`: Validated configuration instance

**Raises:**
- `ValidationError`: If configuration validation fails

##### to_dict()

```python
def to_dict(self) -> Dict[str, Any]
```

Converts current configuration to dictionary.

**Returns:**
- `Dict[str, Any]`: Dictionary representation of the configuration

##### save_to_file()

```python
def save_to_file(
    self,
    file_path: Union[str, Path],
    create_dirs: bool = True
) -> None
```

Saves current configuration to a JSON file.

**Parameters:**
- `file_path` (Union[str, Path]): Path to save configuration file
- `create_dirs` (bool): Whether to create parent directories

**Raises:**
- `ConfigurationError`: If file cannot be written

**Example Usage:**
```python
config = (CacheConfigBuilder()
    .for_environment("production")
    .with_redis("redis://prod:6379")
    .with_compression(threshold=2000, level=6)
    .with_ai_features(text_hash_threshold=1500)
    .build())
```

### Class: EnvironmentPresets

Pre-configured cache settings for different environments.

```python
from app.infrastructure.cache.config import EnvironmentPresets
```

#### Static Methods

##### development()

```python
@staticmethod
def development() -> CacheConfig
```

Development environment preset with balanced performance and debugging.

**Returns:**
- `CacheConfig`: Configuration optimized for development

##### testing()

```python
@staticmethod
def testing() -> CacheConfig
```

Testing environment preset with minimal caching and fast expiration.

**Returns:**
- `CacheConfig`: Configuration optimized for testing

##### production()

```python
@staticmethod
def production() -> CacheConfig
```

Production environment preset with optimized performance and security.

**Returns:**
- `CacheConfig`: Configuration optimized for production

##### ai_development()

```python
@staticmethod
def ai_development() -> CacheConfig
```

AI development preset with AI features and development-friendly settings.

**Returns:**
- `CacheConfig`: Configuration optimized for AI development

##### ai_production()

```python
@staticmethod
def ai_production() -> CacheConfig
```

AI production preset with AI features and production-optimized settings.

**Returns:**
- `CacheConfig`: Configuration optimized for AI production workloads

### Class: ValidationResult

Result of configuration validation containing validation status and details.

```python
from app.infrastructure.cache.config import ValidationResult
```

#### Attributes

```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
```

#### Methods

##### add_error()

```python
def add_error(self, message: str) -> None
```

Adds an error message and marks validation as invalid.

##### add_warning()

```python
def add_warning(self, message: str) -> None
```

Adds a warning message.

---

## CacheInterface Contract

### Abstract Class: CacheInterface

Base interface that all cache implementations must implement.

```python
from app.infrastructure.cache.base import CacheInterface
```

#### Abstract Methods

##### get()

```python
@abstractmethod
async def get(self, key: str) -> Any
```

Retrieves a value from the cache.

**Parameters:**
- `key` (str): The cache key to retrieve

**Returns:**
- `Any`: The cached value, or None if not found

##### set()

```python
@abstractmethod
async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None
```

Stores a value in the cache.

**Parameters:**
- `key` (str): The cache key to store
- `value` (Any): The value to cache
- `ttl` (Optional[int]): Time-to-live in seconds (optional)

##### delete()

```python
@abstractmethod
async def delete(self, key: str) -> None
```

Removes a value from the cache.

**Parameters:**
- `key` (str): The cache key to delete

### Callback System APIs

#### Available Callback Events

The cache implementations support the following callback events:

- `get_success`: Fired when a cache get operation succeeds
- `get_miss`: Fired when a cache get operation results in a miss
- `set_success`: Fired when a cache set operation succeeds
- `delete_success`: Fired when a cache delete operation succeeds

#### Callback Registration

##### register_callback()

```python
def register_callback(self, event: str, callback: Callable) -> None
```

Registers a callback function for cache events.

**Parameters:**
- `event` (str): Event name (get_success, get_miss, set_success, delete_success)
- `callback` (Callable): The callback function to execute

**Callback Signatures:**
- `get_success(key: str, value: Any) -> None`
- `get_miss(key: str) -> None`
- `set_success(key: str, value: Any) -> None`
- `delete_success(key: str) -> None`

**Example:**
```python
def on_cache_hit(key: str, value: Any):
    print(f"Cache hit for key: {key}")

def on_cache_miss(key: str):
    print(f"Cache miss for key: {key}")

cache.register_callback('get_success', on_cache_hit)
cache.register_callback('get_miss', on_cache_miss)
```

---

## Dependency Injection Functions

### Primary Dependency Functions

#### get_cache_service()

```python
async def get_cache_service(
    config: CacheConfig = Depends(get_cache_config)
) -> CacheInterface
```

Primary dependency function for general-purpose cache access.

> **💡 Dependency injection patterns**: See the [Cache Usage Guide](./usage-guide.md#dependency-injection-patterns) for FastAPI dependency injection examples.

**Parameters:**
- `config` (CacheConfig): Cache configuration dependency

**Returns:**
- `CacheInterface`: Configured cache instance

**Usage:**
```python
@app.get("/data")
async def get_data(cache: CacheInterface = Depends(get_cache_service)):
    return await cache.get("data_key")
```

#### get_web_cache_service()

```python
async def get_web_cache_service(
    config: CacheConfig = Depends(get_cache_config)
) -> CacheInterface
```

Dependency function for web application cache with optimized settings.

**Parameters:**
- `config` (CacheConfig): Cache configuration dependency

**Returns:**
- `CacheInterface`: Web-optimized cache instance

#### get_ai_cache_service()

```python
async def get_ai_cache_service(
    config: CacheConfig = Depends(get_cache_config)
) -> CacheInterface
```

Dependency function for AI application cache with enhanced features.

**Parameters:**
- `config` (CacheConfig): Cache configuration dependency

**Returns:**
- `CacheInterface`: AI-optimized cache instance

### Configuration Dependencies

#### get_cache_config()

```python
async def get_cache_config(
    settings: Settings = Depends(get_settings)
) -> CacheConfig
```

Dependency function for cache configuration.

**Parameters:**
- `settings` (Settings): Application settings dependency

**Returns:**
- `CacheConfig`: Configured cache settings

#### get_settings()

```python
def get_settings() -> Settings
```

Dependency function for application settings.

**Returns:**
- `Settings`: Application settings instance

### Testing Dependencies

> **💡 Testing strategies**: See the [Cache Testing Guide](../CACHE_TESTING.md) for comprehensive testing patterns, mocking strategies, and test utilities.

#### get_test_cache()

```python
async def get_test_cache() -> CacheInterface
```

Dependency function for testing cache with minimal configuration.

**Returns:**
- `CacheInterface`: Test-optimized cache instance

#### get_test_redis_cache()

```python
async def get_test_redis_cache() -> CacheInterface
```

Dependency function for Redis-specific testing cache.

**Returns:**
- `CacheInterface`: Redis test cache instance

### Utility Dependencies

#### get_fallback_cache_service()

```python
async def get_fallback_cache_service() -> CacheInterface
```

Dependency function providing a fallback cache with safe defaults.

**Returns:**
- `CacheInterface`: InMemoryCache instance with safe defaults

#### validate_cache_configuration()

```python
async def validate_cache_configuration(
    config: CacheConfig = Depends(get_cache_config)
) -> CacheConfig
```

Dependency function that validates cache configuration.

**Parameters:**
- `config` (CacheConfig): Cache configuration to validate

**Returns:**
- `CacheConfig`: Validated configuration

**Raises:**
- `ValidationError`: If configuration validation fails

#### get_cache_service_conditional()

```python
async def get_cache_service_conditional(
    use_redis: bool = True,
    config: CacheConfig = Depends(get_cache_config)
) -> CacheInterface
```

Conditional dependency function for cache selection.

**Parameters:**
- `use_redis` (bool): Whether to use Redis or memory cache
- `config` (CacheConfig): Cache configuration dependency

**Returns:**
- `CacheInterface`: Conditionally selected cache instance

### Cleanup and Health Check Dependencies

#### cleanup_cache_registry()

```python
async def cleanup_cache_registry() -> Dict[str, Any]
```

Cleanup function for cache registry and connections.

**Returns:**
- `Dict[str, Any]`: Cleanup status and statistics

#### get_cache_health_status()

```python
async def get_cache_health_status(
    cache: CacheInterface = Depends(get_cache_service)
) -> Dict[str, Any]
```

Dependency function for cache health status.

**Parameters:**
- `cache` (CacheInterface): Cache instance to check

**Returns:**
- `Dict[str, Any]`: Health status information

---

## Benchmark APIs

### Class: CachePerformanceBenchmark

Main benchmarking orchestration class for comprehensive performance testing.

> **💡 Performance optimization**: See the [Cache Usage Guide](./usage-guide.md#performance-monitoring-and-benchmarking) for practical benchmarking examples and performance optimization strategies.

```python
from app.infrastructure.cache.benchmarks.core import CachePerformanceBenchmark
```

#### Constructor

```python
def __init__(
    self,
    cache: CacheInterface,
    config: Optional[BenchmarkConfig] = None
)
```

Initializes the benchmark with a cache instance and optional configuration.

**Parameters:**
- `cache` (CacheInterface): Cache instance to benchmark
- `config` (Optional[BenchmarkConfig]): Benchmark configuration

#### Core Benchmark Methods

##### run_single_benchmark()

```python
async def run_single_benchmark(
    self,
    operation: str,
    iterations: int,
    data_size: int = 1000
) -> BenchmarkResult
```

Runs a single benchmark for a specific operation.

**Parameters:**
- `operation` (str): Operation to benchmark ("get", "set", "delete")
- `iterations` (int): Number of iterations to perform
- `data_size` (int): Size of test data in bytes

**Returns:**
- `BenchmarkResult`: Detailed benchmark results

##### run_comprehensive_benchmark()

```python
async def run_comprehensive_benchmark(
    self,
    iterations_per_operation: int = 1000
) -> BenchmarkSuite
```

Runs a comprehensive benchmark across all operations.

**Parameters:**
- `iterations_per_operation` (int): Iterations per operation type

**Returns:**
- `BenchmarkSuite`: Complete benchmark suite results

### Class: BenchmarkResult

Data model for individual benchmark results.

```python
from app.infrastructure.cache.benchmarks.models import BenchmarkResult
```

#### Attributes

```python
@dataclass
class BenchmarkResult:
    operation: str
    iterations: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    operations_per_second: float
    cache_hit_rate: Optional[float]
    memory_usage_mb: float
    memory_peak_mb: float
    success_rate: float
    error_count: int
    timestamp: float
    metadata: Dict[str, Any]
```

### Class: BenchmarkSuite

Collection of benchmark results with comparison capabilities.

```python
from app.infrastructure.cache.benchmarks.models import BenchmarkSuite
```

#### Methods

##### add_result()

```python
def add_result(self, result: BenchmarkResult) -> None
```

Adds a benchmark result to the suite.

##### get_summary()

```python
def get_summary(self) -> Dict[str, Any]
```

Gets a summary of all benchmark results.

##### compare_with()

```python
def compare_with(self, other: 'BenchmarkSuite') -> ComparisonResult
```

Compares this suite with another benchmark suite.

### Class: PerformanceRegressionDetector

Automated regression detection and alerting.

```python
from app.infrastructure.cache.benchmarks.core import PerformanceRegressionDetector
```

#### Constructor

```python
def __init__(
    self,
    warning_threshold: float = 10.0,
    critical_threshold: float = 25.0
)
```

#### Methods

##### detect_timing_regressions()

```python
def detect_timing_regressions(
    self,
    old_result: BenchmarkResult,
    new_result: BenchmarkResult
) -> List[Dict[str, Any]]
```

Detects timing-related performance regressions.

##### detect_memory_regressions()

```python
def detect_memory_regressions(
    self,
    old_result: BenchmarkResult,
    new_result: BenchmarkResult
) -> List[Dict[str, Any]]
```

Detects memory-related performance regressions.

### Benchmark Configuration

#### Class: BenchmarkConfig

Configuration for benchmark execution.

```python
from app.infrastructure.cache.benchmarks.config import BenchmarkConfig
```

#### Class: ConfigPresets

Pre-configured benchmark settings.

```python
from app.infrastructure.cache.benchmarks.config import ConfigPresets
```

##### Static Methods

```python
@staticmethod
def quick() -> BenchmarkConfig
    """Quick benchmark preset for development."""

@staticmethod
def standard() -> BenchmarkConfig
    """Standard benchmark preset for CI/CD."""

@staticmethod
def comprehensive() -> BenchmarkConfig
    """Comprehensive benchmark preset for detailed analysis."""
```

---

## Exception Types

### Custom Exceptions

All cache infrastructure APIs use custom exceptions that extend the base exception hierarchy:

#### ConfigurationError

```python
from app.core.exceptions import ConfigurationError
```

Raised for configuration-related issues including invalid parameters, missing configuration, and configuration conflicts.

**Common Causes:**
- Invalid cache configuration parameters
- Missing required configuration values
- Configuration conflicts between parameters
- Invalid environment variable values

#### ValidationError

```python
from app.core.exceptions import ValidationError
```

Raised for input validation failures with specific field information.

**Common Causes:**
- Invalid parameter types or values
- Parameter values outside allowed ranges
- Missing required parameters
- Invalid parameter combinations

#### InfrastructureError

```python
from app.core.exceptions import InfrastructureError
```

Raised for infrastructure-related issues including Redis connection failures and service unavailability.

**Common Causes:**
- Redis connection failures
- Network connectivity issues
- Service unavailability
- Infrastructure resource exhaustion

### Exception Context Information

All custom exceptions include contextual information for debugging:

```python
try:
    config = CacheConfigBuilder().build()
except ValidationError as e:
    print(f"Error: {e}")
    print(f"Context: {e.context}")
```

### HTTP Status Code Mapping

Custom exceptions automatically map to appropriate HTTP status codes via `get_http_status_for_exception`:

- `ConfigurationError` → 500 Internal Server Error
- `ValidationError` → 422 Unprocessable Entity
- `InfrastructureError` → 503 Service Unavailable

---

## Usage Examples

### Basic Cache Usage

```python
from app.infrastructure.cache.factory import CacheFactory

# Create a cache for web applications
factory = CacheFactory()
cache = await factory.for_web_app(
    redis_url="redis://localhost:6379",
    default_ttl=3600
)

# Basic operations
await cache.set("user:123", {"name": "John", "email": "john@example.com"})
user_data = await cache.get("user:123")
await cache.delete("user:123")
```

### AI Cache Usage

```python
# Create an AI-optimized cache
cache = await factory.for_ai_app(
    operation_ttls={
        "summarize": 1800,  # 30 minutes
        "sentiment": 3600,  # 1 hour
    }
)

# Cache AI responses
await cache.cache_response(
    text="Long document to analyze...",
    operation="summarize",
    options={"max_length": 100},
    response={"summary": "Brief summary..."}
)
```

### Configuration Builder Usage

```python
from app.infrastructure.cache.config import CacheConfigBuilder

# Build a configuration with fluent interface
config = (CacheConfigBuilder()
    .for_environment("production")
    .with_redis("redis://prod:6379", use_tls=True)
    .with_compression(threshold=2000, level=6)
    .with_ai_features(
        text_hash_threshold=1500,
        operation_ttls={"summarize": 7200}
    )
    .build())

# Create cache from configuration
cache = await factory.create_cache_from_config(config.to_dict())
```

### Dependency Injection Usage

```python
from fastapi import Depends
from app.infrastructure.cache.dependencies import get_cache_service

@app.get("/api/data")
async def get_data(
    cache: CacheInterface = Depends(get_cache_service)
):
    data = await cache.get("api_data")
    if data is None:
        data = fetch_data_from_database()
        await cache.set("api_data", data, ttl=3600)
    return data
```

### Callback System Usage

```python
def track_cache_hits(key: str, value: Any):
    metrics.increment("cache.hits", tags={"key_prefix": key.split(":")[0]})

def track_cache_misses(key: str):
    metrics.increment("cache.misses", tags={"key_prefix": key.split(":")[0]})

# Register callbacks
cache.register_callback('get_success', track_cache_hits)
cache.register_callback('get_miss', track_cache_misses)
```

### Benchmark Usage

```python
from app.infrastructure.cache.benchmarks.core import CachePerformanceBenchmark
from app.infrastructure.cache.benchmarks.config import ConfigPresets

# Create and run benchmarks
benchmark = CachePerformanceBenchmark(cache, ConfigPresets.standard())
results = await benchmark.run_comprehensive_benchmark(iterations_per_operation=1000)

# Analyze results
summary = results.get_summary()
print(f"Average GET duration: {summary['get']['avg_duration_ms']:.2f}ms")
print(f"Operations per second: {summary['get']['operations_per_second']:.0f}")
```

### Environment Presets Usage

```python
from app.infrastructure.cache.config import EnvironmentPresets

# Use pre-configured environments
dev_config = EnvironmentPresets.development()
prod_config = EnvironmentPresets.production()
ai_config = EnvironmentPresets.ai_production()

# Create caches with presets
dev_cache = await factory.create_cache_from_config(dev_config.to_dict())
prod_cache = await factory.create_cache_from_config(prod_config.to_dict())
```

---

## Related Documentation

### Cache Documentation

- **[Cache Infrastructure Guide](./CACHE.md)** - Comprehensive cache infrastructure overview with architecture, features, and configuration patterns
- **[Cache Usage Guide](./usage-guide.md)** - Practical implementation examples with quickstart patterns and advanced optimization strategies
- **[Cache Migration Guide](../CACHE_MIGRATION.md)** - Migration and upgrade procedures for existing cache implementations
- **[Cache Testing Guide](../CACHE_TESTING.md)** - Testing patterns, mocking strategies, and test utilities for cache infrastructure
- **[Cache Configuration Guide](../CACHE_ENVIRONMENT_CONFIG.md)** - Environment variable configuration and preset management
- **[Cache Performance Benchmarking Guide](./benchmarking.md)** - Performance testing framework for API endpoints and comprehensive cache analysis

### Related Infrastructure Documentation

- **[Monitoring Guide](../MONITORING.md)** - Performance monitoring, metrics collection, and alerting strategies
- **[AI Services Guide](../AI.md)** - AI service integration patterns that leverage cache infrastructure
- **[Resilience Guide](../RESILIENCE.md)** - Resilience patterns including circuit breakers and fallback mechanisms
- **[Security Guide](../SECURITY.md)** - Security considerations for cache infrastructure and data protection

### Developer Resources

- **[Cache Developer Experience Guide](../CACHE_DEVELOPER_EXPERIENCE.md)** - Development tools, debugging utilities, and performance optimization
- **[Cache Presets Guide](../CACHE_PRESET_GUIDE.md)** - Pre-configured cache settings for different environments and use cases

---

## Getting Started

This API reference provides the complete interface specification for the cache infrastructure. All APIs are designed to be type-safe, well-documented, and provide comprehensive error handling with contextual information for debugging and monitoring.

**New to the cache infrastructure?** Start with the [Cache Infrastructure Guide](./CACHE.md) for an overview of the architecture and features, then explore the [Cache Usage Guide](./usage-guide.md) for practical implementation examples.