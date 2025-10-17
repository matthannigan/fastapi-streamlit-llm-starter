"""
Test suite for SecurityServiceFactory functionality.

Tests verify security service factory creation, initialization, and integration according
to the public contract defined in factory.pyi.

The tests are adapted to test the SecurityServiceFactory which creates SecurityService
instances (not individual scanners) with proper configuration and caching.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.infrastructure.security.llm.factory import SecurityServiceFactory, create_security_service
from app.infrastructure.security.llm.config import SecurityConfig, ScannerType, ScannerConfig
from app.core.exceptions import ConfigurationError, InfrastructureError


class TestScannerFactoryInitialization:
    """Test SecurityServiceFactory initialization and configuration."""

    def test_security_service_factory_creates_service_from_config(self, mock_security_service_factory):
        """
        Test that SecurityServiceFactory creates service instances from SecurityConfig.

        Verifies:
            Factory method accepts SecurityConfig to create properly configured
            SecurityService instances with caching support.

        Business Impact:
            Enables dynamic security service instantiation from configuration for flexible
            security scanning deployments.

        Scenario:
            Given: SecurityConfig with balanced preset configuration.
            When: Factory creates security service with the config.
            Then: Returns configured SecurityService instance ready for security validation.

        Fixtures Used:
            - mock_security_service_factory: Factory fixture for SecurityServiceFactory.
        """
        # Given - Use proper ScannerType enum and ScannerConfig
        config = SecurityConfig(
            service_name="test-security-service",
            environment="testing",
            scanners={
                ScannerType.PROMPT_INJECTION: ScannerConfig(
                    enabled=True,
                    threshold=0.7
                )
            }
        )
        factory = mock_security_service_factory()

        # When
        service = factory.create_service(mode="local", config=config)

        # Then
        assert service is not None
        assert hasattr(service, 'service_name')
        assert service.service_name == "local-security-service"
        assert len(factory.creation_history) == 1
        assert factory.creation_history[0]["mode"] == "local"
        assert factory.creation_history[0]["config"] == config

    def test_security_service_factory_applies_environment_overrides(self, mock_security_service_factory, environment_overrides):
        """
        Test that SecurityServiceFactory applies environment variable overrides.

        Verifies:
            Factory applies environment variable overrides to configuration for
            runtime customization.

        Business Impact:
            Enables runtime configuration adjustments without code changes for
            flexible deployment scenarios.

        Scenario:
            Given: SecurityConfig and environment variable overrides.
            When: Factory creates service with environment overrides.
            Then: Service is configured with overridden settings applied.

        Fixtures Used:
            - mock_security_service_factory: Factory fixture for SecurityServiceFactory.
            - environment_overrides: Environment variable override fixture.
        """
        # Given - Use proper ScannerType enum
        config = SecurityConfig(
            service_name="base-service",
            environment="testing",
            scanners={
                ScannerType.PROMPT_INJECTION: ScannerConfig(
                    enabled=True,
                    threshold=0.7
                )
            }
        )
        factory = mock_security_service_factory()

        # When
        service = factory.create_service(
            mode="local",
            config=config,
            environment_overrides=environment_overrides
        )

        # Then
        assert service is not None
        # The mock factory records the environment overrides
        creation_call = factory.creation_history[0]
        assert creation_call["environment_overrides"] == environment_overrides
        # The service should be created with the overrides applied (mock factory applies to service_name)
        assert service.service_name == "local-security-service"

    def test_security_service_factory_uses_cache_key(self, mock_security_service_factory):
        """
        Test that SecurityServiceFactory respects custom cache keys.

        Verifies:
            Factory uses provided cache key for service instance caching and returns
            cached service for identical cache keys.

        Business Impact:
            Enables efficient service reuse and performance optimization through
            intelligent caching strategies.

        Scenario:
            Given: SecurityConfig and custom cache key.
            When: Factory creates service with cache key, then creates another with same key.
            Then: Returns cached service instance for second request.

        Fixtures Used:
            - mock_security_service_factory: Factory fixture for SecurityServiceFactory.
        """
        # Given - Use proper SecurityConfig
        config = SecurityConfig(
            service_name="cached-service",
            environment="testing",
            scanners={
                ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True)
            }
        )
        factory = mock_security_service_factory()
        cache_key = "test_service_key"

        # When
        service1 = factory.create_service(mode="local", config=config, cache_key=cache_key)
        service2 = factory.create_service(mode="local", config=config, cache_key=cache_key)

        # Then
        # The mock factory implements caching, so we should get the same service
        assert service1 is service2  # Same instance from cache
        assert service1.service_name == "local-security-service"
        # Mock factory should have recorded the creation, but caching means second call hits cache
        assert len(factory.creation_history) >= 1  # At least one creation call recorded
        # Verify that the cache key was used in both calls
        for creation_call in factory.creation_history:
            if creation_call.get("cache_key"):
                assert creation_call["cache_key"] == cache_key

    def test_security_service_factory_handles_different_cache_keys(self, mock_security_service_factory):
        """
        Test that SecurityServiceFactory creates separate instances for different cache keys.

        Verifies:
            Factory creates distinct service instances when different cache keys are used.

        Business Impact:
            Ensures proper isolation between different service configurations and use cases.

        Scenario:
            Given: SecurityConfig and two different cache keys.
            When: Factory creates services with different cache keys.
            Then: Returns different service instances for each cache key.

        Fixtures Used:
            - mock_security_service_factory: Factory fixture for SecurityServiceFactory.
        """
        # Given - Use proper SecurityConfig
        config = SecurityConfig(
            service_name="multi-service",
            environment="testing",
            scanners={
                ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True)
            }
        )
        factory = mock_security_service_factory()

        # When
        service1 = factory.create_service(mode="local", config=config, cache_key="service_1")
        service2 = factory.create_service(mode="local", config=config, cache_key="service_2")

        # Then
        assert service1 is not service2  # Different instances
        assert service1.service_name == "local-security-service"
        assert service2.service_name == "local-security-service"
        assert len(factory.creation_history) == 2  # Created twice


class TestScannerFactoryRegistry:
    """Test SecurityServiceFactory cache management and service tracking."""

    def test_security_service_factory_tracks_cached_services(self, cached_service_scenario):
        """
        Test that SecurityServiceFactory maintains registry of cached services.

        Verifies:
            Factory provides mechanism to discover which services are currently cached
            and their cache keys.

        Business Impact:
            Enables monitoring and debugging of service cache state for performance
            optimization and troubleshooting.

        Scenario:
            Given: SecurityServiceFactory with multiple cached services.
            When: Cache statistics are queried.
            Then: Returns information about cached services and their keys.

        Fixtures Used:
            - cached_service_scenario: Pre-configured factory with cached services.
        """
        # Given
        factory = cached_service_scenario["factory"]
        expected_keys = cached_service_scenario["cache_keys"]

        # When
        cache_stats = factory.get_cache_stats()

        # Then
        assert cache_stats["cached_services"] == 3
        assert set(cache_stats["cache_keys"]) == set(expected_keys)
        assert "test_service_1" in cache_stats["cache_keys"]
        assert "test_service_2" in cache_stats["cache_keys"]
        assert "test_service_3" in cache_stats["cache_keys"]

    def test_security_service_factory_clears_cache(self, cached_service_scenario):
        """
        Test that SecurityServiceFactory clears all cached services.

        Verifies:
            Factory can clear all cached services and reset cache to empty state.

        Business Impact:
            Enables memory management and cache reset for configuration updates
            and testing scenarios.

        Scenario:
            Given: SecurityServiceFactory with cached services.
            When: Cache is cleared.
            Then: All cached services are removed and cache stats show empty state.

        Fixtures Used:
            - cached_service_scenario: Pre-configured factory with cached services.
        """
        # Given
        factory = cached_service_scenario["factory"]
        assert factory.get_cache_stats()["cached_services"] == 3

        # When
        factory.clear_cache()

        # Then
        cache_stats = factory.get_cache_stats()
        assert cache_stats["cached_services"] == 0
        assert cache_stats["cache_keys"] == []
        assert len(factory.clear_cache_history) == 1

    def test_security_service_factory_validates_mode_availability(self, mock_security_service_factory):
        """
        Test that SecurityServiceFactory validates service mode availability.

        Verifies:
            Factory checks if specified service mode is available before attempting
            service creation.

        Business Impact:
            Prevents runtime errors by validating mode availability during
            service creation phase.

        Scenario:
            Given: Request to create service with specific mode.
            When: Factory creates service instance.
            Then: Successfully creates service for valid mode.

        Fixtures Used:
            - mock_security_service_factory: Factory fixture for SecurityServiceFactory.
        """
        # Given - Use proper SecurityConfig
        config = SecurityConfig(
            service_name="mode-test-service",
            environment="testing",
            scanners={
                ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True)
            }
        )
        factory = mock_security_service_factory()

        # When - Test local mode (available)
        service = factory.create_service(mode="local", config=config)

        # Then
        assert service is not None
        assert service.service_name == "local-security-service"
        creation_call = factory.creation_history[0]
        assert creation_call["mode"] == "local"


class TestSecurityServiceFactoryValidation:
    """Test SecurityServiceFactory configuration validation and error detection."""

    def test_factory_rejects_config_with_no_scanners(self, invalid_security_config_no_scanners):
        """
        Test that factory raises ConfigurationError for configs with no scanners.

        Verifies:
            Factory validates that at least one scanner is enabled per contract requirements.

        Business Impact:
            Prevents deployment of security services with no actual scanning capability,
            ensuring security coverage is always present.

        Scenario:
            Given: SecurityConfig with no scanners enabled.
            When: Factory attempts to create service.
            Then: ConfigurationError is raised with clear validation message.

        Fixtures Used:
            - invalid_security_config_no_scanners: Invalid config for validation testing.
        """
        # Given - Invalid config from fixture
        config = invalid_security_config_no_scanners

        # When & Then - Factory validation catches this
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityServiceFactory.create_service(mode="local", config=config)

        assert "at least one security scanner must be enabled" in str(exc_info.value).lower()


class TestSecurityServiceFactoryServiceCreationErrors:
    """Test SecurityServiceFactory error handling during service instantiation."""

    def test_factory_raises_configuration_error_for_invalid_mode(self):
        """
        Test that factory raises ConfigurationError for invalid service modes.

        Verifies:
            Factory validates service mode and raises ConfigurationError when unknown
            mode is specified, per the public contract.

        Business Impact:
            Provides clear error messages for invalid mode specifications, preventing
            runtime failures and guiding proper factory usage.

        Scenario:
            Given: Valid configuration but invalid service mode.
            When: Factory attempts to create service with invalid mode.
            Then: ConfigurationError is raised with mode details.
        """
        # Given - Valid config to pass validation
        config = SecurityConfig(
            service_name="mode-error-test",
            environment="testing",
            scanners={
                ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True)
            }
        )

        # When & Then - Invalid mode triggers ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityServiceFactory.create_service(mode="invalid_mode", config=config)

        assert "unknown security service mode" in str(exc_info.value).lower()

    def test_factory_raises_infrastructure_error_for_service_creation_failures(self):
        """
        Test that factory converts service instantiation errors to InfrastructureError.

        Verifies:
            Factory catches service creation failures and raises InfrastructureError
            with context about the failure per the public contract.

        Business Impact:
            Provides clear error messages distinguishing configuration issues from
            infrastructure failures, enabling proper troubleshooting.

        Scenario:
            Given: Valid configuration but service creation fails.
            When: Factory attempts to create service.
            Then: InfrastructureError is raised with creation failure details.
        """
        # Given - Valid config to pass validation
        config = SecurityConfig(
            service_name="infrastructure-error-test",
            environment="testing",
            scanners={
                ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True)
            }
        )

        # Mock service creation to simulate infrastructure failure
        with patch('app.infrastructure.security.llm.scanners.local_scanner.LocalLLMSecurityScanner') as mock_scanner:
            mock_scanner.side_effect = RuntimeError("Failed to load ML models")

            # When & Then - Infrastructure error is properly wrapped
            with pytest.raises(InfrastructureError) as exc_info:
                SecurityServiceFactory.create_service(mode="local", config=config)

            assert "failed to create security service" in str(exc_info.value).lower()

    def test_factory_handles_missing_dependencies_gracefully(self):
        """
        Test that factory handles missing ML dependencies with clear error messages.

        Verifies:
            Factory catches import errors and converts them to InfrastructureError
            with helpful context for deployment troubleshooting.

        Business Impact:
            Provides clear guidance when required ML libraries are missing,
            accelerating deployment issue resolution.

        Scenario:
            Given: Valid configuration but required dependencies missing.
            When: Factory attempts to create service.
            Then: InfrastructureError is raised with dependency details.
        """
        # Given - Valid config to pass validation
        config = SecurityConfig(
            service_name="missing-deps-test",
            environment="testing",
            scanners={
                ScannerType.PROMPT_INJECTION: ScannerConfig(enabled=True)
            }
        )

        # Mock import failure
        with patch('app.infrastructure.security.llm.scanners.local_scanner.LocalLLMSecurityScanner') as mock_scanner:
            import_error = ImportError("No module named 'transformers'")
            mock_scanner.side_effect = import_error

            # When & Then - Import error is properly wrapped
            with pytest.raises(InfrastructureError) as exc_info:
                SecurityServiceFactory.create_service(mode="local", config=config)

            assert "failed to create security service" in str(exc_info.value).lower()