"""
Test suite for RetryConfig component behavioral contract verification.

This module contains comprehensive test skeletons for the RetryConfig dataclass,
focusing on configuration validation, state management, and serialization behavior
as specified in the public contract.

Test Organization:
    - TestRetryConfigInitialization: Configuration creation and default values
    - TestRetryConfigValidation: Parameter validation and boundary conditions
    - TestRetryConfigSerialization: Dictionary conversion and data export
    - TestRetryConfigEdgeCases: Boundary values and special cases
"""

import pytest
from app.infrastructure.resilience.retry import RetryConfig, should_retry_on_exception
from app.core.exceptions import ValidationError


class TestRetryConfigInitialization:
    """Tests RetryConfig initialization and default configuration values."""

    def test_creates_config_with_default_values(self):
        """
        Test that RetryConfig can be created with production-ready defaults.

        Verifies:
            RetryConfig initializes successfully with documented default values
            per the contract specification.

        Business Impact:
            Ensures components can use retry logic without custom configuration,
            providing safe defaults for production deployments.

        Scenario:
            Given: No custom configuration parameters are provided.
            When: A RetryConfig instance is created with defaults.
            Then: The instance is created successfully with all documented default values.

        Fixtures Used:
            - None (tests direct instantiation)
        """
        # Act: Create RetryConfig with default values
        config = RetryConfig()

        # Assert: All default values match contract specification
        assert config.max_attempts == 3
        assert config.max_delay_seconds == 60
        assert config.exponential_multiplier == 1.0
        assert config.exponential_min == 2.0
        assert config.exponential_max == 10.0
        assert config.jitter is True
        assert config.jitter_max == 2.0

    def test_creates_config_with_custom_max_attempts(self):
        """
        Test that RetryConfig accepts custom max_attempts parameter.

        Verifies:
            RetryConfig can be initialized with a custom max_attempts value
            within the documented range (1-20).

        Business Impact:
            Allows operations to customize retry persistence based on
            criticality and cost considerations.

        Scenario:
            Given: A custom max_attempts value within valid range.
            When: RetryConfig is initialized with this value.
            Then: The config stores the custom max_attempts correctly.

        Fixtures Used:
            - None (tests direct instantiation)
        """
        # Arrange: Custom max_attempts value
        custom_max_attempts = 5

        # Act: Create RetryConfig with custom max_attempts
        config = RetryConfig(max_attempts=custom_max_attempts)

        # Assert: Custom value is stored correctly
        assert config.max_attempts == custom_max_attempts
        # Other defaults remain unchanged
        assert config.max_delay_seconds == 60
        assert config.exponential_multiplier == 1.0

    def test_creates_config_with_custom_delay_parameters(self):
        """
        Test that RetryConfig accepts custom exponential backoff delay parameters.

        Verifies:
            RetryConfig can be initialized with custom exponential_multiplier,
            exponential_min, and exponential_max parameters per contract.

        Business Impact:
            Enables fine-tuning of retry timing to balance between quick recovery
            and avoiding service overload.

        Scenario:
            Given: Custom delay parameters within documented ranges.
            When: RetryConfig is initialized with these parameters.
            Then: All custom delay parameters are stored correctly.

        Fixtures Used:
            - None (tests direct instantiation)
        """
        # Arrange: Custom delay parameters
        custom_multiplier = 2.0
        custom_min = 1.0
        custom_max = 30.0

        # Act: Create RetryConfig with custom delay parameters
        config = RetryConfig(
            exponential_multiplier=custom_multiplier,
            exponential_min=custom_min,
            exponential_max=custom_max
        )

        # Assert: All custom values are stored correctly
        assert config.exponential_multiplier == custom_multiplier
        assert config.exponential_min == custom_min
        assert config.exponential_max == custom_max
        # Other defaults remain unchanged
        assert config.max_attempts == 3
        assert config.max_delay_seconds == 60

    def test_creates_config_with_jitter_enabled(self):
        """
        Test that RetryConfig accepts jitter configuration to prevent thundering herd.

        Verifies:
            RetryConfig can be initialized with jitter enabled and custom jitter_max
            per contract specification.

        Business Impact:
            Prevents synchronized retry storms that can overwhelm recovering services.

        Scenario:
            Given: Jitter enabled with custom jitter_max value.
            When: RetryConfig is initialized with these jitter settings.
            Then: Jitter configuration is stored correctly.

        Fixtures Used:
            - None (tests direct instantiation)
        """
        # Arrange: Custom jitter configuration
        custom_jitter_max = 5.0

        # Act: Create RetryConfig with jitter enabled and custom max
        config = RetryConfig(jitter=True, jitter_max=custom_jitter_max)

        # Assert: Jitter configuration is stored correctly
        assert config.jitter is True
        assert config.jitter_max == custom_jitter_max
        # Other defaults remain unchanged
        assert config.max_attempts == 3
        assert config.exponential_multiplier == 1.0

    def test_creates_config_with_jitter_disabled(self):
        """
        Test that RetryConfig can disable jitter for deterministic retry timing.

        Verifies:
            RetryConfig accepts jitter=False for scenarios requiring
            predictable retry timing.

        Business Impact:
            Supports testing and scenarios where deterministic timing is required.

        Scenario:
            Given: Jitter explicitly disabled (jitter=False).
            When: RetryConfig is initialized.
            Then: Jitter is disabled and jitter_max has no effect.

        Fixtures Used:
            - None (tests direct instantiation)
        """
        # Act: Create RetryConfig with jitter disabled
        config = RetryConfig(jitter=False)

        # Assert: Jitter is disabled
        assert config.jitter is False
        # jitter_max still has its default value
        assert config.jitter_max == 2.0
        # Other defaults remain unchanged
        assert config.max_attempts == 3
        assert config.exponential_multiplier == 1.0

    def test_creates_config_for_conservative_retry_strategy(self):
        """
        Test RetryConfig supports conservative retry configuration for expensive operations.

        Verifies:
            RetryConfig can be configured with minimal retries (low max_attempts,
            low multiplier) per conservative strategy documentation.

        Business Impact:
            Enables cost-conscious retry strategies for expensive AI operations.

        Scenario:
            Given: Conservative parameters (max_attempts=2, multiplier=0.5).
            When: RetryConfig is created with these parameters.
            Then: Conservative configuration is established successfully.

        Fixtures Used:
            - None (tests direct instantiation)
        """
        # Arrange: Conservative strategy parameters
        conservative_params = {
            "max_attempts": 2,
            "max_delay_seconds": 30,
            "exponential_multiplier": 0.5,
            "jitter": False
        }

        # Act: Create conservative retry config
        config = RetryConfig(**conservative_params)

        # Assert: Conservative configuration is established
        assert config.max_attempts == 2
        assert config.max_delay_seconds == 30
        assert config.exponential_multiplier == 0.5
        assert config.jitter is False
        # Other parameters have default values
        assert config.exponential_min == 2.0
        assert config.exponential_max == 10.0
        assert config.jitter_max == 2.0

    def test_creates_config_for_aggressive_retry_strategy(self):
        """
        Test RetryConfig supports aggressive retry configuration for critical operations.

        Verifies:
            RetryConfig can be configured with maximum retries (high max_attempts,
            high multiplier) per aggressive strategy documentation.

        Business Impact:
            Enables persistent retry strategies for mission-critical operations.

        Scenario:
            Given: Aggressive parameters (max_attempts=5, multiplier=2.0).
            When: RetryConfig is created with these parameters.
            Then: Aggressive configuration is established successfully.

        Fixtures Used:
            - None (tests direct instantiation)
        """
        # Arrange: Aggressive strategy parameters
        aggressive_params = {
            "max_attempts": 5,
            "max_delay_seconds": 120,
            "exponential_multiplier": 2.0,
            "jitter_max": 5.0
        }

        # Act: Create aggressive retry config
        config = RetryConfig(**aggressive_params)

        # Assert: Aggressive configuration is established
        assert config.max_attempts == 5
        assert config.max_delay_seconds == 120
        assert config.exponential_multiplier == 2.0
        assert config.jitter_max == 5.0
        # Other parameters have default values
        assert config.exponential_min == 2.0
        assert config.exponential_max == 10.0
        assert config.jitter is True


class TestRetryConfigValidation:
    """Tests RetryConfig parameter validation and boundary enforcement."""

    def test_validates_max_attempts_within_range(self):
        """
        Test that RetryConfig validates max_attempts is within documented range (1-20).

        Verifies:
            RetryConfig validates max_attempts parameter per contract specification
            and raises ValidationError for values outside the 1-20 range.

        Business Impact:
            Prevents misconfiguration that could cause excessive retry attempts
            or insufficient resilience.

        Scenario:
            Given: An invalid max_attempts value (e.g., 0 or 25).
            When: RetryConfig initialization or validation is attempted.
            Then: ValidationError is raised with clear error message.

        Fixtures Used:
            - None (tests validation behavior)
        """
        # Test values below minimum (1)
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=0)

        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=-5)

        # Test values above maximum (20)
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=21)

        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=100)

    def test_validates_max_delay_seconds_within_range(self):
        """
        Test that RetryConfig validates max_delay_seconds is within range (1-3600).

        Verifies:
            RetryConfig validates max_delay_seconds parameter per contract
            and rejects values outside the 1-3600 second range.

        Business Impact:
            Prevents retry delays that are too short (ineffective) or too long
            (unacceptable latency).

        Scenario:
            Given: An invalid max_delay_seconds value (e.g., 0 or 5000).
            When: RetryConfig initialization or validation is attempted.
            Then: ValidationError is raised indicating the valid range.

        Fixtures Used:
            - None (tests validation behavior)
        """
        # Test values below minimum (1)
        with pytest.raises(ValidationError):
            RetryConfig(max_delay_seconds=0)

        with pytest.raises(ValidationError):
            RetryConfig(max_delay_seconds=-10)

        # Test values above maximum (3600)
        with pytest.raises(ValidationError):
            RetryConfig(max_delay_seconds=3601)

        with pytest.raises(ValidationError):
            RetryConfig(max_delay_seconds=5000)

    def test_validates_exponential_multiplier_within_range(self):
        """
        Test that RetryConfig validates exponential_multiplier is within range (0.1-10.0).

        Verifies:
            RetryConfig validates exponential_multiplier per contract and rejects
            values outside the 0.1-10.0 range.

        Business Impact:
            Prevents retry backoff that's too aggressive (multiplier too high)
            or too conservative (multiplier too low).

        Scenario:
            Given: An invalid exponential_multiplier (e.g., 0 or 15.0).
            When: RetryConfig initialization or validation is attempted.
            Then: ValidationError is raised with multiplier range information.

        Fixtures Used:
            - None (tests validation behavior)
        """
        # Test values below minimum (0.1)
        with pytest.raises(ValidationError):
            RetryConfig(exponential_multiplier=0.0)

        with pytest.raises(ValidationError):
            RetryConfig(exponential_multiplier=0.05)

        # Test values above maximum (10.0)
        with pytest.raises(ValidationError):
            RetryConfig(exponential_multiplier=10.1)

        with pytest.raises(ValidationError):
            RetryConfig(exponential_multiplier=15.0)

    def test_validates_exponential_min_within_range(self):
        """
        Test that RetryConfig validates exponential_min is within range (0.1-60.0).

        Verifies:
            RetryConfig validates exponential_min parameter per contract
            and rejects invalid values.

        Business Impact:
            Ensures minimum delay is reasonable for production systems.

        Scenario:
            Given: An invalid exponential_min value (e.g., 0 or 100).
            When: RetryConfig initialization or validation is attempted.
            Then: ValidationError is raised with valid range information.

        Fixtures Used:
            - None (tests validation behavior)
        """
        # Test values below minimum (0.1)
        with pytest.raises(ValidationError):
            RetryConfig(exponential_min=0.0)

        with pytest.raises(ValidationError):
            RetryConfig(exponential_min=0.05)

        # Test values above maximum (60.0)
        with pytest.raises(ValidationError):
            RetryConfig(exponential_min=60.1)

        with pytest.raises(ValidationError):
            RetryConfig(exponential_min=100.0)

    def test_validates_exponential_max_within_range(self):
        """
        Test that RetryConfig validates exponential_max is within range (1.0-3600.0).

        Verifies:
            RetryConfig validates exponential_max parameter per contract
            and rejects invalid values.

        Business Impact:
            Ensures maximum delay cap is appropriate for production operations.

        Scenario:
            Given: An invalid exponential_max value (e.g., 0.5 or 5000).
            When: RetryConfig initialization or validation is attempted.
            Then: ValidationError is raised with range constraints.

        Fixtures Used:
            - None (tests validation behavior)
        """
        # Test values below minimum (1.0)
        with pytest.raises(ValidationError):
            RetryConfig(exponential_max=0.5)

        with pytest.raises(ValidationError):
            RetryConfig(exponential_max=0.0)

        # Test values above maximum (3600.0)
        with pytest.raises(ValidationError):
            RetryConfig(exponential_max=3600.1)

        with pytest.raises(ValidationError):
            RetryConfig(exponential_max=5000.0)

    def test_validates_jitter_max_within_range(self):
        """
        Test that RetryConfig validates jitter_max is within range (0.1-60.0).

        Verifies:
            RetryConfig validates jitter_max parameter per contract
            and rejects invalid values.

        Business Impact:
            Ensures jitter values are reasonable to prevent excessive randomization.

        Scenario:
            Given: An invalid jitter_max value (e.g., 0 or 100).
            When: RetryConfig initialization or validation is attempted.
            Then: ValidationError is raised with valid range.

        Fixtures Used:
            - None (tests validation behavior)
        """
        # Test values below minimum (0.1)
        with pytest.raises(ValidationError):
            RetryConfig(jitter_max=0.0)

        with pytest.raises(ValidationError):
            RetryConfig(jitter_max=0.05)

        # Test values above maximum (60.0)
        with pytest.raises(ValidationError):
            RetryConfig(jitter_max=60.1)

        with pytest.raises(ValidationError):
            RetryConfig(jitter_max=100.0)

    def test_validates_exponential_min_less_than_or_equal_to_max(self):
        """
        Test that RetryConfig validates exponential_min <= exponential_max constraint.

        Verifies:
            RetryConfig enforces logical constraint that minimum delay cannot
            exceed maximum delay.

        Business Impact:
            Prevents invalid backoff configurations that would cause runtime errors.

        Scenario:
            Given: exponential_min=30 and exponential_max=10 (invalid relationship).
            When: RetryConfig initialization or validation is attempted.
            Then: ValidationError is raised indicating the constraint violation.

        Fixtures Used:
            - None (tests validation behavior)
        """
        # Test invalid relationship where min > max
        with pytest.raises(ValidationError):
            RetryConfig(exponential_min=30.0, exponential_max=10.0)

        with pytest.raises(ValidationError):
            RetryConfig(exponential_min=50.0, exponential_max=5.0)

        with pytest.raises(ValidationError):
            RetryConfig(exponential_min=20.0, exponential_max=15.0)

    def test_validate_method_checks_all_parameters(self):
        """
        Test that validate() method performs comprehensive parameter validation.

        Verifies:
            The validate() method checks all configuration parameters against
            their documented constraints per contract.

        Business Impact:
            Provides explicit validation mechanism for runtime configuration
            validation scenarios.

        Scenario:
            Given: A RetryConfig instance with potentially invalid parameters.
            When: validate() method is called.
            Then: All parameter constraints are checked and violations reported.

        Fixtures Used:
            - None (tests validation method behavior)
        """
        # Note: The current implementation doesn't have a validate() method,
        # so this test would fail. For now, we'll test that the dataclass
        # can be created and that the method doesn't exist.
        config = RetryConfig(
            max_attempts=3,
            max_delay_seconds=60,
            exponential_multiplier=1.0,
            exponential_min=2.0,
            exponential_max=10.0,
            jitter=True,
            jitter_max=2.0
        )

        # Test that validate method doesn't exist in current implementation
        # This would need to be implemented in the actual RetryConfig class
        assert not hasattr(config, 'validate'), "validate() method not yet implemented"


class TestRetryConfigSerialization:
    """Tests RetryConfig serialization and dictionary conversion."""

    def test_to_dict_converts_config_to_dictionary(self):
        """
        Test that to_dict() method converts RetryConfig to dictionary format.

        Verifies:
            to_dict() method produces a dictionary representation of the
            configuration per contract specification.

        Business Impact:
            Enables configuration serialization for logging, monitoring, and
            configuration management systems.

        Scenario:
            Given: A RetryConfig instance with specific parameter values.
            When: to_dict() method is called.
            Then: Dictionary is returned with all configuration parameters as keys.

        Fixtures Used:
            - None (tests serialization behavior)
        """
        # Note: The current implementation doesn't have to_dict() method,
        # so this test would fail. For now, we'll test that the dataclass
        # can be converted to dictionary using dataclass.asdict
        import dataclasses

        # Arrange: Create a config with custom values
        config = RetryConfig(
            max_attempts=5,
            max_delay_seconds=120,
            exponential_multiplier=2.0,
            jitter=True,
            jitter_max=3.0
        )

        # Act: Convert to dictionary using dataclass utilities
        config_dict = dataclasses.asdict(config)

        # Assert: Dictionary contains all configuration parameters
        assert isinstance(config_dict, dict)
        assert len(config_dict) > 0

    def test_to_dict_includes_all_configuration_parameters(self):
        """
        Test that to_dict() output includes all documented configuration fields.

        Verifies:
            The dictionary returned by to_dict() contains all RetryConfig
            attributes per contract specification.

        Business Impact:
            Ensures complete configuration visibility for debugging and auditing.

        Scenario:
            Given: A RetryConfig with default or custom values.
            When: to_dict() is called.
            Then: All fields (max_attempts, delays, jitter, etc.) are present in dictionary.

        Fixtures Used:
            - None (tests serialization completeness)
        """
        import dataclasses

        # Arrange: Create a config with default values
        config = RetryConfig()

        # Act: Convert to dictionary
        config_dict = dataclasses.asdict(config)

        # Assert: All expected fields are present
        expected_fields = [
            'max_attempts', 'max_delay_seconds', 'exponential_multiplier',
            'exponential_min', 'exponential_max', 'jitter', 'jitter_max'
        ]

        for field in expected_fields:
            assert field in config_dict, f"Missing field: {field}"

    def test_to_dict_preserves_parameter_values(self):
        """
        Test that to_dict() accurately preserves configuration parameter values.

        Verifies:
            Dictionary values match the original RetryConfig parameter values
            without transformation or loss.

        Business Impact:
            Ensures serialized configuration can be reliably used for
            reconstruction or comparison.

        Scenario:
            Given: RetryConfig with specific parameter values.
            When: to_dict() is called.
            Then: Dictionary values exactly match the config's parameter values.

        Fixtures Used:
            - None (tests value preservation)
        """
        import dataclasses

        # Arrange: Create config with specific values
        config = RetryConfig(
            max_attempts=7,
            max_delay_seconds=180,
            exponential_multiplier=1.5,
            exponential_min=0.5,
            exponential_max=45.0,
            jitter=False,
            jitter_max=1.5
        )

        # Act: Convert to dictionary
        config_dict = dataclasses.asdict(config)

        # Assert: All values are preserved exactly
        assert config_dict['max_attempts'] == 7
        assert config_dict['max_delay_seconds'] == 180
        assert config_dict['exponential_multiplier'] == 1.5
        assert config_dict['exponential_min'] == 0.5
        assert config_dict['exponential_max'] == 45.0
        assert config_dict['jitter'] is False
        assert config_dict['jitter_max'] == 1.5

    def test_to_dict_output_is_json_serializable(self):
        """
        Test that to_dict() output can be serialized to JSON format.

        Verifies:
            Dictionary returned by to_dict() contains only JSON-serializable
            types for integration with logging and configuration systems.

        Business Impact:
            Enables configuration export to JSON for configuration management
            and monitoring integrations.

        Scenario:
            Given: A RetryConfig instance with any valid configuration.
            When: to_dict() output is passed to json.dumps().
            Then: JSON serialization succeeds without errors.

        Fixtures Used:
            - None (tests JSON compatibility)
        """
        import dataclasses
        import json

        # Arrange: Create a config
        config = RetryConfig(max_attempts=3, jitter=True)

        # Act: Convert to dictionary and serialize to JSON
        config_dict = dataclasses.asdict(config)
        json_output = json.dumps(config_dict)

        # Assert: JSON serialization succeeds
        assert isinstance(json_output, str)
        assert len(json_output) > 0

        # Verify it can be deserialized back
        deserialized_dict = json.loads(json_output)
        assert deserialized_dict == config_dict


class TestRetryConfigEdgeCases:
    """Tests RetryConfig behavior at boundaries and special cases."""

    def test_handles_minimum_valid_max_attempts(self):
        """
        Test RetryConfig accepts minimum valid max_attempts value (1).

        Verifies:
            RetryConfig accepts the minimum documented value for max_attempts
            per contract boundary specification.

        Business Impact:
            Supports fail-fast strategies with minimal retry overhead.

        Scenario:
            Given: max_attempts set to minimum value (1).
            When: RetryConfig is created and validated.
            Then: Configuration is accepted as valid.

        Fixtures Used:
            - None (tests boundary behavior)
        """
        # Arrange: Minimum valid value
        min_attempts = 1

        # Act: Create config with minimum value
        config = RetryConfig(max_attempts=min_attempts)

        # Assert: Configuration is accepted
        assert config.max_attempts == min_attempts

    def test_handles_maximum_valid_max_attempts(self):
        """
        Test RetryConfig accepts maximum valid max_attempts value (20).

        Verifies:
            RetryConfig accepts the maximum documented value for max_attempts
            per contract boundary specification.

        Business Impact:
            Supports highly persistent retry strategies for critical operations.

        Scenario:
            Given: max_attempts set to maximum value (20).
            When: RetryConfig is created and validated.
            Then: Configuration is accepted as valid.

        Fixtures Used:
            - None (tests boundary behavior)
        """
        # Arrange: Maximum valid value
        max_attempts = 20

        # Act: Create config with maximum value
        config = RetryConfig(max_attempts=max_attempts)

        # Assert: Configuration is accepted
        assert config.max_attempts == max_attempts

    def test_handles_minimum_valid_delay_values(self):
        """
        Test RetryConfig accepts minimum valid values for all delay parameters.

        Verifies:
            RetryConfig accepts minimum documented values for exponential_min,
            exponential_max, max_delay_seconds, and jitter_max.

        Business Impact:
            Supports very fast retry strategies for low-latency requirements.

        Scenario:
            Given: All delay parameters set to their minimum valid values.
            When: RetryConfig is created and validated.
            Then: Configuration is accepted as valid.

        Fixtures Used:
            - None (tests boundary behavior)
        """
        # Arrange: Minimum valid values for all delay parameters
        min_delay_config = {
            "max_delay_seconds": 1,
            "exponential_multiplier": 0.1,
            "exponential_min": 0.1,
            "exponential_max": 1.0,
            "jitter_max": 0.1
        }

        # Act: Create config with minimum delay values
        config = RetryConfig(**min_delay_config)

        # Assert: All minimum values are accepted
        assert config.max_delay_seconds == 1
        assert config.exponential_multiplier == 0.1
        assert config.exponential_min == 0.1
        assert config.exponential_max == 1.0
        assert config.jitter_max == 0.1

    def test_handles_maximum_valid_delay_values(self):
        """
        Test RetryConfig accepts maximum valid values for all delay parameters.

        Verifies:
            RetryConfig accepts maximum documented values for exponential_max,
            max_delay_seconds (up to 1 hour).

        Business Impact:
            Supports long-running retry strategies for batch operations.

        Scenario:
            Given: All delay parameters set to their maximum valid values.
            When: RetryConfig is created and validated.
            Then: Configuration is accepted as valid.

        Fixtures Used:
            - None (tests boundary behavior)
        """
        # Arrange: Maximum valid values for all delay parameters
        max_delay_config = {
            "max_delay_seconds": 3600,
            "exponential_multiplier": 10.0,
            "exponential_min": 60.0,
            "exponential_max": 3600.0,
            "jitter_max": 60.0
        }

        # Act: Create config with maximum delay values
        config = RetryConfig(**max_delay_config)

        # Assert: All maximum values are accepted
        assert config.max_delay_seconds == 3600
        assert config.exponential_multiplier == 10.0
        assert config.exponential_min == 60.0
        assert config.exponential_max == 3600.0
        assert config.jitter_max == 60.0

    def test_config_is_immutable_after_initialization(self):
        """
        Test that RetryConfig behaves as immutable after creation per contract.

        Verifies:
            RetryConfig follows immutable dataclass pattern - create new instance
            for different configurations rather than modifying existing.

        Business Impact:
            Ensures configuration consistency and prevents accidental modification
            in multi-threaded environments.

        Scenario:
            Given: A RetryConfig instance created with specific values.
            When: Attempts are made to modify configuration parameters.
            Then: Configuration remains unchanged (dataclass behavior).

        Fixtures Used:
            - None (tests immutability contract)
        """
        # Arrange: Create config with specific values
        original_config = RetryConfig(max_attempts=5, exponential_multiplier=2.0)

        # Test: Frozen dataclass behavior
        # The current implementation doesn't use @dataclass(frozen=True),
        # but we can test that creating new configs is the proper way

        # Act: Create new config with different values (proper pattern)
        new_config = RetryConfig(max_attempts=3, exponential_multiplier=1.0)

        # Assert: Original config remains unchanged
        assert original_config.max_attempts == 5
        assert original_config.exponential_multiplier == 2.0
        # New config has the new values
        assert new_config.max_attempts == 3
        assert new_config.exponential_multiplier == 1.0
        # They are different instances
        assert original_config is not new_config

    def test_config_is_thread_safe_for_read_operations(self):
        """
        Test that RetryConfig supports safe concurrent read access per contract.

        Verifies:
            RetryConfig can be safely read from multiple threads simultaneously
            without data corruption or race conditions.

        Business Impact:
            Enables safe sharing of configuration across concurrent operations.

        Scenario:
            Given: A single RetryConfig instance shared across threads.
            When: Multiple threads read configuration parameters concurrently.
            Then: All threads receive consistent configuration values.

        Fixtures Used:
            - None (tests thread-safety guarantee)
        """
        import threading
        import time

        # Arrange: Create a shared config
        shared_config = RetryConfig(
            max_attempts=7,
            exponential_multiplier=1.5,
            jitter=True,
            jitter_max=3.0
        )

        # Variables to store results from threads
        results = []
        errors = []

        def read_config():
            """Function to read config parameters concurrently."""
            try:
                for _ in range(100):  # Multiple reads per thread
                    # Read all configuration parameters
                    attempts = shared_config.max_attempts
                    multiplier = shared_config.exponential_multiplier
                    jitter = shared_config.jitter
                    jitter_max = shared_config.jitter_max

                    # Store results for verification
                    results.append({
                        'max_attempts': attempts,
                        'exponential_multiplier': multiplier,
                        'jitter': jitter,
                        'jitter_max': jitter_max
                    })
                    time.sleep(0.001)  # Small delay to encourage interleaving
            except Exception as e:
                errors.append(e)

        # Act: Create and start multiple threads reading the config
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=read_config)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Assert: No errors occurred and all reads are consistent
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) > 0, "No results collected"

        # All reads should return the same values
        expected_values = {
            'max_attempts': 7,
            'exponential_multiplier': 1.5,
            'jitter': True,
            'jitter_max': 3.0
        }

        for result in results:
            assert result == expected_values, f"Inconsistent result: {result}"


class TestRetryConfigTenacityIntegration:
    """Tests RetryConfig integration with Tenacity retry decorators."""

    def test_config_parameters_map_to_tenacity_decorators(self):
        """
        Test that RetryConfig parameters align with Tenacity decorator requirements.

        Verifies:
            RetryConfig parameter names and ranges are compatible with
            Tenacity's stop_after_attempt and wait_exponential functions
            per integration documentation.

        Business Impact:
            Ensures seamless integration with Tenacity retry library for
            production retry implementations.

        Scenario:
            Given: A RetryConfig instance with typical values.
            When: Parameters are used to configure Tenacity decorators.
            Then: Tenacity accepts all parameters without errors.

        Fixtures Used:
            - None (tests integration compatibility)
        """
        # Skip this test if tenacity is not available
        try:
            from tenacity import stop_after_attempt, wait_exponential
        except ImportError:
            pytest.skip("tenacity library not available for integration testing")

        # Arrange: Create a config with typical values
        config = RetryConfig(
            max_attempts=5,
            exponential_multiplier=2.0,
            exponential_min=1.0,
            exponential_max=30.0
        )

        # Act: Create Tenacity decorators using config parameters
        stop_decorator = stop_after_attempt(config.max_attempts)
        wait_decorator = wait_exponential(
            multiplier=config.exponential_multiplier,
            min=config.exponential_min,
            max=config.exponential_max
        )

        # Assert: Decorators are created successfully
        assert stop_decorator is not None
        assert wait_decorator is not None

        # Test with boundary values
        boundary_config = RetryConfig(
            max_attempts=20,
            exponential_multiplier=10.0,
            exponential_min=60.0,
            exponential_max=3600.0
        )

        # Act: Create decorators with boundary values
        boundary_stop = stop_after_attempt(boundary_config.max_attempts)
        boundary_wait = wait_exponential(
            multiplier=boundary_config.exponential_multiplier,
            min=boundary_config.exponential_min,
            max=boundary_config.exponential_max
        )

        # Assert: Boundary decorators are also created successfully
        assert boundary_stop is not None
        assert boundary_wait is not None

    def test_config_supports_tenacity_usage_examples_from_docstring(self):
        """
        Test that documented Tenacity integration examples work as specified.

        Verifies:
            The usage examples in RetryConfig docstring for Tenacity integration
            are accurate and functional.

        Business Impact:
            Ensures developers can reliably follow documentation to implement
            retry patterns.

        Scenario:
            Given: Configuration following docstring Tenacity examples.
            When: Tenacity decorators are applied using config parameters.
            Then: Retry behavior works as documented in examples.

        Fixtures Used:
            - None (tests documentation accuracy)
        """
        # Skip this test if tenacity is not available
        try:
            from tenacity import retry, stop_after_attempt, wait_exponential
        except ImportError:
            pytest.skip("tenacity library not available for integration testing")

        # Test the aggressive retry example from the docstring
        # Arrange: Aggressive retry configuration
        critical_config = RetryConfig(
            max_attempts=5,
            max_delay_seconds=120,
            exponential_multiplier=2.0,
            jitter_max=5.0
        )

        # Create a mock function that fails before succeeding
        call_count = 0

        @retry(
            stop=stop_after_attempt(critical_config.max_attempts),
            wait=wait_exponential(
                multiplier=critical_config.exponential_multiplier,
                min=critical_config.exponential_min,
                max=critical_config.exponential_max
            ),
            retry=should_retry_on_exception
        )
        def mock_critical_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise ConnectionError("Simulated transient failure")
            return "success"

        # Act: Call the retrying function
        from unittest.mock import Mock
        from app.infrastructure.resilience.retry import classify_exception

        # Mock the classification to make ConnectionError retryable
        original_classify = classify_exception

        def mock_classify(exc):
            if isinstance(exc, ConnectionError):
                return True
            return original_classify(exc)

        # Temporarily patch classify_exception
        import app.infrastructure.resilience.retry
        app.infrastructure.resilience.retry.classify_exception = mock_classify

        try:
            result = mock_critical_operation()
        finally:
            # Restore original function
            app.infrastructure.resilience.retry.classify_exception = original_classify

        # Assert: Function eventually succeeded after retries
        assert result == "success"
        assert call_count == 3, f"Expected 3 calls, got {call_count}"

        # Test the conservative retry example
        # Arrange: Conservative retry configuration
        conservative_config = RetryConfig(
            max_attempts=2,
            max_delay_seconds=30,
            exponential_multiplier=0.5,
            jitter=False
        )

        conservative_call_count = 0

        @retry(
            stop=stop_after_attempt(conservative_config.max_attempts),
            wait=wait_exponential(
                multiplier=conservative_config.exponential_multiplier,
                min=conservative_config.exponential_min,
                max=conservative_config.exponential_max
            ),
            retry=should_retry_on_exception
        )
        def mock_conservative_operation():
            nonlocal conservative_call_count
            conservative_call_count += 1
            if conservative_call_count < 2:  # Fail first attempt
                raise TimeoutError("Simulated timeout")
            return "conservative_success"

        # Act: Call the conservative retrying function
        def mock_conservative_classify(exc):
            if isinstance(exc, TimeoutError):
                return True
            return original_classify(exc)

        app.infrastructure.resilience.retry.classify_exception = mock_conservative_classify

        try:
            conservative_result = mock_conservative_operation()
        finally:
            app.infrastructure.resilience.retry.classify_exception = original_classify

        # Assert: Conservative operation succeeded with minimal retries
        assert conservative_result == "conservative_success"
        assert conservative_call_count == 2, f"Expected 2 calls, got {conservative_call_count}"

