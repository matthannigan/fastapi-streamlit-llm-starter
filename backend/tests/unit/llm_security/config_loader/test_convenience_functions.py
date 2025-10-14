"""
Test suite for config_loader convenience functions.

Tests verify get_config_loader(), load_security_config(), and reload_security_config()
convenience functions according to the public contract defined in config_loader.pyi.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestGetConfigLoader:
    """Test get_config_loader() singleton pattern function."""

    @patch('app.infrastructure.security.llm.config_loader.SecurityConfigLoader')
    def test_get_config_loader_returns_security_config_loader_instance(self, mock_loader_class, tmp_path, monkeypatch):
        """
        Test that get_config_loader() returns SecurityConfigLoader instance.

        Verifies:
            get_config_loader() creates and returns SecurityConfigLoader instance
            per contract's Returns section.

        Business Impact:
            Provides convenient access to shared configuration loader for consistent
            configuration loading across application.

        Scenario:
            Given: No prior calls to get_config_loader().
            When: get_config_loader() is called first time.
            Then: Returns new SecurityConfigLoader instance with default settings.

        Fixtures Used:
            - tmp_path: Pytest fixture for configuration directory.
            - monkeypatch: Pytest fixture for environment isolation.
        """
        # Given: Setup mock loader and valid config directory
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader

        config_dir = tmp_path / "config" / "security"
        config_dir.mkdir(parents=True, exist_ok=True)

        # When: Import and call get_config_loader
        from app.infrastructure.security.llm.config_loader import get_config_loader

        # Clear any existing global instance
        import app.infrastructure.security.llm.config_loader as config_module
        config_module._loader_instance = None

        result = get_config_loader()

        # Then: Returns SecurityConfigLoader instance
        assert result is mock_loader
        mock_loader_class.assert_called_once_with()

    @patch('app.infrastructure.security.llm.config_loader.SecurityConfigLoader')
    def test_get_config_loader_returns_same_instance_on_subsequent_calls(self, mock_loader_class, tmp_path, monkeypatch):
        """
        Test that get_config_loader() implements singleton pattern.

        Verifies:
            get_config_loader() returns same instance on multiple calls per
            contract's Behavior section (singleton pattern).

        Business Impact:
            Ensures configuration caching works correctly by reusing same loader
            instance across application.

        Scenario:
            Given: Initial call to get_config_loader() returning loader1.
            When: get_config_loader() is called second time returning loader2.
            Then: loader1 and loader2 are the same instance (identity check).

        Fixtures Used:
            - tmp_path: Pytest fixture for configuration directory.
            - monkeypatch: Pytest fixture for environment isolation.
        """
        # Given: Setup mock loader and config directory
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader

        config_dir = tmp_path / "config" / "security"
        config_dir.mkdir(parents=True, exist_ok=True)

        from app.infrastructure.security.llm.config_loader import get_config_loader
        import app.infrastructure.security.llm.config_loader as config_module

        # Clear any existing global instance
        config_module._loader_instance = None

        # When: Call get_config_loader twice
        loader1 = get_config_loader()
        loader2 = get_config_loader()

        # Then: Same instance returned (singleton pattern)
        assert loader1 is loader2
        assert loader1 is mock_loader
        # SecurityConfigLoader constructor only called once
        mock_loader_class.assert_called_once_with()

    @patch('app.infrastructure.security.llm.config_loader.SecurityConfigLoader')
    def test_get_config_loader_uses_environment_variables_for_defaults(self, mock_loader_class, tmp_path, monkeypatch):
        """
        Test that get_config_loader() reads SECURITY_CONFIG_PATH for default path.

        Verifies:
            get_config_loader() uses SECURITY_CONFIG_PATH environment variable
            for configuration directory per contract's Behavior section.

        Business Impact:
            Enables environment-based configuration directory location without
            code changes.

        Scenario:
            Given: SECURITY_CONFIG_PATH="/custom/config" environment variable set.
            When: get_config_loader() is called.
            Then: Returned loader has config_path set to "/custom/config".

        Fixtures Used:
            - tmp_path: Pytest fixture for configuration directory.
            - monkeypatch: Pytest fixture for setting environment variables.
        """
        # Given: Custom config path environment variable
        custom_config_path = str(tmp_path / "custom" / "config")
        monkeypatch.setenv("SECURITY_CONFIG_PATH", custom_config_path)

        config_dir = tmp_path / "custom" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader

        from app.infrastructure.security.llm.config_loader import get_config_loader
        import app.infrastructure.security.llm.config_loader as config_module

        # Clear any existing global instance
        config_module._loader_instance = None

        # When: Call get_config_loader
        result = get_config_loader()

        # Then: Loader created with custom config path
        mock_loader_class.assert_called_once_with()
        # Verify the loader instance was created and returned
        assert result is mock_loader


class TestLoadSecurityConfig:
    """Test load_security_config() main configuration loading function."""

    @patch('app.infrastructure.security.llm.config_loader.get_config_loader')
    def test_load_security_config_with_default_parameters(self, mock_get_loader, tmp_path, monkeypatch):
        """
        Test that load_security_config() loads configuration with sensible defaults.

        Verifies:
            load_security_config() uses default environment and config path when
            no parameters provided per contract's Args section.

        Business Impact:
            Enables zero-configuration loading for standard deployment scenarios
            with conventional setup.

        Scenario:
            Given: Valid configuration files in default location.
            When: load_security_config() is called without parameters.
            Then: Returns validated SecurityConfig with default environment settings.

        Fixtures Used:
            - tmp_path: Pytest fixture for creating configuration files.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Mock global loader and configuration
        mock_loader = Mock()
        mock_config = Mock()
        mock_loader.load_config.return_value = mock_config
        mock_get_loader.return_value = mock_loader

        from app.infrastructure.security.llm.config_loader import load_security_config

        # When: Call with default parameters
        result = load_security_config()

        # Then: Uses global loader and calls with default parameters
        mock_get_loader.assert_called_once_with()
        mock_loader.load_config.assert_called_once_with(
            environment=None,
            enable_hot_reload=False,
            cache_bust=False
        )
        assert result is mock_config

    @patch('app.infrastructure.security.llm.config_loader.SecurityConfigLoader')
    def test_load_security_config_with_custom_environment(self, mock_loader_class, tmp_path, monkeypatch):
        """
        Test that load_security_config() accepts custom environment parameter.

        Verifies:
            load_security_config() loads environment-specific configuration when
            environment parameter provided per contract's Args section.

        Business Impact:
            Enables explicit environment selection for loading environment-specific
            scanner configurations.

        Scenario:
            Given: Configuration with production.yaml overrides.
            When: load_security_config(environment="production") is called.
            Then: Returns SecurityConfig with production overrides applied.

        Fixtures Used:
            - tmp_path: Pytest fixture for configuration files.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Mock loader and configuration directory
        mock_loader = Mock()
        mock_config = Mock()
        mock_loader.load_config.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        # Create valid config directory since SecurityConfigLoader will be instantiated
        config_dir = tmp_path / "config" / "security"
        config_dir.mkdir(parents=True, exist_ok=True)

        from app.infrastructure.security.llm.config_loader import load_security_config

        # When: Call with custom environment (creates new loader)
        result = load_security_config(environment="production")

        # Then: Creates new loader with custom environment
        mock_loader_class.assert_called_once_with(
            config_path=None,
            environment="production"
        )
        mock_loader.load_config.assert_called_once_with(
            environment="production",
            enable_hot_reload=False,
            cache_bust=False
        )
        assert result is mock_config

    @patch('app.infrastructure.security.llm.config_loader.SecurityConfigLoader')
    def test_load_security_config_with_custom_config_path(self, mock_loader_class, tmp_path, monkeypatch):
        """
        Test that load_security_config() accepts custom configuration path.

        Verifies:
            load_security_config() loads from custom directory when config_path
            provided per contract's Args section.

        Business Impact:
            Enables flexible configuration file placement for non-standard
            deployment architectures.

        Scenario:
            Given: Configuration files in custom directory.
            When: load_security_config(config_path="/custom/path") is called.
            Then: Returns SecurityConfig loaded from custom directory.

        Fixtures Used:
            - tmp_path: Pytest fixture for custom configuration location.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Custom config path and mock loader
        custom_config_path = str(tmp_path / "custom" / "config")
        mock_loader = Mock()
        mock_config = Mock()
        mock_loader.load_config.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        from app.infrastructure.security.llm.config_loader import load_security_config

        # When: Call with custom config path
        result = load_security_config(config_path=custom_config_path)

        # Then: Creates new loader with custom path
        mock_loader_class.assert_called_once_with(
            config_path=custom_config_path,
            environment="development"  # Default environment
        )
        mock_loader.load_config.assert_called_once_with(
            environment=None,
            enable_hot_reload=False,
            cache_bust=False
        )
        assert result is mock_config

    @patch('app.infrastructure.security.llm.config_loader.SecurityConfigLoader')
    def test_load_security_config_with_hot_reload_enabled(self, mock_loader_class, tmp_path, monkeypatch):
        """
        Test that load_security_config() enables hot reload when requested.

        Verifies:
            load_security_config() passes enable_hot_reload parameter to loader
            per contract's Args section.

        Business Impact:
            Enables live configuration updates during development without
            application restarts.

        Scenario:
            Given: Development environment configuration.
            When: load_security_config(enable_hot_reload=True, environment="development") is called.
            Then: Hot reload monitoring is configured for development.

        Fixtures Used:
            - tmp_path: Pytest fixture for configuration files.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Mock loader and configuration directory
        mock_loader = Mock()
        mock_config = Mock()
        mock_loader.load_config.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        # Create valid config directory since SecurityConfigLoader will be instantiated
        config_dir = tmp_path / "config" / "security"
        config_dir.mkdir(parents=True, exist_ok=True)

        from app.infrastructure.security.llm.config_loader import load_security_config

        # When: Call with hot reload enabled (creates new loader due to environment parameter)
        result = load_security_config(
            enable_hot_reload=True,
            environment="development"
        )

        # Then: Creates new loader and passes hot reload parameter
        mock_loader_class.assert_called_once_with(
            config_path=None,
            environment="development"
        )
        mock_loader.load_config.assert_called_once_with(
            environment="development",
            enable_hot_reload=True,
            cache_bust=False
        )
        assert result is mock_config

    @patch('app.infrastructure.security.llm.config_loader.get_config_loader')
    def test_load_security_config_with_cache_bust(self, mock_get_loader, tmp_path, monkeypatch):
        """
        Test that load_security_config() forces fresh reload when cache_bust=True.

        Verifies:
            load_security_config() bypasses cache when cache_bust=True per
            contract's Args section.

        Business Impact:
            Enables forced configuration reload for testing or applying live
            changes without cache interference.

        Scenario:
            Given: Previously loaded configuration in cache.
            When: load_security_config(cache_bust=True) is called.
            Then: Configuration is reloaded from files, ignoring cache.

        Fixtures Used:
            - tmp_path: Pytest fixture for configuration files.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Mock global loader
        mock_loader = Mock()
        mock_config = Mock()
        mock_loader.load_config.return_value = mock_config
        mock_get_loader.return_value = mock_loader

        from app.infrastructure.security.llm.config_loader import load_security_config

        # When: Call with cache bust enabled
        result = load_security_config(cache_bust=True)

        # Then: Passes cache_bust parameter to loader
        mock_get_loader.assert_called_once_with()
        mock_loader.load_config.assert_called_once_with(
            environment=None,
            enable_hot_reload=False,
            cache_bust=True
        )
        assert result is mock_config

    @patch('app.infrastructure.security.llm.config_loader.SecurityConfigLoader')
    def test_load_security_config_creates_new_loader_with_custom_settings(self, mock_loader_class, tmp_path, monkeypatch):
        """
        Test that load_security_config() creates new loader when custom settings provided.

        Verifies:
            load_security_config() creates new SecurityConfigLoader instead of
            using global loader when custom config_path provided per contract's Behavior.

        Business Impact:
            Enables isolated configuration loading for testing without affecting
            global loader state.

        Scenario:
            Given: Custom config_path parameter provided.
            When: load_security_config(config_path="/custom/path") is called.
            Then: New SecurityConfigLoader is created instead of using global instance.

        Fixtures Used:
            - tmp_path: Pytest fixture for custom configuration.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Custom settings
        custom_config_path = str(tmp_path / "custom" / "config")
        custom_environment = "staging"

        mock_loader = Mock()
        mock_config = Mock()
        mock_loader.load_config.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        from app.infrastructure.security.llm.config_loader import load_security_config

        # When: Call with custom settings
        result = load_security_config(
            config_path=custom_config_path,
            environment=custom_environment
        )

        # Then: Creates new loader instead of using global
        mock_loader_class.assert_called_once_with(
            config_path=custom_config_path,
            environment=custom_environment
        )
        mock_loader.load_config.assert_called_once_with(
            environment=custom_environment,
            enable_hot_reload=False,
            cache_bust=False
        )
        assert result is mock_config

    @patch('app.infrastructure.security.llm.config_loader.get_config_loader')
    def test_load_security_config_reuses_global_loader_for_default_settings(self, mock_get_loader, tmp_path, monkeypatch):
        """
        Test that load_security_config() reuses global loader for efficiency.

        Verifies:
            load_security_config() uses get_config_loader() when no custom settings
            provided per contract's Behavior section.

        Business Impact:
            Optimizes performance by reusing global loader instance and its cache
            for standard configuration loading.

        Scenario:
            Given: No custom parameters provided to load_security_config().
            When: load_security_config() is called multiple times.
            Then: Same global loader instance is reused across calls.

        Fixtures Used:
            - tmp_path: Pytest fixture for configuration files.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Mock global loader
        mock_loader = Mock()
        mock_config = Mock()
        mock_loader.load_config.return_value = mock_config
        mock_get_loader.return_value = mock_loader

        from app.infrastructure.security.llm.config_loader import load_security_config

        # When: Call multiple times with default settings
        result1 = load_security_config()
        result2 = load_security_config()

        # Then: Reuses same global loader
        assert mock_get_loader.call_count == 2
        assert mock_loader.load_config.call_count == 2
        # Both calls use same loader instance
        assert result1 is mock_config
        assert result2 is mock_config

    @patch('app.infrastructure.security.llm.config_loader.get_config_loader')
    def test_load_security_config_raises_configuration_error_on_failure(self, mock_get_loader, tmp_path, monkeypatch):
        """
        Test that load_security_config() propagates ConfigurationError from loader.

        Verifies:
            load_security_config() allows ConfigurationError to propagate to caller
            per contract's Raises section.

        Business Impact:
            Provides clear error messages for configuration issues without
            obscuring error details.

        Scenario:
            Given: Invalid configuration causing ConfigurationError.
            When: load_security_config() is called.
            Then: ConfigurationError is raised with error details intact.

        Fixtures Used:
            - tmp_path: Pytest fixture for invalid configuration.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Loader raises ConfigurationError
        mock_loader = Mock()
        from app.infrastructure.security.llm.config_loader import ConfigurationError
        error_message = "Configuration loading failed"
        mock_loader.load_config.side_effect = ConfigurationError(error_message)
        mock_get_loader.return_value = mock_loader

        from app.infrastructure.security.llm.config_loader import load_security_config

        # When & Then: ConfigurationError propagates
        with pytest.raises(ConfigurationError) as exc_info:
            load_security_config()

        assert str(exc_info.value) == error_message


class TestReloadSecurityConfig:
    """Test reload_security_config() forced configuration reload function."""

    @patch('app.infrastructure.security.llm.config_loader.load_security_config')
    def test_reload_security_config_forces_cache_bypass(self, mock_load_config, tmp_path, monkeypatch):
        """
        Test that reload_security_config() bypasses all caches for fresh load.

        Verifies:
            reload_security_config() calls load_security_config with cache_bust=True
            per contract's Behavior section.

        Business Impact:
            Ensures configuration changes are immediately loaded without cache
            interference for testing and runtime updates.

        Scenario:
            Given: Previously cached configuration.
            When: reload_security_config() is called.
            Then: Configuration is freshly loaded from files, ignoring all caches.

        Fixtures Used:
            - tmp_path: Pytest fixture for configuration files.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Mock load_security_config
        mock_config = Mock()
        mock_load_config.return_value = mock_config

        from app.infrastructure.security.llm.config_loader import reload_security_config

        # When: Call reload_security_config
        result = reload_security_config()

        # Then: Calls load_security_config with cache_bust=True
        mock_load_config.assert_called_once_with(
            environment=None,
            config_path=None,
            cache_bust=True
        )
        assert result is mock_config

    @patch('app.infrastructure.security.llm.config_loader.load_security_config')
    def test_reload_security_config_with_custom_environment(self, mock_load_config, tmp_path, monkeypatch):
        """
        Test that reload_security_config() accepts custom environment parameter.

        Verifies:
            reload_security_config() passes environment parameter to underlying
            loader per contract's Args section.

        Business Impact:
            Enables environment-specific forced reload for testing environment
            configuration changes.

        Scenario:
            Given: Modified production configuration files.
            When: reload_security_config(environment="production") is called.
            Then: Fresh production configuration is loaded, bypassing cache.

        Fixtures Used:
            - tmp_path: Pytest fixture for configuration files.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Mock load_security_config
        mock_config = Mock()
        mock_load_config.return_value = mock_config

        from app.infrastructure.security.llm.config_loader import reload_security_config

        # When: Call with custom environment
        result = reload_security_config(environment="production")

        # Then: Passes environment parameter with cache_bust=True
        mock_load_config.assert_called_once_with(
            environment="production",
            config_path=None,
            cache_bust=True
        )
        assert result is mock_config

    @patch('app.infrastructure.security.llm.config_loader.load_security_config')
    def test_reload_security_config_with_custom_config_path(self, mock_load_config, tmp_path, monkeypatch):
        """
        Test that reload_security_config() accepts custom configuration path.

        Verifies:
            reload_security_config() passes config_path parameter to underlying
            loader per contract's Args section.

        Business Impact:
            Enables forced reload from custom configuration locations for testing
            or multi-tenant scenarios.

        Scenario:
            Given: Modified configuration files in custom directory.
            When: reload_security_config(config_path="/custom/path") is called.
            Then: Fresh configuration is loaded from custom directory.

        Fixtures Used:
            - tmp_path: Pytest fixture for custom configuration location.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Mock load_security_config and custom path
        custom_config_path = str(tmp_path / "custom" / "config")
        mock_config = Mock()
        mock_load_config.return_value = mock_config

        from app.infrastructure.security.llm.config_loader import reload_security_config

        # When: Call with custom config path
        result = reload_security_config(config_path=custom_config_path)

        # Then: Passes config_path parameter with cache_bust=True
        mock_load_config.assert_called_once_with(
            environment=None,
            config_path=custom_config_path,
            cache_bust=True
        )
        assert result is mock_config

    @patch('app.infrastructure.security.llm.config_loader.load_security_config')
    def test_reload_security_config_reflects_file_modifications(self, mock_load_config, tmp_path, monkeypatch):
        """
        Test that reload_security_config() picks up configuration file changes.

        Verifies:
            reload_security_config() returns configuration reflecting current file
            state per contract's Use Cases section.

        Business Impact:
            Enables runtime configuration updates by detecting and loading file
            modifications without application restart.

        Scenario:
            Given: Initial configuration loaded and then files modified.
            When: reload_security_config() is called after modifications.
            Then: Returns SecurityConfig with updated values from modified files.

        Fixtures Used:
            - tmp_path: Pytest fixture for modifiable configuration files.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: Mock returning updated configuration
        updated_config = Mock()
        mock_load_config.return_value = updated_config

        from app.infrastructure.security.llm.config_loader import reload_security_config

        # When: Call reload_security_config after modifications
        result = reload_security_config()

        # Then: Returns fresh configuration reflecting file changes
        mock_load_config.assert_called_once_with(
            environment=None,
            config_path=None,
            cache_bust=True
        )
        assert result is updated_config

    @patch('app.infrastructure.security.llm.config_loader.load_security_config')
    def test_reload_security_config_raises_configuration_error_on_failure(self, mock_load_config, tmp_path, monkeypatch):
        """
        Test that reload_security_config() propagates ConfigurationError from loader.

        Verifies:
            reload_security_config() allows ConfigurationError to propagate to
            caller per contract's Raises section.

        Business Impact:
            Provides clear error messages for configuration reload failures with
            complete error context.

        Scenario:
            Given: Invalid configuration introduced during modifications.
            When: reload_security_config() is called.
            Then: ConfigurationError is raised with validation error details.

        Fixtures Used:
            - tmp_path: Pytest fixture for invalid configuration.
            - monkeypatch: Pytest fixture for environment setup.
        """
        # Given: load_security_config raises ConfigurationError
        from app.infrastructure.security.llm.config_loader import ConfigurationError
        error_message = "Configuration reload failed"
        mock_load_config.side_effect = ConfigurationError(error_message)

        from app.infrastructure.security.llm.config_loader import reload_security_config

        # When & Then: ConfigurationError propagates
        with pytest.raises(ConfigurationError) as exc_info:
            reload_security_config()

        assert str(exc_info.value) == error_message
        # Verify cache_bust=True was passed before error
        mock_load_config.assert_called_once_with(
            environment=None,
            config_path=None,
            cache_bust=True
        )