"""
Unit tests for Security Service Factory.

This test module verifies that the security service factory properly handles
creation and configuration of security service instances as documented
in the public contract.

Test Coverage:
    - Factory creates LocalLLMSecurityScanner for "local" mode
    - Factory raises error for unknown security modes
    - Factory returns consistent SecurityService protocol interface
    - Factory with different configuration parameters
    - Security service interface compliance
    - Configuration model validation
    - Environment override behavior
    - Service caching functionality

Business Critical:
    Proper factory behavior ensures security services are configured correctly
    before any security operations, preventing security vulnerabilities.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.core.exceptions import ConfigurationError  # type: ignore
from app.infrastructure.security.llm.factory import (
    SecurityServiceFactory,
    create_security_service,
    get_security_service,
    create_security_service_from_preset,
)
from app.infrastructure.security.llm.config import (
    SecurityConfig,
    PresetName,
    ScannerConfig,
    ScannerType,
    ViolationAction,
)
from app.infrastructure.security.llm.protocol import SecurityService


class TestSecurityServiceFactory:
    """
    Test suite for SecurityServiceFactory class behavior.

    Scope:
        Tests the factory methods covering all documented creation scenarios
        from Args and Raises sections.

    Business Critical:
        Proper factory behavior ensures security services are created with
        correct configuration, preventing security misconfigurations.
    """

    def test_create_service_with_local_mode_returns_local_scanner(self) -> None:
        """
        Test that create_service with "local" mode returns LocalLLMSecurityScanner.

        Verifies:
            Factory successfully creates local scanner instance as documented
            in create_service docstring.
        """
        # Create service with local mode
        service = SecurityServiceFactory.create_service(mode="local")

        # Verify service type and protocol compliance
        assert service is not None
        assert isinstance(service, SecurityService)

        # Verify service has expected methods
        assert hasattr(service, "validate_input")
        assert hasattr(service, "validate_output")
        assert hasattr(service, "get_metrics")
        assert hasattr(service, "health_check")
        assert callable(service.validate_input)
        assert callable(service.validate_output)

    def test_create_service_with_unknown_mode_raises_configuration_error(self) -> None:
        """
        Test that create_service raises ConfigurationError for unknown mode.

        Verifies:
            Factory raises ConfigurationError for invalid security modes
            as documented in Raises section of create_service docstring.
        """
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityServiceFactory.create_service(mode="unknown_mode")

        assert "Unknown security service mode" in str(exc_info.value)
        assert "unknown_mode" in str(exc_info.value)

    def test_create_service_with_saas_mode_raises_not_implemented_error(self) -> None:
        """
        Test that create_service raises NotImplementedError for SaaS mode.

        Verifies:
            Factory properly handles future SaaS mode by raising NotImplementedError
            with clear message.
        """
        with pytest.raises(NotImplementedError) as exc_info:
            SecurityServiceFactory.create_service(mode="saas")

        assert "SaaS mode is not yet implemented" in str(exc_info.value)

    def test_create_service_with_custom_config(self) -> None:
        """
        Test that create_service accepts and uses custom configuration.

        Verifies:
            Factory successfully creates service with custom configuration
            as documented in Args section of create_service docstring.
        """
        # Create custom configuration
        config = SecurityConfig()
        config.scanners[ScannerType.PROMPT_INJECTION] = ScannerConfig(
            enabled=True,
            threshold=0.9,
            action=ViolationAction.BLOCK,
        )
        config.performance.max_concurrent_scans = 5

        # Create service with custom config
        service = SecurityServiceFactory.create_service(
            mode="local",
            config=config
        )

        # Verify service created successfully
        assert service is not None
        assert isinstance(service, SecurityService)

    def test_create_service_with_environment_overrides(self) -> None:
        """
        Test that create_service applies environment variable overrides.

        Verifies:
            Factory successfully applies environment overrides as documented
            in Args section of create_service docstring.
        """
        # Define environment overrides
        env_overrides = {
            "max_concurrent_scans": 10,
            "enable_caching": True,
            "toxicity_threshold": 0.8,
        }

        # Create service with environment overrides
        service = SecurityServiceFactory.create_service(
            mode="local",
            environment_overrides=env_overrides
        )

        # Verify service created successfully
        assert service is not None
        assert isinstance(service, SecurityService)

    def test_create_service_caches_instances_with_same_config(self) -> None:
        """
        Test that create_service caches instances with same configuration.

        Verifies:
            Factory returns cached instance for same configuration as documented
            in implementation details.
        """
        # Create first service
        service1 = SecurityServiceFactory.create_service(mode="local")

        # Create second service with same config
        service2 = SecurityServiceFactory.create_service(mode="local")

        # Should return same cached instance
        assert service1 is service2

    def test_create_service_with_different_configs_creates_different_instances(self) -> None:
        """
        Test that create_service creates different instances for different configs.

        Verifies:
            Factory creates separate instances for different configurations.
        """
        # Create first service
        service1 = SecurityServiceFactory.create_service(mode="local")

        # Create second service with different config
        config = SecurityConfig()
        config.performance.max_concurrent_scans = 15
        service2 = SecurityServiceFactory.create_service(
            mode="local",
            config=config
        )

        # Should return different instances
        assert service1 is not service2

    def test_create_service_invalid_config_raises_configuration_error(self) -> None:
        """
        Test that create_service raises ConfigurationError for invalid config.

        Verifies:
            Factory validates configuration and raises ConfigurationError
            for invalid configurations as documented in Raises section.
        """
        # Create invalid config (no scanners enabled)
        config = SecurityConfig()
        # All scanners disabled by default

        with pytest.raises(ConfigurationError) as exc_info:
            SecurityServiceFactory.create_service(
                mode="local",
                config=config
            )

        assert "At least one security scanner must be enabled" in str(exc_info.value)

    def test_clear_cache_removes_all_cached_services(self) -> None:
        """
        Test that clear_cache removes all cached services.

        Verifies:
            Factory cache clearing functionality works correctly.
        """
        # Create cached service
        service = SecurityServiceFactory.create_service(mode="local")

        # Verify cache has services
        cache_stats = SecurityServiceFactory.get_cache_stats()
        assert cache_stats["cached_services"] > 0

        # Clear cache
        SecurityServiceFactory.clear_cache()

        # Verify cache is empty
        cache_stats = SecurityServiceFactory.get_cache_stats()
        assert cache_stats["cached_services"] == 0

    def test_get_cache_stats_returns_cache_information(self) -> None:
        """
        Test that get_cache_stats returns cache statistics.

        Verifies:
            Factory returns accurate cache statistics information.
        """
        # Create cached service
        SecurityServiceFactory.create_service(mode="local")

        # Get cache stats
        stats = SecurityServiceFactory.get_cache_stats()

        # Verify stats structure
        assert "cached_services" in stats
        assert "cache_keys" in stats
        assert isinstance(stats["cached_services"], int)
        assert isinstance(stats["cache_keys"], list)
        assert stats["cached_services"] > 0


class TestSecurityServiceFactoryFunctions:
    """
    Test suite for convenience functions in factory module.

    Scope:
        Tests global factory functions covering all documented usage scenarios.
    """

    def test_create_security_service_creates_local_service_by_default(self) -> None:
        """
        Test that create_security_service creates local service by default.

        Verifies:
            Convenience function creates local service with default mode
            as documented in function docstring.
        """
        service = create_security_service()

        assert service is not None
        assert isinstance(service, SecurityService)

    @patch.dict("os.environ", {"SECURITY_MODE": "local"})
    def test_get_security_service_uses_environment_variable(self) -> None:
        """
        Test that get_security_service uses SECURITY_MODE environment variable.

        Verifies:
            Dependency injection function reads environment variables
            as documented in function docstring.
        """
        service = get_security_service()

        assert service is not None
        assert isinstance(service, SecurityService)

    def test_create_security_service_from_preset_creates_service(self) -> None:
        """
        Test that create_security_service_from_preset creates service from preset.

        Verifies:
            Preset-based service creation works as documented
            in function docstring.
        """
        service = create_security_service_from_preset(
            preset=PresetName.BALANCED,
            mode="local"
        )

        assert service is not None
        assert isinstance(service, SecurityService)

    def test_create_security_service_from_preset_with_invalid_preset_raises_error(self) -> None:
        """
        Test that create_security_service_from_preset raises error for invalid preset.

        Verifies:
            Function validates preset names and raises ConfigurationError
            for invalid presets.
        """
        with pytest.raises(ConfigurationError) as exc_info:
            create_security_service_from_preset(preset="invalid_preset")

        assert "Invalid preset" in str(exc_info.value)
        assert "invalid_preset" in str(exc_info.value)

    def test_create_security_service_from_preset_with_string_preset(self) -> None:
        """
        Test that create_security_service_from_preset accepts string presets.

        Verifies:
            Function accepts both enum and string preset values
            as documented in function docstring.
        """
        service = create_security_service_from_preset(
            preset="balanced",
            mode="local"
        )

        assert service is not None
        assert isinstance(service, SecurityService)


class TestSecurityServiceFactoryConfiguration:
    """
    Test suite for factory configuration loading and validation.

    Scope:
        Tests configuration loading, merging, and validation behavior.
    """

    def test_load_configuration_uses_default_when_none_provided(self) -> None:
        """
        Test that _load_configuration creates default config when none provided.

        Verifies:
            Factory creates sensible default configuration as documented
            in internal method behavior.
        """
        config = SecurityServiceFactory._load_configuration(None, None)

        assert config is not None
        assert isinstance(config, SecurityConfig)

    def test_load_configuration_applies_environment_overrides(self) -> None:
        """
        Test that _load_configuration applies environment variable overrides.

        Verifies:
            Factory correctly merges environment overrides as documented
            in internal method behavior.
        """
        env_overrides = {
            "max_concurrent_scans": 20,
            "enable_caching": True,
        }

        config = SecurityServiceFactory._load_configuration(None, env_overrides)

        assert config is not None
        assert isinstance(config, SecurityConfig)

    def test_validate_configuration_rejects_invalid_performance_settings(self) -> None:
        """
        Test that _validate_configuration rejects invalid performance settings.

        Verifies:
            Factory validates performance configuration and raises errors
            for invalid values.
        """
        config = SecurityConfig()
        config.performance.max_concurrent_scans = 0  # Invalid

        with pytest.raises(ConfigurationError) as exc_info:
            SecurityServiceFactory._validate_configuration(config)

        assert "max_concurrent_scans must be at least 1" in str(exc_info.value)

    def test_validate_configuration_rejects_low_memory_limit(self) -> None:
        """
        Test that _validate_configuration rejects low memory limits.

        Verifies:
            Factory validates memory configuration and raises errors
            for insufficient limits.
        """
        config = SecurityConfig()
        config.performance.max_memory_mb = 100  # Too low

        with pytest.raises(ConfigurationError) as exc_info:
            SecurityServiceFactory._validate_configuration(config)

        assert "max_memory_mb must be at least 512" in str(exc_info.value)

    def test_generate_cache_key_creates_consistent_keys(self) -> None:
        """
        Test that _generate_cache_key creates consistent cache keys.

        Verifies:
            Factory generates deterministic cache keys for same configuration.
        """
        key1 = SecurityServiceFactory._generate_cache_key("local", None, None)
        key2 = SecurityServiceFactory._generate_cache_key("local", None, None)

        assert key1 == key2
        assert isinstance(key1, str)
        assert key1.startswith("security_service_local_")

    def test_generate_cache_key_creates_different_keys_for_different_configs(self) -> None:
        """
        Test that _generate_cache_key creates different keys for different configs.

        Verifies:
            Factory generates different cache keys for different configurations.
        """
        config1 = SecurityConfig()
        config2 = SecurityConfig()
        config2.performance.max_concurrent_scans = 15

        key1 = SecurityServiceFactory._generate_cache_key("local", config1, None)
        key2 = SecurityServiceFactory._generate_cache_key("local", config2, None)

        assert key1 != key2


class TestSecurityServiceFactoryEnvironmentOverrides:
    """
    Test suite for environment variable override functionality.

    Scope:
        Tests environment variable loading and override application.
    """

    @patch.dict("os.environ", {
        "SECURITY_MODE": "local",
        "SECURITY_PRESET": "strict",
        "SECURITY_DEBUG": "true",
        "SECURITY_MAX_CONCURRENT_SCANS": "25",
        "SECURITY_ENABLE_CACHING": "true",
        "SECURITY_CACHE_TTL": "7200",
        "SECURITY_TOXICITY_THRESHOLD": "0.85",
        "SECURITY_PII_ACTION": "redact",
        "SECURITY_LOG_LEVEL": "DEBUG",
        "SECURITY_INCLUDE_SCANNED_TEXT": "false"
    })
    def test_load_environment_overrides_reads_all_security_variables(self) -> None:
        """
        Test that _load_environment_overrides reads all security environment variables.

        Verifies:
            Factory loads all supported security environment variables
            as documented in implementation.
        """
        overrides = SecurityServiceFactory._load_environment_overrides()

        # Verify all expected overrides are loaded
        assert "security_mode" in overrides
        assert "security_preset" in overrides
        assert "security_debug" in overrides
        assert "max_concurrent_scans" in overrides
        assert "enable_caching" in overrides
        assert "cache_ttl_seconds" in overrides
        assert "toxicity_threshold" in overrides
        assert "pii_action" in overrides
        assert "log_level" in overrides
        assert "include_scanned_text" in overrides

        # Verify values
        assert overrides["security_mode"] == "local"
        assert overrides["security_preset"] == "strict"
        assert overrides["security_debug"] == "true"
        assert overrides["max_concurrent_scans"] == 25
        assert overrides["enable_caching"] == "true"
        assert overrides["cache_ttl_seconds"] == 7200
        assert overrides["toxicity_threshold"] == 0.85
        assert overrides["pii_action"] == "redact"
        assert overrides["log_level"] == "DEBUG"
        assert overrides["include_scanned_text"] == "false"

    @patch.dict("os.environ", {
        "SECURITY_MAX_CONCURRENT_SCANS": "invalid_number",
        "SECURITY_CACHE_TTL": "invalid_number",
        "SECURITY_TOXICITY_THRESHOLD": "invalid_float"
    })
    def test_load_environment_overrides_handles_invalid_values_gracefully(self) -> None:
        """
        Test that _load_environment_overrides handles invalid environment values.

        Verifies:
            Factory gracefully handles invalid environment variable values
            and logs warnings.
        """
        with patch("logging.getLogger") as mock_logger:
            mock_log = MagicMock()
            mock_logger.return_value = mock_log

            overrides = SecurityServiceFactory._load_environment_overrides()

            # Should not include invalid values
            assert "max_concurrent_scans" not in overrides
            assert "cache_ttl_seconds" not in overrides
            assert "toxicity_threshold" not in overrides

            # Should log warnings
            assert mock_log.warning.call_count >= 3

    def test_load_environment_overrides_returns_empty_dict_when_no_env_vars_set(self) -> None:
        """
        Test that _load_environment_overrides returns empty dict when no env vars set.

        Verifies:
            Factory returns empty dictionary when no security environment
            variables are set.
        """
        with patch.dict("os.environ", {}, clear=True):
            overrides = SecurityServiceFactory._load_environment_overrides()

            assert overrides == {}

    @patch.dict("os.environ", {"SECURITY_PRESET": "invalid_preset"})
    def test_create_default_configuration_falls_back_to_balanced_for_invalid_preset(self) -> None:
        """
        Test that _create_default_configuration falls back to balanced for invalid preset.

        Verifies:
            Factory falls back to balanced preset when invalid preset
            is specified in environment.
        """
        with patch("logging.getLogger") as mock_logger:
            mock_log = MagicMock()
            mock_logger.return_value = mock_log

            config = SecurityServiceFactory._create_default_configuration()

            # Should create valid config
            assert config is not None
            assert isinstance(config, SecurityConfig)

            # Should log warning about invalid preset
            mock_log.warning.assert_called_with(
                "Invalid SECURITY_PRESET 'invalid_preset', using 'balanced' preset"
            )
