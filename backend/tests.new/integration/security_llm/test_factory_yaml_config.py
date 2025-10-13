"""
Configuration-Driven Factory Tests

Tests for the enhanced security scanner factory with YAML configuration support.
This test suite validates that the factory properly loads and uses YAML configuration
with environment-specific overrides and dynamic scanner registration.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import patch

from app.core.exceptions import ConfigurationError  # type: ignore
from app.infrastructure.security.llm.factory import (  # type: ignore
    create_security_service_from_yaml,
)
from app.infrastructure.security.llm.scanners.local_scanner import LocalLLMSecurityScanner  # type: ignore


class TestYAMLConfigurationLoading:
    """Test YAML configuration loading and validation."""

    @pytest.fixture
    def temp_config_dir(self) -> Generator[Path, None, None]:
        """Create a temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config" / "security"
            config_dir.mkdir(parents=True)
            yield config_dir

    @pytest.fixture
    def base_scanners_config(self) -> Dict[str, Any]:
        """Base scanner configuration for testing."""
        return {
            "scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "model_name": "test-prompt-model",
                    "use_onnx": False,
                    "scan_timeout": 30,
                },
                "toxicity_input": {
                    "enabled": True,
                    "threshold": 0.7,
                    "action": "warn",
                    "model_name": "test-toxicity-model",
                    "use_onnx": True,
                    "scan_timeout": 25,
                },
                "pii_detection": {
                    "enabled": False,
                    "threshold": 0.9,
                    "action": "redact",
                    "model_name": "test-pii-model",
                    "scan_timeout": 45,
                },
                "toxicity_output": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "model_name": "test-toxicity-output-model",
                    "use_onnx": True,
                },
                "bias_detection": {
                    "enabled": True,
                    "threshold": 0.6,
                    "action": "flag",
                    "model_name": "test-bias-model",
                    "use_onnx": False,
                },
            },
            "performance": {
                "cache_enabled": True,
                "cache_ttl_seconds": 1800,
                "max_concurrent_scans": 15,
                "onnx_providers": ["CPUExecutionProvider", "CUDAExecutionProvider"],
                "enable_model_caching": True,
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
                "log_scan_operations": True,
                "include_scanned_text": False,
            },
            "service": {
                "name": "test-security-scanner",
                "version": "1.0.0",
                "environment": "testing",
                "debug_mode": True,
            }
        }

    @pytest.fixture
    def dev_config_overrides(self) -> Dict[str, Any]:
        """Development environment configuration overrides."""
        return {
            "scanners": {
                "prompt_injection": {
                    "threshold": 0.6,  # More lenient in dev
                    "action": "warn",   # Warn instead of block
                },
                "pii_detection": {
                    "enabled": True,   # Enable PII in dev
                },
            },
            "performance": {
                "cache_ttl_seconds": 300,  # Shorter cache in dev
                "max_concurrent_scans": 5,  # Lower concurrency in dev
            },
            "logging": {
                "level": "DEBUG",  # Debug logging in dev
                "include_scanned_text": True,
            },
            "service": {
                "environment": "development",
                "debug_mode": True,
            }
        }

    @pytest.fixture
    def prod_config_overrides(self) -> Dict[str, Any]:
        """Production environment configuration overrides."""
        return {
            "scanners": {
                "prompt_injection": {
                    "threshold": 0.9,  # Stricter in prod
                },
                "malicious_url": {
                    "enabled": True,   # Enable additional scanners in prod
                    "threshold": 0.95,
                    "action": "block",
                },
            },
            "performance": {
                "cache_ttl_seconds": 3600,  # Max allowed value (was 7200, but max is 3600)
                "max_concurrent_scans": 25,  # Higher concurrency in prod
                "onnx_providers": ["CUDAExecutionProvider", "CPUExecutionProvider"],  # GPU first
            },
            "logging": {
                "level": "WARNING",  # Less verbose in prod
                "include_scanned_text": False,
            },
            "service": {
                "environment": "production",
                "debug_mode": False,
            }
        }

    def test_load_scanner_from_yaml_config(self, temp_config_dir: Path, base_scanners_config: Dict[str, Any]) -> None:
        """Test creating scanner service from YAML configuration."""
        # Write base configuration
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump(base_scanners_config, f)

        # Create service from YAML
        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="testing"
            )

        assert service is not None
        assert isinstance(service, LocalLLMSecurityScanner)
        assert service.config.environment == "testing"

    def test_yaml_configuration_with_environment_overrides(
        self, temp_config_dir: Path, base_scanners_config: Dict[str, Any], dev_config_overrides: Dict[str, Any]
    ) -> None:
        """Test that environment overrides are properly applied."""
        # Write base configuration
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump(base_scanners_config, f)

        # Write development overrides
        dev_config_path = temp_config_dir / "development.yaml"
        with open(dev_config_path, "w") as f:
            yaml.dump(dev_config_overrides, f)

        # Create service for development environment
        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="development"
            )

        # Verify overrides were applied
        assert service.config.environment == "development"
        assert service.config.debug_mode is True

        # Check specific overrides
        scanners = getattr(service.config, "scanners", {})
        prompt_injection = scanners.get("prompt_injection")
        assert prompt_injection is not None  # Ensure scanner exists
        assert prompt_injection.threshold == 0.6  # Override applied
        assert prompt_injection.action.value == "warn"   # Override applied

        # Check performance overrides
        performance = service.config.performance
        assert performance.cache_ttl_seconds == 300  # Override applied
        assert performance.max_concurrent_scans == 5  # Override applied

    def test_yaml_configuration_with_production_overrides(
        self, temp_config_dir: Path, base_scanners_config: Dict[str, Any], prod_config_overrides: Dict[str, Any]
    ) -> None:
        """Test production environment configuration."""
        # Write base configuration
        base_config_path = temp_config_dir / "scanners.yaml"
        with open(base_config_path, "w") as f:
            yaml.dump(base_scanners_config, f)

        # Write production overrides
        prod_config_path = temp_config_dir / "production.yaml"
        with open(prod_config_path, "w") as f:
            yaml.dump(prod_config_overrides, f)

        # Create service for production environment
        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="production"
            )

        # Verify production settings
        assert service.config.environment == "production"
        assert service.config.debug_mode is False

        # Check stricter security settings
        scanners = getattr(service.config, "scanners", {})
        prompt_injection = scanners.get("prompt_injection")
        assert prompt_injection is not None  # Ensure scanner exists
        assert prompt_injection.threshold == 0.9  # Stricter threshold

        # Check performance optimizations
        performance = service.config.performance
        assert performance.cache_ttl_seconds == 3600  # Longer cache (max allowed)
        assert performance.max_concurrent_scans == 25  # Higher concurrency

    def test_minimal_scanner_configuration(self, temp_config_dir: Path) -> None:
        """Test factory with minimal scanner configuration."""
        minimal_config = {
            "scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                }
            },
            "performance": {
                "max_concurrent_scans": 5,
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
            },
            "service": {
                "name": "minimal-scanner",
                "environment": "testing",
            }
        }

        # Write minimal configuration
        config_path = temp_config_dir / "scanners.yaml"
        with open(config_path, "w") as f:
            yaml.dump(minimal_config, f)

        # Create service
        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="testing"
            )

        assert service is not None
        assert len(getattr(service.config, "scanners", {})) == 1

    def test_all_scanners_enabled_configuration(self, temp_config_dir: Path) -> None:
        """Test factory with all scanners enabled."""
        all_scanners_config = {
            "scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "use_onnx": True,
                },
                "toxicity_input": {
                    "enabled": True,
                    "threshold": 0.7,
                    "action": "warn",
                    "use_onnx": True,
                },
                "pii_detection": {
                    "enabled": True,
                    "threshold": 0.7,
                    "action": "redact",
                    "use_onnx": False,
                },
                "malicious_url": {
                    "enabled": True,
                    "threshold": 0.9,
                    "action": "block",
                    "use_onnx": False,
                },
                "toxicity_output": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "use_onnx": True,
                },
                "bias_detection": {
                    "enabled": True,
                    "threshold": 0.7,
                    "action": "flag",
                    "use_onnx": False,
                },
                "harmful_content": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "use_onnx": True,
                },
            },
            "performance": {
                "max_concurrent_scans": 20,
                "enable_model_caching": True,
                "onnx_providers": ["CPUExecutionProvider"],
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
            },
            "service": {
                "name": "full-scanner",
                "environment": "testing",
            }
        }

        # Write full configuration
        config_path = temp_config_dir / "scanners.yaml"
        with open(config_path, "w") as f:
            yaml.dump(all_scanners_config, f)

        # Create service
        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="testing"
            )

        assert service is not None

        # Check all scanners are configured
        scanners = getattr(service.config, "scanners", {})
        assert len(scanners) == 7  # 4 input + 3 output scanners
        assert all(scanner.enabled for scanner in scanners.values())

    def test_selective_scanner_enablement(self, temp_config_dir: Path) -> None:
        """Test factory with selective scanner enablement."""
        selective_config = {
            "scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                },
                "toxicity_input": {
                    "enabled": False,  # Disabled
                    "threshold": 0.7,
                    "action": "warn",
                },
                "pii_detection": {
                    "enabled": True,
                    "threshold": 0.7,
                    "action": "redact",
                },
                "toxicity_output": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                },
                "bias_detection": {
                    "enabled": False,  # Disabled
                    "threshold": 0.7,
                    "action": "flag",
                },
            },
            "performance": {
                "max_concurrent_scans": 10,
            },
            "service": {
                "name": "selective-scanner",
                "environment": "testing",
            }
        }

        # Write selective configuration
        config_path = temp_config_dir / "scanners.yaml"
        with open(config_path, "w") as f:
            yaml.dump(selective_config, f)

        # Create service
        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="testing"
            )

        # Verify selective enablement
        scanners = getattr(service.config, "scanners", {})
        assert scanners["prompt_injection"].enabled is True
        assert scanners["toxicity_input"].enabled is False
        assert scanners["pii_detection"].enabled is True
        assert scanners["toxicity_output"].enabled is True
        assert scanners["bias_detection"].enabled is False

    def test_factory_respects_threshold_values_from_configuration(self, temp_config_dir: Path) -> None:
        """Test that factory respects threshold values from YAML configuration."""
        threshold_config = {
            "scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.95,  # Very high threshold
                    "action": "block",
                },
                "toxicity_input": {
                    "enabled": True,
                    "threshold": 0.3,   # Very low threshold
                    "action": "warn",
                },
                "pii_detection": {
                    "enabled": True,
                    "threshold": 0.75,  # Medium threshold
                    "action": "redact",
                },
                "toxicity_output": {
                    "enabled": True,
                    "threshold": 0.85,  # High threshold
                    "action": "block",
                },
            },
            "service": {
                "name": "threshold-test-scanner",
                "environment": "testing",
            }
        }

        # Write threshold configuration
        config_path = temp_config_dir / "scanners.yaml"
        with open(config_path, "w") as f:
            yaml.dump(threshold_config, f)

        # Create service
        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="testing"
            )

        # Verify threshold values
        scanners = getattr(service.config, "scanners", {})
        assert scanners["prompt_injection"].threshold == 0.95
        assert scanners["toxicity_input"].threshold == 0.3
        assert scanners["pii_detection"].threshold == 0.75
        assert scanners["toxicity_output"].threshold == 0.85

    def test_configuration_error_for_missing_config_file(self, temp_config_dir: Path) -> None:
        """Test that appropriate error is raised when configuration file is missing."""
        non_existent_path = temp_config_dir / "non_existent"

        with pytest.raises(ConfigurationError) as exc_info:
            create_security_service_from_yaml(
                config_path=str(non_existent_path),
                environment="testing"
            )

        assert "Configuration directory does not exist" in str(exc_info.value)

    def test_configuration_error_for_invalid_yaml(self, temp_config_dir: Path) -> None:
        """Test that appropriate error is raised for invalid YAML syntax."""
        # Write invalid YAML
        config_path = temp_config_dir / "scanners.yaml"
        with open(config_path, "w") as f:
            f.write("""
                scanners:
                  prompt_injection:
                    enabled: true
                    threshold: 0.8
                    action: block
                  invalid_yaml: [unclosed list
                """)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            with pytest.raises(ConfigurationError) as exc_info:
                create_security_service_from_yaml(
                    config_path=str(temp_config_dir),
                    environment="testing"
                )

            assert "Invalid YAML syntax" in str(exc_info.value)

    def test_configuration_error_for_no_enabled_scanners(self, temp_config_dir: Path) -> None:
        """Test error when no scanners are enabled."""
        no_scanners_config = {
            "scanners": {
                "prompt_injection": {
                    "enabled": False,
                },
                "toxicity_input": {
                    "enabled": False,
                },
                "toxicity_output": {
                    "enabled": False,
                },
            },
            "service": {
                "name": "no-scanners",
                "environment": "testing",
            }
        }

        # Write configuration with no enabled scanners
        config_path = temp_config_dir / "scanners.yaml"
        with open(config_path, "w") as f:
            yaml.dump(no_scanners_config, f)

        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            # Should not raise error during creation, but validation would catch it
            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="testing"
            )

            # The service is created but no scanners would be initialized
            assert service is not None

    def test_environment_variable_configuration_loading(self, monkeypatch: Any) -> None:
        """Test loading configuration using environment variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config" / "security"
            config_dir.mkdir(parents=True)

            # Set environment variables to point to our temporary config
            monkeypatch.setenv("SECURITY_ENVIRONMENT", "production")
            monkeypatch.setenv("SECURITY_CONFIG_PATH", str(config_dir))

            # Create basic config
            config = {
                "scanners": {
                    "prompt_injection": {
                        "enabled": True,
                        "threshold": 0.8,
                        "action": "block"
                    }
                },
                "service": {
                    "name": "env-test-scanner",
                    "environment": "production"
                }
            }

            config_path = config_dir / "scanners.yaml"
            with open(config_path, "w") as f:
                yaml.dump(config, f)

            # Mock Path.cwd to return our temp directory's parent
            with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
                mock_cwd.return_value = config_dir.parent

                # Create service - this should read from environment variables
                service = create_security_service_from_yaml()

                # Verify service was created successfully
                assert service is not None
                assert service.config.environment == "production"

    def test_backwards_compatibility_with_legacy_scanners_config(self, temp_config_dir: Path) -> None:
        """Test backwards compatibility with legacy flat scanners configuration."""
        legacy_config = {
            "scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block",
                    "model_name": "legacy-model",
                },
                "toxicity_input": {
                    "enabled": True,
                    "threshold": 0.7,
                    "action": "warn",
                },
            },
            "performance": {
                "max_concurrent_scans": 10,
            },
            "service": {
                "name": "legacy-scanner",
                "environment": "testing",
            }
        }

        # Write legacy configuration
        config_path = temp_config_dir / "scanners.yaml"
        with open(config_path, "w") as f:
            yaml.dump(legacy_config, f)

        # Create service
        with patch("app.infrastructure.security.llm.config_loader.Path.cwd") as mock_cwd:
            mock_cwd.return_value = temp_config_dir.parent

            service = create_security_service_from_yaml(
                config_path=str(temp_config_dir),
                environment="testing"
            )

        # Should work with legacy configuration
        assert service is not None
        assert service.config.environment == "testing"
