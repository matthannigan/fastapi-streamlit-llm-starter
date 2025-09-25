"""
Parameter mapping utilities for cache inheritance and validation.

This module provides comprehensive parameter mapping functionality to enable
proper inheritance between cache implementations. It separates AI-specific
parameters from generic cache parameters and validates compatibility.

## Classes

- **ValidationResult**: Parameter validation results with detailed error reporting
- **CacheParameterMapper**: Main parameter mapping and validation logic

## Key Features

- **Parameter Separation**: Clean separation of AI-specific and generic parameters
- **Parameter Mapping**: Intelligent mapping between different parameter naming schemes
- **Validation**: Comprehensive compatibility validation with detailed error messages
- **Transformation**: Parameter value transformation and normalization
- **Debugging Support**: Detailed logging for parameter mapping troubleshooting

## Usage

```python
mapper = CacheParameterMapper()
ai_params = {
    'redis_url': 'redis://localhost:6379',
        ...     'text_hash_threshold': 1000,
        ...     'memory_cache_size': 100,
        ...     'compression_threshold': 1000
        ... }
        >>> generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        >>> print(f"Generic: {generic_params}")
        >>> print(f"AI-specific: {ai_specific_params}")

    Parameter validation:
        >>> validation_result = mapper.validate_parameter_compatibility(ai_params)
        >>> if not validation_result.is_valid:
        ...     for error in validation_result.errors:
        ...         print(f"Error: {error}")
        ... else:
        ...     print("All parameters are compatible")

Architecture Context:
    This module provides parameter mapping for cache inheritance, separating
    AI-specific parameters from generic Redis parameters for clean inheritance.

Dependencies:
    - dataclasses: For ValidationResult structure
    - typing: For type annotations and generics
    - logging: For debugging and monitoring
    - app.core.exceptions: For custom exception handling
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple
from app.core.exceptions import ConfigurationError


@dataclass
class ValidationResult:
    """
    Comprehensive parameter validation result with detailed error reporting and recommendations.
    
    Provides structured validation feedback for cache parameter mapping and compatibility checking.
    Includes specific error messages, warnings for suboptimal configurations, and intelligent
    recommendations for parameter optimization.
    
    Attributes:
        is_valid: bool indicating whether all parameters passed validation checks
        errors: List[str] specific validation error messages requiring correction
        warnings: List[str] configuration warnings for suboptimal but valid settings
        recommendations: List[str] intelligent suggestions for parameter optimization
        parameter_conflicts: Dict[str, str] mapping of conflicting parameters to conflict descriptions
        ai_specific_params: Set[str] of parameters identified as AI-specific
        generic_params (Set[str]): Set of parameters identified as generic Redis parameters
        context (Dict[str, Any]): Additional validation context information
    
    Behavior:
        - Aggregates validation results from multiple parameter checking phases
        - Provides actionable error messages with specific parameter references
        - Includes performance and security recommendations for configuration improvement
        - Maintains validation context for debugging and troubleshooting
        - Thread-safe result structure for concurrent validation operations
    
    Examples:
        >>> result = ValidationResult()
        >>> result.errors.append("redis_url cannot be empty")
        >>> result.warnings.append("Low TTL may impact performance")
        >>> result.recommendations.append("Consider enabling compression")
        >>>
        >>> if result.is_valid:
        ...     print("Configuration validated successfully")
        ... else:
        ...     for error in result.errors:
        ...         logger.error(f"Validation error: {error}")
    
    Example:
        >>> result = ValidationResult(
        ...     is_valid=False,
        ...     errors=["Invalid compression_threshold: must be positive"],
        ...     warnings=["memory_cache_size conflicts with l1_cache_size"],
        ...     recommendations=["Consider using l1_cache_size instead of memory_cache_size"]
        ... )
        >>> if not result.is_valid:
        ...     for error in result.errors:
        ...         print(f"❌ {error}")
    """

    def add_error(self, message: str) -> None:
        """
        Add a validation error and mark result as invalid.
        """
        ...

    def add_warning(self, message: str) -> None:
        """
        Add a non-fatal validation warning.
        """
        ...

    def add_recommendation(self, message: str) -> None:
        """
        Add a configuration recommendation.
        """
        ...

    def add_conflict(self, parameter: str, description: str) -> None:
        """
        Add a parameter conflict with description.
        """
        ...


class CacheParameterMapper:
    """
    Parameter mapping system for cache inheritance architecture.
    
    Provides parameter separation, mapping, and validation to support
    AIResponseCache inheritance from GenericRedisCache. Separates AI-specific
    parameters from generic Redis parameters and validates configuration.
    
    Key Methods:
        map_ai_to_generic_params(): Separate AI parameters from generic parameters
        validate_parameter_compatibility(): Validate parameter configuration
    
    Usage:
        mapper = CacheParameterMapper()
        ai_params = {
            'redis_url': 'redis://localhost:6379',
            'text_hash_threshold': 1000,
            'memory_cache_size': 100
        }
    
        generic_params, ai_specific = mapper.map_ai_to_generic_params(ai_params)
        validation = mapper.validate_parameter_compatibility(ai_params)
    """

    def __init__(self):
        """
        Initialize the parameter mapper with comprehensive parameter definitions.
        """
        ...

    def map_ai_to_generic_params(self, ai_params: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Separate AI parameters into generic Redis parameters and AI-specific parameters.
        
        This method performs the core parameter separation logic, mapping AI parameters
        to their generic equivalents where applicable and separating truly AI-specific
        parameters for specialized handling.
        
        Args:
            ai_params (Dict[str, Any]): Dictionary of AI cache parameters including both
                                      generic and AI-specific parameters
        
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: A tuple containing:
                - generic_params: Parameters suitable for GenericRedisCache initialization
                - ai_specific_params: Parameters unique to AI cache functionality
        
        Raises:
            ValidationError: If critical parameter validation fails
            ConfigurationError: If parameter mapping encounters unresolvable conflicts
        
        Example:
            >>> mapper = CacheParameterMapper()
            >>> ai_params = {
            ...     'redis_url': 'redis://localhost:6379',
            ...     'memory_cache_size': 100,
            ...     'text_hash_threshold': 1000,
            ...     'compression_threshold': 2000
            ... }
            >>> generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
            >>> # generic_params = {'redis_url': '...', 'l1_cache_size': 100, 'compression_threshold': 2000}
            >>> # ai_specific_params = {'text_hash_threshold': 1000}
        """
        ...

    def validate_parameter_compatibility(self, ai_params: Dict[str, Any]) -> ValidationResult:
        """
        Validate parameter compatibility and identify potential conflicts.
        
        Performs comprehensive validation of AI cache parameters including:
        - Type and value range validation
        - Parameter conflict detection
        - Configuration consistency checks
        - Best practice recommendations
        
        Args:
            ai_params (Dict[str, Any]): Dictionary of AI cache parameters to validate
        
        Returns:
            ValidationResult: Comprehensive validation result with errors, warnings,
                            and recommendations for optimal configuration
        
        Example:
            >>> mapper = CacheParameterMapper()
            >>> params = {'memory_cache_size': -10, 'text_hash_threshold': 'invalid'}
            >>> result = mapper.validate_parameter_compatibility(params)
            >>> if not result.is_valid:
            ...     for error in result.errors:
            ...         print(f"Error: {error}")
            Error: Parameter 'memory_cache_size' must be >= 1, got -10
            Error: Parameter 'text_hash_threshold' must be int, got str
        """
        ...

    def get_parameter_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about parameter classifications and mappings.
        
        Returns:
            Dict[str, Any]: Dictionary containing complete parameter information including
                          classifications, mappings, and validation rules
        
        Example:
            >>> mapper = CacheParameterMapper()
            >>> info = mapper.get_parameter_info()
            >>> print(f"Generic parameters: {info['generic_parameters']}")
            >>> print(f"Parameter mappings: {info['parameter_mappings']}")
        """
        ...
