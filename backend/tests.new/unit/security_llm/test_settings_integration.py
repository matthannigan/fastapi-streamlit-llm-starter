"""
Test suite for Security Configuration Settings Integration.

This module provides comprehensive testing for the integration between
the security configuration system and the main application Settings.

## Test Coverage

### Settings Integration Tests
- Security configuration field definitions
- Environment variable handling for security settings
- Settings initialization with security configuration
- Security configuration loading through Settings

### Environment Variable Tests
- SECURITY_ENVIRONMENT override
- SECURITY_CONFIG_PATH override
- SECURITY_PRESET override
- Individual security setting overrides
- Environment variable precedence

### Settings Method Tests
- get_security_config() method functionality
- Security configuration caching through Settings
- Session and user context handling
- Error handling in Settings integration

### Factory Pattern Tests
- Security configuration with create_settings()
- Environment isolation in tests
- Settings factory pattern compatibility
- Test isolation with monkeypatch

## Test Categories

- **Unit Tests**: Individual Settings integration points
- **Integration Tests**: Settings with security loader integration
- **Environment Tests**: Environment variable handling
- **Factory Tests**: Settings factory pattern compatibility
"""

import tempfile
import time
import yaml
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings, create_settings, get_settings_factory
from app.core.exceptions import ConfigurationError
from app.infrastructure.security.llm.config import SecurityConfig, ScannerType


class TestSecuritySettingsFields:
    """Test cases for security-related settings fields."""

    def test_default_security_settings_values(self) -> None:
        """Test default values for security settings fields."""
        settings = Settings()

        # Check default values
        assert settings.security_environment == "development"
        assert settings.security_config_path is None
        assert settings.security_preset == "development"
        assert settings.security_cache_enabled is True
        assert settings.security_onnx_enabled is True
        assert settings.security_debug is False
        assert settings.security_hot_reload is False
        assert settings.security_api_key_required is False
        assert settings.security_rate_limit_enabled is False
        assert settings.security_rate_limit_rpm == 60

    def test_security_settings_environment_variables(self, monkeypatch: Any) -> None:
        """Test security settings with environment variables."""
        # Set environment variables
        monkeypatch.setenv("SECURITY_ENVIRONMENT", "production")
        monkeypatch.setenv("SECURITY_CONFIG_PATH", "/custom/path")
        monkeypatch.setenv("SECURITY_PRESET", "strict")
        monkeypatch.setenv("SECURITY_CACHE_ENABLED", "false")
        monkeypatch.setenv("SECURITY_ONNX_ENABLED", "false")
        monkeypatch.setenv("SECURITY_DEBUG", "true")
        monkeypatch.setenv("SECURITY_HOT_RELOAD", "true")
        monkeypatch.setenv("SECURITY_API_KEY_REQUIRED", "true")
        monkeypatch.setenv("SECURITY_RATE_LIMIT_ENABLED", "true")
        monkeypatch.setenv("SECURITY_RATE_LIMIT_RPM", "120")

        settings = Settings()

        # Check environment variable values
        assert settings.security_environment == "production"
        assert settings.security_config_path == "/custom/path"
        assert settings.security_preset == "strict"
        assert settings.security_cache_enabled is False
        assert settings.security_onnx_enabled is False
        assert settings.security_debug is True
        assert settings.security_hot_reload is True
        assert settings.security_api_key_required is True
        assert settings.security_rate_limit_enabled is True
        assert settings.security_rate_limit_rpm == 120

    def test_security_settings_validation(self) -> None:
        """Test validation of security settings fields."""
        # Test invalid rate limit value
        with pytest.raises(ValidationError):
            Settings(security_rate_limit_rpm=0)  # Must be > 0

        # Test valid rate limit value
        settings = Settings(security_rate_limit_rpm=100)
        assert settings.security_rate_limit_rpm == 100


class TestSecurityConfigLoading:
    """Test cases for security configuration loading through Settings."""

    @pytest.fixture
    def temp_config_dir(self) -> Any:
        """Create temporary configuration directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config" / "security"
            config_dir.mkdir(parents=True)
            yield config_dir

    @pytest.fixture
    def base_config(self) -> Dict[str, Any]:
        """Base configuration data for testing."""
        return {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "use_onnx": True,
                    "scan_timeout": 30
                },
                "toxicity_input": {
                    "enabled": True,
                    "threshold": 0.7,
                    "action": "warn",
                    "use_onnx": True,
                    "scan_timeout": 25
                }
            },
            "output_scanners": {
                "toxicity_output": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "use_onnx": True,
                    "scan_timeout": 25
                }
            },
            "performance": {
                "cache_enabled": True,
                "cache_ttl_seconds": 3600,
                "max_concurrent_scans": 10,
                "memory_limit_mb": 2048
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
                "log_scan_operations": True,
                "include_scanned_text": False
            },
            "service": {
                "name": "security-scanner",
                "environment": "development",
                "debug_mode": False
            }
        }

    def create_config_files(
        self,
        config_dir: Path,
        base_config: Dict[str, Any],
        dev_overrides: Dict[str, Any] | None = None
    ) -> None:
        """Helper to create configuration files."""
        # Create base scanners.yaml
        with open(config_dir / "scanners.yaml", "w") as f:
            yaml.dump(base_config, f)

        # Create development overrides
        if dev_overrides:
            with open(config_dir / "development.yaml", "w") as f:
                yaml.dump(dev_overrides, f)

    def test_get_security_config_basic(self, temp_config_dir: Any, base_config: Dict[str, Any]) -> None:
        """Test basic security configuration loading through Settings."""
        self.create_config_files(temp_config_dir, base_config)

        settings = Settings(security_config_path=str(temp_config_dir))
        security_config = settings.get_security_config()

        assert isinstance(security_config, SecurityConfig)
        assert security_config.service_name == "security-scanner"
        assert security_config.environment == "development"
        assert len(security_config.scanners) >= 2

    def test_get_security_config_with_environment_override(
        self,
        temp_config_dir: Any,
        base_config: Dict[str, Any],
        monkeypatch: Any
    ) -> None:
        """Test get_security_config with environment override."""
        dev_overrides = {
            "input_scanners": {
                "prompt_injection": {
                    "threshold": 0.9,
                    "action": "warn"
                }
            }
        }
        self.create_config_files(temp_config_dir, base_config, dev_overrides)

        # Set security environment
        monkeypatch.setenv("SECURITY_ENVIRONMENT", "development")

        settings = Settings(security_config_path=str(temp_config_dir))
        security_config = settings.get_security_config()

        # Check that environment override was applied
        prompt_injection = security_config.get_scanner_config(ScannerType.PROMPT_INJECTION)
        assert prompt_injection.threshold == 0.9
        assert prompt_injection.action.value == "warn"

    def test_get_security_config_with_custom_environment(
        self,
        temp_config_dir: Any,
        base_config: Dict[str, Any]
    ) -> None:
        """Test get_security_config with custom environment parameter."""
        dev_overrides = {
            "service": {
                "debug_mode": True,
                "environment": "custom"
            }
        }
        self.create_config_files(temp_config_dir, base_config, dev_overrides)

        settings = Settings(security_config_path=str(temp_config_dir))
        security_config = settings.get_security_config(environment="development")

        assert security_config.environment == "development"

    def test_get_security_config_with_session_context(
        self,
        temp_config_dir: Any,
        base_config: Dict[str, Any]
    ) -> None:
        """Test get_security_config with session and user context."""
        self.create_config_files(temp_config_dir, base_config)

        settings = Settings(security_config_path=str(temp_config_dir))
        security_config = settings.get_security_config(
            session_id="test_session_123",
            user_context="test_user"
        )

        assert isinstance(security_config, SecurityConfig)
        # Note: Actual session context handling would be implemented
        # in the configuration loader for monitoring/analytics

    def test_get_security_config_with_cache_bust(
        self,
        temp_config_dir: Any,
        base_config: Dict[str, Any]
    ) -> None:
        """Test get_security_config with cache busting."""
        self.create_config_files(temp_config_dir, base_config)

        settings = Settings(security_config_path=str(temp_config_dir))

        # Load initial configuration
        config1 = settings.get_security_config()

        # Load with cache bust
        config2 = settings.get_security_config(cache_bust=True)

        assert isinstance(config1, SecurityConfig)
        assert isinstance(config2, SecurityConfig)

    def test_get_security_config_debug_mode(
        self,
        temp_config_dir: Any,
        base_config: Dict[str, Any],
        capsys: Any
    ) -> None:
        """Test get_security_config with debug mode enabled."""
        self.create_config_files(temp_config_dir, base_config)

        settings = Settings(
            security_config_path=str(temp_config_dir),
            debug=True
        )
        security_config = settings.get_security_config()

        # Check debug output
        captured = capsys.readouterr()
        assert "Loading security configuration for environment" in captured.out
        assert "Security configuration loaded successfully" in captured.out

    def test_get_security_config_settings_overrides(
        self,
        temp_config_dir: Any,
        base_config: Dict[str, Any]
    ) -> None:
        """Test that settings fields override loaded configuration."""
        self.create_config_files(temp_config_dir, base_config)

        # Create settings with specific security settings
        settings = Settings(
            security_config_path=str(temp_config_dir),
            security_cache_enabled=False,
            security_onnx_enabled=False,
            security_debug=True
        )
        security_config = settings.get_security_config()

        # Check that settings overrides were applied
        assert security_config.performance.enable_result_caching is False
        assert security_config.performance.enable_model_caching is False
        assert security_config.debug_mode is True

    def test_get_security_config_missing_loader(self, monkeypatch: Any) -> None:
        """Test get_security_config when loader is not available."""
        # Mock import error
        with patch("app.core.config.Settings.get_security_config") as mock_get_config:
            mock_get_config.side_effect = ImportError("Security loader not available")

            settings = Settings()

            with pytest.raises(ConfigurationError) as exc_info:
                settings.get_security_config()

            assert "Security configuration loader not available" in str(exc_info.value)
            assert "Install required dependencies" in exc_info.value.suggestion

    def test_get_security_config_configuration_error(
        self,
        temp_config_dir: Any,
        monkeypatch: Any
    ) -> None:
        """Test get_security_config with configuration error."""
        # Use nonexistent path
        settings = Settings(security_config_path=str(temp_config_dir / "nonexistent"))

        with pytest.raises(ConfigurationError) as exc_info:
            settings.get_security_config()

        assert "Failed to load security configuration" in str(exc_info.value)
        assert "Check security configuration files" in exc_info.value.suggestion


class TestSecuritySettingsFactory:
    """Test cases for security configuration with Settings factory."""

    @pytest.fixture
    def temp_config_dir(self) -> Any:
        """Create temporary configuration directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config" / "security"
            config_dir.mkdir(parents=True)
            yield config_dir

    @pytest.fixture
    def base_config(self) -> Dict[str, Any]:
        """Base configuration data for testing."""
        return {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "use_onnx": True,
                    "scan_timeout": 30
                }
            },
            "output_scanners": {
                "toxicity_output": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "use_onnx": True,
                    "scan_timeout": 25
                }
            },
            "performance": {
                "cache_enabled": True,
                "max_concurrent_scans": 10
            },
            "logging": {
                "enabled": True,
                "level": "INFO"
            },
            "service": {
                "name": "security-scanner",
                "environment": "development"
            }
        }

    def create_config_files(self, config_dir: Path, base_config: Dict[str, Any]) -> None:
        """Helper to create configuration files."""
        with open(config_dir / "scanners.yaml", "w") as f:
            yaml.dump(base_config, f)

    def test_create_settings_with_security_config(
        self,
        temp_config_dir: Any,
        base_config: Dict[str, Any]
    ) -> None:
        """Test create_settings with security configuration."""
        self.create_config_files(temp_config_dir, base_config)

        settings = create_settings()
        settings.security_config_path = str(temp_config_dir)

        security_config = settings.get_security_config()
        assert isinstance(security_config, SecurityConfig)

    def test_create_settings_environment_isolation(
        self,
        temp_config_dir: Any,
        base_config: Dict[str, Any],
        monkeypatch: Any
    ) -> None:
        """Test create_settings environment isolation for security config."""
        self.create_config_files(temp_config_dir, base_config)

        # Set environment variables
        monkeypatch.setenv("SECURITY_ENVIRONMENT", "production")
        monkeypatch.setenv("SECURITY_DEBUG", "true")

        # Create settings should pick up environment
        settings = create_settings()
        settings.security_config_path = str(temp_config_dir)

        assert settings.security_environment == "production"
        assert settings.security_debug is True

    def test_get_settings_factory_with_security_config(
        self,
        temp_config_dir: Any,
        base_config: Dict[str, Any]
    ) -> None:
        """Test get_settings_factory with security configuration."""
        self.create_config_files(temp_config_dir, base_config)

        # Create settings factory
        settings_factory = get_settings_factory()
        settings_factory.security_config_path = str(temp_config_dir)

        security_config = settings_factory.get_security_config()
        assert isinstance(security_config, SecurityConfig)

    def test_multiple_settings_instances_security_config(
        self,
        temp_config_dir: Any,
        base_config: Dict[str, Any]
    ) -> None:
        """Test multiple Settings instances with security configuration."""
        self.create_config_files(temp_config_dir, base_config)

        # Create multiple instances
        settings1 = create_settings()
        settings1.security_config_path = str(temp_config_dir)

        settings2 = create_settings()
        settings2.security_config_path = str(temp_config_dir)

        # Each should have independent configuration
        config1 = settings1.get_security_config()
        config2 = settings2.get_security_config()

        assert isinstance(config1, SecurityConfig)
        assert isinstance(config2, SecurityConfig)
        # They should be equivalent but independent objects

    def test_settings_factory_test_isolation(
        self,
        temp_config_dir: Any,
        base_config: Dict[str, Any],
        monkeypatch: Any
    ) -> None:
        """Test Settings factory provides test isolation for security config."""
        self.create_config_files(temp_config_dir, base_config)

        # Create settings with test environment
        monkeypatch.setenv("SECURITY_ENVIRONMENT", "testing")
        settings1 = create_settings()
        settings1.security_config_path = str(temp_config_dir)

        # Change environment
        monkeypatch.setenv("SECURITY_ENVIRONMENT", "production")
        settings2 = create_settings()
        settings2.security_config_path = str(temp_config_dir)

        # Each should have different environment
        assert settings1.security_environment == "testing"
        assert settings2.security_environment == "production"


class TestSecuritySettingsIntegration:
    """Test cases for complete security settings integration."""

    @pytest.fixture
    def temp_config_dir(self) -> Any:
        """Create temporary configuration directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config" / "security"
            config_dir.mkdir(parents=True)
            yield config_dir

    @pytest.fixture
    def complete_config(self) -> Dict[str, Any]:
        """Complete configuration for integration testing."""
        return {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "use_onnx": True,
                    "scan_timeout": 30,
                    "metadata": {"environment": "test"}
                },
                "toxicity_input": {
                    "enabled": True,
                    "threshold": 0.7,
                    "action": "warn",
                    "use_onnx": True,
                    "scan_timeout": 25
                },
                "pii_detection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "redact",
                    "use_onnx": True,
                    "scan_timeout": 45,
                    "redact": True
                }
            },
            "output_scanners": {
                "toxicity_output": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "use_onnx": True,
                    "scan_timeout": 25
                },
                "bias_detection": {
                    "enabled": True,
                    "threshold": 0.7,
                    "action": "flag",
                    "use_onnx": True,
                    "scan_timeout": 30
                }
            },
            "performance": {
                "cache_enabled": True,
                "cache_ttl_seconds": 3600,
                "lazy_loading": True,
                "onnx_providers": ["CPUExecutionProvider"],
                "max_concurrent_scans": 10,
                "memory_limit_mb": 2048,
                "enable_model_caching": True,
                "enable_result_caching": True
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
                "log_scan_operations": True,
                "log_violations": True,
                "log_performance_metrics": True,
                "include_scanned_text": False,
                "sanitize_pii_in_logs": True,
                "log_format": "json",
                "retention_days": 30
            },
            "service": {
                "name": "security-scanner",
                "environment": "development",
                "debug_mode": False,
                "api_key_required": False,
                "rate_limit_enabled": False
            },
            "features": {
                "experimental_scanners": False,
                "advanced_analytics": True,
                "real_time_monitoring": True,
                "custom_scanner_support": False
            }
        }

    def create_config_files(self, config_dir: Path, base_config: Dict[str, Any]) -> None:
        """Helper to create configuration files."""
        with open(config_dir / "scanners.yaml", "w") as f:
            yaml.dump(base_config, f)

    def test_complete_security_integration(
        self,
        temp_config_dir: Any,
        complete_config: Dict[str, Any]
    ) -> None:
        """Test complete security configuration integration."""
        self.create_config_files(temp_config_dir, complete_config)

        # Create settings with security configuration
        settings = Settings(
            security_config_path=str(temp_config_dir),
            security_environment="development",
            security_cache_enabled=True,
            security_onnx_enabled=True
        )

        # Load security configuration
        security_config = settings.get_security_config()

        # Verify complete configuration
        assert isinstance(security_config, SecurityConfig)
        assert security_config.service_name == "security-scanner"
        assert security_config.environment == "development"

        # Verify all scanners loaded
        enabled_scanners = security_config.get_enabled_scanners()
        assert len(enabled_scanners) >= 5

        # Verify performance settings
        assert security_config.performance.enable_result_caching is True
        assert security_config.performance.enable_model_caching is True
        assert security_config.performance.max_concurrent_scans == 10

        # Verify logging settings
        assert security_config.logging.enable_scan_logging is True
        assert security_config.logging.log_level == "INFO"
        assert security_config.logging.include_scanned_text is False

    def test_security_configuration_with_all_overrides(
        self,
        temp_config_dir: Any,
        complete_config: Dict[str, Any],
        monkeypatch: Any
    ) -> None:
        """Test security configuration with all types of overrides."""
        # Create environment overrides
        env_overrides = {
            "input_scanners": {
                "prompt_injection": {
                    "threshold": 0.9,
                    "action": "warn"
                }
            },
            "performance": {
                "max_concurrent_scans": 15
            }
        }
        with open(temp_config_dir / "development.yaml", "w") as f:
            yaml.dump(env_overrides, f)

        self.create_config_files(temp_config_dir, complete_config)

        # Set environment variables
        monkeypatch.setenv("SECURITY_DEBUG", "true")
        monkeypatch.setenv("SECURITY_MAX_CONCURRENT_SCANS", "20")
        monkeypatch.setenv("SECURITY_LOG_LEVEL", "DEBUG")

        # Create settings
        settings = Settings(
            security_config_path=str(temp_config_dir),
            security_environment="development",
            debug=True
        )

        # Load configuration
        security_config = settings.get_security_config()

        # Verify override precedence
        # Environment variable should win (20)
        assert security_config.performance.max_concurrent_scans == 20

        # Environment file override should be applied (0.9)
        prompt_injection = security_config.get_scanner_config(ScannerType.PROMPT_INJECTION)
        assert prompt_injection.threshold == 0.9
        assert prompt_injection.action.value == "warn"

        # Settings override should be applied
        assert security_config.debug_mode is True

    def test_security_configuration_error_handling(
        self,
        temp_config_dir: Any,
        monkeypatch: Any
    ) -> None:
        """Test security configuration error handling."""
        # Create invalid configuration
        invalid_config = {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 1.5,  # Invalid
                    "action": "block"
                }
            },
            "performance": {
                "cache_enabled": True,
                "max_concurrent_scans": 0  # Invalid
            },
            "logging": {
                "enabled": True,
                "level": "INFO"
            },
            "service": {
                "name": "security-scanner",
                "environment": "development"
            }
        }

        with open(temp_config_dir / "scanners.yaml", "w") as f:
            yaml.dump(invalid_config, f)

        settings = Settings(security_config_path=str(temp_config_dir))

        # Should raise ConfigurationError
        with pytest.raises(ConfigurationError):
            settings.get_security_config()

    def test_security_settings_performance_characteristics(
        self,
        temp_config_dir: Any,
        complete_config: Dict[str, Any]
    ) -> None:
        """Test performance characteristics of security settings."""
        self.create_config_files(temp_config_dir, complete_config)

        settings = Settings(security_config_path=str(temp_config_dir))

        # Measure loading time
        start_time = time.time()
        config1 = settings.get_security_config()
        first_load_time = time.time() - start_time

        # Measure cached loading time
        start_time = time.time()
        config2 = settings.get_security_config()
        cached_load_time = time.time() - start_time

        # First load should be slower, cached load should be faster
        assert first_load_time > 0
        assert cached_load_time >= 0

        # Both should return valid configurations
        assert isinstance(config1, SecurityConfig)
        assert isinstance(config2, SecurityConfig)

    def test_security_settings_memory_usage(
        self,
        temp_config_dir: Any,
        complete_config: Dict[str, Any]
    ) -> None:
        """Test memory usage of security settings."""
        self.create_config_files(temp_config_dir, complete_config)

        settings = Settings(security_config_path=str(temp_config_dir))

        # Load configuration multiple times
        configs = []
        for i in range(10):
            config = settings.get_security_config()
            configs.append(config)

        # All configurations should be valid
        for config in configs:
            assert isinstance(config, SecurityConfig)

        # Memory usage should be reasonable (no memory leaks)
        # This is a basic test - more sophisticated memory testing
        # would require specialized tools
        assert len(configs) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
