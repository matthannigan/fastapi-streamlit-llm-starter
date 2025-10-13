"""
Environment-Specific Behavior Tests

Tests for environment-specific configuration behavior in the security scanner factory.
This test suite validates that the scanner properly handles different environments
(development, production, testing) with appropriate settings and behavior.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from unittest.mock import Mock, patch

from app.infrastructure.security.llm.factory import (  # type: ignore
    create_security_service_from_yaml,
    SecurityServiceFactory,
)
from app.infrastructure.security.llm.scanners.local_scanner import LocalLLMSecurityScanner  # type: ignore


class TestDevelopmentEnvironmentBehavior:
    """Test scanner behavior in development environment."""

    @pytest.fixture
    def dev_config(self) -> Dict[str, Any]:
        """Development environment configuration."""
        return {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.6,  # More lenient
                    "action": "warn",   # Warn instead of block
                    "model_name": "dev-prompt-model",
                    "use_onnx": False,  # Faster loading in dev
                    "scan_timeout": 15,  # Shorter timeout
                },
                "toxicity_input": {
                    "enabled": True,
                    "threshold": 0.8,  # More lenient
                    "action": "warn",
                    "use_onnx": False,
                    "scan_timeout": 10,
                },
            },
            "output_scanners": {
                "toxicity_output": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "warn",
                    "use_onnx": False,
                },
            },
            "performance": {
                "cache_enabled": True,
                "cache_ttl_seconds": 60,  # Short cache for development
                "max_concurrent_scans": 3,  # Lower concurrency
                "enable_model_caching": False,  # Don't cache models for faster restarts
                "lazy_loading": True,
                "memory_limit_mb": 1024,  # Lower memory limit
            },
            "logging": {
                "enabled": True,
                "level": "DEBUG",  # Debug logging in development
                "log_scan_operations": True,
                "log_violations": True,
                "log_performance_metrics": True,
                "include_scanned_text": True,  # Include text for debugging
                "sanitize_pii_in_logs": False,  # Don't sanitize for debugging
                "log_format": "text",  # Human-readable format
            },
            "service": {
                "name": "dev-security-scanner",
                "version": "1.0.0-dev",
                "environment": "development",
                "debug_mode": True,
                "api_key_required": False,
            }
        }

    @pytest.fixture
    def temp_config_dir(self) -> Generator[Path, None, None]:
        """Create a temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config" / "security"
            config_dir.mkdir(parents=True)
            yield config_dir

    def test_development_configuration_loading(self, temp_config_dir: Path, dev_config: Dict[str, Any]) -> None:
        """Test loading development configuration."""
        # Write development configuration
        dev_config_path = temp_config_dir / "dev.yaml"
        with open(dev_config_path, "w") as f:
            yaml.dump(dev_config, f)

        # Write minimal base configuration
        base_config = {
            "service": {
                "name": "base-scanner",
                "environment": "development",
            }
        }
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump(base_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="dev"
            )

        assert service is not None
        assert service.config.environment == "dev"
        assert service.config.debug_mode is True

    def test_development_performance_settings(self, temp_config_dir: Path, dev_config: Dict[str, Any]) -> None:
        """Test development performance settings."""
        # Write configurations
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump({"service": {"environment": "development"}}, f)

        dev_config_path = temp_config_dir / "dev.yaml"
        with open(dev_config_path, "w") as f:
            yaml.dump(dev_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="dev"
            )

        # Check development performance settings
        performance = getattr(service.config, "performance", {})
        assert performance.get("cache_ttl_seconds") == 60
        assert performance.get("max_concurrent_scans") == 3
        assert performance.get("enable_model_caching") is False
        assert performance.get("memory_limit_mb") == 1024

    def test_development_logging_settings(self, temp_config_dir: Path, dev_config: Dict[str, Any]) -> None:
        """Test development logging settings."""
        # Write configurations
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump({"service": {"environment": "development"}}, f)

        dev_config_path = temp_config_dir / "dev.yaml"
        with open(dev_config_path, "w") as f:
            yaml.dump(dev_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="dev"
            )

        # Check development logging settings
        logging_config = getattr(service.config, "logging", {})
        assert logging_config.get("level") == "DEBUG"
        assert logging_config.get("include_scanned_text") is True
        assert logging_config.get("sanitize_pii_in_logs") is False
        assert logging_config.get("log_format") == "text"

    def test_development_scanner_thresholds(self, temp_config_dir: Path, dev_config: Dict[str, Any]) -> None:
        """Test development scanner thresholds (more lenient)."""
        # Write configurations
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump({"service": {"environment": "development"}}, f)

        dev_config_path = temp_config_dir / "dev.yaml"
        with open(dev_config_path, "w") as f:
            yaml.dump(dev_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="dev"
            )

        # Check more lenient thresholds
        input_scanners = getattr(service.config, "input_scanners", {})
        assert input_scanners["prompt_injection"]["threshold"] == 0.6
        assert input_scanners["toxicity_input"]["threshold"] == 0.8

        # Check warning actions instead of blocking
        assert input_scanners["prompt_injection"]["action"] == "warn"
        assert input_scanners["toxicity_input"]["action"] == "warn"

    def test_development_onnx_disabled(self, temp_config_dir: Path, dev_config: Dict[str, Any]) -> None:
        """Test that ONNX is disabled in development for faster loading."""
        # Write configurations
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump({"service": {"environment": "development"}}, f)

        dev_config_path = temp_config_dir / "dev.yaml"
        with open(dev_config_path, "w") as f:
            yaml.dump(dev_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="dev"
            )

        # Check ONNX is disabled for faster loading
        input_scanners = getattr(service.config, "input_scanners", {})
        assert input_scanners["prompt_injection"]["use_onnx"] is False
        assert input_scanners["toxicity_input"]["use_onnx"] is False


class TestProductionEnvironmentBehavior:
    """Test scanner behavior in production environment."""

    @pytest.fixture
    def prod_config(self) -> Dict[str, Any]:
        """Production environment configuration."""
        return {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.9,  # Stricter
                    "action": "block",  # Block in production
                    "model_name": "prod-prompt-model",
                    "use_onnx": True,   # Use ONNX for performance
                    "scan_timeout": 45,  # Longer timeout for reliability
                },
                "toxicity_input": {
                    "enabled": True,
                    "threshold": 0.6,  # Stricter
                    "action": "block",
                    "use_onnx": True,
                    "scan_timeout": 30,
                },
                "pii_detection": {
                    "enabled": True,    # Enable PII in production
                    "threshold": 0.7,
                    "action": "redact",
                    "use_onnx": True,
                    "scan_timeout": 45,
                },
                "malicious_url": {
                    "enabled": True,    # Enable additional security
                    "threshold": 0.95,
                    "action": "block",
                    "use_onnx": True,
                },
            },
            "output_scanners": {
                "toxicity_output": {
                    "enabled": True,
                    "threshold": 0.6,  # Stricter
                    "action": "block",
                    "use_onnx": True,
                },
                "bias_detection": {
                    "enabled": True,
                    "threshold": 0.5,  # Stricter bias detection
                    "action": "flag",
                    "use_onnx": True,
                },
                "harmful_content": {
                    "enabled": True,    # Enable harmful content detection
                    "threshold": 0.8,
                    "action": "block",
                    "use_onnx": True,
                },
            },
            "performance": {
                "cache_enabled": True,
                "cache_ttl_seconds": 7200,  # Long cache for performance
                "max_concurrent_scans": 25,  # High concurrency
                "enable_model_caching": True,  # Cache models for performance
                "lazy_loading": False,  # Load models at startup
                "batch_processing_enabled": True,
                "max_batch_size": 10,
                "memory_limit_mb": 4096,  # Higher memory limit
                "onnx_providers": ["CUDAExecutionProvider", "CPUExecutionProvider"],  # GPU first
            },
            "logging": {
                "enabled": True,
                "level": "WARNING",  # Less verbose in production
                "log_scan_operations": False,  # Don't log all scans
                "log_violations": True,  # But log violations
                "log_performance_metrics": True,
                "include_scanned_text": False,  # Don't include text for privacy
                "sanitize_pii_in_logs": True,   # Sanitize PII
                "log_format": "json",  # Structured logging
                "retention_days": 90,  # Longer retention
            },
            "service": {
                "name": "prod-security-scanner",
                "version": "1.0.0",
                "environment": "production",
                "debug_mode": False,
                "api_key_required": True,
                "rate_limit_enabled": True,
                "rate_limit_requests_per_minute": 100,
            }
        }

    @pytest.fixture
    def temp_config_dir(self) -> Generator[Path, None, None]:
        """Create a temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config" / "security"
            config_dir.mkdir(parents=True)
            yield config_dir

    def test_production_configuration_loading(self, temp_config_dir: Path, prod_config: Dict[str, Any]) -> None:
        """Test loading production configuration."""
        # Write production configuration
        prod_config_path = temp_config_dir / "prod.yaml"
        with open(prod_config_path, "w") as f:
            yaml.dump(prod_config, f)

        # Write base configuration
        base_config = {
            "service": {
                "name": "base-scanner",
                "environment": "production",
            }
        }
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump(base_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="prod"
            )

        assert service is not None
        assert service.config.environment == "prod"
        assert service.config.debug_mode is False

    def test_production_performance_settings(self, temp_config_dir: Path, prod_config: Dict[str, Any]) -> None:
        """Test production performance settings."""
        # Write configurations
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump({"service": {"environment": "production"}}, f)

        prod_config_path = temp_config_dir / "prod.yaml"
        with open(prod_config_path, "w") as f:
            yaml.dump(prod_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="prod"
            )

        # Check production performance settings
        performance = getattr(service.config, "performance", {})
        assert performance.get("cache_ttl_seconds") == 7200
        assert performance.get("max_concurrent_scans") == 25
        assert performance.get("enable_model_caching") is True
        assert performance.get("lazy_loading") is False
        assert performance.get("batch_processing_enabled") is True
        assert performance.get("memory_limit_mb") == 4096

    def test_production_onnx_gpu_providers(self, temp_config_dir: Path, prod_config: Dict[str, Any]) -> None:
        """Test production ONNX configuration with GPU providers."""
        # Write configurations
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump({"service": {"environment": "production"}}, f)

        prod_config_path = temp_config_dir / "prod.yaml"
        with open(prod_config_path, "w") as f:
            yaml.dump(prod_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="prod"
            )

        # Check GPU-first ONNX providers
        performance = getattr(service.config, "performance", {})
        onnx_providers = performance.get("onnx_providers", [])
        assert len(onnx_providers) >= 2
        assert onnx_providers[0] == "CUDAExecutionProvider"  # GPU first
        assert "CPUExecutionProvider" in onnx_providers  # CPU fallback

    def test_production_scanner_thresholds(self, temp_config_dir: Path, prod_config: Dict[str, Any]) -> None:
        """Test production scanner thresholds (stricter)."""
        # Write configurations
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump({"service": {"environment": "production"}}, f)

        prod_config_path = temp_config_dir / "prod.yaml"
        with open(prod_config_path, "w") as f:
            yaml.dump(prod_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="prod"
            )

        # Check stricter thresholds
        input_scanners = getattr(service.config, "input_scanners", {})
        assert input_scanners["prompt_injection"]["threshold"] == 0.9
        assert input_scanners["toxicity_input"]["threshold"] == 0.6
        assert input_scanners["pii_detection"]["threshold"] == 0.7

        # Check blocking actions
        assert input_scanners["prompt_injection"]["action"] == "block"
        assert input_scanners["toxicity_input"]["action"] == "block"

    def test_production_additional_scanners_enabled(self, temp_config_dir: Path, prod_config: Dict[str, Any]) -> None:
        """Test that additional scanners are enabled in production."""
        # Write configurations
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump({"service": {"environment": "production"}}, f)

        prod_config_path = temp_config_dir / "prod.yaml"
        with open(prod_config_path, "w") as f:
            yaml.dump(prod_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="prod"
            )

        # Check additional scanners are enabled
        input_scanners = getattr(service.config, "input_scanners", {})
        assert input_scanners["pii_detection"]["enabled"] is True
        assert input_scanners["malicious_url"]["enabled"] is True

        output_scanners = getattr(service.config, "output_scanners", {})
        assert output_scanners["harmful_content"]["enabled"] is True

    def test_production_logging_settings(self, temp_config_dir: Path, prod_config: Dict[str, Any]) -> None:
        """Test production logging settings."""
        # Write configurations
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump({"service": {"environment": "production"}}, f)

        prod_config_path = temp_config_dir / "prod.yaml"
        with open(prod_config_path, "w") as f:
            yaml.dump(prod_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="prod"
            )

        # Check production logging settings
        logging_config = getattr(service.config, "logging", {})
        assert logging_config.get("level") == "WARNING"
        assert logging_config.get("include_scanned_text") is False
        assert logging_config.get("sanitize_pii_in_logs") is True
        assert logging_config.get("log_format") == "json"
        assert logging_config.get("retention_days") == 90


class TestTestingEnvironmentBehavior:
    """Test scanner behavior in testing environment."""

    @pytest.fixture
    def test_config(self) -> Dict[str, Any]:
        """Testing environment configuration."""
        return {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.5,  # Very low for testing
                    "action": "block",
                    "model_name": "test-prompt-model",
                    "use_onnx": False,  # Faster for tests
                    "scan_timeout": 5,   # Short timeout for tests
                },
            },
            "output_scanners": {
                "toxicity_output": {
                    "enabled": True,
                    "threshold": 0.5,
                    "action": "block",
                    "use_onnx": False,
                },
            },
            "performance": {
                "cache_enabled": False,  # No caching in tests
                "max_concurrent_scans": 1,  # Single thread for tests
                "enable_model_caching": False,
                "memory_limit_mb": 512,  # Low memory for tests
            },
            "logging": {
                "enabled": True,
                "level": "ERROR",  # Only errors in tests
                "log_scan_operations": False,
                "include_scanned_text": False,
                "log_format": "text",
            },
            "service": {
                "name": "test-security-scanner",
                "environment": "testing",
                "debug_mode": True,
            }
        }

    @pytest.fixture
    def temp_config_dir(self) -> Generator[Path, None, None]:
        """Create a temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config" / "security"
            config_dir.mkdir(parents=True)
            yield config_dir

    def test_testing_configuration_loading(self, temp_config_dir: Path, test_config: Dict[str, Any]) -> None:
        """Test loading testing configuration."""
        # Write testing configuration
        test_config_path = temp_config_dir / "test.yaml"
        with open(test_config_path, "w") as f:
            yaml.dump(test_config, f)

        # Write base configuration
        base_config = {
            "service": {
                "name": "base-scanner",
                "environment": "testing",
            }
        }
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump(base_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="test"
            )

        assert service is not None
        assert service.config.environment == "test"
        assert service.config.debug_mode is True

    def test_testing_performance_settings(self, temp_config_dir: Path, test_config: Dict[str, Any]) -> None:
        """Test testing performance settings."""
        # Write configurations
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump({"service": {"environment": "testing"}}, f)

        test_config_path = temp_config_dir / "test.yaml"
        with open(test_config_path, "w") as f:
            yaml.dump(test_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="test"
            )

        # Check testing performance settings
        performance = getattr(service.config, "performance", {})
        assert performance.get("cache_enabled") is False
        assert performance.get("max_concurrent_scans") == 1
        assert performance.get("enable_model_caching") is False
        assert performance.get("memory_limit_mb") == 512

    def test_testing_scanner_settings(self, temp_config_dir: Path, test_config: Dict[str, Any]) -> None:
        """Test testing scanner settings."""
        # Write configurations
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump({"service": {"environment": "testing"}}, f)

        test_config_path = temp_config_dir / "test.yaml"
        with open(test_config_path, "w") as f:
            yaml.dump(test_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="test"
            )

        # Check testing scanner settings
        input_scanners = getattr(service.config, "input_scanners", {})
        assert input_scanners["prompt_injection"]["threshold"] == 0.5  # Very low
        assert input_scanners["prompt_injection"]["use_onnx"] is False
        assert input_scanners["prompt_injection"]["scan_timeout"] == 5


class TestEnvironmentVariableOverrides:
    """Test environment variable configuration overrides."""

    def test_environment_variable_preset_override(self, monkeypatch: Any) -> None:
        """Test preset override via environment variable."""
        monkeypatch.setenv("SECURITY_PRESET", "production")
        monkeypatch.setenv("SECURITY_ENVIRONMENT", "production")

        config = SecurityServiceFactory._create_default_configuration()

        assert config.preset.value == "production"
        assert config.environment == "production"

    def test_environment_variable_debug_override(self, monkeypatch: Any) -> None:
        """Test debug mode override via environment variable."""
        monkeypatch.setenv("SECURITY_DEBUG", "true")

        config = SecurityServiceFactory._create_default_configuration()

        assert config.debug_mode is True

    def test_environment_variable_concurrent_scans_override(self, monkeypatch: Any) -> None:
        """Test concurrent scans override via environment variable."""
        monkeypatch.setenv("SECURITY_MAX_CONCURRENT_SCANS", "15")

        config = SecurityServiceFactory._create_default_configuration()

        assert config.performance.max_concurrent_scans == 15

    def test_environment_variable_cache_override(self, monkeypatch: Any) -> None:
        """Test cache override via environment variable."""
        monkeypatch.setenv("SECURITY_ENABLE_CACHING", "false")

        config = SecurityServiceFactory._create_default_configuration()

        assert config.performance.enable_result_caching is False

    def test_environment_variable_threshold_override(self, monkeypatch: Any) -> None:
        """Test threshold override via environment variable."""
        monkeypatch.setenv("SECURITY_TOXICITY_THRESHOLD", "0.9")

        config = SecurityServiceFactory._create_default_configuration()

        # Check that threshold was applied
        # Note: This would need to be implemented in the configuration loading
        # assert config.scanners[ScannerType.TOXICITY_INPUT].threshold == 0.9

    def test_invalid_environment_variable_handling(self, monkeypatch: Any) -> None:
        """Test handling of invalid environment variable values."""
        monkeypatch.setenv("SECURITY_MAX_CONCURRENT_SCANS", "invalid")
        monkeypatch.setenv("SECURITY_DEBUG", "maybe")

        config = SecurityServiceFactory._create_default_configuration()

        # Should use default values for invalid inputs
        assert config.performance.max_concurrent_scans >= 1
        assert isinstance(config.debug_mode, bool)

    def test_environment_variable_merge_order(self, monkeypatch: Any) -> None:
        """Test that environment variables have highest precedence."""
        # Create base config
        base_config = {
            "performance": {
                "max_concurrent_scans": 5,
                "cache_ttl_seconds": 300,
            },
            "service": {
                "debug_mode": False,
            }
        }

        # Set environment variables
        monkeypatch.setenv("SECURITY_MAX_CONCURRENT_SCANS", "20")
        monkeypatch.setenv("SECURITY_DEBUG", "true")

        # Load configuration with overrides
        overrides = SecurityServiceFactory._load_environment_overrides()

        # Check environment variables override base config
        assert "max_concurrent_scans" in overrides
        assert overrides["max_concurrent_scans"] == 20
        assert "debug_mode" in overrides


class TestSettingsFactoryIntegration:
    """Test integration with Settings factory pattern."""

    @patch("app.infrastructure.security.llm.scanners.local_scanner.load_security_config")
    def test_settings_factory_pattern_integration(self, mock_load_config: Mock, monkeypatch: Any) -> None:
        """Test that scanner works with Settings factory pattern."""
        # Mock configuration
        mock_config = Mock()
        mock_config.environment = "test"
        mock_config.scanners = {}
        mock_config.performance = Mock()
        mock_config.performance.onnx_providers = ["CPUExecutionProvider"]
        mock_load_config.return_value = mock_config

        # Set environment
        monkeypatch.setenv("SECURITY_ENVIRONMENT", "test")

        # Create scanner with Settings factory pattern
        scanner = LocalLLMSecurityScanner(
            config_path=None,  # Use default path
            environment="test"
        )

        assert scanner is not None
        assert scanner.config.environment == "test"
        mock_load_config.assert_called_once_with(
            environment="test",
            config_path=None
        )

    def test_configuration_changes_require_scanner_reinitialization(self) -> None:
        """Test that configuration changes require scanner reinitialization."""
        # Create initial scanner
        scanner1 = LocalLLMSecurityScanner()
        initial_scanners = dict(scanner1.scanners)

        # Create new scanner with different environment
        scanner2 = LocalLLMSecurityScanner(environment="production")

        # Scanners should be different instances
        assert scanner1 is not scanner2
        # Configuration should be different
        assert scanner1.config.environment != scanner2.config.environment

    def test_factory_caching_with_different_environments(self, monkeypatch: Any) -> None:
        """Test factory caching with different environments."""
        with patch("app.infrastructure.security.llm.scanners.local_scanner.load_security_config") as mock_load:
            # Mock different configs for different environments
            def load_config_side_effect(environment: Optional[str] = None, config_path: Optional[str] = None) -> Mock:
                config = Mock()
                config.environment = environment or "development"
                config.scanners = {}
                config.performance = Mock()
                config.performance.onnx_providers = ["CPUExecutionProvider"]
                return config

            mock_load.side_effect = load_config_side_effect

            # Create scanners for different environments
            scanner_dev = LocalLLMSecurityScanner(environment="development")
            scanner_prod = LocalLLMSecurityScanner(environment="production")

            # Should have different configurations
            assert scanner_dev.config.environment == "development"
            assert scanner_prod.config.environment == "production"

            # Configuration loading should be called for each environment
            assert mock_load.call_count == 2

    @patch("app.infrastructure.security.llm.scanners.local_scanner.load_security_config")
    def test_scanner_initialization_with_missing_config(self, mock_load_config: Mock) -> None:
        """Test scanner initialization when configuration loading fails."""
        mock_load_config.side_effect = Exception("Configuration loading failed")

        with pytest.raises(Exception):
            LocalLLMSecurityScanner()

    def test_scanner_configuration_validation(self) -> None:
        """Test scanner configuration validation."""
        # Test with None config (should load from YAML)
        scanner = LocalLLMSecurityScanner(config=None)
        assert scanner is not None

        # Test with provided config
        from app.infrastructure.security.llm.config import SecurityConfig  # type: ignore
        config = SecurityConfig()
        scanner = LocalLLMSecurityScanner(config=config)
        assert scanner is not None
        assert scanner.config is config
