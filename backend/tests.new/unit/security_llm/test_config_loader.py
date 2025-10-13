"""
Test suite for Security Configuration Loader.

This module provides comprehensive testing for the YAML-based configuration system,
including loading, validation, merging, and caching functionality.

## Test Coverage

### Configuration Loading Tests
- Base configuration loading from scanners.yaml
- Environment-specific override loading
- Environment variable interpolation
- Configuration file validation and error handling

### Configuration Merging Tests
- Base configuration with environment overrides
- Environment variable overrides
- Deep merging of nested structures
- Configuration precedence rules

### Validation Tests
- Pydantic model validation
- Scanner name validation
- Threshold range validation
- Performance settings validation
- Clear error messages with suggestions

### Performance Tests
- Configuration caching functionality
- Cache invalidation on file changes
- Hot reload functionality
- Memory usage and cleanup

### Error Handling Tests
- Missing configuration files
- Invalid YAML syntax
- Invalid configuration values
- Unknown scanner types
- Network and file system errors

## Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Performance Tests**: Caching and performance validation
- **Error Handling Tests**: Robustness and error recovery
"""

import tempfile
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Generator

import pytest

from app.infrastructure.security.llm.config_loader import (
    SecurityConfigLoader,
    ConfigurationError,
    load_security_config,
    reload_security_config,
    get_config_loader
)
from app.infrastructure.security.llm.config import SecurityConfig, ScannerType, ViolationAction


class TestSecurityConfigLoader:
    """Test cases for SecurityConfigLoader class."""

    @pytest.fixture
    def temp_config_dir(self) -> Generator[Path, None, None]:
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

    @pytest.fixture
    def dev_config_overrides(self) -> Dict[str, Any]:
        """Development environment configuration overrides."""
        return {
            "input_scanners": {
                "prompt_injection": {
                    "threshold": 0.9,
                    "action": "warn"
                }
            },
            "performance": {
                "cache_ttl_seconds": 300,
                "max_concurrent_scans": 5
            },
            "logging": {
                "level": "DEBUG",
                "include_scanned_text": True
            },
            "service": {
                "debug_mode": True
            }
        }

    def create_config_files(
        self,
        config_dir: Path,
        base_config: Dict[str, Any],
        dev_overrides: Dict[str, Any] | None = None,
        prod_overrides: Dict[str, Any] | None = None
    ) -> None:
        """Helper to create configuration files."""
        # Create base scanners.yaml
        with open(config_dir / "scanners.yaml", "w") as f:
            yaml.dump(base_config, f)

        # Create development overrides
        if dev_overrides:
            with open(config_dir / "dev.yaml", "w") as f:
                yaml.dump(dev_overrides, f)

        # Create production overrides
        if prod_overrides:
            with open(config_dir / "prod.yaml", "w") as f:
                yaml.dump(prod_overrides, f)

    def test_loader_initialization(self, temp_config_dir: Path) -> None:
        """Test SecurityConfigLoader initialization."""
        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            environment="test",
            cache_enabled=False
        )

        assert loader.config_path == temp_config_dir
        assert loader.environment == "test"
        assert loader.cache_enabled is False
        assert loader.debug_mode is False

    def test_loader_initialization_with_defaults(self, temp_config_dir: Path) -> None:
        """Test SecurityConfigLoader initialization with defaults."""
        loader = SecurityConfigLoader(config_path=temp_config_dir)

        assert loader.config_path == temp_config_dir
        assert loader.environment == "development"
        assert loader.cache_enabled is True
        assert loader.debug_mode is False

    def test_loader_initialization_nonexistent_directory(self) -> None:
        """Test loader initialization with nonexistent directory."""
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfigLoader(config_path="/nonexistent/path")

        assert "Configuration directory does not exist" in str(exc_info.value)
        assert exc_info.value.suggestion is not None
        assert "Create the configuration directory" in exc_info.value.suggestion

    def test_load_base_configuration(self, temp_config_dir: Path, base_config: Dict[str, Any]) -> None:
        """Test loading base configuration."""
        self.create_config_files(temp_config_dir, base_config)

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            cache_enabled=False
        )

        config = loader.load_config()

        assert isinstance(config, SecurityConfig)
        assert config.service_name == "security-scanner"
        assert config.environment == "development"
        assert len(config.scanners) == 3  # prompt_injection, toxicity_input, toxicity_output

        # Check specific scanner configurations
        prompt_injection = config.get_scanner_config(ScannerType.PROMPT_INJECTION)
        assert prompt_injection is not None
        assert prompt_injection.enabled is True
        assert prompt_injection.threshold == 0.8
        assert prompt_injection.action == ViolationAction.BLOCK

    def test_load_configuration_with_environment_overrides(
        self,
        temp_config_dir: Path,
        base_config: Dict[str, Any],
        dev_config_overrides: Dict[str, Any]
    ) -> None:
        """Test loading configuration with environment overrides."""
        self.create_config_files(temp_config_dir, base_config, dev_config_overrides)

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            environment="development",
            cache_enabled=False
        )

        config = loader.load_config()

        # Check that overrides were applied
        prompt_injection = config.get_scanner_config(ScannerType.PROMPT_INJECTION)
        assert prompt_injection is not None
        assert prompt_injection.threshold == 0.9  # Override applied
        assert prompt_injection.action == ViolationAction.WARN  # Override applied

        # Check performance overrides
        assert config.performance.cache_ttl_seconds == 300  # Override applied
        assert config.performance.max_concurrent_scans == 5  # Override applied

        # Check logging overrides
        assert config.logging.log_level == "DEBUG"  # Override applied
        assert config.logging.include_scanned_text is True  # Override applied

    def test_load_configuration_with_environment_variables(
        self,
        temp_config_dir: Path,
        base_config: Dict[str, Any],
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading configuration with environment variable overrides."""
        self.create_config_files(temp_config_dir, base_config)

        # Set environment variables
        monkeypatch.setenv("SECURITY_PRESET", "production")
        monkeypatch.setenv("SECURITY_DEBUG", "true")
        monkeypatch.setenv("SECURITY_CACHE_ENABLED", "false")
        monkeypatch.setenv("SECURITY_MAX_CONCURRENT_SCANS", "15")
        monkeypatch.setenv("SECURITY_LOG_LEVEL", "ERROR")

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            cache_enabled=False
        )

        config = loader.load_config()

        # Check that environment variables were applied
        assert config.debug_mode is True  # From SECURITY_DEBUG
        assert config.performance.max_concurrent_scans == 15  # From SECURITY_MAX_CONCURRENT_SCANS

    def test_environment_variable_interpolation(self, temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variable interpolation in YAML."""
        # Set environment variables
        monkeypatch.setenv("CUSTOM_THRESHOLD", "0.85")
        monkeypatch.setenv("SERVICE_NAME", "custom-scanner")
        monkeypatch.setenv("DEFAULT_TIMEOUT", "35")

        config_with_interpolation = {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": "${CUSTOM_THRESHOLD}",
                    "action": "block",
                    "scan_timeout": "${DEFAULT_TIMEOUT}"
                }
            },
            "service": {
                "name": "${SERVICE_NAME}",
                "environment": "development"
            },
            "performance": {
                "cache_enabled": True,
                "max_concurrent_scans": 10
            },
            "logging": {
                "enabled": True,
                "level": "INFO"
            }
        }

        self.create_config_files(temp_config_dir, config_with_interpolation)

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            cache_enabled=False
        )

        config = loader.load_config()

        # Check that interpolation worked
        assert config.service_name == "custom-scanner"
        prompt_injection = config.get_scanner_config(ScannerType.PROMPT_INJECTION)
        assert prompt_injection is not None
        assert prompt_injection.threshold == 0.85
        assert prompt_injection.scan_timeout == 35

    def test_configuration_precedence(
        self,
        temp_config_dir: Path,
        base_config: Dict[str, Any],
        dev_config_overrides: Dict[str, Any],
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test configuration precedence rules."""
        self.create_config_files(temp_config_dir, base_config, dev_config_overrides)

        # Set environment variable (highest precedence)
        monkeypatch.setenv("SECURITY_MAX_CONCURRENT_SCANS", "20")

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            environment="development",
            cache_enabled=False
        )

        config = loader.load_config()

        # Base: 10, Dev override: 5, Env var: 20
        # Environment variable should win
        assert config.performance.max_concurrent_scans == 20

    def test_configuration_caching(
        self,
        temp_config_dir: Path,
        base_config: Dict[str, Any],
        dev_config_overrides: Dict[str, Any]
    ) -> None:
        """Test configuration caching functionality."""
        self.create_config_files(temp_config_dir, base_config, dev_config_overrides)

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            environment="development",
            cache_enabled=True,
            cache_ttl=60
        )

        # First load should cache the configuration
        config1 = loader.load_config()
        assert loader.get_cache_info()["cached_entries"] == 1

        # Second load should use cache
        config2 = loader.load_config()
        assert config1 is config2  # Should be the same object (cached)

        # Cache bust should force reload
        config3 = loader.load_config(cache_bust=True)
        assert config1 is not config3  # Should be different objects

    def test_cache_invalidation_on_file_change(
        self,
        temp_config_dir: Path,
        base_config: Dict[str, Any],
        dev_config_overrides: Dict[str, Any]
    ) -> None:
        """Test cache invalidation when configuration files change."""
        self.create_config_files(temp_config_dir, base_config, dev_config_overrides)

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            environment="development",
            cache_enabled=True
        )

        # Load initial configuration
        config1 = loader.load_config()
        prompt_injection_config = config1.get_scanner_config(ScannerType.PROMPT_INJECTION)
        assert prompt_injection_config is not None
        initial_threshold = prompt_injection_config.threshold

        # Modify configuration file
        time.sleep(0.1)  # Ensure different timestamp
        modified_overrides = dev_config_overrides.copy()
        modified_overrides["input_scanners"]["prompt_injection"]["threshold"] = 0.95

        with open(temp_config_dir / "dev.yaml", "w") as f:
            yaml.dump(modified_overrides, f)

        # Load again should detect file change and reload
        config2 = loader.load_config()
        prompt_injection_config2 = config2.get_scanner_config(ScannerType.PROMPT_INJECTION)
        assert prompt_injection_config2 is not None
        new_threshold = prompt_injection_config2.threshold

        assert initial_threshold != new_threshold
        assert new_threshold == 0.95

    def test_missing_base_configuration_file(self, temp_config_dir: Path) -> None:
        """Test handling of missing base configuration file."""
        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            cache_enabled=False
        )

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_config()

        assert "Base configuration file not found" in str(exc_info.value)
        assert "scanners.yaml" in str(exc_info.value)
        assert exc_info.value.suggestion is not None
        assert "Create scanners.yaml" in exc_info.value.suggestion

    def test_invalid_yaml_syntax(self, temp_config_dir: Path, base_config: Dict[str, Any]) -> None:
        """Test handling of invalid YAML syntax."""
        # Create file with invalid YAML
        with open(temp_config_dir / "scanners.yaml", "w") as f:
            f.write("invalid: yaml: content:\n  - missing\n    proper: indentation")

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            cache_enabled=False
        )

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_config()

        assert "Invalid YAML syntax" in str(exc_info.value)
        assert exc_info.value.suggestion is not None
        assert "Fix YAML syntax errors" in exc_info.value.suggestion

    def test_invalid_configuration_values(self, temp_config_dir: Path) -> None:
        """Test handling of invalid configuration values."""
        invalid_config = {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 1.5,  # Invalid threshold (> 1.0)
                    "action": "block"
                }
            },
            "performance": {
                "cache_enabled": True,
                "max_concurrent_scans": 0  # Invalid value (< 1)
            },
            "logging": {
                "enabled": True,
                "level": "INFO"
            }
        }

        self.create_config_files(temp_config_dir, invalid_config)

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            cache_enabled=False
        )

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_config()

        assert "Configuration validation failed" in str(exc_info.value)

    def test_unknown_scanner_types(self, temp_config_dir: Path) -> None:
        """Test handling of unknown scanner types."""
        config_with_unknown_scanners = {
            "input_scanners": {
                "unknown_scanner": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block"
                },
                "another_unknown": {
                    "enabled": True,
                    "threshold": 0.7,
                    "action": "warn"
                }
            },
            "output_scanners": {
                "toxicity_output": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block"
                }
            },
            "performance": {
                "cache_enabled": True,
                "max_concurrent_scans": 10
            },
            "logging": {
                "enabled": True,
                "level": "INFO"
            }
        }

        self.create_config_files(temp_config_dir, config_with_unknown_scanners)

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            cache_enabled=False
        )

        config = loader.load_config()

        # Should only load known scanners
        assert len(config.scanners) == 1  # Only toxicity_output
        assert ScannerType.TOXICITY_OUTPUT in config.scanners

    def test_configuration_info_methods(self, temp_config_dir: Path, base_config: Dict[str, Any]) -> None:
        """Test configuration information methods."""
        self.create_config_files(temp_config_dir, base_config)

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            debug_mode=True
        )

        # Test cache info
        cache_info = loader.get_cache_info()
        assert cache_info["cache_enabled"] is True
        assert cache_info["config_path"] == str(temp_config_dir)
        assert cache_info["environment"] == "development"

        # Test cache clearing
        loader.load_config()  # Load to populate cache
        loader.clear_cache()
        cache_info = loader.get_cache_info()
        assert cache_info["cached_entries"] == 0

    def test_debug_mode_logging(
        self,
        temp_config_dir: Path,
        base_config: Dict[str, Any],
        capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test debug mode logging output."""
        self.create_config_files(temp_config_dir, base_config)

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            debug_mode=True,
            cache_enabled=False
        )

        config = loader.load_config()

        # Check debug output
        captured = capsys.readouterr()
        assert "Loading security configuration for environment: development" in captured.out
        assert "Successfully loaded security configuration" in captured.out
        assert f"Enabled scanners: {len(config.get_enabled_scanners())}" in captured.out


class TestConfigurationLoaderFunctions:
    """Test cases for module-level configuration loader functions."""

    @pytest.fixture
    def temp_config_dir(self) -> Generator[Path, None, None]:
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
                "cache_ttl_seconds": 3600,
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

    def test_load_security_config_function(self, temp_config_dir: Path, base_config: Dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the load_security_config function."""
        self.create_config_files(temp_config_dir, base_config)

        # Set configuration path
        monkeypatch.setenv("SECURITY_CONFIG_PATH", str(temp_config_dir))

        config = load_security_config()

        assert isinstance(config, SecurityConfig)
        assert config.service_name == "security-scanner"
        assert len(config.scanners) == 2

    def test_load_security_config_with_custom_path(self, temp_config_dir: Path, base_config: Dict[str, Any]) -> None:
        """Test load_security_config with custom path."""
        self.create_config_files(temp_config_dir, base_config)

        config = load_security_config(config_path=str(temp_config_dir))

        assert isinstance(config, SecurityConfig)
        assert config.service_name == "security-scanner"

    def test_load_security_config_with_environment(self, temp_config_dir: Path, base_config: Dict[str, Any]) -> None:
        """Test load_security_config with environment override."""
        self.create_config_files(temp_config_dir, base_config)

        # Create environment override file
        env_overrides = {
            "input_scanners": {
                "prompt_injection": {
                    "threshold": 0.9
                }
            }
        }
        with open(temp_config_dir / "production.yaml", "w") as f:
            yaml.dump(env_overrides, f)

        config = load_security_config(
            config_path=str(temp_config_dir),
            environment="production"
        )

        prompt_injection = config.get_scanner_config(ScannerType.PROMPT_INJECTION)
        assert prompt_injection is not None
        assert prompt_injection.threshold == 0.9

    def test_reload_security_config_function(self, temp_config_dir: Path, base_config: Dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the reload_security_config function."""
        self.create_config_files(temp_config_dir, base_config)

        # Set configuration path
        monkeypatch.setenv("SECURITY_CONFIG_PATH", str(temp_config_dir))

        # Load initial configuration
        config1 = load_security_config()

        # Load again should use cache
        config2 = reload_security_config()
        assert config1 is not config2  # Should be different objects (cache busted)

    def test_get_config_loader_singleton(self, temp_config_dir: Path, base_config: Dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the get_config_loader singleton function."""
        self.create_config_files(temp_config_dir, base_config)

        # Set configuration path
        monkeypatch.setenv("SECURITY_CONFIG_PATH", str(temp_config_dir))

        loader1 = get_config_loader()
        loader2 = get_config_loader()

        # Should return the same instance
        assert loader1 is loader2

    def test_load_security_config_cache_bust(self, temp_config_dir: Path, base_config: Dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
        """Test load_security_config with cache_bust parameter."""
        self.create_config_files(temp_config_dir, base_config)

        # Set configuration path
        monkeypatch.setenv("SECURITY_CONFIG_PATH", str(temp_config_dir))

        # Load initial configuration
        config1 = load_security_config()

        # Load with cache bust should create new instance
        config2 = load_security_config(cache_bust=True)
        assert config1 is not config2


class TestConfigurationErrorHandling:
    """Test cases for configuration error handling."""

    def test_configuration_error_creation(self) -> None:
        """Test ConfigurationError creation and formatting."""
        error = ConfigurationError(
            "Test error message",
            suggestion="Test suggestion",
            file_path="/test/path.yaml"
        )

        error_str = str(error)
        assert "Test error message" in error_str
        assert "Test suggestion" in error_str
        assert "/test/path.yaml" in error_str

    def test_configuration_error_without_suggestion(self) -> None:
        """Test ConfigurationError without suggestion."""
        error = ConfigurationError("Test error message")

        error_str = str(error)
        assert "Test error message" in error_str
        assert "Suggestion:" not in error_str

    def test_configuration_error_without_file_path(self) -> None:
        """Test ConfigurationError without file path."""
        error = ConfigurationError(
            "Test error message",
            suggestion="Test suggestion"
        )

        error_str = str(error)
        assert "Test error message" in error_str
        assert "Test suggestion" in error_str
        assert "Configuration error in" not in error_str


class TestPerformanceAndMemory:
    """Test cases for performance and memory usage."""

    @pytest.fixture
    def temp_config_dir(self) -> Generator[Path, None, None]:
        """Create temporary configuration directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config" / "security"
            config_dir.mkdir(parents=True)
            yield config_dir

    @pytest.fixture
    def large_config(self) -> Dict[str, Any]:
        """Create a large configuration for performance testing."""
        config: Dict[str, Any] = {
            "input_scanners": {},
            "output_scanners": {},
            "performance": {
                "cache_enabled": True,
                "cache_ttl_seconds": 3600,
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

        # Add many scanners
        input_scanners = config["input_scanners"]
        for i in range(100):
            input_scanners[f"scanner_{i}"] = {
                "enabled": True,
                "threshold": 0.8,
                "action": "block",
                "scan_timeout": 30
            }

        return config

    def test_large_configuration_loading(self, temp_config_dir: Path, large_config: Dict[str, Any]) -> None:
        """Test loading large configuration files."""
        with open(temp_config_dir / "scanners.yaml", "w") as f:
            yaml.dump(large_config, f)

        loader = SecurityConfigLoader(
            config_path=temp_config_dir,
            cache_enabled=False
        )

        start_time = time.time()
        config = loader.load_config()
        load_time = time.time() - start_time

        # Should load within reasonable time (less than 1 second)
        assert load_time < 1.0
        assert isinstance(config, SecurityConfig)

    def test_memory_cleanup(self, temp_config_dir: Path) -> None:
        """Test memory cleanup after loader is destroyed."""
        config_dict = {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "use_onnx": True,
                    "scan_timeout": 30
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

        with open(temp_config_dir / "scanners.yaml", "w") as f:
            yaml.dump(config_dict, f)

        # Create loader and load configuration
        loader = SecurityConfigLoader(config_path=temp_config_dir)
        config = loader.load_config()

        # Check cache is populated
        assert len(loader._cache) > 0

        # Clear cache
        loader.clear_cache()
        assert len(loader._cache) == 0

        # Loader should be garbage collectable
        del loader
        # No assertion needed - just ensure no exceptions during cleanup


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
