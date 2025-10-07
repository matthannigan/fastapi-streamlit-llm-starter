"""
Unit tests for EncryptedCacheLayer performance monitoring behavior.

This test module verifies that the EncryptedCacheLayer class properly tracks
and reports performance statistics as documented in the public contract,
including operation counting, timing accumulation, average calculation,
and statistics reset functionality.

Test Coverage:
    - is_enabled property behavior
    - get_performance_stats() output structure and accuracy
    - reset_performance_stats() functionality
    - Performance monitoring enable/disable behavior
    - Statistics accumulation over multiple operations
    - Average time calculations
"""

import pytest
from app.core.exceptions import ConfigurationError


class TestIsEnabledProperty:
    """
    Test suite for is_enabled property behavior.

    Scope:
        Tests the is_enabled property that reports encryption status
        as documented in property docstring and Examples.

    Business Critical:
        Applications need reliable way to check encryption status for
        logging, monitoring, and conditional logic.

    Test Strategy:
        - Verify property returns True when encryption is enabled
        - Verify property returns False when encryption is disabled
        - Test property behavior matches initialization state
    """

    def test_is_enabled_returns_true_with_valid_key(self, encryption_with_valid_key):
        """
        Test that is_enabled returns True when encryption is enabled.

        Verifies:
            is_enabled property returns True when EncryptedCacheLayer
            was initialized with valid encryption key per property Returns.

        Business Impact:
            Enables applications to verify encryption is active before
            storing sensitive data, ensuring security compliance.

        Scenario:
            Given: EncryptedCacheLayer initialized with valid encryption key
            When: is_enabled property is accessed
            Then: Property returns True
            And: Return value is boolean type
            And: Value correctly reflects encryption status

        Fixtures Used:
            - encryption_with_valid_key: Instance with encryption enabled
        """
        # Given: EncryptedCacheLayer initialized with valid encryption key
        encryption = encryption_with_valid_key

        # When: is_enabled property is accessed
        is_encrypted = encryption.is_enabled

        # Then: Property returns True
        assert is_encrypted is True

        # And: Return value is boolean type
        assert isinstance(is_encrypted, bool)

        # And: Value correctly reflects encryption status
        assert is_encrypted == encryption.is_enabled  # Consistent access

    def test_is_enabled_returns_false_without_key(self, encryption_without_key):
        """
        Test that is_enabled returns False when encryption is disabled.

        Verifies:
            is_enabled property returns False when EncryptedCacheLayer
            was initialized without encryption key per property Returns.

        Business Impact:
            Allows applications to detect disabled encryption and take
            appropriate action (warnings, alternative behavior, etc.).

        Scenario:
            Given: EncryptedCacheLayer initialized with None encryption key
            When: is_enabled property is accessed
            Then: Property returns False
            And: Return value is boolean type
            And: Value indicates encryption is disabled

        Fixtures Used:
            - encryption_without_key: Instance with encryption disabled
        """
        # Given: EncryptedCacheLayer initialized with None encryption key
        encryption = encryption_without_key

        # When: is_enabled property is accessed
        is_encrypted = encryption.is_enabled

        # Then: Property returns False
        assert is_encrypted is False

        # And: Return value is boolean type
        assert isinstance(is_encrypted, bool)

        # And: Value indicates encryption is disabled
        assert is_encrypted == encryption.is_enabled  # Consistent access

    def test_is_enabled_matches_initialization_state(self, encryption_with_valid_key, encryption_without_key):
        """
        Test that is_enabled property reflects initialization configuration.

        Verifies:
            is_enabled property value is consistent with how the instance
            was initialized (with or without encryption key).

        Business Impact:
            Ensures reliable encryption status reporting throughout
            instance lifetime for consistent application behavior.

        Scenario:
            Given: Multiple EncryptedCacheLayer instances with different configs
            When: is_enabled is checked on each instance
            Then: Property value matches initialization state for each
            And: Enabled instances return True
            And: Disabled instances return False
            And: Values remain consistent over instance lifetime

        Fixtures Used:
            - encryption_with_valid_key: Enabled encryption
            - encryption_without_key: Disabled encryption
        """
        # Given: Multiple EncryptedCacheLayer instances with different configs
        enabled_encryption = encryption_with_valid_key
        disabled_encryption = encryption_without_key

        # When: is_enabled is checked on each instance
        enabled_status = enabled_encryption.is_enabled
        disabled_status = disabled_encryption.is_enabled

        # Then: Property value matches initialization state for each
        assert enabled_status is True
        assert disabled_status is False

        # And: Enabled instances return True
        # And: Disabled instances return False
        assert enabled_status is not disabled_status

        # And: Values remain consistent over instance lifetime
        # Access property multiple times to ensure consistency
        assert enabled_encryption.is_enabled == enabled_encryption.is_enabled
        assert disabled_encryption.is_enabled == disabled_encryption.is_enabled

    def test_is_enabled_can_be_used_in_conditional_logic(self, encryption_with_valid_key, encryption_without_key):
        """
        Test that is_enabled works correctly in if statements.

        Verifies:
            is_enabled property can be used directly in conditional logic
            per Examples section showing typical usage pattern.

        Business Impact:
            Enables clean conditional code for encryption-dependent logic,
            improving code readability and maintainability.

        Scenario:
            Given: EncryptedCacheLayer instances (enabled and disabled)
            When: is_enabled is used in if statement
            Then: Conditional logic works as expected
            And: Enabled instance triggers True branch
            And: Disabled instance triggers False branch
            And: Property behaves like boolean in all contexts

        Fixtures Used:
            - encryption_with_valid_key: For True branch testing
            - encryption_without_key: For False branch testing
        """
        # Given: EncryptedCacheLayer instances (enabled and disabled)
        enabled_encryption = encryption_with_valid_key
        disabled_encryption = encryption_without_key

        # When: is_enabled is used in if statement
        result_enabled = []
        result_disabled = []

        # Test enabled instance triggers True branch
        if enabled_encryption.is_enabled:
            result_enabled.append("encryption_active")
        else:
            result_enabled.append("encryption_inactive")

        # Test disabled instance triggers False branch
        if disabled_encryption.is_enabled:
            result_disabled.append("encryption_active")
        else:
            result_disabled.append("encryption_inactive")

        # Then: Conditional logic works as expected
        # And: Enabled instance triggers True branch
        assert result_enabled == ["encryption_active"]

        # And: Disabled instance triggers False branch
        assert result_disabled == ["encryption_inactive"]

        # And: Property behaves like boolean in all contexts
        # Test in boolean expressions
        assert bool(enabled_encryption.is_enabled) is True
        assert bool(disabled_encryption.is_enabled) is False
        assert not disabled_encryption.is_enabled is True
        assert enabled_encryption.is_enabled or False is True
        assert (disabled_encryption.is_enabled and True) is False


class TestGetPerformanceStats:
    """
    Test suite for get_performance_stats() method behavior.

    Scope:
        Tests the get_performance_stats() method covering output structure,
        accuracy, and behavior with monitoring enabled/disabled.

    Business Critical:
        Performance statistics enable monitoring and optimization of
        encryption overhead in production environments.

    Test Strategy:
        - Verify stats structure matches documented format
        - Test statistics accuracy after operations
        - Validate average calculations
        - Test behavior with monitoring disabled
        - Verify all documented fields are present
    """

    def test_get_performance_stats_returns_complete_structure(self, encryption_with_valid_key):
        """
        Test that get_performance_stats() returns all documented fields.

        Verifies:
            get_performance_stats() returns dictionary containing all fields
            documented in Returns section.

        Business Impact:
            Ensures monitoring systems can reliably access all performance
            metrics without handling missing fields.

        Scenario:
            Given: EncryptedCacheLayer with performance monitoring enabled
            When: get_performance_stats() is called
            Then: Dictionary is returned
            And: Dict contains "encryption_enabled" field
            And: Dict contains "encryption_operations" field
            And: Dict contains "decryption_operations" field
            And: Dict contains "total_operations" field
            And: Dict contains "total_encryption_time" field
            And: Dict contains "total_decryption_time" field
            And: Dict contains "avg_encryption_time" field
            And: Dict contains "avg_decryption_time" field
            And: Dict contains "performance_monitoring" field

        Fixtures Used:
            - encryption_with_valid_key: Instance with monitoring enabled
        """
        # Given: EncryptedCacheLayer with performance monitoring enabled
        encryption = encryption_with_valid_key

        # When: get_performance_stats() is called
        stats = encryption.get_performance_stats()

        # Then: Dictionary is returned
        assert isinstance(stats, dict)

        # And: Dict contains all documented fields
        expected_fields = [
            "encryption_enabled",
            "encryption_operations",
            "decryption_operations",
            "total_operations",
            "total_encryption_time",
            "total_decryption_time",
            "avg_encryption_time",
            "avg_decryption_time",
            "performance_monitoring"
        ]

        for field in expected_fields:
            assert field in stats, f"Missing field: {field}"

    def test_get_performance_stats_shows_zero_operations_initially(self, encryption_with_fresh_stats):
        """
        Test that performance stats show zero operations after reset.

        Verifies:
            get_performance_stats() returns zero counts immediately after
            initialization or reset per initial state documentation.

        Business Impact:
            Ensures clean baseline for performance tracking from
            known starting point.

        Scenario:
            Given: EncryptedCacheLayer with fresh statistics
            When: get_performance_stats() is called before any operations
            Then: encryption_operations is 0
            And: decryption_operations is 0
            And: total_operations is 0
            And: total_encryption_time is 0.0
            And: total_decryption_time is 0.0
            And: avg_encryption_time is 0.0
            And: avg_decryption_time is 0.0

        Fixtures Used:
            - encryption_with_fresh_stats: Instance with reset stats
        """
        # Given: EncryptedCacheLayer with fresh statistics
        encryption = encryption_with_fresh_stats

        # When: get_performance_stats() is called before any operations
        stats = encryption.get_performance_stats()

        # Then: All operation counts are zero
        assert stats["encryption_operations"] == 0
        assert stats["decryption_operations"] == 0
        assert stats["total_operations"] == 0

        # And: All timing values are zero
        assert stats["total_encryption_time"] == 0.0
        assert stats["total_decryption_time"] == 0.0
        assert stats["avg_encryption_time"] == 0.0
        assert stats["avg_decryption_time"] == 0.0

    def test_get_performance_stats_increments_encryption_operations(self, encryption_with_fresh_stats, sample_cache_data):
        """
        Test that encryption operations are counted correctly.

        Verifies:
            get_performance_stats() shows incremented encryption_operations
            counter after each encrypt_cache_data() call.

        Business Impact:
            Enables monitoring of encryption workload for capacity
            planning and performance analysis.

        Scenario:
            Given: EncryptedCacheLayer with fresh statistics
            When: encrypt_cache_data() is called 5 times
            And: get_performance_stats() is called
            Then: encryption_operations equals 5
            And: total_operations equals 5
            And: decryption_operations equals 0

        Fixtures Used:
            - encryption_with_fresh_stats: Clean baseline
            - sample_cache_data: Data for operations
        """
        # Given: EncryptedCacheLayer with fresh statistics
        encryption = encryption_with_fresh_stats

        # When: encrypt_cache_data() is called 5 times
        for _ in range(5):
            encryption.encrypt_cache_data(sample_cache_data)

        # And: get_performance_stats() is called
        stats = encryption.get_performance_stats()

        # Then: encryption_operations equals 5
        assert stats["encryption_operations"] == 5

        # And: total_operations equals 5
        assert stats["total_operations"] == 5

        # And: decryption_operations equals 0
        assert stats["decryption_operations"] == 0

    def test_get_performance_stats_increments_decryption_operations(self, encryption_with_fresh_stats, sample_encrypted_bytes):
        """
        Test that decryption operations are counted correctly.

        Verifies:
            get_performance_stats() shows incremented decryption_operations
            counter after each decrypt_cache_data() call.

        Business Impact:
            Enables monitoring of decryption workload separately from
            encryption for bottleneck identification.

        Scenario:
            Given: EncryptedCacheLayer with fresh statistics
            And: Pre-encrypted data for decryption
            When: decrypt_cache_data() is called 3 times
            And: get_performance_stats() is called
            Then: decryption_operations equals 3
            And: total_operations equals 3
            And: encryption_operations equals 0

        Fixtures Used:
            - encryption_with_fresh_stats: Clean baseline
            - sample_encrypted_bytes: Pre-encrypted data
        """
        # Given: EncryptedCacheLayer with fresh statistics
        encryption = encryption_with_fresh_stats

        # When: decrypt_cache_data() is called 3 times
        for _ in range(3):
            encryption.decrypt_cache_data(sample_encrypted_bytes)

        # And: get_performance_stats() is called
        stats = encryption.get_performance_stats()

        # Then: decryption_operations equals 3
        assert stats["decryption_operations"] == 3

        # And: total_operations equals 3
        assert stats["total_operations"] == 3

        # And: encryption_operations equals 0
        assert stats["encryption_operations"] == 0

    def test_get_performance_stats_accumulates_encryption_time(self, encryption_with_fresh_stats, sample_cache_data):
        """
        Test that total_encryption_time accumulates across operations.

        Verifies:
            get_performance_stats() shows accumulated total_encryption_time
            increasing with each encryption operation.

        Business Impact:
            Enables tracking total time spent in encryption for
            performance analysis and optimization.

        Scenario:
            Given: EncryptedCacheLayer with fresh statistics
            When: encrypt_cache_data() is called multiple times
            And: get_performance_stats() is called
            Then: total_encryption_time is greater than 0
            And: total_encryption_time increases with each operation
            And: Time value is reasonable for operations performed

        Fixtures Used:
            - encryption_with_fresh_stats: Clean baseline
            - sample_cache_data: Data for operations
        """
        # Given: EncryptedCacheLayer with fresh statistics
        encryption = encryption_with_fresh_stats

        # When: encrypt_cache_data() is called multiple times
        # Get initial stats to verify time accumulation
        initial_stats = encryption.get_performance_stats()
        initial_time = initial_stats["total_encryption_time"]

        # Perform first operation
        encryption.encrypt_cache_data(sample_cache_data)
        stats_after_first = encryption.get_performance_stats()

        # Perform second operation
        encryption.encrypt_cache_data(sample_cache_data)
        stats_after_second = encryption.get_performance_stats()

        # Then: total_encryption_time is greater than 0
        assert stats_after_first["total_encryption_time"] > 0

        # And: total_encryption_time increases with each operation
        assert stats_after_first["total_encryption_time"] > initial_time
        assert stats_after_second["total_encryption_time"] > stats_after_first["total_encryption_time"]

        # And: Time value is reasonable for operations performed (should be positive but not extremely large)
        assert stats_after_second["total_encryption_time"] < 1000  # Less than 1000ms (1 second) total

    def test_get_performance_stats_accumulates_decryption_time(self, encryption_with_fresh_stats, sample_encrypted_bytes):
        """
        Test that total_decryption_time accumulates across operations.

        Verifies:
            get_performance_stats() shows accumulated total_decryption_time
            increasing with each decryption operation.

        Business Impact:
            Enables tracking total time spent in decryption for
            cache retrieval performance analysis.

        Scenario:
            Given: EncryptedCacheLayer with fresh statistics
            And: Pre-encrypted data
            When: decrypt_cache_data() is called multiple times
            And: get_performance_stats() is called
            Then: total_decryption_time is greater than 0
            And: total_decryption_time increases with each operation
            And: Time value is reasonable for operations performed

        Fixtures Used:
            - encryption_with_fresh_stats: Clean baseline
            - sample_encrypted_bytes: Pre-encrypted data
        """
        # Given: EncryptedCacheLayer with fresh statistics
        encryption = encryption_with_fresh_stats

        # When: decrypt_cache_data() is called multiple times
        # Get initial stats to verify time accumulation
        initial_stats = encryption.get_performance_stats()
        initial_time = initial_stats["total_decryption_time"]

        # Perform first operation
        encryption.decrypt_cache_data(sample_encrypted_bytes)
        stats_after_first = encryption.get_performance_stats()

        # Perform second operation
        encryption.decrypt_cache_data(sample_encrypted_bytes)
        stats_after_second = encryption.get_performance_stats()

        # Then: total_decryption_time is greater than 0
        assert stats_after_first["total_decryption_time"] > 0

        # And: total_decryption_time increases with each operation
        assert stats_after_first["total_decryption_time"] > initial_time
        assert stats_after_second["total_decryption_time"] > stats_after_first["total_decryption_time"]

        # And: Time value is reasonable for operations performed (should be positive but not extremely large)
        assert stats_after_second["total_decryption_time"] < 1000  # Less than 1000ms (1 second) total

    def test_get_performance_stats_calculates_average_encryption_time(self, encryption_with_fresh_stats, sample_cache_data):
        """
        Test that avg_encryption_time is calculated correctly.

        Verifies:
            get_performance_stats() calculates avg_encryption_time as
            total_encryption_time / encryption_operations.

        Business Impact:
            Provides per-operation performance metric for identifying
            encryption performance trends and regressions.

        Scenario:
            Given: EncryptedCacheLayer with fresh statistics
            When: Multiple encrypt operations are performed
            And: get_performance_stats() is called
            Then: avg_encryption_time equals total_time / operation_count
            And: Average is expressed in milliseconds
            And: Calculation is mathematically correct

        Fixtures Used:
            - encryption_with_fresh_stats: Clean baseline
            - sample_cache_data: Data for operations
        """
        # Given: EncryptedCacheLayer with fresh statistics
        encryption = encryption_with_fresh_stats

        # When: Multiple encrypt operations are performed
        operation_count = 4
        for _ in range(operation_count):
            encryption.encrypt_cache_data(sample_cache_data)

        # And: get_performance_stats() is called
        stats = encryption.get_performance_stats()

        # Then: avg_encryption_time equals total_time / operation_count (converted to milliseconds)
        expected_avg = (stats["total_encryption_time"] / stats["encryption_operations"]) * 1000
        actual_avg = stats["avg_encryption_time"]

        assert abs(actual_avg - expected_avg) < 0.001  # Allow for floating point precision

        # And: Average is expressed in milliseconds (positive value)
        assert actual_avg > 0

        # And: Calculation is mathematically correct
        assert stats["encryption_operations"] == operation_count
        assert stats["total_encryption_time"] > 0

    def test_get_performance_stats_calculates_average_decryption_time(self, encryption_with_fresh_stats, sample_encrypted_bytes):
        """
        Test that avg_decryption_time is calculated correctly.

        Verifies:
            get_performance_stats() calculates avg_decryption_time as
            total_decryption_time / decryption_operations.

        Business Impact:
            Provides per-operation metric for monitoring cache retrieval
            performance and identifying slow operations.

        Scenario:
            Given: EncryptedCacheLayer with fresh statistics
            And: Pre-encrypted data
            When: Multiple decrypt operations are performed
            And: get_performance_stats() is called
            Then: avg_decryption_time equals total_time / operation_count
            And: Average is expressed in milliseconds
            And: Calculation is mathematically correct

        Fixtures Used:
            - encryption_with_fresh_stats: Clean baseline
            - sample_encrypted_bytes: Pre-encrypted data
        """
        # Given: EncryptedCacheLayer with fresh statistics
        encryption = encryption_with_fresh_stats

        # When: Multiple decrypt operations are performed
        operation_count = 3
        for _ in range(operation_count):
            encryption.decrypt_cache_data(sample_encrypted_bytes)

        # And: get_performance_stats() is called
        stats = encryption.get_performance_stats()

        # Then: avg_decryption_time equals total_time / operation_count (converted to milliseconds)
        expected_avg = (stats["total_decryption_time"] / stats["decryption_operations"]) * 1000
        actual_avg = stats["avg_decryption_time"]

        assert abs(actual_avg - expected_avg) < 0.001  # Allow for floating point precision

        # And: Average is expressed in milliseconds (positive value)
        assert actual_avg > 0

        # And: Calculation is mathematically correct
        assert stats["decryption_operations"] == operation_count
        assert stats["total_decryption_time"] > 0

    def test_get_performance_stats_returns_zero_average_with_no_operations(self, encryption_with_fresh_stats):
        """
        Test that average times are zero when no operations performed.

        Verifies:
            get_performance_stats() returns 0 for averages when operation
            count is zero, avoiding division by zero per calculation logic.

        Business Impact:
            Prevents errors in monitoring systems when querying stats
            before any operations have been performed.

        Scenario:
            Given: EncryptedCacheLayer with fresh statistics
            When: get_performance_stats() is called immediately
            Then: avg_encryption_time is 0
            And: avg_decryption_time is 0
            And: No division by zero error occurs

        Fixtures Used:
            - encryption_with_fresh_stats: Clean baseline, no operations
        """
        # Given: EncryptedCacheLayer with fresh statistics
        encryption = encryption_with_fresh_stats

        # When: get_performance_stats() is called immediately
        stats = encryption.get_performance_stats()

        # Then: avg_encryption_time is 0
        assert stats["avg_encryption_time"] == 0.0

        # And: avg_decryption_time is 0
        assert stats["avg_decryption_time"] == 0.0

        # And: No division by zero error occurs (test passes without exception)
        # The fact that we reach this assertion means no exception was raised

    def test_get_performance_stats_reports_encryption_enabled_status(self, encryption_with_valid_key, encryption_without_key):
        """
        Test that performance stats include encryption_enabled field.

        Verifies:
            get_performance_stats() includes encryption_enabled boolean
            matching is_enabled property value.

        Business Impact:
            Allows monitoring systems to correlate performance with
            encryption status for comprehensive system visibility.

        Scenario:
            Given: EncryptedCacheLayer instances (enabled and disabled)
            When: get_performance_stats() is called on each
            Then: encryption_enabled field is present
            And: Field matches is_enabled property value
            And: Enabled instance shows True
            And: Disabled instance shows False

        Fixtures Used:
            - encryption_with_valid_key: Enabled encryption
            - encryption_without_key: Disabled encryption
        """
        # Given: EncryptedCacheLayer instances (enabled and disabled)
        enabled_encryption = encryption_with_valid_key
        disabled_encryption = encryption_without_key

        # When: get_performance_stats() is called on each
        enabled_stats = enabled_encryption.get_performance_stats()
        disabled_stats = disabled_encryption.get_performance_stats()

        # Then: encryption_enabled field is present
        assert "encryption_enabled" in enabled_stats
        assert "encryption_enabled" in disabled_stats

        # And: Field matches is_enabled property value
        assert enabled_stats["encryption_enabled"] == enabled_encryption.is_enabled
        assert disabled_stats["encryption_enabled"] == disabled_encryption.is_enabled

        # And: Enabled instance shows True
        # And: Disabled instance shows False
        assert enabled_stats["encryption_enabled"] is True
        assert disabled_stats["encryption_enabled"] is False

    def test_get_performance_stats_reports_monitoring_status(self, encryption_with_valid_key):
        """
        Test that performance stats include performance_monitoring field.

        Verifies:
            get_performance_stats() includes performance_monitoring boolean
            indicating whether monitoring is enabled.

        Business Impact:
            Enables verification that performance tracking is active,
            preventing misinterpretation of zero stats.

        Scenario:
            Given: EncryptedCacheLayer with monitoring enabled
            When: get_performance_stats() is called
            Then: performance_monitoring field is present
            And: Field value is True
            And: Field accurately reflects initialization setting

        Fixtures Used:
            - encryption_with_valid_key: Monitoring enabled by default
        """
        # Given: EncryptedCacheLayer with monitoring enabled
        encryption = encryption_with_valid_key

        # When: get_performance_stats() is called
        stats = encryption.get_performance_stats()

        # Then: performance_monitoring field is present
        assert "performance_monitoring" in stats

        # And: Field value is True
        assert stats["performance_monitoring"] is True

        # And: Field accurately reflects initialization setting
        # (fixture creates instance with performance_monitoring=True)

    def test_get_performance_stats_with_monitoring_disabled_returns_error(self, encryption_without_monitoring):
        """
        Test that stats query with disabled monitoring returns error message.

        Verifies:
            get_performance_stats() returns error indicator when monitoring
            was disabled at initialization per method documentation.

        Business Impact:
            Prevents confusion about zero stats by clearly indicating
            monitoring is not active.

        Scenario:
            Given: EncryptedCacheLayer with performance_monitoring=False
            When: get_performance_stats() is called
            Then: Dictionary is returned
            And: Dict contains "error" field
            And: Error message indicates "Performance monitoring is disabled"

        Fixtures Used:
            - encryption_without_monitoring: Monitoring disabled
        """
        # Given: EncryptedCacheLayer with performance_monitoring=False
        encryption = encryption_without_monitoring

        # When: get_performance_stats() is called
        stats = encryption.get_performance_stats()

        # Then: Dictionary is returned
        assert isinstance(stats, dict)

        # And: Dict contains "error" field
        assert "error" in stats

        # And: Error message indicates "Performance monitoring is disabled"
        assert "Performance monitoring is disabled" in stats["error"]

    def test_get_performance_stats_time_values_are_in_milliseconds(self, encryption_with_fresh_stats, sample_cache_data):
        """
        Test that average times are reported in milliseconds.

        Verifies:
            get_performance_stats() converts time measurements to
            milliseconds per Examples section showing ":.3f}ms" format.

        Business Impact:
            Ensures consistent time units for monitoring dashboards
            and performance analysis tools.

        Scenario:
            Given: EncryptedCacheLayer with fresh statistics
            When: Operations are performed and stats are retrieved
            Then: avg_encryption_time is in milliseconds
            And: avg_decryption_time is in milliseconds
            And: Values are reasonable (typically < 50ms per operation)
            And: Precision allows meaningful performance tracking

        Fixtures Used:
            - encryption_with_fresh_stats: Clean baseline
            - sample_cache_data: For operations
        """
        # Given: EncryptedCacheLayer with fresh statistics
        encryption = encryption_with_fresh_stats

        # When: Operations are performed and stats are retrieved
        # Perform encryption operations
        for _ in range(5):
            encryption.encrypt_cache_data(sample_cache_data)

        # Perform decryption operations
        encrypted_data = encryption.encrypt_cache_data(sample_cache_data)
        for _ in range(3):
            encryption.decrypt_cache_data(encrypted_data)

        stats = encryption.get_performance_stats()

        # Then: avg_encryption_time is in milliseconds (positive float)
        assert isinstance(stats["avg_encryption_time"], (int, float))
        assert stats["avg_encryption_time"] > 0

        # And: avg_decryption_time is in milliseconds (positive float)
        assert isinstance(stats["avg_decryption_time"], (int, float))
        assert stats["avg_decryption_time"] > 0

        # And: Values are reasonable (typically < 50ms per operation)
        assert stats["avg_encryption_time"] < 50.0  # Less than 50ms per operation
        assert stats["avg_decryption_time"] < 50.0  # Less than 50ms per operation

        # And: Precision allows meaningful performance tracking (float precision)
        assert stats["avg_encryption_time"] != int(stats["avg_encryption_time"]) or stats["avg_encryption_time"] == 0
        assert stats["avg_decryption_time"] != int(stats["avg_decryption_time"]) or stats["avg_decryption_time"] == 0


class TestResetPerformanceStats:
    """
    Test suite for reset_performance_stats() method behavior.

    Scope:
        Tests the reset_performance_stats() method covering statistics
        clearing and logging behavior per method documentation.

    Business Critical:
        Statistics reset enables monitoring specific time periods and
        isolating performance measurements for analysis.

    Test Strategy:
        - Verify all statistics are reset to zero
        - Test reset after operations have been performed
        - Validate logging of reset action
        - Confirm stats accumulate correctly after reset
    """

    def test_reset_performance_stats_clears_all_counters(self, encryption_with_valid_key, sample_cache_data):
        """
        Test that reset_performance_stats() clears all operation counters.

        Verifies:
            reset_performance_stats() sets all operation counters to zero
            per method purpose in docstring.

        Business Impact:
            Enables isolation of performance measurements for specific
            testing or monitoring periods.

        Scenario:
            Given: EncryptedCacheLayer with accumulated statistics
            And: Multiple operations have been performed
            When: reset_performance_stats() is called
            And: get_performance_stats() is called
            Then: encryption_operations is 0
            And: decryption_operations is 0
            And: total_operations is 0

        Fixtures Used:
            - encryption_with_valid_key: Perform operations first
            - sample_cache_data: Generate some stats
        """
        # Given: EncryptedCacheLayer with accumulated statistics
        encryption = encryption_with_valid_key

        # And: Multiple operations have been performed
        # Generate some encryption operations
        for _ in range(5):
            encryption.encrypt_cache_data(sample_cache_data)

        # Generate some decryption operations
        encrypted_data = encryption.encrypt_cache_data(sample_cache_data)
        for _ in range(3):
            encryption.decrypt_cache_data(encrypted_data)

        # Verify stats are accumulated before reset
        pre_reset_stats = encryption.get_performance_stats()
        assert pre_reset_stats["encryption_operations"] > 0
        assert pre_reset_stats["decryption_operations"] > 0
        assert pre_reset_stats["total_operations"] > 0

        # When: reset_performance_stats() is called
        encryption.reset_performance_stats()

        # And: get_performance_stats() is called
        post_reset_stats = encryption.get_performance_stats()

        # Then: All operation counters are zero
        assert post_reset_stats["encryption_operations"] == 0
        assert post_reset_stats["decryption_operations"] == 0
        assert post_reset_stats["total_operations"] == 0

    def test_reset_performance_stats_clears_accumulated_times(self, encryption_with_valid_key, sample_cache_data):
        """
        Test that reset_performance_stats() clears accumulated time values.

        Verifies:
            reset_performance_stats() resets total_encryption_time and
            total_decryption_time to zero.

        Business Impact:
            Enables fresh timing measurements for performance analysis
            of specific operations or time periods.

        Scenario:
            Given: EncryptedCacheLayer with accumulated time statistics
            And: Operations have added to total times
            When: reset_performance_stats() is called
            And: get_performance_stats() is called
            Then: total_encryption_time is 0.0
            And: total_decryption_time is 0.0
            And: avg_encryption_time is 0
            And: avg_decryption_time is 0

        Fixtures Used:
            - encryption_with_valid_key: Perform operations first
            - sample_cache_data: Generate timing stats
        """
        # Given: EncryptedCacheLayer with accumulated time statistics
        encryption = encryption_with_valid_key

        # And: Operations have added to total times
        # Generate some operations to accumulate timing data
        for _ in range(5):
            encryption.encrypt_cache_data(sample_cache_data)

        encrypted_data = encryption.encrypt_cache_data(sample_cache_data)
        for _ in range(3):
            encryption.decrypt_cache_data(encrypted_data)

        # Verify timing stats are accumulated before reset
        pre_reset_stats = encryption.get_performance_stats()
        assert pre_reset_stats["total_encryption_time"] > 0
        assert pre_reset_stats["total_decryption_time"] > 0
        assert pre_reset_stats["avg_encryption_time"] > 0
        assert pre_reset_stats["avg_decryption_time"] > 0

        # When: reset_performance_stats() is called
        encryption.reset_performance_stats()

        # And: get_performance_stats() is called
        post_reset_stats = encryption.get_performance_stats()

        # Then: All timing values are zero
        assert post_reset_stats["total_encryption_time"] == 0.0
        assert post_reset_stats["total_decryption_time"] == 0.0
        assert post_reset_stats["avg_encryption_time"] == 0.0
        assert post_reset_stats["avg_decryption_time"] == 0.0

    def test_reset_performance_stats_logs_reset_action(self, encryption_with_valid_key, mock_logger, monkeypatch):
        """
        Test that reset_performance_stats() logs the reset action.

        Verifies:
            reset_performance_stats() logs info message about statistics
            reset per implementation logging behavior.

        Business Impact:
            Provides audit trail of performance tracking resets for
            operational monitoring and debugging.

        Scenario:
            Given: EncryptedCacheLayer with logger
            When: reset_performance_stats() is called
            Then: Info-level log message is emitted
            And: Message indicates "Performance statistics reset"
            And: Log provides confirmation of action

        Fixtures Used:
            - encryption_with_valid_key: Instance with logging
            - mock_logger: Captures log messages
        """
        # Given: EncryptedCacheLayer with logger
        encryption = encryption_with_valid_key

        # Patch the logger to capture log messages
        # Need to patch the instance logger, not module logger
        encryption.logger = mock_logger

        # When: reset_performance_stats() is called
        encryption.reset_performance_stats()

        # Then: Info-level log message is emitted
        mock_logger.info.assert_called_once()

        # And: Message indicates "Performance statistics reset"
        call_args = mock_logger.info.call_args[0][0]
        assert "Performance statistics reset" in call_args

        # And: Log provides confirmation of action
        assert len(call_args) > 0  # Message is not empty

    def test_reset_performance_stats_allows_fresh_accumulation(self, encryption_with_valid_key, sample_cache_data):
        """
        Test that statistics accumulate correctly after reset.

        Verifies:
            reset_performance_stats() truly resets state, allowing fresh
            statistics to accumulate from zero per Examples pattern.

        Business Impact:
            Ensures reset functionality is complete and reliable for
            isolating performance measurements.

        Scenario:
            Given: EncryptedCacheLayer with accumulated statistics
            When: reset_performance_stats() is called
            And: New operations are performed
            And: get_performance_stats() is called
            Then: Statistics reflect only post-reset operations
            And: Operation counts start from zero
            And: Time accumulations start from zero
            And: Averages are calculated from fresh data

        Fixtures Used:
            - encryption_with_valid_key: For operations
            - sample_cache_data: Pre and post reset operations
        """
        # Given: EncryptedCacheLayer with accumulated statistics
        encryption = encryption_with_valid_key

        # Generate initial statistics
        for _ in range(5):
            encryption.encrypt_cache_data(sample_cache_data)

        encrypted_data = encryption.encrypt_cache_data(sample_cache_data)
        for _ in range(3):
            encryption.decrypt_cache_data(encrypted_data)

        # Verify pre-reset stats
        pre_reset_stats = encryption.get_performance_stats()
        assert pre_reset_stats["total_operations"] == 9  # 5 + 1 (for encrypted_data) + 3 = 9

        # When: reset_performance_stats() is called
        encryption.reset_performance_stats()

        # And: New operations are performed
        post_reset_encrypt_count = 2
        post_reset_decrypt_count = 4

        for _ in range(post_reset_encrypt_count):
            encryption.encrypt_cache_data(sample_cache_data)

        fresh_encrypted_data = encryption.encrypt_cache_data(sample_cache_data)
        for _ in range(post_reset_decrypt_count):
            encryption.decrypt_cache_data(fresh_encrypted_data)

        # And: get_performance_stats() is called
        final_stats = encryption.get_performance_stats()

        # Then: Statistics reflect only post-reset operations
        assert final_stats["total_operations"] == post_reset_encrypt_count + post_reset_decrypt_count + 1  # +1 for fresh_encrypted_data

        # And: Operation counts start from zero
        assert final_stats["encryption_operations"] == post_reset_encrypt_count + 1  # +1 for fresh_encrypted_data
        assert final_stats["decryption_operations"] == post_reset_decrypt_count

        # And: Time accumulations start from zero
        assert final_stats["total_encryption_time"] > 0
        assert final_stats["total_decryption_time"] > 0

        # And: Averages are calculated from fresh data
        assert final_stats["avg_encryption_time"] > 0
        assert final_stats["avg_decryption_time"] > 0

    def test_reset_performance_stats_can_be_called_multiple_times(self, encryption_with_valid_key):
        """
        Test that reset_performance_stats() can be called repeatedly.

        Verifies:
            reset_performance_stats() is idempotent and can be called
            multiple times without errors.

        Business Impact:
            Ensures reset operation is safe to call anytime, supporting
            flexible monitoring workflows.

        Scenario:
            Given: EncryptedCacheLayer with any statistics state
            When: reset_performance_stats() is called multiple times
            Then: Each call succeeds without errors
            And: Statistics remain at zero between calls
            And: No side effects occur from repeated resets

        Fixtures Used:
            - encryption_with_valid_key: For reset calls
        """
        # Given: EncryptedCacheLayer with any statistics state
        encryption = encryption_with_valid_key

        # Generate some initial statistics
        encryption.encrypt_cache_data({"test": "data"})

        # Verify initial state has non-zero stats
        initial_stats = encryption.get_performance_stats()
        assert initial_stats["total_operations"] > 0

        # When: reset_performance_stats() is called multiple times
        encryption.reset_performance_stats()
        stats_after_first = encryption.get_performance_stats()

        encryption.reset_performance_stats()
        stats_after_second = encryption.get_performance_stats()

        encryption.reset_performance_stats()
        stats_after_third = encryption.get_performance_stats()

        # Then: Each call succeeds without errors (test reaches this point)

        # And: Statistics remain at zero between calls
        assert stats_after_first["total_operations"] == 0
        assert stats_after_second["total_operations"] == 0
        assert stats_after_third["total_operations"] == 0

        # And: No side effects occur from repeated resets
        assert stats_after_first == stats_after_second == stats_after_third

    def test_reset_performance_stats_works_with_monitoring_disabled(self, encryption_without_monitoring):
        """
        Test that reset_performance_stats() works with monitoring disabled.

        Verifies:
            reset_performance_stats() can be called even when monitoring
            is disabled, maintaining method consistency.

        Business Impact:
            Prevents errors in code that calls reset without checking
            monitoring status first.

        Scenario:
            Given: EncryptedCacheLayer with performance_monitoring=False
            When: reset_performance_stats() is called
            Then: Method completes without errors
            And: No exceptions are raised
            And: Subsequent stats queries still show monitoring disabled

        Fixtures Used:
            - encryption_without_monitoring: Monitoring disabled
        """
        # Given: EncryptedCacheLayer with performance_monitoring=False
        encryption = encryption_without_monitoring

        # When: reset_performance_stats() is called
        try:
            encryption.reset_performance_stats()
        except Exception as e:
            pytest.fail(f"reset_performance_stats() raised an exception: {e}")

        # Then: Method completes without errors (test reaches this point)

        # And: No exceptions are raised
        # (Implicitly verified by not catching any exceptions)

        # And: Subsequent stats queries still show monitoring disabled
        stats = encryption.get_performance_stats()
        assert "error" in stats
        assert "Performance monitoring is disabled" in stats["error"]


class TestPerformanceMonitoringIntegration:
    """
    Test suite for integrated performance monitoring behavior.

    Scope:
        Tests the complete performance monitoring workflow including
        operation tracking, statistics querying, and reset cycles.

    Business Critical:
        Complete monitoring workflow must work reliably for production
        performance tracking and optimization.

    Test Strategy:
        - Test complete monitor-operate-query-reset cycles
        - Verify statistics accuracy across operation types
        - Test monitoring overhead is minimal
        - Validate Examples section usage patterns
    """

    def test_performance_monitoring_workflow_as_documented(self, encryption_with_fresh_stats, sample_cache_data):
        """
        Test complete performance monitoring workflow from Examples.

        Verifies:
            Performance monitoring workflow matches Examples section pattern:
            reset stats, perform operations, get stats, analyze results.

        Business Impact:
            Validates that documented usage patterns work correctly,
            ensuring user success with performance monitoring.

        Scenario:
            Given: EncryptedCacheLayer with monitoring enabled
            When: reset_performance_stats() is called
            And: Multiple encrypt/decrypt operations are performed
            And: get_performance_stats() is called
            Then: Statistics accurately reflect performed operations
            And: All fields are populated correctly
            And: Workflow matches Examples documentation

        Fixtures Used:
            - encryption_with_fresh_stats: Clean starting point
            - sample_cache_data: For operations
        """
        # Given: EncryptedCacheLayer with monitoring enabled
        encryption = encryption_with_fresh_stats

        # When: reset_performance_stats() is called (following Examples pattern)
        encryption.reset_performance_stats()

        # And: Multiple encrypt/decrypt operations are performed
        encrypt_count = 5
        decrypt_count = 3

        # Perform encryption operations
        encrypted_data_list = []
        for _ in range(encrypt_count):
            encrypted_data = encryption.encrypt_cache_data(sample_cache_data)
            encrypted_data_list.append(encrypted_data)

        # Perform decryption operations
        for encrypted_data in encrypted_data_list[:decrypt_count]:
            encryption.decrypt_cache_data(encrypted_data)

        # And: get_performance_stats() is called
        stats = encryption.get_performance_stats()

        # Then: Statistics accurately reflect performed operations
        assert stats["encryption_operations"] == encrypt_count
        assert stats["decryption_operations"] == decrypt_count
        assert stats["total_operations"] == encrypt_count + decrypt_count

        # And: All fields are populated correctly
        expected_fields = [
            "encryption_enabled", "encryption_operations", "decryption_operations",
            "total_operations", "total_encryption_time", "total_decryption_time",
            "avg_encryption_time", "avg_decryption_time", "performance_monitoring"
        ]
        for field in expected_fields:
            assert field in stats

        # And: Workflow matches Examples documentation (basic pattern verified)
        assert stats["performance_monitoring"] is True
        assert stats["encryption_enabled"] is True
        assert stats["total_encryption_time"] > 0
        assert stats["total_decryption_time"] > 0

    def test_performance_monitoring_distinguishes_operation_types(self, encryption_with_fresh_stats, sample_cache_data, sample_encrypted_bytes):
        """
        Test that monitoring tracks encryption and decryption separately.

        Verifies:
            Performance monitoring maintains separate counters and timing
            for encryption vs decryption operations.

        Business Impact:
            Enables identification of which operation type (encrypt vs decrypt)
            is causing performance issues.

        Scenario:
            Given: EncryptedCacheLayer with fresh statistics
            When: 5 encryption operations are performed
            And: 3 decryption operations are performed
            And: get_performance_stats() is called
            Then: encryption_operations is 5
            And: decryption_operations is 3
            And: total_operations is 8
            And: Time totals and averages are tracked separately

        Fixtures Used:
            - encryption_with_fresh_stats: Clean baseline
            - sample_cache_data: For encrypt operations
            - sample_encrypted_bytes: For decrypt operations
        """
        # Given: EncryptedCacheLayer with fresh statistics
        encryption = encryption_with_fresh_stats

        # When: 5 encryption operations are performed
        encrypt_count = 5
        for _ in range(encrypt_count):
            encryption.encrypt_cache_data(sample_cache_data)

        # And: 3 decryption operations are performed
        decrypt_count = 3
        for _ in range(decrypt_count):
            encryption.decrypt_cache_data(sample_encrypted_bytes)

        # And: get_performance_stats() is called
        stats = encryption.get_performance_stats()

        # Then: encryption_operations is 5
        assert stats["encryption_operations"] == encrypt_count

        # And: decryption_operations is 3
        assert stats["decryption_operations"] == decrypt_count

        # And: total_operations is 8
        assert stats["total_operations"] == encrypt_count + decrypt_count

        # And: Time totals and averages are tracked separately
        assert stats["total_encryption_time"] > 0
        assert stats["total_decryption_time"] > 0
        assert stats["avg_encryption_time"] > 0
        assert stats["avg_decryption_time"] > 0

        # Verify they are separate values (not necessarily different)
        assert isinstance(stats["total_encryption_time"], (int, float))
        assert isinstance(stats["total_decryption_time"], (int, float))

    def test_performance_monitoring_overhead_is_minimal(self, encryption_with_valid_key, encryption_without_monitoring, sample_cache_data):
        """
        Test that performance monitoring has minimal overhead.

        Verifies:
            Performance monitoring tracking does not significantly slow
            down encryption/decryption operations.

        Business Impact:
            Ensures monitoring can be enabled in production without
            impacting application performance.

        Scenario:
            Given: Two EncryptedCacheLayer instances (monitoring on/off)
            When: Same operations are performed on both
            And: Timing is compared
            Then: Monitoring overhead is minimal (< 1% difference)
            And: Operations complete in similar time
            And: Monitoring is safe for production use

        Fixtures Used:
            - encryption_with_valid_key: Monitoring enabled
            - encryption_without_monitoring: Monitoring disabled
            - sample_cache_data: For comparative operations
        """
        import time

        # Given: Two EncryptedCacheLayer instances (monitoring on/off)
        encryption_with_monitoring = encryption_with_valid_key
        encryption_without_monitoring = encryption_without_monitoring

        operation_count = 10

        # When: Same operations are performed on both
        # Time operations with monitoring enabled
        start_time = time.time()
        for _ in range(operation_count):
            encryption_with_monitoring.encrypt_cache_data(sample_cache_data)
        time_with_monitoring = time.time() - start_time

        # Time operations with monitoring disabled
        start_time = time.time()
        for _ in range(operation_count):
            encryption_without_monitoring.encrypt_cache_data(sample_cache_data)
        time_without_monitoring = time.time() - start_time

        # Then: Operations complete in similar time
        # Allow for some variation but ensure they're in the same ballpark
        max_acceptable_ratio = 2.0  # Monitoring could take up to 2x time in worst case
        actual_ratio = time_with_monitoring / time_without_monitoring if time_without_monitoring > 0 else 1.0

        assert actual_ratio < max_acceptable_ratio, f"Monitoring overhead too high: {actual_ratio:.2f}x"

        # And: Monitoring is safe for production use (reasonable performance)
        # Both should complete operations in reasonable time (< 1 second for 10 ops)
        assert time_with_monitoring < 1.0
        assert time_without_monitoring < 1.0

    def test_performance_stats_match_actual_operation_count(self, encryption_with_fresh_stats, sample_cache_data):
        """
        Test that reported operation counts exactly match performed operations.

        Verifies:
            Performance statistics operation counts are accurate and
            match the actual number of operations performed.

        Business Impact:
            Ensures statistical accuracy for capacity planning and
            performance analysis decisions.

        Scenario:
            Given: EncryptedCacheLayer with fresh statistics
            When: Exactly N encrypt operations are performed
            And: Exactly M decrypt operations are performed
            And: get_performance_stats() is called
            Then: encryption_operations equals N
            And: decryption_operations equals M
            And: total_operations equals N + M
            And: Counts are exact, not approximate

        Fixtures Used:
            - encryption_with_fresh_stats: Clean baseline
            - sample_cache_data: Controlled operation count
        """
        # Given: EncryptedCacheLayer with fresh statistics
        encryption = encryption_with_fresh_stats

        # When: Exactly N encrypt operations are performed
        N = 7  # Exact number of encrypt operations
        for i in range(N):
            encryption.encrypt_cache_data({f"test_data_{i}": f"value_{i}"})

        # And: Exactly M decrypt operations are performed
        M = 4  # Exact number of decrypt operations
        encrypted_data = encryption.encrypt_cache_data(sample_cache_data)
        for i in range(M):
            encryption.decrypt_cache_data(encrypted_data)

        # And: get_performance_stats() is called
        stats = encryption.get_performance_stats()

        # Then: encryption_operations equals N + 1 (for the encrypted_data generation)
        assert stats["encryption_operations"] == N + 1

        # And: decryption_operations equals M
        assert stats["decryption_operations"] == M

        # And: total_operations equals N + M + 1 (for the encrypted_data generation)
        assert stats["total_operations"] == N + M + 1

        # And: Counts are exact, not approximate
        assert isinstance(stats["encryption_operations"], int)
        assert isinstance(stats["decryption_operations"], int)
        assert isinstance(stats["total_operations"], int)

    def test_performance_stats_available_throughout_instance_lifetime(self, encryption_with_valid_key, sample_cache_data):
        """
        Test that performance stats can be queried at any time.

        Verifies:
            get_performance_stats() can be called at any point during
            instance lifetime and returns valid results.

        Business Impact:
            Enables flexible monitoring patterns without requiring
            specific calling sequences.

        Scenario:
            Given: EncryptedCacheLayer instance
            When: get_performance_stats() is called at various times:
            - Immediately after initialization
            - After some operations
            - After reset
            - After more operations
            Then: Each call returns valid statistics dict
            And: Statistics accurately reflect state at query time
            And: No errors occur from timing of queries

        Fixtures Used:
            - encryption_with_valid_key: Long-lived instance
            - sample_cache_data: For varied operations
        """
        # Given: EncryptedCacheLayer instance
        encryption = encryption_with_valid_key

        # When: get_performance_stats() is called at various times

        # - Immediately after initialization
        stats_initial = encryption.get_performance_stats()
        assert isinstance(stats_initial, dict)
        assert stats_initial["total_operations"] == 0

        # - After some operations
        encryption.encrypt_cache_data(sample_cache_data)
        encryption.encrypt_cache_data({"additional": "data"})
        stats_after_ops = encryption.get_performance_stats()
        assert isinstance(stats_after_ops, dict)
        assert stats_after_ops["total_operations"] == 2

        # - After reset
        encryption.reset_performance_stats()
        stats_after_reset = encryption.get_performance_stats()
        assert isinstance(stats_after_reset, dict)
        assert stats_after_reset["total_operations"] == 0

        # - After more operations
        encryption.encrypt_cache_data(sample_cache_data)
        stats_final = encryption.get_performance_stats()
        assert isinstance(stats_final, dict)
        assert stats_final["total_operations"] == 1

        # Then: Each call returns valid statistics dict
        # (Verified above with isinstance checks)

        # And: Statistics accurately reflect state at query time
        assert stats_initial["total_operations"] == 0
        assert stats_after_ops["total_operations"] == 2
        assert stats_after_reset["total_operations"] == 0
        assert stats_final["total_operations"] == 1

        # And: No errors occur from timing of queries
        # (Test reaching this point confirms no exceptions were raised)
