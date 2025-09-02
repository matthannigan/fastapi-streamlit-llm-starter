---
sidebar_label: test_factory
---

# Unit tests for CacheFactory explicit cache instantiation.

  file_path: `backend/tests/infrastructure/cache/factory/test_factory.py`

This test suite verifies the observable behaviors documented in the
CacheFactory public contract (factory.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/developer/TESTING.md.

Coverage Focus:
    - Infrastructure service (>90% test coverage requirement)
    - Behavior verification per docstring specifications
    - Factory method cache creation and configuration
    - Error handling and graceful fallback patterns

External Dependencies:
    - Settings configuration (mocked): Application configuration management
    - Redis client library (fakeredis): Redis connection simulation for cache creation
    - Standard library components (typing): For type annotations and dependency injection

## TestCacheFactoryInitialization

Test suite for CacheFactory initialization and basic functionality.

Scope:
    - Factory instance creation and default configuration
    - Basic initialization patterns per docstring specifications
    
Business Critical:
    Factory initialization determines cache behavior for all application types
    
Test Strategy:
    - Unit tests for factory initialization
    - Verification of default configuration behavior
    - Validation of factory instance readiness
    
External Dependencies:
    - None (testing pure factory initialization)

### test_factory_creates_with_default_configuration()

```python
def test_factory_creates_with_default_configuration(self):
```

Test that CacheFactory initializes with appropriate default configuration.

Verifies:
    Factory instance is created and ready for cache instantiation
    
Business Impact:
    Ensures developers can use factory with minimal configuration
    
Scenario:
    Given: No configuration parameters provided
    When: CacheFactory is instantiated
    Then: Factory instance is created with sensible defaults ready for use
    
Edge Cases Covered:
    - Default parameter handling
    - Factory readiness validation
    
Mocks Used:
    - None (pure initialization test)
    
Related Tests:
    - test_factory_maintains_configuration_state()

### test_factory_maintains_configuration_state()

```python
def test_factory_maintains_configuration_state(self):
```

Test that CacheFactory maintains internal configuration state correctly.

Verifies:
    Factory instance preserves configuration for subsequent cache creation
    
Business Impact:
    Ensures consistent cache behavior across multiple factory method calls
    
Scenario:
    Given: Factory instance is created
    When: Factory configuration is accessed
    Then: Configuration remains consistent and available for cache creation
    
Edge Cases Covered:
    - Configuration persistence across method calls
    - State isolation between factory instances
    
Mocks Used:
    - None (state verification test)
    
Related Tests:
    - test_factory_creates_with_default_configuration()

## TestWebApplicationCacheCreation

Test suite for web application optimized cache creation.

Scope:
    - for_web_app() method behavior and configuration
    - Web application specific cache optimizations
    - Parameter validation and default behavior
    - Redis connection handling and fallback scenarios
    
Business Critical:
    Web application caches serve session data, API responses, and page content
    
Test Strategy:
    - Unit tests for web app cache creation with various configurations
    - Integration tests with mocked Redis for connection validation
    - Fallback behavior testing when Redis is unavailable
    - Parameter validation and error handling
    
External Dependencies:
    - Settings configuration (mocked): Application and cache configuration
    - Redis client library (fakeredis): Redis connection simulation for integration tests

### test_for_web_app_creates_generic_redis_cache_with_default_settings()

```python
async def test_for_web_app_creates_generic_redis_cache_with_default_settings(self):
```

Test that for_web_app() creates a cache with web-optimized behavior.

Verifies:
    Web application cache is created with balanced performance behavior
    
Business Impact:
    Provides optimal caching performance for typical web application patterns
    
Scenario:
    Given: Factory instance with default configuration
    When: for_web_app() is called without parameters
    Then: Cache is created that supports standard cache operations
    And: Cache has appropriate fallback behavior when Redis unavailable
    
Edge Cases Covered:
    - Default parameter application
    - Web optimization presets
    - Redis URL default handling
    
Behavior Validated:
    - Cache provides standard get/set/delete interface
    - Cache handles connection failures gracefully
    - Cache supports TTL functionality
    
Related Tests:
    - test_for_web_app_applies_custom_parameters()
    - test_for_web_app_validates_parameter_combinations()

### test_for_web_app_applies_custom_parameters_correctly()

```python
async def test_for_web_app_applies_custom_parameters_correctly(self):
```

Test that for_web_app() properly applies custom configuration parameters.

Verifies:
    Custom parameters override defaults while maintaining web optimization behavior
    
Business Impact:
    Allows web applications to fine-tune cache performance for specific needs
    
Scenario:
    Given: Factory instance ready for cache creation
    When: for_web_app() is called with custom TTL and configuration
    Then: Cache is created with custom behavior that respects the parameters
    
Edge Cases Covered:
    - Custom TTL values affect cache expiration behavior
    - Custom Redis URL affects connection target
    - Cache maintains web application optimization patterns
    
Behavior Validated:
    - Cache respects custom TTL settings
    - Cache provides consistent interface regardless of parameters
    - Cache functionality works with custom configuration
    
Related Tests:
    - test_for_web_app_creates_generic_redis_cache_with_default_settings()
    - test_for_web_app_validates_parameter_combinations()

### test_for_web_app_validates_parameter_combinations()

```python
async def test_for_web_app_validates_parameter_combinations(self):
```

Test that for_web_app() validates parameter combinations and raises appropriate errors.

Verifies:
    Invalid parameter combinations are rejected with descriptive error messages
    
Business Impact:
    Prevents misconfigured caches that could degrade web application performance
    
Scenario:
    Given: Factory instance ready for cache creation
    When: for_web_app() is called with conflicting or invalid parameters
    Then: ValidationError is raised with specific configuration guidance
    
Edge Cases Covered:
    - Invalid TTL values (negative, zero, extremely large)
    - Invalid cache sizes (negative, zero, extremely large)
    - Invalid compression levels (outside 1-9 range)
    - Malformed Redis URL formats
    - Parameter combination conflicts
    
Mocks Used:
    - None (validation logic test)
    
Related Tests:
    - test_for_web_app_applies_custom_parameters_correctly()
    - test_for_web_app_handles_redis_connection_failure()

### test_for_web_app_handles_redis_connection_failure_with_memory_fallback()

```python
async def test_for_web_app_handles_redis_connection_failure_with_memory_fallback(self):
```

Test that for_web_app() falls back to InMemoryCache when Redis connection fails.

Verifies:
    Graceful degradation to memory cache when Redis is unavailable
    
Business Impact:
    Ensures web applications remain functional during Redis outages
    
Scenario:
    Given: Factory configured for web application cache
    When: for_web_app() is called with impossible Redis URL
    Then: Cache is returned that works (fallback behavior)
    
Edge Cases Covered:
    - Redis connection timeout
    - Redis server unavailable
    - Network connectivity issues
    
Behavior Validated:
    - Factory returns a working cache despite Redis failure
    - Cache supports all required operations
    - Fallback cache type is appropriate (InMemoryCache)
    
Related Tests:
    - test_for_web_app_raises_error_when_redis_required()

### test_for_web_app_raises_error_when_redis_required()

```python
async def test_for_web_app_raises_error_when_redis_required(self):
```

Test that for_web_app() raises InfrastructureError when fail_on_connection_error=True.

Verifies:
    Strict Redis requirement enforcement when explicitly requested
    
Business Impact:
    Allows critical web applications to fail fast rather than degrade silently
    
Scenario:
    Given: Factory configured with fail_on_connection_error=True
    When: for_web_app() is called but Redis connection fails
    Then: InfrastructureError is raised with connection failure details
    
Edge Cases Covered:
    - Explicit Redis requirement scenarios
    - Error message clarity and debugging information
    - Different connection failure types
    
Mocks Used:
    - Redis connection mocking to simulate failures (acceptable for error handling testing)
    
Related Tests:
    - test_for_web_app_handles_redis_connection_failure_with_memory_fallback()
    - test_for_web_app_validates_parameter_combinations()

### test_for_web_app_strict_redis_requirement_with_invalid_url()

```python
async def test_for_web_app_strict_redis_requirement_with_invalid_url(self):
```

Integration test: Verify error handling with real invalid Redis configuration.

Tests factory's error handling behavior using real Redis connection attempts
with invalid URLs to verify actual error handling without mocking.

Scenario:
    Given: Factory configured with fail_on_connection_error=True
    When: for_web_app() is called with completely invalid Redis URL
    Then: InfrastructureError is raised from actual connection failure

## TestAIApplicationCacheCreation

Test suite for AI application optimized cache creation.

Scope:
    - for_ai_app() method behavior and AI-specific configurations
    - AI application cache optimizations (compression, TTLs, text handling)
    - AIResponseCache creation with operation-specific settings
    - Enhanced monitoring and performance tracking integration
    
Business Critical:
    AI application caches store expensive-to-compute AI responses and embeddings
    
Test Strategy:
    - Unit tests for AI cache creation with AI-specific parameters
    - Integration tests with mocked AIResponseCache for feature validation
    - Performance optimization verification (compression, text hashing)
    - Operation-specific TTL and monitoring integration testing
    
External Dependencies:
    - Settings configuration (mocked): Application and cache configuration
    - Redis client library (fakeredis): Redis connection simulation for integration tests

### test_for_ai_app_creates_ai_response_cache_with_default_settings()

```python
async def test_for_ai_app_creates_ai_response_cache_with_default_settings(self):
```

Test that for_ai_app() creates a cache with AI-optimized behavior.

Verifies:
    AI application cache is created with enhanced AI-specific functionality
    
Business Impact:
    Provides optimal caching performance for AI workloads with large responses
    
Scenario:
    Given: Factory instance with default configuration
    When: for_ai_app() is called without parameters
    Then: Cache is created that supports AI-specific operations
    And: Cache provides AI key generation and text handling capabilities
    
Edge Cases Covered:
    - AI-specific default parameters
    - Enhanced compression settings
    - Text hashing threshold defaults
    - AI operation monitoring defaults
    
Behavior Validated:
    - Cache provides standard cache interface
    - Cache includes AI-specific features (build_key method)
    - Cache handles AI operations appropriately
    
Related Tests:
    - test_for_ai_app_applies_operation_specific_ttls()
    - test_for_ai_app_configures_text_hashing_threshold()

### test_for_ai_app_applies_operation_specific_ttls()

```python
async def test_for_ai_app_applies_operation_specific_ttls(self):
```

Test that for_ai_app() properly accepts operation-specific TTL parameters.

Verifies:
    AI cache factory accepts custom operation TTL configurations
    
Business Impact:
    Balances cache freshness with AI processing cost savings across operations
    
Scenario:
    Given: Factory configured with operation-specific TTL mappings
    When: for_ai_app() is called with operation_ttls parameter
    Then: Cache is created that accepts the operation TTL configuration
    And: Cache provides consistent interface regardless of TTL settings
    
Edge Cases Covered:
    - Multiple operation TTL configurations
    - TTL parameter acceptance and validation
    - Cache creation with custom configuration
    
Behavior Validated:
    - Factory accepts operation_ttls parameter without error
    - Cache creation succeeds with custom TTL configuration
    - Cache provides standard interface
    
Related Tests:
    - test_for_ai_app_creates_ai_response_cache_with_default_settings()
    - test_for_ai_app_validates_operation_ttl_parameters()

### test_for_ai_app_configures_text_hashing_threshold()

```python
async def test_for_ai_app_configures_text_hashing_threshold(self):
```

Test that for_ai_app() properly configures text hashing threshold for key generation.

Verifies:
    Large text inputs are handled efficiently through intelligent key generation
    
Business Impact:
    Prevents cache key length issues while maintaining cache efficiency for AI text processing
    
Scenario:
    Given: Factory configured for AI application cache
    When: for_ai_app() is called with text_hash_threshold parameter
    Then: AIResponseCache is created with specified threshold for text hashing behavior
    
Edge Cases Covered:
    - Small threshold values for aggressive hashing
    - Large threshold values for direct text inclusion
    - Threshold validation and boundary conditions
    - Integration with CacheKeyGenerator
    
Mocks Used:
    - None
    
Related Tests:
    - test_for_ai_app_applies_operation_specific_ttls()
    - test_for_ai_app_integrates_with_performance_monitoring()

### test_for_ai_app_integrates_with_performance_monitoring()

```python
async def test_for_ai_app_integrates_with_performance_monitoring(self, real_performance_monitor):
```

Test that for_ai_app() properly integrates performance monitoring for AI metrics.

Verifies:
    AI-specific performance metrics are collected for monitoring and optimization
    
Business Impact:
    Enables monitoring of AI cache performance for cost optimization and SLA compliance
    
Scenario:
    Given: Factory configured with performance monitoring enabled
    When: for_ai_app() is called with monitoring integration
    Then: Cache is created with performance monitor configured for AI metrics
    
Edge Cases Covered:
    - Performance monitor integration
    - AI-specific metric collection
    - Monitoring configuration validation
    - Optional monitoring behavior
    
Mocks Used:
    - None (uses real performance monitor)
    
Related Tests:
    - test_for_ai_app_configures_text_hashing_threshold()
    - test_for_ai_app_handles_redis_connection_failure_with_fallback()

### test_for_ai_app_validates_operation_ttl_parameters()

```python
async def test_for_ai_app_validates_operation_ttl_parameters(self):
```

Test that for_ai_app() validates operation TTL parameters and raises appropriate errors.

Verifies:
    Invalid operation TTL configurations are rejected with descriptive error messages
    
Business Impact:
    Prevents misconfigured AI caches that could impact processing cost efficiency
    
Scenario:
    Given: Factory instance ready for AI cache creation
    When: for_ai_app() is called with invalid operation TTL parameters
    Then: ValidationError is raised with specific TTL configuration guidance
    
Edge Cases Covered:
    - Invalid TTL values (negative, zero, extremely large)
    - Unknown operation names in TTL configuration
    - TTL parameter type validation
    - Operation TTL consistency validation
    
Mocks Used:
    - None (validation logic test)
    
Related Tests:
    - test_for_ai_app_applies_operation_specific_ttls()
    - test_for_ai_app_handles_redis_connection_failure_with_fallback()

### test_for_ai_app_handles_redis_connection_failure_with_fallback()

```python
async def test_for_ai_app_handles_redis_connection_failure_with_fallback(self):
```

Test that for_ai_app() falls back to InMemoryCache when Redis connection fails.

Verifies:
    Graceful degradation to memory cache preserving AI application functionality
    
Business Impact:
    Ensures AI applications continue functioning during Redis outages
    
Scenario:
    Given: Factory configured for AI application cache
    When: for_ai_app() is called but Redis connection fails
    Then: InMemoryCache is returned with AI configuration warnings logged
    
Edge Cases Covered:
    - Redis connection failures during AI cache creation
    - Fallback behavior with AI-specific configuration loss
    - Warning message clarity for AI degradation
    - Memory cache limitations for AI workloads
    
Mocks Used:
    - Redis connection mocking to simulate failures
    
Related Tests:
    - test_for_ai_app_integrates_with_performance_monitoring()
    - test_for_ai_app_raises_error_when_redis_required_for_ai()

### test_for_ai_app_raises_error_when_redis_required_for_ai()

```python
async def test_for_ai_app_raises_error_when_redis_required_for_ai(self):
```

Test that for_ai_app() raises InfrastructureError when fail_on_connection_error=True.

Verifies:
    Strict Redis requirement enforcement for critical AI applications
    
Business Impact:
    Allows critical AI applications to fail fast rather than lose AI-specific features
    
Scenario:
    Given: Factory configured with fail_on_connection_error=True for AI cache
    When: for_ai_app() is called but Redis connection fails
    Then: InfrastructureError is raised with AI-specific connection failure details
    
Edge Cases Covered:
    - AI application critical dependency on Redis
    - Error message specificity for AI cache failures
    - Different AI connection failure scenarios
    
Mocks Used:
    - Redis connection mocking to simulate failures (acceptable for factory error handling testing)
    
Related Tests:
    - test_for_ai_app_handles_redis_connection_failure_with_fallback()
    - test_for_ai_app_validates_operation_ttl_parameters()

### test_for_ai_app_strict_redis_requirement_with_invalid_url()

```python
async def test_for_ai_app_strict_redis_requirement_with_invalid_url(self):
```

Integration test: Verify AI cache error handling with real invalid Redis configuration.

Tests factory's AI error handling behavior using real Redis connection attempts
with invalid URLs to verify actual error handling without mocking.

Scenario:
    Given: Factory configured with fail_on_connection_error=True
    When: for_ai_app() is called with completely invalid Redis URL
    Then: InfrastructureError is raised from actual connection failure

## TestTestingCacheCreation

Test suite for testing environment optimized cache creation.

Scope:
    - for_testing() method behavior and testing-specific configurations
    - Test database isolation and short TTL configurations
    - Memory cache option for isolated testing scenarios
    - Fast operation settings for minimal test overhead
    
Business Critical:
    Testing caches enable reliable automated testing without interference
    
Test Strategy:
    - Unit tests for testing cache creation with test-specific parameters
    - Verification of test isolation features (database selection, TTLs)
    - Memory cache testing option validation
    - Performance optimization for test execution speed
    
External Dependencies:
    - Settings configuration (mocked): Application and cache configuration
    - Redis client library (fakeredis): Redis connection simulation for integration tests

### test_for_testing_creates_cache_with_test_optimizations()

```python
async def test_for_testing_creates_cache_with_test_optimizations(self):
```

Test that for_testing() creates cache with testing-optimized behavior.

Verifies:
    Testing cache is created with behavior suitable for test environments
    
Business Impact:
    Ensures test suites run efficiently without cache interference between tests
    
Scenario:
    Given: Factory instance configured for testing environment
    When: for_testing() is called with default parameters
    Then: Cache is created with appropriate testing behavior
    And: Cache provides standard interface with testing-appropriate performance
    
Edge Cases Covered:
    - Default testing configuration application
    - Test database isolation behavior
    - Fast operation settings for test efficiency
    - Memory usage appropriate for testing
    
Behavior Validated:
    - Cache provides standard cache interface
    - Cache works appropriately for testing scenarios
    - Cache handles fallback gracefully when Redis unavailable
    
Related Tests:
    - test_for_testing_uses_test_database_for_isolation()
    - test_for_testing_applies_short_ttls_for_quick_expiration()

### test_for_testing_uses_test_database_for_isolation()

```python
async def test_for_testing_uses_test_database_for_isolation(self):
```

Test that for_testing() uses Redis test database for test isolation.

Verifies:
    Testing cache uses separate Redis database to avoid production data conflicts
    
Business Impact:
    Prevents test data from interfering with development or production caches
    
Scenario:
    Given: Factory configured for testing with default settings
    When: for_testing() is called without custom Redis URL
    Then: Cache is created targeting Redis database 15 for test isolation
    
Edge Cases Covered:
    - Default test database selection (DB 15)
    - Custom test database configuration
    - Test database URL parsing and validation
    - Database isolation verification
    
Mocks Used:
    - none
    
Related Tests:
    - test_for_testing_creates_cache_with_test_optimizations()
    - test_for_testing_supports_custom_test_database()

### test_for_testing_applies_short_ttls_for_quick_expiration()

```python
async def test_for_testing_applies_short_ttls_for_quick_expiration(self):
```

Test that for_testing() applies short TTL values for quick test data expiration.

Verifies:
    Test data expires quickly to prevent interference between test runs
    
Business Impact:
    Ensures test isolation and prevents stale test data affecting subsequent tests
    
Scenario:
    Given: Factory configured for testing environment
    When: for_testing() is called with default or custom short TTL
    Then: Cache is created with TTL appropriate for test execution timeframes
    
Edge Cases Covered:
    - Default 1-minute TTL for testing
    - Custom short TTL values (seconds range)
    - TTL validation for testing scenarios
    - Balance between isolation and test performance
    
Mocks Used:
    - None
    
Related Tests:
    - test_for_testing_uses_test_database_for_isolation()
    - test_for_testing_creates_memory_cache_when_requested()

### test_for_testing_creates_memory_cache_when_requested()

```python
async def test_for_testing_creates_memory_cache_when_requested(self):
```

Test that for_testing() creates InMemoryCache when use_memory_cache=True.

Verifies:
    Pure memory cache is available for completely isolated testing scenarios
    
Business Impact:
    Enables testing without any Redis dependency for maximum test isolation
    
Scenario:
    Given: Factory configured for testing with memory cache option
    When: for_testing() is called with use_memory_cache=True
    Then: InMemoryCache is created for completely isolated testing
    
Edge Cases Covered:
    - Memory cache selection over Redis for testing
    - Memory cache configuration for testing scenarios
    - Isolation benefits of pure memory caching
    - Memory cache limitations awareness
    
Mocks Used:
    - None
    
Related Tests:
    - test_for_testing_applies_short_ttls_for_quick_expiration()
    - test_for_testing_supports_custom_test_database()

### test_for_testing_supports_custom_test_database()

```python
async def test_for_testing_supports_custom_test_database(self):
```

Test that for_testing() supports custom test database configuration.

Verifies:
    Custom Redis test databases can be specified for advanced testing scenarios
    
Business Impact:
    Allows parallel test execution with different database isolation levels
    
Scenario:
    Given: Factory configured for testing with custom database
    When: for_testing() is called with custom Redis URL specifying test database
    Then: Cache is created targeting specified test database for isolation
    
Edge Cases Covered:
    - Custom test database selection (non-default)
    - Redis URL parsing with database specification
    - Database number validation and boundaries
    - Test isolation with multiple databases
    
Mocks Used:
    - None
    
Related Tests:
    - test_for_testing_uses_test_database_for_isolation()
    - test_for_testing_validates_testing_parameters()

### test_for_testing_validates_testing_parameters()

```python
async def test_for_testing_validates_testing_parameters(self):
```

Test that for_testing() validates testing parameters and raises appropriate errors.

Verifies:
    Invalid testing configurations are rejected with helpful error messages
    
Business Impact:
    Prevents misconfigured testing caches that could cause test failures
    
Scenario:
    Given: Factory instance ready for testing cache creation
    When: for_testing() is called with invalid testing parameters
    Then: ValidationError is raised with specific testing configuration guidance
    
Edge Cases Covered:
    - Invalid TTL values for testing scenarios
    - Invalid test database specifications
    - Parameter combination validation for testing
    - Testing-specific parameter constraints
    
Mocks Used:
    - None (validation logic test)
    
Related Tests:
    - test_for_testing_supports_custom_test_database()
    - test_for_testing_handles_redis_unavailable_in_tests()

### test_for_testing_handles_redis_unavailable_in_tests()

```python
async def test_for_testing_handles_redis_unavailable_in_tests(self):
```

Test that for_testing() gracefully handles Redis unavailability during testing.

Verifies:
    Testing continues with memory fallback when Redis is unavailable
    
Business Impact:
    Ensures test suites can run in environments without Redis infrastructure
    
Scenario:
    Given: Factory configured for testing but Redis is unavailable
    When: for_testing() is called but Redis connection fails
    Then: InMemoryCache fallback is used with appropriate testing configuration
    
Edge Cases Covered:
    - Redis unavailability during testing
    - Graceful fallback behavior for test environments
    - Memory cache configuration preservation
    - Testing isolation with fallback cache
    
Mocks Used:
    - Redis connection mocking to simulate unavailability
    
Related Tests:
    - test_for_testing_creates_memory_cache_when_requested()
    - test_for_testing_validates_testing_parameters()

## TestConfigurationBasedCacheCreation

Test suite for configuration-driven cache creation.

Scope:
    - create_cache_from_config() method behavior and flexible configuration
    - Configuration dictionary parsing and validation
    - Automatic cache type detection (Generic vs AI)
    - Parameter mapping from configuration to cache instances
    
Business Critical:
    Configuration-based creation enables dynamic cache setup from external config files
    
Test Strategy:
    - Unit tests for configuration parsing and cache type detection
    - Parameter mapping validation from config dictionaries
    - Cache type selection logic testing (Generic vs AI)
    - Configuration validation and error handling
    
External Dependencies:
    - None

### test_create_cache_from_config_creates_generic_cache_for_basic_config()

```python
async def test_create_cache_from_config_creates_generic_cache_for_basic_config(self):
```

Test that create_cache_from_config() creates GenericRedisCache for basic configuration.

Verifies:
    Basic cache configuration results in GenericRedisCache creation
    
Business Impact:
    Enables straightforward cache configuration without AI-specific complexity
    
Scenario:
    Given: Factory with basic cache configuration dictionary
    When: create_cache_from_config() is called without AI-specific parameters
    Then: GenericRedisCache is created with configuration parameters applied
    
Edge Cases Covered:
    - Minimal required configuration (redis_url only)
    - Basic configuration with common parameters
    - Configuration parameter mapping validation
    - Generic cache type selection logic
    
Mocks Used:
    - None
    
Related Tests:
    - test_create_cache_from_config_creates_ai_cache_when_ai_params_present()
    - test_create_cache_from_config_validates_required_parameters()

### test_create_cache_from_config_creates_ai_cache_when_ai_params_present()

```python
async def test_create_cache_from_config_creates_ai_cache_when_ai_params_present(self):
```

Test that create_cache_from_config() creates AIResponseCache when AI parameters are present.

Verifies:
    Configuration with AI-specific parameters triggers AIResponseCache creation
    
Business Impact:
    Enables automatic AI cache selection based on configuration content
    
Scenario:
    Given: Factory with configuration containing AI-specific parameters
    When: create_cache_from_config() is called with text_hash_threshold or operation_ttls
    Then: AIResponseCache is created with AI-specific configuration applied
    
Edge Cases Covered:
    - AI parameter detection logic (text_hash_threshold, operation_ttls)
    - AI configuration parameter mapping
    - AI cache type selection triggers
    - Mixed parameter configuration handling
    
Mocks Used:
    - None
    
Related Tests:
    - test_create_cache_from_config_creates_generic_cache_for_basic_config()
    - test_create_cache_from_config_maps_parameters_correctly()

### test_create_cache_from_config_maps_parameters_correctly()

```python
async def test_create_cache_from_config_maps_parameters_correctly(self):
```

Test that create_cache_from_config() correctly maps configuration parameters to cache instances.

Verifies:
    Configuration dictionary parameters are properly mapped to cache creation calls
    
Business Impact:
    Ensures configuration-driven cache setup preserves all specified settings
    
Scenario:
    Given: Factory with comprehensive configuration dictionary
    When: create_cache_from_config() is called with various parameters
    Then: Appropriate cache type is created with all configuration parameters mapped
    
Edge Cases Covered:
    - Complete parameter mapping for generic caches
    - Complete parameter mapping for AI caches
    - Parameter type conversion and validation
    - Optional parameter handling and defaults
    
Mocks Used:
    - None
    
Related Tests:
    - test_create_cache_from_config_creates_ai_cache_when_ai_params_present()
    - test_create_cache_from_config_validates_parameter_types()

### test_create_cache_from_config_validates_required_parameters()

```python
async def test_create_cache_from_config_validates_required_parameters(self):
```

Test that create_cache_from_config() validates required configuration parameters.

Verifies:
    Missing required parameters are detected and appropriate errors are raised
    
Business Impact:
    Prevents invalid cache configurations that could cause runtime failures
    
Scenario:
    Given: Factory ready for configuration-based cache creation
    When: create_cache_from_config() is called with incomplete configuration
    Then: ValidationError is raised identifying missing required parameters
    
Edge Cases Covered:
    - Missing redis_url parameter
    - Empty configuration dictionary
    - Partial configuration with critical parameters missing
    - Required vs optional parameter distinction
    
Mocks Used:
    - None (validation logic test)
    
Related Tests:
    - test_create_cache_from_config_validates_parameter_types()
    - test_create_cache_from_config_handles_configuration_conflicts()

### test_create_cache_from_config_validates_parameter_types()

```python
async def test_create_cache_from_config_validates_parameter_types(self):
```

Test that create_cache_from_config() validates configuration parameter types.

Verifies:
    Configuration parameters with incorrect types are rejected with helpful errors
    
Business Impact:
    Prevents configuration errors that could cause unexpected cache behavior
    
Scenario:
    Given: Factory with configuration containing incorrect parameter types
    When: create_cache_from_config() is called with type-mismatched parameters
    Then: ValidationError is raised with specific type requirement guidance
    
Edge Cases Covered:
    - String parameters provided as integers
    - Integer parameters provided as strings
    - Boolean parameters provided as strings or integers
    - Dictionary parameters provided as strings
    - Type conversion possibilities vs strict validation
    
Mocks Used:
    - None (validation logic test)
    
Related Tests:
    - test_create_cache_from_config_validates_required_parameters()
    - test_create_cache_from_config_handles_configuration_conflicts()

### test_create_cache_from_config_handles_configuration_conflicts()

```python
async def test_create_cache_from_config_handles_configuration_conflicts(self):
```

Test that create_cache_from_config() detects and handles configuration conflicts.

Verifies:
    Conflicting configuration parameters are identified with resolution guidance
    
Business Impact:
    Prevents ambiguous cache configurations that could lead to unexpected behavior
    
Scenario:
    Given: Factory with configuration containing conflicting parameters
    When: create_cache_from_config() is called with parameter conflicts
    Then: ConfigurationError is raised with conflict resolution guidance
    
Edge Cases Covered:
    - Conflicting cache type indicators
    - Incompatible parameter combinations
    - Resource constraint conflicts (memory vs performance)
    - Configuration precedence rules
    
Mocks Used:
    - None (validation logic test)
    
Related Tests:
    - test_create_cache_from_config_validates_parameter_types()
    - test_create_cache_from_config_handles_redis_connection_failure()

### test_create_cache_from_config_handles_redis_connection_failure()

```python
async def test_create_cache_from_config_handles_redis_connection_failure(self):
```

Test that create_cache_from_config() handles Redis connection failures gracefully.

Verifies:
    Configuration-based cache creation falls back appropriately when Redis unavailable
    
Business Impact:
    Ensures configuration-driven applications can start with degraded cache functionality
    
Scenario:
    Given: Factory with valid configuration but Redis connection fails
    When: create_cache_from_config() is called but Redis is unavailable
    Then: InMemoryCache fallback is created with configuration warnings
    
Edge Cases Covered:
    - Redis connection failure during configuration-based creation
    - Fallback behavior with configuration parameter preservation
    - Warning messages for configuration-driven fallback
    - Configuration-specific error handling
    
Mocks Used:
    - Redis connection mocking to simulate failures
    
Related Tests:
    - test_create_cache_from_config_handles_configuration_conflicts()
    - test_create_cache_from_config_enforces_strict_redis_requirement()

### test_create_cache_from_config_enforces_strict_redis_requirement()

```python
async def test_create_cache_from_config_enforces_strict_redis_requirement(self):
```

Test that create_cache_from_config() enforces strict Redis requirements when specified.

Verifies:
    Configuration-based creation can require Redis connectivity without fallback
    
Business Impact:
    Allows configuration-driven applications to fail fast for critical cache dependencies
    
Scenario:
    Given: Factory with configuration and fail_on_connection_error=True
    When: create_cache_from_config() is called but Redis connection fails
    Then: InfrastructureError is raised with configuration-specific failure details
    
Edge Cases Covered:
    - Strict Redis requirements in configuration context
    - Configuration-specific error messages
    - Different failure scenarios with configuration context
    - Error message specificity for configuration debugging
    
Mocks Used:
    - Redis connection mocking to simulate failures
    
Related Tests:
    - test_create_cache_from_config_handles_redis_connection_failure()
    - test_create_cache_from_config_handles_configuration_conflicts()
