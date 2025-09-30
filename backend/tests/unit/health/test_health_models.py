"""
Unit tests for health monitoring data models and enums.

Tests the data structures used for health reporting including status enums,
component status dataclasses, and system health aggregation models.

Test Coverage:
    - HealthStatus enum values and behavior
    - ComponentStatus dataclass creation and attributes
    - SystemHealthStatus dataclass creation and attributes
    - HealthCheckError exception hierarchy
"""

import pytest
import time
from app.infrastructure.monitoring.health import (
    HealthStatus,
    ComponentStatus,
    SystemHealthStatus,
    HealthCheckError,
    HealthCheckTimeoutError,
)


class TestHealthStatusEnum:
    """
    Test suite for HealthStatus enumeration.

    Scope:
        - Enum value definitions
        - String value representations
        - Enum comparison behavior

    Business Critical:
        Consistent health status values ensure reliable monitoring and alerting
        across all system components.
    """

    def test_health_status_has_healthy_value(self):
        """
        Test that HealthStatus includes HEALTHY value.

        Verifies:
            HEALTHY status is available per HealthStatus docstring Values specification.

        Business Impact:
            Enables signaling of fully operational components.

        Scenario:
            Given: HealthStatus enumeration
            When: HealthStatus.HEALTHY is accessed
            Then: Value is available
            And: String representation is "healthy"

        Fixtures Used:
            None - tests enum definition
        """
        assert HealthStatus.HEALTHY is not None
        assert HealthStatus.HEALTHY.value == "healthy"

    def test_health_status_has_degraded_value(self):
        """
        Test that HealthStatus includes DEGRADED value.

        Verifies:
            DEGRADED status is available per HealthStatus docstring Values specification.

        Business Impact:
            Enables signaling of operational but reduced functionality.

        Scenario:
            Given: HealthStatus enumeration
            When: HealthStatus.DEGRADED is accessed
            Then: Value is available
            And: String representation is "degraded"

        Fixtures Used:
            None - tests enum definition
        """
        assert HealthStatus.DEGRADED is not None
        assert HealthStatus.DEGRADED.value == "degraded"

    def test_health_status_has_unhealthy_value(self):
        """
        Test that HealthStatus includes UNHEALTHY value.

        Verifies:
            UNHEALTHY status is available per HealthStatus docstring Values specification.

        Business Impact:
            Enables signaling of critical component failures.

        Scenario:
            Given: HealthStatus enumeration
            When: HealthStatus.UNHEALTHY is accessed
            Then: Value is available
            And: String representation is "unhealthy"

        Fixtures Used:
            None - tests enum definition
        """
        assert HealthStatus.UNHEALTHY is not None
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_health_status_values_are_lowercase_strings(self):
        """
        Test that HealthStatus enum values are lowercase strings.

        Verifies:
            Enum values follow consistent naming convention for API responses.

        Business Impact:
            Ensures consistent JSON serialization in health endpoints.

        Scenario:
            Given: HealthStatus enumeration
            When: Enum values are examined
            Then: HealthStatus.HEALTHY.value == "healthy"
            And: HealthStatus.DEGRADED.value == "degraded"
            And: HealthStatus.UNHEALTHY.value == "unhealthy"
            And: All values are lowercase strings

        Fixtures Used:
            None - tests enum value format
        """
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        for status in HealthStatus:
            assert isinstance(status.value, str)
            assert status.value.islower()

    def test_health_status_supports_equality_comparison(self):
        """
        Test that HealthStatus enum supports equality comparison.

        Verifies:
            Enum values can be compared for equality in health logic.

        Business Impact:
            Enables status comparison in aggregation and filtering logic.

        Scenario:
            Given: HealthStatus enum values
            When: Equality comparisons are performed
            Then: HealthStatus.HEALTHY == HealthStatus.HEALTHY
            And: HealthStatus.HEALTHY != HealthStatus.DEGRADED
            And: Comparison operations work as expected

        Fixtures Used:
            None - tests enum comparison
        """
        assert HealthStatus.HEALTHY == HealthStatus.HEALTHY
        assert HealthStatus.HEALTHY != HealthStatus.DEGRADED
        assert HealthStatus.DEGRADED != HealthStatus.UNHEALTHY


class TestComponentStatus:
    """
    Test suite for ComponentStatus dataclass.

    Scope:
        - Dataclass instantiation
        - Required and optional attributes
        - Default values
        - Attribute types

    Business Critical:
        ComponentStatus provides standardized health reporting structure
        for all monitored components.
    """

    def test_component_status_creates_with_required_fields(self):
        """
        Test that ComponentStatus can be created with required fields.

        Verifies:
            ComponentStatus instantiation with name and status per
            ComponentStatus dataclass definition.

        Business Impact:
            Enables basic component health reporting.

        Scenario:
            Given: Component name "database" and HealthStatus.HEALTHY
            When: ComponentStatus is instantiated with these fields
            Then: Instance is created successfully
            And: name attribute is "database"
            And: status attribute is HealthStatus.HEALTHY

        Fixtures Used:
            None - tests dataclass instantiation
        """
        status = ComponentStatus(name="database", status=HealthStatus.HEALTHY)
        assert status.name == "database"
        assert status.status == HealthStatus.HEALTHY

    def test_component_status_includes_optional_message_field(self):
        """
        Test that ComponentStatus accepts optional message field.

        Verifies:
            Message field for diagnostic information per ComponentStatus
            Attributes specification.

        Business Impact:
            Enables detailed status descriptions for troubleshooting.

        Scenario:
            Given: Component name, status, and message "Connection successful"
            When: ComponentStatus is instantiated with message
            Then: Instance is created successfully
            And: message attribute contains the provided string

        Fixtures Used:
            None - tests optional field
        """
        status = ComponentStatus(name="db", status=HealthStatus.HEALTHY, message="OK")
        assert status.message == "OK"

    def test_component_status_message_defaults_to_empty_string(self):
        """
        Test that ComponentStatus message field defaults to empty string.

        Verifies:
            Default message value per ComponentStatus dataclass definition.

        Business Impact:
            Simplifies ComponentStatus creation when no message needed.

        Scenario:
            Given: Component name and status only
            When: ComponentStatus is instantiated without message
            Then: Instance is created successfully
            And: message attribute is empty string ""

        Fixtures Used:
            None - tests default value
        """
        status = ComponentStatus(name="db", status=HealthStatus.HEALTHY)
        assert status.message == ""

    def test_component_status_includes_response_time_field(self):
        """
        Test that ComponentStatus includes response_time_ms field.

        Verifies:
            Response time tracking per ComponentStatus Attributes specification.

        Business Impact:
            Provides performance metrics for health monitoring.

        Scenario:
            Given: Component information and response_time_ms=45.2
            When: ComponentStatus is instantiated with response time
            Then: Instance is created successfully
            And: response_time_ms attribute is 45.2

        Fixtures Used:
            None - tests timing field
        """
        status = ComponentStatus(name="db", status=HealthStatus.HEALTHY, response_time_ms=45.2)
        assert status.response_time_ms == 45.2

    def test_component_status_response_time_defaults_to_zero(self):
        """
        Test that ComponentStatus response_time_ms defaults to 0.0.

        Verifies:
            Default response time value per ComponentStatus dataclass definition.

        Business Impact:
            Simplifies ComponentStatus creation with sensible default.

        Scenario:
            Given: Component name and status only
            When: ComponentStatus is instantiated without response_time_ms
            Then: Instance is created successfully
            And: response_time_ms attribute is 0.0

        Fixtures Used:
            None - tests default value
        """
        status = ComponentStatus(name="db", status=HealthStatus.HEALTHY)
        assert status.response_time_ms == 0.0

    def test_component_status_includes_optional_metadata_field(self):
        """
        Test that ComponentStatus accepts optional metadata dictionary.

        Verifies:
            Metadata field for component-specific information per
            ComponentStatus Attributes specification.

        Business Impact:
            Enables detailed diagnostic information in health reports.

        Scenario:
            Given: Component information and metadata dictionary
            When: ComponentStatus is instantiated with metadata
            Then: Instance is created successfully
            And: metadata attribute contains the provided dictionary
            And: Metadata can include arbitrary component-specific data

        Fixtures Used:
            None - tests optional metadata
        """
        metadata = {"key": "value"}
        status = ComponentStatus(name="db", status=HealthStatus.HEALTHY, metadata=metadata)
        assert status.metadata == metadata

    def test_component_status_metadata_defaults_to_none(self):
        """
        Test that ComponentStatus metadata field defaults to None.

        Verifies:
            Default metadata value per ComponentStatus dataclass definition.

        Business Impact:
            Simplifies ComponentStatus creation when no metadata needed.

        Scenario:
            Given: Component name and status only
            When: ComponentStatus is instantiated without metadata
            Then: Instance is created successfully
            And: metadata attribute is None

        Fixtures Used:
            None - tests default value
        """
        status = ComponentStatus(name="db", status=HealthStatus.HEALTHY)
        assert status.metadata is None

    def test_component_status_supports_complete_instantiation(self):
        """
        Test that ComponentStatus can be fully instantiated with all fields.

        Verifies:
            Complete ComponentStatus creation per ComponentStatus Usage examples.

        Business Impact:
            Demonstrates comprehensive health reporting capabilities.

        Scenario:
            Given: All ComponentStatus fields provided:
                - name: "database"
                - status: HealthStatus.HEALTHY
                - message: "Connection successful"
                - response_time_ms: 45.2
                - metadata: {"connection_pool": "active", "query_test": "passed"}
            When: ComponentStatus is instantiated with all fields
            Then: Instance is created successfully
            And: All attributes match provided values
            And: Instance is ready for health reporting

        Fixtures Used:
            None - tests complete instantiation
        """
        metadata = {"connection_pool": "active", "query_test": "passed"}
        status = ComponentStatus(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Connection successful",
            response_time_ms=45.2,
            metadata=metadata
        )
        assert status.name == "database"
        assert status.status == HealthStatus.HEALTHY
        assert status.message == "Connection successful"
        assert status.response_time_ms == 45.2
        assert status.metadata == metadata

    def test_component_status_supports_dataclass_equality(self):
        """
        Test that ComponentStatus dataclass supports equality comparison.

        Verifies:
            Dataclass equality semantics for testing and comparison.

        Business Impact:
            Enables testing of health check results and component comparison.

        Scenario:
            Given: Two ComponentStatus instances with identical values
            When: Equality comparison is performed
            Then: Instances are equal
            And: ComponentStatus with different values are not equal

        Fixtures Used:
            None - tests dataclass equality
        """
        s1 = ComponentStatus(name="db", status=HealthStatus.HEALTHY)
        s2 = ComponentStatus(name="db", status=HealthStatus.HEALTHY)
        s3 = ComponentStatus(name="db", status=HealthStatus.DEGRADED)
        assert s1 == s2
        assert s1 != s3


class TestSystemHealthStatus:
    """
    Test suite for SystemHealthStatus dataclass.

    Scope:
        - Dataclass instantiation
        - Required fields (overall_status, components, timestamp)
        - Attribute types and relationships

    Business Critical:
        SystemHealthStatus provides aggregated system-wide health reporting
        for operational monitoring and alerting.
    """

    def test_system_health_status_creates_with_required_fields(self):
        """
        Test that SystemHealthStatus can be created with required fields.

        Verifies:
            SystemHealthStatus instantiation per SystemHealthStatus
            dataclass definition.

        Business Impact:
            Enables system-wide health reporting.

        Scenario:
            Given: overall_status, components list, and timestamp
            When: SystemHealthStatus is instantiated
            Then: Instance is created successfully
            And: overall_status attribute is set
            And: components attribute contains ComponentStatus list
            And: timestamp attribute is set

        Fixtures Used:
            None - tests dataclass instantiation
        """
        ts = time.time()
        status = SystemHealthStatus(
            overall_status=HealthStatus.HEALTHY,
            components=[],
            timestamp=ts
        )
        assert status.overall_status == HealthStatus.HEALTHY
        assert status.components == []
        assert status.timestamp == ts

    def test_system_health_status_includes_overall_status_field(self):
        """
        Test that SystemHealthStatus includes overall_status field.

        Verifies:
            Aggregated health status per SystemHealthStatus Attributes specification.

        Business Impact:
            Provides single-value system health indicator for monitoring.

        Scenario:
            Given: SystemHealthStatus with overall_status=HealthStatus.HEALTHY
            When: Instance is examined
            Then: overall_status field is HealthStatus.HEALTHY
            And: Field uses HealthStatus enum

        Fixtures Used:
            None - tests required field
        """
        status = SystemHealthStatus(overall_status=HealthStatus.DEGRADED, components=[], timestamp=time.time())
        assert status.overall_status == HealthStatus.DEGRADED
        assert isinstance(status.overall_status, HealthStatus)

    def test_system_health_status_includes_components_list(self):
        """
        Test that SystemHealthStatus includes components list.

        Verifies:
            Component status list per SystemHealthStatus Attributes specification.

        Business Impact:
            Provides detailed per-component health information.

        Scenario:
            Given: SystemHealthStatus with multiple ComponentStatus objects
            When: Instance is examined
            Then: components field is a list
            And: List contains ComponentStatus instances
            And: Each component's detailed status is accessible

        Fixtures Used:
            None - tests components list
        """
        components = [ComponentStatus(name="db", status=HealthStatus.HEALTHY)]
        status = SystemHealthStatus(overall_status=HealthStatus.HEALTHY, components=components, timestamp=time.time())
        assert isinstance(status.components, list)
        assert status.components[0].name == "db"

    def test_system_health_status_includes_timestamp_field(self):
        """
        Test that SystemHealthStatus includes timestamp field.

        Verifies:
            Timestamp for caching and monitoring per SystemHealthStatus
            Attributes specification.

        Business Impact:
            Enables cache validation and time-series monitoring.

        Scenario:
            Given: SystemHealthStatus with timestamp value
            When: Instance is examined
            Then: timestamp field is a float (Unix timestamp)
            And: Timestamp represents health check execution time

        Fixtures Used:
            None - tests timestamp field
        """
        ts = time.time()
        status = SystemHealthStatus(overall_status=HealthStatus.HEALTHY, components=[], timestamp=ts)
        assert isinstance(status.timestamp, float)
        assert status.timestamp == ts

    def test_system_health_status_supports_empty_components_list(self):
        """
        Test that SystemHealthStatus accepts empty components list.

        Verifies:
            Empty components list is valid per SystemHealthStatus usage patterns.

        Business Impact:
            Handles health monitoring before components are registered.

        Scenario:
            Given: overall_status and empty components list
            When: SystemHealthStatus is instantiated
            Then: Instance is created successfully
            And: components list is empty []
            And: overall_status still indicates system health

        Fixtures Used:
            None - tests edge case
        """
        status = SystemHealthStatus(overall_status=HealthStatus.HEALTHY, components=[], timestamp=time.time())
        assert status.components == []

    def test_system_health_status_supports_complete_instantiation(self):
        """
        Test that SystemHealthStatus can be fully instantiated with all data.

        Verifies:
            Complete system health reporting per SystemHealthStatus Usage examples.

        Business Impact:
            Demonstrates comprehensive system health monitoring capabilities.

        Scenario:
            Given: Complete system health data:
                - overall_status: HealthStatus.DEGRADED
                - components: [database HEALTHY, cache DEGRADED, ai_model HEALTHY]
                - timestamp: current Unix time
            When: SystemHealthStatus is instantiated
            Then: Instance is created successfully
            And: All attributes match provided values
            And: Instance ready for operational monitoring

        Fixtures Used:
            None - tests complete instantiation
        """
        components = [
            ComponentStatus(name="db", status=HealthStatus.HEALTHY),
            ComponentStatus(name="cache", status=HealthStatus.DEGRADED)
        ]
        ts = time.time()
        status = SystemHealthStatus(overall_status=HealthStatus.DEGRADED, components=components, timestamp=ts)
        assert status.overall_status == HealthStatus.DEGRADED
        assert status.components == components
        assert status.timestamp == ts

    def test_system_health_status_supports_dataclass_equality(self):
        """
        Test that SystemHealthStatus dataclass supports equality comparison.

        Verifies:
            Dataclass equality semantics for testing.

        Business Impact:
            Enables testing of aggregated health check results.

        Scenario:
            Given: Two SystemHealthStatus instances with identical values
            When: Equality comparison is performed
            Then: Instances are equal
            And: SystemHealthStatus with different values are not equal

        Fixtures Used:
            None - tests dataclass equality
        """
        ts = time.time()
        s1 = SystemHealthStatus(overall_status=HealthStatus.HEALTHY, components=[], timestamp=ts)
        s2 = SystemHealthStatus(overall_status=HealthStatus.HEALTHY, components=[], timestamp=ts)
        s3 = SystemHealthStatus(overall_status=HealthStatus.DEGRADED, components=[], timestamp=ts)
        assert s1 == s2
        assert s1 != s3


class TestHealthCheckExceptions:
    """
    Test suite for health check exception hierarchy.

    Scope:
        - HealthCheckError base exception
        - HealthCheckTimeoutError specialized exception
        - Exception inheritance
        - Exception instantiation and messages

    Business Critical:
        Exception hierarchy enables proper error handling and classification
        in health monitoring infrastructure.
    """

    def test_health_check_error_is_base_exception(self):
        """
        Test that HealthCheckError serves as base exception.

        Verifies:
            HealthCheckError is Exception subclass per HealthCheckError
            docstring specification.

        Business Impact:
            Provides foundation for health check error handling.

        Scenario:
            Given: HealthCheckError class
            When: Exception inheritance is examined
            Then: HealthCheckError inherits from Exception
            And: Can be caught as base health check exception type

        Fixtures Used:
            None - tests exception hierarchy
        """
        assert issubclass(HealthCheckError, Exception)

    def test_health_check_error_can_be_raised_with_message(self):
        """
        Test that HealthCheckError can be raised with contextual message.

        Verifies:
            Exception instantiation with message per HealthCheckError
            docstring specification.

        Business Impact:
            Enables informative error messages for troubleshooting.

        Scenario:
            Given: Error message "Health check infrastructure failed"
            When: HealthCheckError is raised with message
            Then: Exception can be caught
            And: Exception message is accessible
            And: Message provides context for debugging

        Fixtures Used:
            None - tests exception usage
        """
        with pytest.raises(HealthCheckError, match="failed") as exc_info:
            raise HealthCheckError("failed")
        assert str(exc_info.value) == "failed"

    def test_health_check_timeout_error_inherits_from_health_check_error(self):
        """
        Test that HealthCheckTimeoutError inherits from HealthCheckError.

        Verifies:
            Exception hierarchy per HealthCheckTimeoutError Behavior specification.

        Business Impact:
            Enables catching timeout errors as HealthCheckError or specifically.

        Scenario:
            Given: HealthCheckTimeoutError class
            When: Exception inheritance is examined
            Then: HealthCheckTimeoutError inherits from HealthCheckError
            And: Can be caught as HealthCheckError
            And: Can be caught specifically as HealthCheckTimeoutError

        Fixtures Used:
            None - tests exception inheritance
        """
        assert issubclass(HealthCheckTimeoutError, HealthCheckError)

    def test_health_check_timeout_error_can_be_raised_with_timing_context(self):
        """
        Test that HealthCheckTimeoutError can include timing information.

        Verifies:
            Timeout error with context per HealthCheckTimeoutError
            docstring specification.

        Business Impact:
            Provides timing context for performance troubleshooting.

        Scenario:
            Given: Timeout message with timing context
            When: HealthCheckTimeoutError is raised
            Then: Exception can be caught
            And: Exception message includes timeout details
            And: Message useful for debugging performance issues

        Fixtures Used:
            None - tests exception with context
        """
        with pytest.raises(HealthCheckTimeoutError, match="timed out after 100ms") as exc_info:
            raise HealthCheckTimeoutError("timed out after 100ms")
        assert "100ms" in str(exc_info.value)

    def test_health_check_timeout_error_distinguishable_from_base_error(self):
        """
        Test that HealthCheckTimeoutError can be distinguished from base error.

        Verifies:
            Specific timeout error handling per exception hierarchy design.

        Business Impact:
            Enables different handling for timeouts vs other health check errors
            (timeouts → DEGRADED, errors → UNHEALTHY).

        Scenario:
            Given: Both HealthCheckError and HealthCheckTimeoutError
            When: Exception type checking is performed
            Then: HealthCheckTimeoutError is distinguishable
            And: isinstance() correctly identifies timeout errors
            And: Allows specific handling for timeout scenarios

        Fixtures Used:
            None - tests exception discrimination
        """
        timeout_err = HealthCheckTimeoutError()
        base_err = HealthCheckError()
        assert isinstance(timeout_err, HealthCheckTimeoutError)
        assert isinstance(timeout_err, HealthCheckError)
        assert not isinstance(base_err, HealthCheckTimeoutError)

    def test_health_check_exceptions_support_try_except_handling(self):
        """
        Test that health check exceptions work with try/except blocks.

        Verifies:
            Exception handling patterns per HealthCheckError Usage examples.

        Business Impact:
            Enables proper error recovery in health monitoring code.

        Scenario:
            Given: Code that may raise HealthCheckError or HealthCheckTimeoutError
            When: Try/except blocks are used for error handling
            Then: Exceptions can be caught and handled appropriately
            And: Specific exception types can be distinguished
            And: Error messages are accessible for logging

        Fixtures Used:
            None - tests exception handling patterns
        """
        try:
            raise HealthCheckTimeoutError("timeout")
        except HealthCheckError as e:
            assert "timeout" in str(e)
            assert isinstance(e, HealthCheckTimeoutError)
        except Exception:
            pytest.fail("Did not catch specific exception")
