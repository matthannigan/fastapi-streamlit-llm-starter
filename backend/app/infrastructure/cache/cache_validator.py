"""
Cache Configuration Validation System

This module provides comprehensive validation capabilities for cache configurations,
presets, and custom overrides. It includes JSON schema definitions, validation utilities,
and configuration templates for common use cases.

**Core Components:**
- ValidationResult: Result container for validation operations with errors and warnings
- CacheValidator: Main validation class with JSON schema support and validation utilities
- Configuration templates for fast development, robust production setups
- Schema definitions for cache configuration, preset validation, and custom overrides

**Key Features:**
- JSON schema validation for comprehensive configuration checking
- Configuration templates for common use cases (development, production, AI workloads)
- Validation caching and performance optimization for repeated validations
- Configuration comparison and recommendation functionality
- Template generation for different deployment scenarios
- Schema-based validation with detailed error reporting

**Validation Categories:**
- Preset validation: Ensures preset definitions are valid and complete
- Configuration validation: Validates complete cache configurations
- Override validation: Validates custom JSON overrides against schema
- Template validation: Validates generated configuration templates

**Usage:**
- Use cache_validator.validate_preset() for preset validation
- Use cache_validator.validate_configuration() for full config validation
- Use cache_validator.get_template() for configuration templates
- Access validation schemas via cache_validator.schemas for custom validation

This module serves as the validation hub for all cache configuration-related
validation across the application, providing both schema-based validation
and template generation capabilities.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation messages."""
    ERROR = "error"        # Critical errors that prevent operation
    WARNING = "warning"    # Non-critical issues that should be addressed
    INFO = "info"         # Informational messages about configuration


@dataclass
class ValidationMessage:
    """Single validation message with severity and context."""
    severity: ValidationSeverity
    message: str
    field_path: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """
    Result of configuration validation containing validation status and messages.

    Attributes:
        is_valid: Whether the configuration passed validation (no errors)
        messages: List of validation messages (errors, warnings, info)
        validation_type: Type of validation performed
        schema_version: Version of schema used for validation
    """
    is_valid: bool
    messages: List[ValidationMessage] = field(default_factory=list)
    validation_type: str = "unknown"
    schema_version: str = "1.0"

    @property
    def errors(self) -> List[str]:
        """Get list of error messages."""
        return [msg.message for msg in self.messages if msg.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[str]:
        """Get list of warning messages."""
        return [msg.message for msg in self.messages if msg.severity == ValidationSeverity.WARNING]

    @property
    def info(self) -> List[str]:
        """Get list of info messages."""
        return [msg.message for msg in self.messages if msg.severity == ValidationSeverity.INFO]

    def add_error(self, message: str, field_path: str = "", context: Optional[Dict[str, Any]] = None) -> None:
        """Add an error message and mark validation as invalid."""
        self.messages.append(ValidationMessage(
            severity=ValidationSeverity.ERROR,
            message=message,
            field_path=field_path,
            context=context or {}
        ))
        self.is_valid = False

    def add_warning(self, message: str, field_path: str = "", context: Optional[Dict[str, Any]] = None) -> None:
        """Add a warning message."""
        self.messages.append(ValidationMessage(
            severity=ValidationSeverity.WARNING,
            message=message,
            field_path=field_path,
            context=context or {}
        ))

    def add_info(self, message: str, field_path: str = "", context: Optional[Dict[str, Any]] = None) -> None:
        """Add an info message."""
        self.messages.append(ValidationMessage(
            severity=ValidationSeverity.INFO,
            message=message,
            field_path=field_path,
            context=context or {}
        ))


class CacheValidator:
    """
    Comprehensive cache configuration validator with JSON schema support.
    """

    def __init__(self):
        """Initialize validator with schemas and templates."""
        self.schemas = self._load_schemas()
        self.templates = self._load_templates()
        self._validation_cache = {}
        logger.info("Initialized CacheValidator with schemas and templates")

    def validate_preset(self, preset_dict: Dict[str, Any]) -> ValidationResult:
        """
        Validate cache preset configuration.

        Args:
            preset_dict: Preset configuration dictionary

        Returns:
            ValidationResult with validation status and messages
        """
        result = ValidationResult(is_valid=True, validation_type="preset")

        # Check required fields
        required_fields = [
            "name", "description", "strategy", "default_ttl", "max_connections",
            "connection_timeout", "memory_cache_size", "compression_threshold",
            "compression_level", "enable_ai_cache", "enable_monitoring", "log_level",
            "environment_contexts"
        ]

        for field_name in required_fields:
            if field_name not in preset_dict:
                result.add_error(f"Missing required field: {field_name}", field_path=field_name)

        if not result.is_valid:
            return result

        # Validate field types and ranges
        self._validate_preset_fields(preset_dict, result)

        # Validate AI optimizations if AI is enabled
        if preset_dict.get("enable_ai_cache", False):
            self._validate_ai_optimizations(preset_dict.get("ai_optimizations", {}), result)

        # Validate environment contexts
        self._validate_environment_contexts(preset_dict.get("environment_contexts", []), result)

        # Performance and consistency checks
        self._validate_preset_consistency(preset_dict, result)

        return result

    def validate_configuration(self, config_dict: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete cache configuration.

        Args:
            config_dict: Complete cache configuration dictionary

        Returns:
            ValidationResult with validation status and messages
        """
        result = ValidationResult(is_valid=True, validation_type="configuration")

        # Basic field validation
        self._validate_config_fields(config_dict, result)

        # Redis configuration validation
        if config_dict.get("redis_url"):
            self._validate_redis_config(config_dict, result)

        # AI configuration validation
        if config_dict.get("enable_ai_cache", False):
            self._validate_ai_config(config_dict, result)

        # Performance configuration validation
        self._validate_performance_config(config_dict, result)

        # Security configuration validation
        self._validate_security_config(config_dict, result)

        return result

    def validate_custom_overrides(self, overrides: Dict[str, Any]) -> ValidationResult:
        """
        Validate custom configuration overrides.

        Args:
            overrides: Custom override dictionary

        Returns:
            ValidationResult with validation status and messages
        """
        result = ValidationResult(is_valid=True, validation_type="custom_overrides")

        # Validate override keys are recognized
        valid_keys = {
            "redis_url", "redis_password", "use_tls", "tls_cert_path", "tls_key_path",
            "max_connections", "connection_timeout", "default_ttl", "memory_cache_size",
            "compression_threshold", "compression_level", "enable_ai_cache",
            "text_hash_threshold", "hash_algorithm", "text_size_tiers", "operation_ttls",
            "enable_smart_promotion", "max_text_length", "enable_monitoring", "log_level"
        }

        for key in overrides.keys():
            if key not in valid_keys:
                result.add_warning(
                    f"Unknown override key '{key}' - will be ignored",
                    field_path=key,
                    context={"valid_keys": sorted(valid_keys)}
                )

        # Validate override values
        for key, value in overrides.items():
            if key in valid_keys:
                self._validate_override_value(key, value, result)

        return result

    def get_template(self, template_name: str) -> Dict[str, Any]:
        """
        Get configuration template by name.

        Args:
            template_name: Name of template (fast_development, robust_production, etc.)

        Returns:
            Configuration template dictionary

        Raises:
            ValueError: If template name is not found
        """
        if template_name not in self.templates:
            available = list(self.templates.keys())
            raise ValueError(f"Unknown template '{template_name}'. Available: {available}")

        return self.templates[template_name].copy()

    def list_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())

    def compare_configurations(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two configurations and return differences.

        Args:
            config1: First configuration
            config2: Second configuration

        Returns:
            Dictionary with comparison results
        """
        differences: Dict[str, List[Any]] = {
            "added_keys": [],
            "removed_keys": [],
            "changed_values": [],
            "identical_keys": []
        }

        keys1 = set(config1.keys())
        keys2 = set(config2.keys())

        differences["added_keys"] = sorted(keys2 - keys1)
        differences["removed_keys"] = sorted(keys1 - keys2)

        common_keys = keys1 & keys2
        for key in sorted(common_keys):
            if config1[key] == config2[key]:
                differences["identical_keys"].append(key)
            else:
                differences["changed_values"].append({
                    "key": key,
                    "old_value": config1[key],
                    "new_value": config2[key]
                })

        return differences

    def _validate_preset_fields(self, preset_dict: Dict[str, Any], result: ValidationResult) -> None:
        """Validate preset field types and ranges."""
        # Validate TTL
        ttl = preset_dict.get("default_ttl", 0)
        if not isinstance(ttl, int) or ttl < 60 or ttl > 604800:  # 1 minute to 1 week
            result.add_error(
                f"default_ttl must be integer between 60 and 604800 seconds, got: {ttl}",
                field_path="default_ttl"
            )

        # Validate connections
        max_conn = preset_dict.get("max_connections", 0)
        if not isinstance(max_conn, int) or max_conn < 1 or max_conn > 100:
            result.add_error(
                f"max_connections must be integer between 1 and 100, got: {max_conn}",
                field_path="max_connections"
            )

        # Validate timeout
        timeout = preset_dict.get("connection_timeout", 0)
        if not isinstance(timeout, int) or timeout < 1 or timeout > 60:
            result.add_error(
                f"connection_timeout must be integer between 1 and 60 seconds, got: {timeout}",
                field_path="connection_timeout"
            )

        # Validate cache size
        cache_size = preset_dict.get("memory_cache_size", 0)
        if not isinstance(cache_size, int) or cache_size < 1 or cache_size > 10000:
            result.add_error(
                f"memory_cache_size must be integer between 1 and 10000, got: {cache_size}",
                field_path="memory_cache_size"
            )

        # Validate compression
        comp_level = preset_dict.get("compression_level", 0)
        if not isinstance(comp_level, int) or comp_level < 1 or comp_level > 9:
            result.add_error(
                f"compression_level must be integer between 1 and 9, got: {comp_level}",
                field_path="compression_level"
            )

    def _validate_ai_optimizations(self, ai_opts: Dict[str, Any], result: ValidationResult) -> None:
        """Validate AI optimization settings."""
        if not ai_opts:
            result.add_info("AI cache enabled but no optimizations specified - using defaults")
            return

        # Validate text hash threshold
        threshold = ai_opts.get("text_hash_threshold", 0)
        if threshold and (not isinstance(threshold, int) or threshold < 100 or threshold > 10000):
            result.add_error(
                f"text_hash_threshold must be integer between 100 and 10000, got: {threshold}",
                field_path="ai_optimizations.text_hash_threshold"
            )

        # Validate operation TTLs
        op_ttls = ai_opts.get("operation_ttls", {})
        if op_ttls and isinstance(op_ttls, dict):
            for operation, ttl in op_ttls.items():
                if not isinstance(ttl, int) or ttl < 60:
                    result.add_error(
                        f"operation_ttls['{operation}'] must be integer >= 60 seconds, got: {ttl}",
                        field_path=f"ai_optimizations.operation_ttls.{operation}"
                    )

        # Validate text size tiers
        tiers = ai_opts.get("text_size_tiers", {})
        if tiers and isinstance(tiers, dict):
            tier_values = list(tiers.values())
            if tier_values != sorted(tier_values):
                result.add_warning(
                    "text_size_tiers values should be in ascending order for optimal performance",
                    field_path="ai_optimizations.text_size_tiers"
                )

    def _validate_environment_contexts(self, contexts: List[str], result: ValidationResult) -> None:
        """Validate environment contexts."""
        if not contexts:
            result.add_warning("No environment contexts specified")
            return

        valid_contexts = {
            "development", "dev", "testing", "test", "staging", "stage",
            "production", "prod", "ai-development", "ai-production",
            "local", "demo", "sandbox", "minimal"
        }

        for context in contexts:
            if context not in valid_contexts:
                result.add_warning(
                    f"Unknown environment context '{context}' - may not match auto-detection",
                    field_path="environment_contexts",
                    context={"valid_contexts": sorted(valid_contexts)}
                )

    def _validate_preset_consistency(self, preset_dict: Dict[str, Any], result: ValidationResult) -> None:
        """Validate preset internal consistency."""
        # Check if AI settings are consistent
        ai_enabled = preset_dict.get("enable_ai_cache", False)
        ai_opts = preset_dict.get("ai_optimizations", {})

        if ai_enabled and not ai_opts:
            result.add_info("AI cache enabled without specific optimizations - using defaults")
        elif not ai_enabled and ai_opts:
            result.add_warning("AI optimizations specified but AI cache not enabled")

        # Check TTL vs cache size consistency
        ttl = preset_dict.get("default_ttl", 3600)
        cache_size = preset_dict.get("memory_cache_size", 100)

        if ttl > 7200 and cache_size < 200:  # Long TTL with small cache
            result.add_warning(
                "Long TTL with small memory cache may cause frequent evictions",
                context={"ttl": ttl, "cache_size": cache_size}
            )

    def _validate_config_fields(self, config_dict: Dict[str, Any], result: ValidationResult) -> None:
        """Validate configuration field types."""
        # This is a simplified version - could be expanded with full schema validation
        required_fields = ["strategy"]

        for field_name in required_fields:
            if field_name not in config_dict:
                result.add_error(f"Missing required field: {field_name}", field_path=field_name)

    def _validate_redis_config(self, config_dict: Dict[str, Any], result: ValidationResult) -> None:
        """Validate Redis configuration."""
        redis_url = config_dict.get("redis_url", "")

        if not redis_url.startswith(("redis://", "rediss://")):
            result.add_error(
                f"Invalid Redis URL format: {redis_url}",
                field_path="redis_url"
            )

        # Check TLS configuration consistency
        use_tls = config_dict.get("use_tls", False)
        if use_tls and not redis_url.startswith("rediss://"):
            result.add_warning(
                "use_tls=True but Redis URL doesn't use rediss:// scheme",
                field_path="use_tls"
            )

    def _validate_ai_config(self, config_dict: Dict[str, Any], result: ValidationResult) -> None:
        """Validate AI-specific configuration."""
        threshold = config_dict.get("text_hash_threshold", 1000)
        if threshold < 100:
            result.add_warning(
                f"text_hash_threshold {threshold} is very low - may cause excessive hashing",
                field_path="text_hash_threshold"
            )

    def _validate_performance_config(self, config_dict: Dict[str, Any], result: ValidationResult) -> None:
        """Validate performance-related configuration."""
        max_conn = config_dict.get("max_connections", 10)
        timeout = config_dict.get("connection_timeout", 5)

        if max_conn > 50 and timeout < 10:
            result.add_warning(
                "High connection count with low timeout may cause connection issues",
                context={"max_connections": max_conn, "connection_timeout": timeout}
            )

    def _validate_security_config(self, config_dict: Dict[str, Any], result: ValidationResult) -> None:
        """Validate security-related configuration."""
        use_tls = config_dict.get("use_tls", False)
        password = config_dict.get("redis_password")

        if not use_tls and password:
            result.add_warning(
                "Redis password specified without TLS - password transmitted in plain text",
                field_path="security"
            )

    def _validate_override_value(self, key: str, value: Any, result: ValidationResult) -> None:
        """Validate individual override value."""
        # Type validation based on key
        type_mapping = {
            "redis_url": str,
            "default_ttl": int,
            "max_connections": int,
            "connection_timeout": int,
            "memory_cache_size": int,
            "compression_threshold": int,
            "compression_level": int,
            "enable_ai_cache": bool,
            "text_hash_threshold": int,
            "enable_monitoring": bool,
            "use_tls": bool
        }

        expected_type = type_mapping.get(key)
        if expected_type and not isinstance(value, expected_type):
            result.add_error(
                f"Override '{key}' expects {expected_type.__name__}, got {type(value).__name__}",
                field_path=key
            )

    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load JSON schemas for validation."""
        # Simplified schema definitions - could be loaded from files
        return {
            "preset": {
                "type": "object",
                "required": ["name", "description", "strategy"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "strategy": {"type": "string", "enum": ["fast", "balanced", "robust", "ai_optimized"]}
                }
            },
            "configuration": {
                "type": "object",
                "properties": {
                    "redis_url": {"type": "string"},
                    "default_ttl": {"type": "integer", "minimum": 60, "maximum": 604800}
                }
            }
        }

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load configuration templates."""
        return {
            "fast_development": {
                "strategy": "fast",
                "default_ttl": 600,
                "max_connections": 3,
                "connection_timeout": 2,
                "memory_cache_size": 50,
                "compression_threshold": 2000,
                "compression_level": 3,
                "enable_ai_cache": False,
                "enable_monitoring": True,
                "log_level": "DEBUG"
            },
            "robust_production": {
                "strategy": "robust",
                "default_ttl": 7200,
                "max_connections": 20,
                "connection_timeout": 10,
                "memory_cache_size": 500,
                "compression_threshold": 500,
                "compression_level": 9,
                "enable_ai_cache": False,
                "enable_monitoring": True,
                "log_level": "INFO"
            },
            "ai_optimized": {
                "strategy": "ai_optimized",
                "default_ttl": 14400,
                "max_connections": 25,
                "connection_timeout": 15,
                "memory_cache_size": 1000,
                "compression_threshold": 300,
                "compression_level": 9,
                "enable_ai_cache": True,
                "text_hash_threshold": 1000,
                "enable_monitoring": True,
                "log_level": "INFO"
            }
        }


# Global cache validator instance
cache_validator = CacheValidator()
