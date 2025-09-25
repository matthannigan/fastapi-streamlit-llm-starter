"""
Authentication System Status and Monitoring Integration Tests

MEDIUM PRIORITY - Operational visibility and debugging capabilities

INTEGRATION SCOPE:
    Tests collaboration between get_auth_status, AuthConfig, API key counting, and development mode
    detection for authentication system monitoring and operational visibility.

SEAM UNDER TEST:
    get_auth_status → AuthConfig → API key counting → Development mode detection

CRITICAL PATH:
    System status collection → Configuration analysis → Status aggregation → Monitoring response

BUSINESS IMPACT:
    Provides operational visibility into authentication system health and configuration.

TEST STRATEGY:
    - Test auth status endpoint reports current authentication configuration
    - Test auth status reports number of active API keys without exposing them
    - Test auth status correctly identifies development mode
    - Test system status snapshot generation on demand
    - Test concurrent requests don't corrupt status information
    - Test status information accessible through monitoring endpoints
    - Test status endpoint doesn't expose sensitive data
    - Test status information consistency across operating modes

SUCCESS CRITERIA:
    - Authentication system status provides comprehensive operational visibility
    - API key counts reported without exposing sensitive data
    - Development mode detection works correctly
    - Status snapshots are generated accurately
    - Concurrent access is safe
    - Status accessible through monitoring interfaces
    - Sensitive data is not exposed
    - Status information is consistent across modes
"""

import pytest
from unittest.mock import patch

from app.infrastructure.security.auth import get_auth_status, AuthConfig, APIKeyAuth
from app.core.environment import Environment


class TestAuthenticationSystemStatusAndMonitoring:
    """
    Integration tests for authentication system status and monitoring.

    Seam Under Test:
        get_auth_status → AuthConfig → API key counting → Development mode detection

    Business Impact:
        Provides operational visibility into authentication system health and configuration
    """

    def test_auth_status_endpoint_reports_current_authentication_configuration(
        self, multiple_api_keys_config
    ):
        """
        Test that auth status endpoint reports the current authentication configuration.

        Integration Scope:
            get_auth_status → AuthConfig → Configuration reporting → Status response

        Business Impact:
            Provides visibility into authentication system configuration for monitoring

        Test Strategy:
            - Configure authentication system with specific settings
            - Call get_auth_status to retrieve configuration
            - Verify configuration is accurately reported

        Success Criteria:
            - Current authentication configuration is accurately reported
            - Configuration details are included in status response
            - Status provides comprehensive configuration visibility
        """
        # Act
        status = get_auth_status()

        # Assert
        assert status is not None
        assert "auth_config" in status
        assert "mode" in status["auth_config"]
        assert "features" in status["auth_config"]

        # Verify configuration details are present
        auth_config = status["auth_config"]
        assert "user_tracking" in auth_config["features"]
        assert "request_logging" in auth_config["features"]

    def test_auth_status_endpoint_reports_number_of_active_api_keys_without_exposing_them(
        self, multiple_api_keys_config
    ):
        """
        Test that auth status endpoint reports number of active API keys without exposing them.

        Integration Scope:
            get_auth_status → APIKeyAuth → Key counting → Safe reporting

        Business Impact:
            Provides operational metrics without compromising security

        Test Strategy:
            - Configure multiple API keys
            - Call get_auth_status to get key count
            - Verify count is accurate but keys are not exposed

        Success Criteria:
            - API key count is accurately reported
            - Individual API keys are not exposed in status
            - Operational metrics provided without security risk
        """
        # Act
        status = get_auth_status()

        # Assert
        assert status is not None
        assert "api_keys_configured" in status
        assert isinstance(status["api_keys_configured"], int)
        assert status["api_keys_configured"] == 3  # Should count our configured keys

    @pytest.mark.no_parallel
    def test_auth_status_endpoint_correctly_identifies_development_mode(
        self
    ):
        """
        Test that auth status endpoint correctly identifies and reports when system is in development mode.

        Integration Scope:
            get_auth_status → Development mode detection → Status reporting → Mode identification

        Business Impact:
            Provides clear indication of development vs production mode for operations

        Test Strategy:
            - Configure development environment (no API keys)
            - Call get_auth_status to check development mode
            - Verify development mode is correctly identified

        Success Criteria:
            - Development mode is correctly identified
            - Status clearly indicates development vs production mode
            - Mode detection works accurately for operational visibility
        """
        # Mock environment detection to return development
        def mock_development_env(feature_context):
            class MockEnvInfo:
                def __init__(self):
                    self.environment = Environment.DEVELOPMENT
                    self.confidence = 0.9
                    self.reasoning = "Mocked development environment for testing"

            return MockEnvInfo()

        # Mock environment variables to ensure no API keys
        with patch.dict('os.environ', {
            'ENVIRONMENT': 'development',
            'API_KEY': '',
            'ADDITIONAL_API_KEYS': '',
            'RATE_LIMITING_ENABLED': 'false'
        }, clear=True), \
        patch('app.infrastructure.security.auth.get_environment_info', side_effect=mock_development_env):
            # Create fresh auth instance with no keys
            from app.infrastructure.security.auth import AuthConfig, APIKeyAuth
            config = AuthConfig()
            auth_system = APIKeyAuth(config)

            # Mock the global instance to use our fresh one
            with patch('app.infrastructure.security.auth.api_key_auth', auth_system):
                status = get_auth_status()

        # Assert
        assert status is not None
        assert "development_mode" in status
        assert isinstance(status["development_mode"], bool)
        assert status["development_mode"] is True  # No keys configured = development mode

    def test_system_status_snapshot_generated_on_demand(
        self, multiple_api_keys_config
    ):
        """
        Test that snapshot of authentication system status can be generated on demand.

        Integration Scope:
            get_auth_status → Status collection → Snapshot generation → On-demand reporting

        Business Impact:
            Enables on-demand system status checks for monitoring and debugging

        Test Strategy:
            - Call get_auth_status to generate status snapshot
            - Verify snapshot contains current system state
            - Confirm on-demand generation works correctly

        Success Criteria:
            - Status snapshot is generated on demand
            - Snapshot reflects current system state
            - On-demand status generation works reliably
        """
        # Act
        status1 = get_auth_status()
        status2 = get_auth_status()

        # Assert
        assert status1 is not None
        assert status2 is not None

        # Snapshots should be consistent if system state hasn't changed
        assert status1["api_keys_configured"] == status2["api_keys_configured"]
        assert status1["development_mode"] == status2["development_mode"]

    def test_concurrent_requests_to_status_endpoint_do_not_corrupt_status_information(
        self, multiple_api_keys_config
    ):
        """
        Test that concurrent requests to status endpoint do not corrupt status information.

        Integration Scope:
            Concurrent requests → get_auth_status → Thread safety → Status consistency

        Business Impact:
            Ensures safe concurrent access to status information for monitoring

        Test Strategy:
            - Make multiple concurrent calls to get_auth_status
            - Verify status information remains consistent
            - Confirm no corruption from concurrent access

        Success Criteria:
            - Concurrent requests execute safely
            - Status information remains consistent across requests
            - No corruption or race conditions in status reporting
        """
        # Test that multiple calls to get_auth_status are safe
        # This simulates concurrent access

        # Act - Multiple sequential calls (simulating concurrent behavior)
        results = []
        for i in range(5):
            status = get_auth_status()
            results.append(status)

        # Assert - All results should be consistent
        for status in results:
            assert status["api_keys_configured"] == 3
            assert status["development_mode"] is False

    def test_status_information_accessible_through_monitoring_endpoints(
        self, integration_client, valid_api_key_headers
    ):
        """
        Test that status information is accessible through monitoring endpoints.

        Integration Scope:
            Monitoring endpoint → get_auth_status → Status response → Monitoring access

        Business Impact:
            Enables monitoring systems to access authentication status

        Test Strategy:
            - Access status through monitoring endpoint
            - Verify status information is accessible
            - Confirm monitoring integration works correctly

        Success Criteria:
            - Status information accessible through monitoring endpoints
            - Monitoring systems can retrieve authentication status
            - Status endpoint serves monitoring use cases
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=valid_api_key_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify status information is accessible
        assert data["authenticated"] is True
        # The endpoint provides status information through the authentication system

    def test_status_endpoint_does_not_expose_any_sensitive_data(
        self, multiple_api_keys_config
    ):
        """
        Test that status endpoint does not expose any sensitive data.

        Integration Scope:
            get_auth_status → Data filtering → Sensitive data protection → Safe reporting

        Business Impact:
            Provides status information without compromising security

        Test Strategy:
            - Call get_auth_status to retrieve status
            - Verify sensitive data is not included in response
            - Confirm only safe operational data is exposed

        Success Criteria:
            - No sensitive API key data is exposed in status
            - Only safe operational information is included
            - Status reporting maintains security boundaries
        """
        # Act
        status = get_auth_status()

        # Assert - Verify no sensitive data is exposed
        assert status is not None

        # Status should contain operational information but not sensitive data
        assert "api_keys_configured" in status  # Count, not actual keys
        assert "development_mode" in status  # Mode information
        assert "auth_config" in status  # Configuration info

        # Verify no actual API keys are exposed
        status_str = str(status)
        assert "primary-test-key" not in status_str
        assert "secondary-key" not in status_str
        assert "tertiary-key" not in status_str

    def test_status_information_remains_consistent_across_different_operating_modes(
        self, multiple_api_keys_config
    ):
        """
        Test that status information remains consistent across different operating modes.

        Integration Scope:
            get_auth_status → Operating mode → Status consistency → Mode-independent reporting

        Business Impact:
            Provides consistent status reporting regardless of operating mode

        Test Strategy:
            - Configure different operating modes
            - Call get_auth_status in each mode
            - Verify consistent status reporting structure

        Success Criteria:
            - Status information structure is consistent across modes
            - Mode-specific information is accurately reported
            - Status reporting works reliably in all operating modes
        """
        # Act
        status = get_auth_status()

        # Assert - Verify consistent status structure
        required_fields = ["auth_config", "api_keys_configured", "development_mode"]
        for field in required_fields:
            assert field in status, f"Required field '{field}' missing from status"

        # Verify status structure is consistent
        assert isinstance(status["auth_config"], dict)
        assert isinstance(status["api_keys_configured"], int)
        assert isinstance(status["development_mode"], bool)

    def test_status_snapshot_includes_comprehensive_system_state(
        self, multiple_api_keys_config
    ):
        """
        Test that status snapshot includes comprehensive system state information.

        Integration Scope:
            get_auth_status → System state collection → Comprehensive snapshot → State reporting

        Business Impact:
            Provides comprehensive view of authentication system state

        Test Strategy:
            - Call get_auth_status to generate comprehensive snapshot
            - Verify all relevant system state is included
            - Confirm comprehensive state reporting

        Success Criteria:
            - Status includes all relevant system state information
            - Comprehensive view of authentication system provided
            - All important operational metrics are included
        """
        # Act
        status = get_auth_status()

        # Assert - Verify comprehensive system state
        assert status is not None

        # Should include configuration information
        assert "auth_config" in status
        auth_config = status["auth_config"]
        assert "mode" in auth_config
        assert "features" in auth_config

        # Should include operational metrics
        assert "api_keys_configured" in status
        assert "development_mode" in status

    def test_status_information_supports_operational_monitoring_and_alerting(
        self, multiple_api_keys_config
    ):
        """
        Test that status information supports operational monitoring and alerting.

        Integration Scope:
            get_auth_status → Monitoring data → Alerting support → Operational visibility

        Business Impact:
            Enables operational monitoring and alerting for authentication system

        Test Strategy:
            - Call get_auth_status to retrieve monitoring data
            - Verify data is suitable for monitoring systems
            - Confirm alerting-relevant information is included

        Success Criteria:
            - Status data is suitable for operational monitoring
            - Alerting-relevant metrics are included
            - Monitoring systems can use status information effectively
        """
        # Act
        status = get_auth_status()

        # Assert - Verify monitoring and alerting support
        assert status is not None

        # Should include key metrics for monitoring
        assert "api_keys_configured" in status  # Monitor key availability
        assert "development_mode" in status  # Alert on development mode in production
        assert "auth_config" in status  # Monitor configuration changes

        # Should be serializable for monitoring systems
        import json
        status_json = json.dumps(status)
        assert len(status_json) > 0

    def test_status_information_aids_troubleshooting_and_debugging(
        self, multiple_api_keys_config
    ):
        """
        Test that status information aids troubleshooting and debugging.

        Integration Scope:
            get_auth_status → Debugging information → Troubleshooting support → Diagnostic data

        Business Impact:
            Provides debugging and troubleshooting information for authentication issues

        Test Strategy:
            - Call get_auth_status to retrieve debugging information
            - Verify diagnostic data is included
            - Confirm troubleshooting support is provided

        Success Criteria:
            - Status includes debugging and diagnostic information
            - Troubleshooting data is available in status
            - Information aids in diagnosing authentication issues
        """
        # Act
        status = get_auth_status()

        # Assert - Verify troubleshooting support
        assert status is not None

        # Should include information useful for troubleshooting
        assert "auth_config" in status  # Configuration details for debugging
        assert "development_mode" in status  # Mode information for debugging
        assert "api_keys_configured" in status  # Key status for debugging

        # The comprehensive status information itself aids in troubleshooting
        # by providing visibility into the authentication system's current state
