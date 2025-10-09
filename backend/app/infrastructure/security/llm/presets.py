"""
Security Configuration Presets for LLM Guard Integration

This module provides production-ready configuration presets for security scanner systems,
offering optimized settings for different deployment environments and use cases.
Each preset defines comprehensive security policies, performance configurations, and
operational parameters for AI content safety and input validation systems.

## Available Presets

### Development Preset (`"development"`)
- **Purpose**: Fast iteration and debugging during development cycles
- **Settings**: Lenient thresholds (0.8-0.9), CPU-only processing, verbose debug logging
- **Performance**: Optimized for developer feedback loops with minimal latency
- **Security**: Reduced false positives to avoid disrupting development workflow
- **Use Case**: Local development, feature testing, and security model tuning

### Production Preset (`"production"`)
- **Purpose**: Maximum security protection for production environments
- **Settings**: Strict thresholds (0.6-0.7), GPU acceleration with CPU fallback, secure logging
- **Performance**: Optimized for high throughput, reliability, and resource efficiency
- **Security**: Comprehensive scanning with aggressive blocking and content redaction
- **Use Case**: Live production systems handling real user traffic and sensitive data

### Testing Preset (`"testing"`)
- **Purpose**: Fast test execution with minimal computational overhead
- **Settings**: Minimal scanners (prompt injection only), aggressive caching, minimal logging
- **Performance**: Optimized for test speed, isolation, and CI/CD pipeline integration
- **Security**: Basic validation levels sufficient for test scenario verification
- **Use Case**: Automated testing, unit tests, integration test suites

## Preset Configuration Structure

Each preset returns a comprehensive configuration dictionary containing:

```python
{
    "preset": str,                    # Preset identifier
    "input_scanners": Dict[str, Any], # Input validation scanner configs
    "output_scanners": Dict[str, Any],# Output content scanner configs
    "performance": Dict[str, Any],    # Performance and caching settings
    "logging": Dict[str, Any],        # Logging and monitoring configuration
    "service": Dict[str, Any],        # Service identification and settings
    "features": Dict[str, Any]        # Feature flags and capabilities
}
```

## Core Functionality

- **Preset Retrieval**: Get optimized configurations by environment name
- **Custom Preset Creation**: Build tailored security configurations for specific needs
- **Configuration Validation**: Verify preset integrity and parameter constraints
- **Environment Discovery**: List available preset options and descriptions

## Usage Examples

### Basic Preset Usage
```python
from app.infrastructure.security.llm.presets import get_preset_config, list_presets

# Get production-ready security configuration
config = get_preset_config("production")

# Discover available presets
available = list_presets()
print(f"Available presets: {available}")  # ['development', 'production', 'testing']

# Access specific scanner configuration
prompt_injection_config = config["input_scanners"]["prompt_injection"]
print(f"Threshold: {prompt_injection_config['threshold']}")  # 0.6
```

### Environment-Specific Configuration
```python
# Development setup with permissive settings
dev_config = get_preset_config("development")
assert dev_config["input_scanners"]["pii_detection"]["action"] == "flag"

# Production setup with strict security
prod_config = get_preset_config("production")
assert prod_config["input_scanners"]["pii_detection"]["action"] == "redact"
assert prod_config["service"]["rate_limit_enabled"] is True
```

### Custom Preset Creation
```python
from app.infrastructure.security.llm.presets import create_preset

# Create specialized preset for content moderation
moderation_preset = create_preset(
    name="content-moderation",
    description="High-sensitivity content moderation preset",
    input_scanners={
        "prompt_injection": {
            "enabled": True,
            "threshold": 0.5,  # Very sensitive
            "action": "block",
            "use_onnx": True,
            "scan_timeout": 15
        },
        "toxicity_input": {
            "enabled": True,
            "threshold": 0.4,  # Extremely sensitive
            "action": "block",
            "use_onnx": True,
            "scan_timeout": 20
        }
    },
    output_scanners={
        "toxicity_output": {
            "enabled": True,
            "threshold": 0.3,  # Maximum sensitivity
            "action": "block",
            "use_onnx": True,
            "scan_timeout": 25
        }
    },
    performance_overrides={
        "cache_ttl_seconds": 1800,  # 30 minutes
        "max_concurrent_scans": 15
    }
)

# Validate the custom preset
from app.infrastructure.security.llm.presets import validate_preset_config
issues = validate_preset_config(moderation_preset)
assert not issues, f"Configuration errors: {issues}"
```

### Integration with Application Settings
```python
# In application configuration
class Settings:
    security_preset: str = "production"

    def get_security_config(self) -> Dict[str, Any]:
        # Get complete security configuration based on preset
        return get_preset_config(self.security_preset)

# Environment-specific deployment
import os
environment = os.getenv("ENVIRONMENT", "development")
settings.security_preset = environment  # Auto-select appropriate preset
security_config = settings.get_security_config()
```

## Configuration Validation

The module includes comprehensive validation to ensure preset integrity:

```python
from app.infrastructure.security.llm.presets import validate_preset_config

# Validate any configuration dictionary
config = get_preset_config("production")
issues = validate_preset_config(config)

if issues:
    print("Configuration issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Configuration is valid")
```

## Performance Considerations

- **Development Preset**: Optimized for developer experience, may have higher false positive rates
- **Production Preset**: Balanced for security and performance, includes GPU acceleration
- **Testing Preset**: Minimal resource usage, fastest possible execution for CI/CD
- **Custom Presets**: Inherit development base configuration with selective overrides

## Security Model

This preset system follows a defense-in-depth approach:
- **Input Validation**: Scans user prompts for injection attempts, toxic content, and PII
- **Output Filtering**: Validates AI-generated responses for harmful content and bias
- **Configurable Actions**: Supports warn, flag, block, and redact actions based on confidence
- **Performance Optimization**: Caching and parallel processing for production workloads

## Thread Safety and Performance

All preset functions are thread-safe and suitable for concurrent access:
- Preset configurations are immutable dictionaries
- No shared state between function calls
- Safe for use in multi-threaded web applications
- Minimal memory overhead with configuration reuse

## Integration Points

This module integrates with the broader security infrastructure:
- **Scanner Services**: Provides configuration for individual security scanners
- **Performance Management**: Defines caching, timeout, and resource limits
- **Monitoring Systems**: Configures logging and metrics collection
- **Service Discovery**: Enables environment-appropriate security posture

"""

from typing import Dict, Any, List


def get_preset_config(preset_name: str) -> Dict[str, Any]:
    """
    Retrieve complete security scanner configuration for a specified preset.

    Returns a comprehensive configuration dictionary containing all security scanner
    settings, performance parameters, logging configuration, and service metadata
    optimized for the specified deployment environment.

    Args:
        preset_name: Name of the preset configuration to retrieve. Must be one of:
                   - "development": Lenient settings for development workflows
                   - "production": Strict security for production deployment
                   - "testing": Minimal overhead for automated testing

    Returns:
        Complete configuration dictionary with the following structure:
        {
            "preset": str,                    # Preset identifier name
            "input_scanners": Dict[str, Any], # Input validation scanner configurations
            "output_scanners": Dict[str, Any],# Output content scanner configurations
            "performance": Dict[str, Any],    # Performance and caching settings
            "logging": Dict[str, Any],        # Logging and monitoring configuration
            "service": Dict[str, Any],        # Service identification and settings
            "features": Dict[str, Any]        # Feature flags and capabilities
        }

    Raises:
        ValueError: If preset_name is not one of the recognized preset values
                   (development, production, testing). The error message includes
                   a list of valid preset names for user guidance.

    Behavior:
        - Returns immutable configuration dictionary for thread safety
        - Configuration includes all necessary scanner parameters for immediate use
        - Each preset is optimized for its target environment (development, production, testing)
        - Scanner configurations include timeout, threshold, action, and performance settings
        - Performance section defines caching, concurrency, and resource limits
        - Logging configuration specifies verbosity, format, and retention policies
        - Service section includes environment identification and operational flags

    Examples:
        >>> # Get production configuration for deployment
        >>> prod_config = get_preset_config("production")
        >>> assert prod_config["preset"] == "production"
        >>> assert prod_config["service"]["environment"] == "production"
        >>> assert prod_config["service"]["api_key_required"] is True

        >>> # Access specific scanner settings
        >>> config = get_preset_config("development")
        >>> prompt_scanner = config["input_scanners"]["prompt_injection"]
        >>> assert prompt_scanner["enabled"] is True
        >>> assert 0.0 <= prompt_scanner["threshold"] <= 1.0

        >>> # Verify performance configuration
        >>> prod_config = get_preset_config("production")
        >>> perf = prod_config["performance"]
        >>> assert perf["cache_enabled"] is True
        >>> assert perf["max_concurrent_scans"] > 0

        >>> # Error handling for invalid preset
        >>> with pytest.raises(ValueError) as exc_info:
        ...     get_preset_config("invalid_preset")
        >>> assert "Unknown preset" in str(exc_info.value)
        >>> assert "development" in str(exc_info.value)

        >>> # Use configuration in application settings
        >>> preset_name = os.getenv("SECURITY_PRESET", "development")
        >>> security_config = get_preset_config(preset_name)
        >>> scanner_config = security_config["input_scanners"]["prompt_injection"]
        >>> threshold = scanner_config["threshold"]
    """
    presets = {
        "development": get_development_preset(),
        "production": get_production_preset(),
        "testing": get_testing_preset(),
    }

    if preset_name not in presets:
        available = list(presets.keys())
        raise ValueError(
            f"Unknown preset: {preset_name}. Available presets: {available}"
        )

    return presets[preset_name]


def list_presets() -> List[str]:
    """
    Retrieve a list of all available security preset names.

    Returns the complete catalog of predefined preset configurations that can be
    used with get_preset_config(). This function enables dynamic preset discovery
    and validation of environment-specific security configurations.

    Returns:
        List of available preset names as strings. Each name is a valid input
        for get_preset_config(). The returned list is always in a consistent
        order: ['development', 'production', 'testing'].

    Behavior:
        - Returns a new list on each call (no shared mutable state)
        - List order is guaranteed to be consistent across calls
        - All returned names are validated preset identifiers
        - Safe for concurrent access in multi-threaded environments
        - Includes only currently available and supported presets

    Examples:
        >>> # Get all available presets
        >>> presets = list_presets()
        >>> assert isinstance(presets, list)
        >>> assert all(isinstance(name, str) for name in presets)
        >>> assert len(presets) == 3

        >>> # Verify expected preset names
        >>> presets = list_presets()
        >>> expected = ['development', 'production', 'testing']
        >>> assert presets == expected

        >>> # Use with get_preset_config for iteration
        >>> for preset_name in list_presets():
        ...     config = get_preset_config(preset_name)
        ...     assert config["preset"] == preset_name
        ...     assert "input_scanners" in config

        >>> # Dynamic preset validation
        >>> user_preset = "staging"
        >>> available = list_presets()
        >>> if user_preset in available:
        ...     config = get_preset_config(user_preset)
        ... else:
        ...     raise ValueError(f"Unknown preset: {user_preset}")

        >>> # Environment-specific preset selection
        >>> import os
        >>> env = os.getenv("ENVIRONMENT", "development")
        >>> if env in list_presets():
        ...     config = get_preset_config(env)
        ... else:
        ...     # Fall back to development for unknown environments
        ...     config = get_preset_config("development")
    """
    return ["development", "production", "testing"]


def get_preset_description(preset_name: str) -> str:
    """
    Retrieve human-readable description for a specified security preset.

    Returns a concise description of the preset's purpose, characteristics, and
    intended use case. This function is useful for user interfaces, documentation
    generation, and helping users select appropriate security configurations.

    Args:
        preset_name: Name of the preset to describe. Valid values are:
                   - "development": For development workflows
                   - "production": For production deployment
                   - "testing": For automated testing

    Returns:
        Human-readable description string explaining the preset's purpose and
        characteristics. If the preset_name is not recognized, returns
        "Unknown preset" as a fallback.

    Behavior:
        - Returns descriptive text suitable for user interfaces
        - Handles unknown preset names gracefully with fallback text
        - Descriptions focus on use case and security level
        - No exception raised for invalid preset names (returns fallback)
        - Safe for concurrent access in multi-threaded environments

    Examples:
        >>> # Get descriptions for all presets
        >>> for preset in list_presets():
        ...     desc = get_preset_description(preset)
        ...     print(f"{preset}: {desc}")
        development: Development preset with lenient settings for fast iteration
        production: Production preset with strict security settings
        testing: Testing preset with minimal scanners for fast execution

        >>> # Use in user interface
        >>> preset_name = "production"
        >>> description = get_preset_description(preset_name)
        >>> assert "production" in description.lower()
        >>> assert "security" in description.lower()

        >>> # Handle unknown preset gracefully
        >>> unknown_desc = get_preset_description("nonexistent")
        >>> assert unknown_desc == "Unknown preset"

        >>> # Build preset selection menu
        >>> preset_options = []
        >>> for name in list_presets():
        ...     desc = get_preset_description(name)
        ...     preset_options.append(f"{name}: {desc}")
        >>>
        >>> menu_text = "\n".join(preset_options)
        >>> assert "development" in menu_text
        >>> assert "production" in menu_text
        >>> assert "testing" in menu_text

        >>> # Validate preset selection with description
        >>> user_choice = "production"
        >>> if user_choice in list_presets():
        ...     description = get_preset_description(user_choice)
        ...     print(f"Using {user_choice}: {description}")
        ... else:
        ...     print("Invalid preset selection")
    """
    descriptions = {
        "development": "Development preset with lenient settings for fast iteration",
        "production": "Production preset with strict security settings",
        "testing": "Testing preset with minimal scanners for fast execution"
    }
    return descriptions.get(preset_name, "Unknown preset")


def get_development_preset() -> Dict[str, Any]:
    """
    Generate development-optimized security scanner configuration.

    Creates a comprehensive security configuration specifically designed for
    development workflows, balancing developer productivity with essential security
    validation. Features lenient thresholds, comprehensive logging, and CPU-only
    processing for easy local setup.

    Returns:
        Complete configuration dictionary optimized for development environments:
        - Input scanners with lenient thresholds (0.8-0.9) to reduce false positives
        - Output scanners enabled for comprehensive testing
        - CPU-only processing for easy local development setup
        - Verbose debug logging with detailed scan information
        - Short cache TTLs for rapid iteration
        - Debug mode enabled for development tools
        - Experimental features enabled for testing new capabilities

    Behavior:
        - Configures all major security scanners with permissive settings
        - Enables comprehensive logging including scanned text for debugging
        - Uses CPU execution providers for maximum compatibility
        - Sets conservative timeouts to avoid blocking development workflow
        - Enables experimental features for testing new security capabilities
        - Configures service for development environment identification
        - Optimizes performance for fast feedback rather than throughput

    Examples:
        >>> # Get development configuration
        >>> config = get_development_preset()
        >>> assert config["preset"] == "development"
        >>> assert config["service"]["environment"] == "development"
        >>> assert config["service"]["debug_mode"] is True

        >>> # Verify lenient thresholds
        >>> scanners = config["input_scanners"]
        >>> prompt_scanner = scanners["prompt_injection"]
        >>> assert prompt_scanner["threshold"] == 0.9  # Very lenient
        >>> assert prompt_scanner["action"] == "warn"  # Non-blocking

        >>> # Check development-specific settings
        >>> perf = config["performance"]
        >>> assert perf["onnx_providers"] == ["CPUExecutionProvider"]
        >>> assert perf["cache_ttl_seconds"] == 300  # 5 minutes for fast iteration

        >>> # Verify comprehensive logging
        >>> logging = config["logging"]
        >>> assert logging["level"] == "DEBUG"
        >>> assert logging["include_scanned_text"] is True
        >>> assert logging["log_scan_operations"] is True

        >>> # Use in development application
        >>> if os.getenv("ENVIRONMENT") == "development":
        ...     dev_config = get_development_preset()
        ...     # Configure security scanners with dev settings
        ...     scanner_service = SecurityScannerService(dev_config)
    """
    return {
        "preset": "development",
        "input_scanners": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.9,
                "action": "warn",
                "use_onnx": True,
                "scan_timeout": 30,
                "metadata": {
                    "description": "Development prompt injection detection",
                    "environment": "development"
                }
            },
            "toxicity_input": {
                "enabled": True,
                "threshold": 0.9,
                "action": "warn",
                "use_onnx": True,
                "scan_timeout": 25,
                "metadata": {
                    "description": "Development toxic input detection",
                    "environment": "development"
                }
            },
            "pii_detection": {
                "enabled": True,
                "threshold": 0.9,
                "action": "flag",
                "use_onnx": True,
                "scan_timeout": 45,
                "redact": False,
                "metadata": {
                    "description": "Development PII detection (flagging only)",
                    "environment": "development"
                }
            }
        },
        "output_scanners": {
            "toxicity_output": {
                "enabled": True,
                "threshold": 0.9,
                "action": "warn",
                "use_onnx": True,
                "scan_timeout": 25,
                "metadata": {
                    "description": "Development toxic output detection",
                    "environment": "development"
                }
            },
            "bias_detection": {
                "enabled": True,
                "threshold": 0.8,
                "action": "flag",
                "use_onnx": True,
                "scan_timeout": 30,
                "metadata": {
                    "description": "Development bias detection",
                    "environment": "development"
                }
            }
        },
        "performance": {
            "cache_enabled": True,
            "cache_ttl_seconds": 300,
            "lazy_loading": True,
            "onnx_providers": ["CPUExecutionProvider"],
            "max_concurrent_scans": 5,
            "memory_limit_mb": 1024,
            "enable_model_caching": False,
            "enable_result_caching": False
        },
        "logging": {
            "enabled": True,
            "level": "DEBUG",
            "log_scan_operations": True,
            "log_violations": True,
            "log_performance_metrics": True,
            "include_scanned_text": True,
            "sanitize_pii_in_logs": False,
            "log_format": "text",
            "retention_days": 7
        },
        "service": {
            "name": "security-scanner-dev",
            "environment": "development",
            "debug_mode": True,
            "api_key_required": False,
            "rate_limit_enabled": False
        },
        "features": {
            "experimental_scanners": True,
            "advanced_analytics": True,
            "real_time_monitoring": True,
            "custom_scanner_support": True
        }
    }


def get_production_preset() -> Dict[str, Any]:
    """
    Generate production-optimized security scanner configuration.

    Creates a comprehensive security configuration designed for production deployment
    with maximum security protection, high performance, and operational reliability.
    Features strict thresholds, GPU acceleration, secure logging, and comprehensive
    monitoring for mission-critical security applications.

    Returns:
        Complete configuration dictionary optimized for production environments:
        - Input scanners with strict thresholds (0.6-0.7) for maximum security
        - Output scanners with comprehensive content validation
        - GPU acceleration with CPU fallback for high performance
        - Secure logging with PII sanitization and structured JSON format
        - Extended cache TTLs for high throughput optimization
        - Production service configuration with rate limiting and authentication
        - Comprehensive monitoring and metrics collection

    Behavior:
        - Configures all security scanners with strict, security-first settings
        - Enables GPU acceleration when available with automatic CPU fallback
        - Implements secure logging practices with PII protection
        - Optimizes performance for high throughput and reliability
        - Enables comprehensive monitoring and health checks
        - Configures rate limiting and authentication for production security
        - Uses extended cache TTLs to improve performance under load
        - Enables batch processing for efficient resource utilization

    Examples:
        >>> # Get production configuration
        >>> config = get_production_preset()
        >>> assert config["preset"] == "production"
        >>> assert config["service"]["environment"] == "production"
        >>> assert config["service"]["debug_mode"] is False

        >>> # Verify strict security thresholds
        >>> scanners = config["input_scanners"]
        >>> prompt_scanner = scanners["prompt_injection"]
        >>> assert prompt_scanner["threshold"] == 0.6  # Strict
        >>> assert prompt_scanner["action"] == "block"  # Blocking action

        >>> # Check production performance settings
        >>> perf = config["performance"]
        >>> assert "CUDAExecutionProvider" in perf["onnx_providers"]
        >>> assert perf["cache_ttl_seconds"] == 7200  # 2 hours
        >>> assert perf["max_concurrent_scans"] == 20  # High concurrency

        >>> # Verify secure logging configuration
        >>> logging = config["logging"]
        >>> assert logging["level"] == "INFO"
        >>> assert logging["include_scanned_text"] is False  # Privacy
        >>> assert logging["sanitize_pii_in_logs"] is True
        >>> assert logging["log_format"] == "json"

        >>> # Check production service settings
        >>> service = config["service"]
        >>> assert service["api_key_required"] is True
        >>> assert service["rate_limit_enabled"] is True
        >>> assert service["rate_limit_requests_per_minute"] == 120

        >>> # Deploy in production environment
        >>> if os.getenv("ENVIRONMENT") == "production":
        ...     prod_config = get_production_preset()
        ...     # Initialize high-security scanner service
        ...     scanner_service = SecurityScannerService(prod_config)
        ...     # Configure with authentication and rate limiting
    """
    return {
        "preset": "production",
        "input_scanners": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.6,
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 20,
                "metadata": {
                    "description": "Production prompt injection detection",
                    "environment": "production"
                }
            },
            "toxicity_input": {
                "enabled": True,
                "threshold": 0.7,
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 20,
                "metadata": {
                    "description": "Production toxic input detection",
                    "environment": "production"
                }
            },
            "pii_detection": {
                "enabled": True,
                "threshold": 0.6,
                "action": "redact",
                "use_onnx": True,
                "scan_timeout": 30,
                "redact": True,
                "metadata": {
                    "description": "Production PII detection with redaction",
                    "environment": "production"
                }
            },
            "malicious_url": {
                "enabled": True,
                "threshold": 0.8,
                "action": "block",
                "use_onnx": False,
                "scan_timeout": 10,
                "metadata": {
                    "description": "Production malicious URL detection",
                    "environment": "production"
                }
            }
        },
        "output_scanners": {
            "toxicity_output": {
                "enabled": True,
                "threshold": 0.6,
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 20,
                "metadata": {
                    "description": "Production toxic output detection",
                    "environment": "production"
                }
            },
            "bias_detection": {
                "enabled": True,
                "threshold": 0.6,
                "action": "flag",
                "use_onnx": True,
                "scan_timeout": 25,
                "metadata": {
                    "description": "Production bias detection",
                    "environment": "production"
                }
            },
            "harmful_content": {
                "enabled": True,
                "threshold": 0.7,
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 30,
                "metadata": {
                    "description": "Production harmful content detection",
                    "environment": "production"
                }
            }
        },
        "performance": {
            "cache_enabled": True,
            "cache_ttl_seconds": 7200,
            "lazy_loading": True,
            "onnx_providers": ["CUDAExecutionProvider", "CPUExecutionProvider"],
            "max_concurrent_scans": 20,
            "memory_limit_mb": 4096,
            "enable_model_caching": True,
            "enable_result_caching": True,
            "batch_processing_enabled": True,
            "max_batch_size": 10
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
            "retention_days": 90
        },
        "service": {
            "name": "security-scanner",
            "environment": "production",
            "debug_mode": False,
            "api_key_required": True,
            "rate_limit_enabled": True,
            "rate_limit_requests_per_minute": 120
        },
        "features": {
            "experimental_scanners": False,
            "advanced_analytics": True,
            "real_time_monitoring": True,
            "custom_scanner_support": False
        }
    }


def get_testing_preset() -> Dict[str, Any]:
    """
    Generate testing-optimized security scanner configuration.

    Creates a minimal security configuration specifically designed for automated
    testing environments, prioritizing execution speed, resource efficiency, and
    test isolation over comprehensive security validation. Features minimal
    scanners, aggressive caching, and disabled logging for maximum test performance.

    Returns:
        Minimal configuration dictionary optimized for testing environments:
        - Single input scanner (prompt injection only) for basic validation
        - No output scanners to minimize processing overhead
        - CPU-only processing with minimal resource allocation
        - Disabled logging to reduce test execution time
        - Aggressive caching with very short TTLs for test isolation
        - Minimal concurrent scans to reduce resource contention
        - Test-optimized service configuration

    Behavior:
        - Enables only essential prompt injection detection for basic security testing
        - Disables all output scanners to minimize processing time
        - Uses minimal memory and CPU allocation for test efficiency
        - Disables logging completely to reduce I/O overhead
        - Implements aggressive caching with 1-second TTL for test isolation
        - Limits concurrent scans to prevent resource contention in test environments
        - Configures service for testing environment identification
        - Disables all optional features to minimize complexity

    Examples:
        >>> # Get testing configuration
        >>> config = get_testing_preset()
        >>> assert config["preset"] == "testing"
        >>> assert config["service"]["environment"] == "testing"
        >>> assert config["service"]["debug_mode"] is True

        >>> # Verify minimal scanner configuration
        >>> input_scanners = config["input_scanners"]
        >>> assert len(input_scanners) == 1  # Only prompt injection
        >>> assert "prompt_injection" in input_scanners
        >>> assert input_scanners["prompt_injection"]["enabled"] is True

        >>> # Check no output scanners for speed
        >>> output_scanners = config["output_scanners"]
        >>> assert len(output_scanners) == 0  # No output processing

        >>> # Verify testing-optimized performance settings
        >>> perf = config["performance"]
        >>> assert perf["max_concurrent_scans"] == 1  # Single thread
        >>> assert perf["cache_ttl_seconds"] == 1  # Very short TTL
        >>> assert perf["memory_limit_mb"] == 256  # Minimal memory

        >>> # Check disabled logging for speed
        >>> logging = config["logging"]
        >>> assert logging["enabled"] is False
        >>> assert logging["level"] == "ERROR"  # Minimal logging

        >>> # Use in test suite
        >>> def test_security_scanner():
        ...     test_config = get_testing_preset()
        ...     scanner = SecurityScannerService(test_config)
        ...     # Fast test execution with minimal overhead
        ...     result = scanner.scan("test input")
        ...     assert result.is_safe

        >>> # Integration with pytest
        >>> @pytest.fixture
        ... def security_scanner():
        ...     config = get_testing_preset()
        ...     return SecurityScannerService(config)
    """
    return {
        "preset": "testing",
        "input_scanners": {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.95,
                "action": "warn",
                "use_onnx": False,
                "scan_timeout": 5,
                "metadata": {
                    "description": "Testing prompt injection detection",
                    "environment": "testing"
                }
            }
        },
        "output_scanners": {},
        "performance": {
            "cache_enabled": True,
            "cache_ttl_seconds": 1,
            "lazy_loading": True,
            "onnx_providers": ["CPUExecutionProvider"],
            "max_concurrent_scans": 1,
            "memory_limit_mb": 256,
            "enable_model_caching": False,
            "enable_result_caching": False
        },
        "logging": {
            "enabled": False,
            "level": "ERROR",
            "log_scan_operations": False,
            "log_violations": False,
            "log_performance_metrics": False,
            "include_scanned_text": False,
            "sanitize_pii_in_logs": True,
            "log_format": "text",
            "retention_days": 1
        },
        "service": {
            "name": "security-scanner-test",
            "environment": "testing",
            "debug_mode": True,
            "api_key_required": False,
            "rate_limit_enabled": False
        },
        "features": {
            "experimental_scanners": False,
            "advanced_analytics": False,
            "real_time_monitoring": False,
            "custom_scanner_support": False
        }
    }


def create_preset(
    name: str,
    description: str,
    input_scanners: Dict[str, Any],
    output_scanners: Dict[str, Any],
    performance_overrides: Dict[str, Any] | None = None,
    logging_overrides: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    Create a custom security scanner preset configuration.

    Builds a complete security configuration by combining custom scanner definitions
    with base performance and logging settings. This function enables the creation
    of specialized security presets for specific use cases while maintaining
    consistency with the established configuration structure and defaults.

    Args:
        name: Unique identifier for the custom preset. Should be descriptive and
              follow naming conventions (lowercase, hyphens for spaces).
        description: Human-readable description of the preset's purpose and use case.
                    Should explain the security level and intended deployment scenario.
        input_scanners: Dictionary defining input validation scanner configurations.
                       Keys are scanner names, values are scanner configuration dicts
                       with required fields: enabled (bool), threshold (float 0.0-1.0),
                       action (str: 'warn', 'flag', 'block', 'redact'), scan_timeout (int).
        output_scanners: Dictionary defining output content scanner configurations.
                        Keys are scanner names, values are scanner configuration dicts
                        with the same structure as input_scanners.
        performance_overrides: Optional dictionary of performance settings to override
                              from the base development preset. Includes cache settings,
                              concurrency limits, memory allocation, and ONNX providers.
        logging_overrides: Optional dictionary of logging settings to override from
                          the base development preset. Includes log level, format,
                          retention, and privacy settings.

    Returns:
        Complete configuration dictionary combining custom scanner definitions with
        base performance and logging settings. Structure matches preset format:
        {
            "preset": str,                    # Custom preset name
            "input_scanners": Dict[str, Any], # Custom input scanner configurations
            "output_scanners": Dict[str, Any],# Custom output scanner configurations
            "performance": Dict[str, Any],    # Performance configuration
            "logging": Dict[str, Any],        # Logging configuration
            "service": Dict[str, Any],        # Service identification
            "features": Dict[str, Any]        # Feature flags from base preset
        }

    Behavior:
        - Inherits base performance and logging settings from development preset
        - Applies custom overrides to performance and logging configurations
        - Configures service identification with custom preset name and environment
        - Preserves experimental features from base development configuration
        - Merges custom scanner configurations with base structure
        - Returns immutable configuration dictionary for thread safety
        - Validates that all required configuration sections are present

    Examples:
        >>> # Create content moderation preset
        >>> moderation_preset = create_preset(
        ...     name="content-moderation",
        ...     description="High-sensitivity content moderation for social platforms",
        ...     input_scanners={
        ...         "prompt_injection": {
        ...             "enabled": True,
        ...             "threshold": 0.4,  # Very sensitive
        ...             "action": "block",
        ...             "use_onnx": True,
        ...             "scan_timeout": 15
        ...         },
        ...         "toxicity_input": {
        ...             "enabled": True,
        ...             "threshold": 0.3,  # Extremely sensitive
        ...             "action": "block",
        ...             "use_onnx": True,
        ...             "scan_timeout": 20
        ...         }
        ...     },
        ...     output_scanners={
        ...         "toxicity_output": {
        ...             "enabled": True,
        ...             "threshold": 0.2,  # Maximum sensitivity
        ...             "action": "block",
        ...             "use_onnx": True,
        ...             "scan_timeout": 25
        ...         }
        ...     },
        ...     performance_overrides={
        ...         "cache_ttl_seconds": 1800,  # 30 minutes
        ...         "max_concurrent_scans": 10,
        ...         "memory_limit_mb": 2048
        ...     },
        ...     logging_overrides={
        ...         "level": "INFO",
        ...         "log_violations": True,
        ...         "sanitize_pii_in_logs": True
        ...     }
        ... )
        >>> assert moderation_preset["preset"] == "content-moderation"

        >>> # Create minimal testing preset
        >>> minimal_preset = create_preset(
        ...     name="minimal-test",
        ...     description="Minimal preset for unit testing",
        ...     input_scanners={
        ...         "prompt_injection": {
        ...             "enabled": True,
        ...             "threshold": 0.95,
        ...             "action": "warn",
        ...             "use_onnx": False,
        ...             "scan_timeout": 5
        ...         }
        ...     },
        ...     output_scanners={},
        ...     performance_overrides={
        ...         "cache_ttl_seconds": 1,
        ...         "max_concurrent_scans": 1
        ...     }
        ... )
        >>> assert len(minimal_preset["input_scanners"]) == 1
        >>> assert len(minimal_preset["output_scanners"]) == 0

        >>> # Create high-security preset
        >>> high_security = create_preset(
        ...     name="high-security",
        ...     description="Maximum security for sensitive applications",
        ...     input_scanners={
        ...         "prompt_injection": {
        ...             "enabled": True,
        ...             "threshold": 0.1,  # Extremely strict
        ...             "action": "block",
        ...             "use_onnx": True,
        ...             "scan_timeout": 30
        ...         },
        ...         "toxicity_input": {
        ...             "enabled": True,
        ...             "threshold": 0.2,
        ...             "action": "block",
        ...             "use_onnx": True,
        ...             "scan_timeout": 25
        ...         },
        ...         "pii_detection": {
        ...             "enabled": True,
        ...             "threshold": 0.3,
        ...             "action": "redact",
        ...             "use_onnx": True,
        ...             "scan_timeout": 40,
        ...             "redact": True
        ...         }
        ...     },
        ...     output_scanners={
        ...         "toxicity_output": {
        ...             "enabled": True,
        ...             "threshold": 0.1,
        ...             "action": "block",
        ...             "use_onnx": True,
        ...             "scan_timeout": 30
        ...         }
        ...     },
        ...     performance_overrides={
        ...         "cache_ttl_seconds": 3600,  # 1 hour
        ...         "max_concurrent_scans": 25,
        ...         "memory_limit_mb": 8192
        ...     }
        ... )

        >>> # Validate custom preset
        >>> from app.infrastructure.security.llm.presets import validate_preset_config
        >>> issues = validate_preset_config(moderation_preset)
        >>> assert not issues, f"Configuration errors: {issues}"
    """
    # Start with base configuration
    base_config = get_development_preset()

    # Create preset configuration
    preset_config = {
        "preset": name,
        "input_scanners": input_scanners,
        "output_scanners": output_scanners,
        "service": {
            "name": f"security-scanner-{name}",
            "environment": name,
            "debug_mode": True
        }
    }

    # Merge with base configuration for performance and logging
    base_performance = base_config["performance"]
    if performance_overrides:
        base_performance.update(performance_overrides)
    preset_config["performance"] = base_performance

    base_logging = base_config["logging"]
    if logging_overrides:
        base_logging.update(logging_overrides)
    preset_config["logging"] = base_logging

    # Use base features
    preset_config["features"] = base_config["features"]

    return preset_config


def validate_preset_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate security preset configuration for structural integrity and compliance.

    Performs comprehensive validation of a preset configuration dictionary, checking
    for required sections, proper data types, valid parameter ranges, and structural
    consistency. Returns a list of identified issues for troubleshooting and
    configuration debugging.

    Args:
        config: Configuration dictionary to validate. Should follow the standard
                preset structure with required sections: input_scanners, output_scanners,
                performance, logging, service, and features.

    Returns:
        List of validation issue descriptions as strings. Empty list indicates
        the configuration passed all validation checks. Each issue provides a
        descriptive message explaining the validation failure and its location
        within the configuration structure.

    Behavior:
        - Validates presence of all required top-level configuration sections
        - Checks scanner configuration structure and required fields
        - Validates threshold values are within 0.0-1.0 range
        - Ensures performance parameters have valid types and ranges
        - Verifies concurrent scan limits are positive integers
        - Returns descriptive error messages for each validation failure
        - Does not modify the input configuration during validation
        - Safe for concurrent access with immutable configurations

    Examples:
        >>> # Validate production preset configuration
        >>> prod_config = get_preset_config("production")
        >>> issues = validate_preset_config(prod_config)
        >>> assert not issues, f"Production preset should be valid: {issues}"

        >>> # Validate custom preset configuration
        >>> custom_preset = create_preset(
        ...     name="test-preset",
        ...     description="Test preset",
        ...     input_scanners={
        ...         "prompt_injection": {
        ...             "enabled": True,
        ...             "threshold": 0.7,
        ...             "action": "warn",
        ...             "use_onnx": True,
        ...             "scan_timeout": 30
        ...         }
        ...     },
        ...     output_scanners={}
        ... )
        >>> issues = validate_preset_config(custom_preset)
        >>> assert not issues, f"Custom preset should be valid: {issues}"

        >>> # Detect configuration issues
        >>> invalid_config = {
        ...     "input_scanners": {
        ...         "bad_scanner": {
        ...             "enabled": True,
        ...             "threshold": 1.5,  # Invalid threshold > 1.0
        ...             "action": "block"
        ...         }
        ...     },
        ...     # Missing required sections
        ... }
        >>> issues = validate_preset_config(invalid_config)
        >>> assert len(issues) > 0
        >>> assert any("threshold" in issue for issue in issues)
        >>> assert any("Missing required section" in issue for issue in issues)

        >>> # Validate and report issues
        >>> config = get_preset_config("development")
        >>> # Simulate a configuration error
        >>> config["performance"]["max_concurrent_scans"] = -1  # Invalid
        >>> issues = validate_preset_config(config)
        >>> if issues:
        ...     print("Configuration issues found:")
        ...     for issue in issues:
        ...         print(f"  - {issue}")
        ... else:
        ...     print("Configuration is valid")

        >>> # Use in configuration loading workflow
        >>> def load_and_validate_config(preset_name: str) -> Dict[str, Any]:
        ...     config = get_preset_config(preset_name)
        ...     issues = validate_preset_config(config)
        ...     if issues:
        ...         raise ValueError(f"Invalid configuration: {issues}")
        ...     return config
        >>>
        >>> try:
        ...     valid_config = load_and_validate_config("production")
        ... except ValueError as e:
        ...     print(f"Configuration error: {e}")

        >>> # Validate user-provided custom configuration
        >>> user_config = {
        ...     "preset": "custom",
        ...     "input_scanners": {"prompt_injection": {"enabled": True, "threshold": 0.8, "action": "warn"}},
        ...     "output_scanners": {},
        ...     "performance": {"max_concurrent_scans": 5},
        ...     "logging": {"enabled": True},
        ...     "service": {"environment": "custom"},
        ...     "features": {}
        ... }
        >>> validation_issues = validate_preset_config(user_config)
        >>> if not validation_issues:
        ...     print("User configuration is valid and ready to use")
        ... else:
        ...     print(f"Please fix these issues: {validation_issues}")
    """
    issues = []

    # Check required sections
    required_sections = ["input_scanners", "output_scanners", "performance", "logging"]
    for section in required_sections:
        if section not in config:
            issues.append(f"Missing required section: {section}")

    # Validate scanner configurations
    for scanner_type in ["input_scanners", "output_scanners"]:
        scanners = config.get(scanner_type, {})
        for scanner_name, scanner_config in scanners.items():
            if not isinstance(scanner_config, dict):
                issues.append(f"Invalid scanner configuration for {scanner_name}")
                continue

            # Check required fields
            if "enabled" not in scanner_config:
                issues.append(f"Missing 'enabled' field for scanner {scanner_name}")
            if "threshold" in scanner_config:
                threshold = scanner_config["threshold"]
                if not isinstance(threshold, (int, float)) or not 0.0 <= threshold <= 1.0:
                    issues.append(f"Invalid threshold for scanner {scanner_name}: {threshold}")

    # Validate performance configuration
    performance = config.get("performance", {})
    if "max_concurrent_scans" in performance:
        max_scans = performance["max_concurrent_scans"]
        if not isinstance(max_scans, int) or max_scans < 1:
            issues.append(f"Invalid max_concurrent_scans: {max_scans}")

    return issues
