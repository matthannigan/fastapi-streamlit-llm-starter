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
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationSeverity(str, Enum):
    """
    Severity levels for validation messages.
    """

    ...


@dataclass
class ValidationMessage:
    """
    Single validation message with severity and context.
    """

    ...


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

    @property
    def errors(self) -> List[str]:
        """
        Get list of error messages.
        """
        ...

    @property
    def warnings(self) -> List[str]:
        """
        Get list of warning messages.
        """
        ...

    @property
    def info(self) -> List[str]:
        """
        Get list of info messages.
        """
        ...

    def add_error(self, message: str, field_path: str = '', context: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an error message and mark validation as invalid.
        """
        ...

    def add_warning(self, message: str, field_path: str = '', context: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a warning message.
        """
        ...

    def add_info(self, message: str, field_path: str = '', context: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an info message.
        """
        ...


class CacheValidator:
    """
    Comprehensive cache configuration validator with JSON schema support.
    """

    def __init__(self):
        """
        Initialize validator with schemas and templates.
        """
        ...

    def validate_preset(self, preset_dict: Dict[str, Any]) -> ValidationResult:
        """
        Validate cache preset configuration.
        
        Args:
            preset_dict: Preset configuration dictionary
        
        Returns:
            ValidationResult with validation status and messages
        """
        ...

    def validate_configuration(self, config_dict: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete cache configuration.
        
        Args:
            config_dict: Complete cache configuration dictionary
        
        Returns:
            ValidationResult with validation status and messages
        """
        ...

    def validate_custom_overrides(self, overrides: Dict[str, Any]) -> ValidationResult:
        """
        Validate custom configuration overrides.
        
        Args:
            overrides: Custom override dictionary
        
        Returns:
            ValidationResult with validation status and messages
        """
        ...

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
        ...

    def list_templates(self) -> List[str]:
        """
        Get list of available template names.
        """
        ...

    def compare_configurations(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two configurations and return differences.
        
        Args:
            config1: First configuration
            config2: Second configuration
        
        Returns:
            Dictionary with comparison results
        """
        ...
