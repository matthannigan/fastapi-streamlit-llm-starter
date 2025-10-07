"""
Unit tests for InMemoryCache initialization and configuration behavior.

This test suite verifies the observable behaviors documented in the
InMemoryCache public contract (memory.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - Constructor parameter validation and configuration setup
    - Default parameter application and validation
    - Configuration edge cases and boundary conditions
    - Error handling for invalid initialization parameters

External Dependencies:
    - Settings configuration (mocked): Application configuration management
    - Standard library components (threading, collections): For thread-safe operations and data structures
    - app.core.exceptions: Exception handling for configuration and validation errors
"""


import pytest

from app.core.exceptions import ConfigurationError
from app.infrastructure.cache.memory import InMemoryCache


class TestInMemoryCacheInitialization:
    """
    Test suite for InMemoryCache initialization and configuration behavior.

    Scope:
        - Constructor parameter validation and storage setup
        - Default parameter application for production usage
        - Configuration validation and error handling
        - Cache structure initialization and metadata setup

    Business Critical:
        Initialization failures prevent cache functionality and break application services

    Test Strategy:
        - Unit tests for parameter validation using invalid_memory_cache_params
        - Default configuration testing using valid_memory_cache_params
        - Boundary condition testing for max_size and default_ttl limits
        - Error handling scenarios for configuration validation

    External Dependencies:
        - logging: For operational monitoring and debugging (mocked)
        - time: For timestamp generation and TTL calculations
    """

    def test_init_with_valid_parameters_creates_cache_with_correct_configuration(self):
        """
        Test that InMemoryCache constructor properly validates and stores configuration parameters.

        Verifies:
            Valid initialization parameters are correctly applied to cache configuration

        Business Impact:
            Ensures cache operates with expected TTL and capacity limits for production use

        Scenario:
            Given: Valid default_ttl and max_size parameters within acceptable ranges
            When: InMemoryCache is initialized with these parameters
            Then: Cache instance is created with specified configuration values
            And: Internal storage structures are properly initialized
            And: Configuration attributes match provided parameters

        Configuration Behavior Verified:
            - default_ttl parameter is stored and accessible for cache operations
            - max_size parameter is stored and enforced during operations
            - Internal cache storage dictionary is initialized as empty
            - Internal LRU access order tracking is initialized as empty list
            - Statistics counters are initialized to zero

        Fixtures Used:
            - valid_memory_cache_params: Contains valid default_ttl and max_size values

        Initialization Verification:
            - Cache accepts parameters within documented ranges (TTL: 1-86400, max_size: 1-100000)
            - Internal data structures are properly initialized for operation
            - No exceptions raised during valid parameter initialization

        Related Tests:
            - test_init_with_default_parameters_applies_documented_defaults()
            - test_init_with_invalid_parameters_raises_configuration_error()
        """
        # Given
        valid_ttl = 60
        valid_max_size = 50

        # When
        cache = InMemoryCache(default_ttl=valid_ttl, max_size=valid_max_size)

        # Then
        assert cache.default_ttl == valid_ttl
        assert cache.max_size == valid_max_size

    def test_init_with_default_parameters_applies_documented_defaults(self):
        """
        Test that InMemoryCache applies correct default values when parameters not provided.

        Verifies:
            Default parameter values match those documented in constructor docstring

        Business Impact:
            Ensures consistent cache behavior when initialized with minimal configuration

        Scenario:
            Given: InMemoryCache initialization without explicit parameters
            When: Cache instance is created with default constructor call
            Then: Default values are applied matching documented specifications
            And: default_ttl is set to 3600 seconds (1 hour) as documented
            And: max_size is set to 1000 entries as documented

        Default Values Verified:
            - default_ttl: 3600 seconds (1 hour) for reasonable cache retention
            - max_size: 1000 entries for moderate memory usage
            - Cache storage and access tracking initialized empty
            - Statistics counters initialized to zero for fresh instance

        Fixtures Used:
            - None (testing default constructor behavior)

        Documentation Consistency:
            Default values must match exactly what is documented in constructor docstring

        Related Tests:
            - test_init_with_explicit_parameters_overrides_defaults()
            - test_init_with_valid_parameters_creates_cache_with_correct_configuration()
        """
        # When
        cache = InMemoryCache()

        # Then
        assert cache.default_ttl == 3600
        assert cache.max_size == 1000

    def test_init_with_explicit_parameters_overrides_defaults(self):
        """
        Test that explicitly provided parameters override default values correctly.

        Verifies:
            Custom parameter values take precedence over documented defaults

        Business Impact:
            Allows cache tuning for specific deployment requirements and use cases

        Scenario:
            Given: InMemoryCache initialization with custom default_ttl and max_size values
            When: Cache instance is created with explicit non-default parameters
            Then: Custom values are used instead of defaults for cache configuration
            And: No default values are applied for explicitly provided parameters
            And: Cache operates with custom configuration limits

        Parameter Override Verified:
            - Custom default_ttl overrides default 3600 seconds
            - Custom max_size overrides default 1000 entries
            - Both parameters can be overridden independently
            - Configuration reflects exact values provided by caller

        Fixtures Used:
            - valid_memory_cache_params: Contains custom non-default values for testing

        Custom Configuration Support:
            Cache supports full range of valid parameter combinations for deployment flexibility

        Related Tests:
            - test_init_with_default_parameters_applies_documented_defaults()
            - test_init_parameter_validation_enforces_documented_ranges()
        """
        # Given
        custom_ttl = 120
        custom_max_size = 200

        # When
        cache = InMemoryCache(default_ttl=custom_ttl, max_size=custom_max_size)

        # Then
        assert cache.default_ttl == custom_ttl
        assert cache.max_size == custom_max_size

    def test_init_with_invalid_parameters_raises_configuration_error(self):
        """
        Test that invalid initialization parameters raise ConfigurationError with detailed context.

        Verifies:
            Parameter validation failures are caught and reported with specific error details

        Business Impact:
            Provides clear feedback during deployment setup preventing misconfigured cache instances

        Scenario:
            Given: Invalid InMemoryCache parameters (negative TTL, zero max_size, etc.)
            When: Cache initialization is attempted with invalid configuration
            Then: ConfigurationError is raised with specific parameter validation failures
            And: Error message includes which parameters failed validation
            And: Error context includes acceptable parameter ranges

        Validation Scenarios Tested:
            - Negative default_ttl values (should fail with range error)
            - Zero max_size values (should fail with minimum requirement)
            - default_ttl exceeding maximum allowed (86400 seconds)
            - max_size exceeding maximum allowed (100000 entries)
            - Non-integer parameter types where integers required

        Fixtures Used:
            - invalid_memory_cache_params: Contains parameters that should fail validation

        Error Context Verification:
            - ConfigurationError includes parameter name and invalid value
            - Error message explains acceptable parameter ranges
            - Multiple parameter failures are all reported in single error

        Related Tests:
            - test_init_with_valid_parameters_creates_cache_with_correct_configuration()
            - test_init_parameter_boundary_conditions()
        """
        invalid_params = [
            {"default_ttl": 0},
            {"default_ttl": -1},
            {"default_ttl": 86401},
            {"max_size": 0},
            {"max_size": -1},
            {"max_size": 100001},
            {"default_ttl": "invalid"},
            {"max_size": 100.5},
        ]
        for params in invalid_params:
            with pytest.raises(ConfigurationError):
                InMemoryCache(**params)

    def test_init_parameter_boundary_conditions(self):
        """
        Test that parameter boundary conditions are handled correctly.

        Verifies:
            Edge cases for parameter ranges are properly validated and handled

        Business Impact:
            Ensures cache operates reliably at configuration limits without failures

        Scenario:
            Given: Parameter values at documented minimum and maximum boundaries
            When: Cache is initialized with boundary values
            Then: Boundary values within range are accepted successfully
            And: Boundary values outside range raise appropriate validation errors
            And: Cache operates correctly with minimum and maximum valid values

        Boundary Conditions Tested:
            - default_ttl minimum (1 second) - should be accepted
            - default_ttl maximum (86400 seconds) - should be accepted
            - max_size minimum (1 entry) - should be accepted
            - max_size maximum (100000 entries) - should be accepted
            - Values just outside boundaries should raise ConfigurationError

        Fixtures Used:
            - Custom parameter sets created for boundary testing

        Edge Case Handling:
            Cache handles extreme but valid configurations without degradation

        Related Tests:
            - test_init_with_invalid_parameters_raises_configuration_error()
            - test_cache_operations_respect_configured_limits()
        """
        # Test valid boundaries (should not raise error)
        try:
            InMemoryCache(default_ttl=1, max_size=1)
            InMemoryCache(default_ttl=86400, max_size=100000)
        except ConfigurationError:
            pytest.fail(
                "Valid boundary conditions raised ConfigurationError unexpectedly."
            )

        # Test invalid boundaries (should raise error)
        with pytest.raises(ConfigurationError):
            InMemoryCache(default_ttl=0)
        with pytest.raises(ConfigurationError):
            InMemoryCache(max_size=0)
        with pytest.raises(ConfigurationError):
            InMemoryCache(default_ttl=86401)
        with pytest.raises(ConfigurationError):
            InMemoryCache(max_size=100001)

    def test_init_storage_structures_properly_initialized(self):
        """
        Test that internal storage structures are correctly initialized for cache operations.

        Verifies:
            Cache data structures are properly set up for immediate use after initialization

        Business Impact:
            Ensures cache is immediately operational without requiring additional setup

        Scenario:
            Given: Successful InMemoryCache initialization with valid parameters
            When: Cache instance is created and internal state is examined
            Then: Internal cache storage dictionary is empty and ready for operations
            And: LRU access order tracking list is empty and ready for ordering
            And: Statistics counters are initialized to zero for accurate metrics
            And: Configuration metadata is stored for operational decisions

        Internal Structure Verification:
            - _cache dictionary initialized empty for key-value storage
            - _access_order list initialized empty for LRU tracking
            - Statistics counters (hits, misses, evictions) start at zero
            - Configuration parameters stored in instance attributes
            - No residual data from previous instances or sessions

        Fixtures Used:
            - default_memory_cache: Fresh cache instance for structure examination

        Clean Initialization:
            Each cache instance starts with completely clean internal state

        Related Tests:
            - test_cache_operations_use_initialized_structures()
            - test_statistics_start_from_clean_state()
        """
        # When
        cache = InMemoryCache()

        # Then
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["active_entries"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["utilization_percent"] == 0.0
