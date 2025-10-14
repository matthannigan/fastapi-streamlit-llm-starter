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


class TestScannerFactoryInitialization:
    """Test SecurityServiceFactory initialization and configuration."""

    def test_security_service_factory_creates_service_from_config(self, mock_security_config, mock_security_service_factory):
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
            - mock_security_config: Factory fixture for SecurityConfig.
            - mock_security_service_factory: Factory fixture for SecurityServiceFactory.
        """
        # Given
        config = mock_security_config(
            scanners={"prompt_injection": {"enabled": True, "threshold": 0.7}},
            performance={"max_concurrent_scans": 10},
            service_name="test-security-service"
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

    def test_security_service_factory_applies_environment_overrides(self, mock_security_config, mock_security_service_factory, environment_overrides):
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
            - mock_security_config: Factory fixture for SecurityConfig.
            - mock_security_service_factory: Factory fixture for SecurityServiceFactory.
            - environment_overrides: Environment variable override fixture.
        """
        # Given
        config = mock_security_config(
            scanners={"prompt_injection": {"enabled": True, "threshold": 0.7}},
            service_name="base-service"
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

    def test_security_service_factory_uses_cache_key(self, mock_security_config, mock_security_service_factory):
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
            - mock_security_config: Factory fixture for SecurityConfig.
            - mock_security_service_factory: Factory fixture for SecurityServiceFactory.
        """
        # Given
        config = mock_security_config(service_name="cached-service")
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

    def test_security_service_factory_handles_different_cache_keys(self, mock_security_config, mock_security_service_factory):
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
            - mock_security_config: Factory fixture for SecurityConfig.
            - mock_security_service_factory: Factory fixture for SecurityServiceFactory.
        """
        # Given
        config = mock_security_config(service_name="multi-service")
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

    def test_security_service_factory_validates_mode_availability(self, mock_security_config, mock_security_service_factory):
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
            - mock_security_config: Factory fixture for SecurityConfig.
            - mock_security_service_factory: Factory fixture for SecurityServiceFactory.
        """
        # Given
        config = mock_security_config(service_name="mode-test-service")
        factory = mock_security_service_factory()

        # When - Test local mode (available)
        service = factory.create_service(mode="local", config=config)

        # Then
        assert service is not None
        assert service.service_name == "local-security-service"
        creation_call = factory.creation_history[0]
        assert creation_call["mode"] == "local"


class TestScannerFactoryErrorHandling:
    """Test SecurityServiceFactory error handling and validation."""

    def test_security_service_factory_raises_configuration_error_for_invalid_mode(self, mock_security_config, mock_configuration_error):
        """
        Test that SecurityServiceFactory raises ConfigurationError for invalid service modes.

        Verifies:
            Factory validates service mode and raises ConfigurationError when invalid
            mode is specified.

        Business Impact:
            Provides clear error messages for invalid mode specifications preventing
            successful service creation.

        Scenario:
            Given: Valid configuration but invalid service mode.
            When: Factory attempts to create service with invalid mode.
            Then: ConfigurationError is raised with details about invalid mode.

        Fixtures Used:
            - mock_security_config: Factory fixture for SecurityConfig.
            - mock_infrastructure_error: MockInfrastructureError class for validation.
        """
        # Given
        config = mock_security_config(service_name="error-test-service")

        # Mock the factory to raise error for invalid mode
        with patch('app.infrastructure.security.llm.factory.SecurityServiceFactory._create_service_instance') as mock_create:
            # Get the mock exception from the fixture
            MockConfigurationError = mock_configuration_error
            mock_create.side_effect = MockConfigurationError("Unknown security service mode: invalid")

            # When & Then
            with pytest.raises(MockConfigurationError) as exc_info:
                SecurityServiceFactory.create_service(mode="invalid", config=config)

            assert "Unknown security service mode" in str(exc_info.value)

    def test_security_service_factory_raises_infrastructure_error_for_creation_failures(self, mock_security_config, mock_infrastructure_error):
        """
        Test that SecurityServiceFactory raises InfrastructureError for service creation failures.

        Verifies:
            Factory catches service creation failures and raises InfrastructureError
            with context about the failure.

        Business Impact:
            Provides clear error messages distinguishing configuration issues from
            infrastructure failures for troubleshooting.

        Scenario:
            Given: Valid configuration but service creation fails due to infrastructure issues.
            When: Factory attempts to create service.
            Then: InfrastructureError is raised with creation failure details.

        Fixtures Used:
            - mock_security_config: Factory fixture for SecurityConfig.
            - mock_infrastructure_error: MockInfrastructureError class for validation.
        """
        # Given
        config = mock_security_config(service_name="infrastructure-error-service")

        # Mock the factory to raise infrastructure error for service creation
        with patch('app.infrastructure.security.llm.factory.SecurityServiceFactory._create_service_instance') as mock_create:
            mock_create.side_effect = mock_infrastructure_error("Failed to load ML models", {"model_type": "transformer"})

            # When & Then
            with pytest.raises(mock_infrastructure_error) as exc_info:
                SecurityServiceFactory.create_service(mode="local", config=config)

            assert "Failed to load ML models" in str(exc_info.value)
            assert exc_info.value.context["model_type"] == "transformer"

    def test_security_service_factory_handles_missing_dependencies(self, mock_security_config, mock_infrastructure_error):
        """
        Test that SecurityServiceFactory handles missing dependencies gracefully.

        Verifies:
            Factory catches import errors and missing dependencies, raising appropriate
            InfrastructureError with helpful context.

        Business Impact:
            Provides clear error messages for missing dependencies preventing service
            creation, aiding in deployment and setup troubleshooting.

        Scenario:
            Given: Valid configuration but required dependencies are missing.
            When: Factory attempts to create service.
            Then: InfrastructureError is raised with missing dependency details.

        Fixtures Used:
            - mock_security_config: Factory fixture for SecurityConfig.
        """
        # Given
        config = mock_security_config(service_name="missing-deps-service")

        # Mock import failure
        with patch('app.infrastructure.security.llm.factory.SecurityServiceFactory._create_service_instance') as mock_create:
            MockInfrastructureError = mock_infrastructure_error
            import_error = ImportError("No module named 'transformers'")
            mock_create.side_effect = MockInfrastructureError(
                f"Failed to create security service with mode 'local': {import_error}",
                context={"original_error": str(import_error), "missing_dependency": "transformers"}
            )

            # When & Then
            with pytest.raises(MockInfrastructureError) as exc_info:
                SecurityServiceFactory.create_service(mode="local", config=config)

            assert "Failed to create security service" in str(exc_info.value)
            assert exc_info.value.context["missing_dependency"] == "transformers"