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

# Configure module-level logging
logger = logging.getLogger(__name__)


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

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    parameter_conflicts: Dict[str, str] = field(default_factory=dict)
    ai_specific_params: Set[str] = field(default_factory=set)
    generic_params: Set[str] = field(default_factory=set)
    context: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        """Add a validation error and mark result as invalid."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a non-fatal validation warning."""
        self.warnings.append(message)

    def add_recommendation(self, message: str) -> None:
        """Add a configuration recommendation."""
        self.recommendations.append(message)

    def add_conflict(self, parameter: str, description: str) -> None:
        """Add a parameter conflict with description."""
        self.parameter_conflicts[parameter] = description
        self.add_error(f"Parameter conflict for '{parameter}': {description}")


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
        """Initialize the parameter mapper with comprehensive parameter definitions."""
        logger.debug("Initializing CacheParameterMapper")

        # Define the authoritative parameter classifications based on current cache implementations

        # Generic Redis parameters that are shared between all Redis cache implementations
        self._generic_parameters: Set[str] = {
            "redis_url",  # Redis connection URL
            "default_ttl",  # Default time-to-live for cache entries
            "enable_l1_cache",  # Enable in-memory L1 cache tier
            "l1_cache_size",  # Maximum entries in L1 cache
            "compression_threshold",  # Size threshold for compression
            "compression_level",  # Zlib compression level (1-9)
            "performance_monitor",  # CachePerformanceMonitor instance
            "security_config",  # SecurityConfig for secure connections
        }

        # AI-specific parameters unique to AI response caching
        self._ai_specific_parameters: Set[str] = {
            "text_hash_threshold",  # Character threshold for text hashing
            "hash_algorithm",  # Hash algorithm for large texts
            "text_size_tiers",  # Text categorization thresholds
            "operation_ttls",  # TTL values per AI operation type
        }

        # Parameter mappings: AI parameter -> Generic parameter
        # These handle cases where AI parameters map to generic equivalents
        self._parameter_mappings: Dict[str, str] = {
            "memory_cache_size": "l1_cache_size",  # AI uses memory_cache_size, generic uses l1_cache_size
        }

        # Conflicting parameters that have different meanings in each context
        self._parameter_conflicts: Dict[str, str] = {
            # Currently no known conflicts, but structure ready for future conflicts
        }

        # Valid value ranges and types for parameter validation
        self._parameter_validators: Dict[str, Dict[str, Any]] = {
            "redis_url": {
                "type": str,
                "required": False,
                "validator": self._validate_redis_url,
            },
            "default_ttl": {
                "type": int,
                "required": False,
                "min_value": 1,
                "max_value": 86400 * 365,  # 1 year max
            },
            "enable_l1_cache": {"type": bool, "required": False},
            "l1_cache_size": {
                "type": int,
                "required": False,
                "min_value": 1,
                "max_value": 10000,
            },
            "memory_cache_size": {
                "type": int,
                "required": False,
                "min_value": 1,
                "max_value": 10000,
            },
            "compression_threshold": {
                "type": int,
                "required": False,
                "min_value": 0,
                "max_value": 1024 * 1024,  # 1MB max
            },
            "compression_level": {
                "type": int,
                "required": False,
                "min_value": 1,
                "max_value": 9,
            },
            "text_hash_threshold": {
                "type": int,
                "required": False,
                "min_value": 1,
                "max_value": 100000,
            },
            "text_size_tiers": {
                "type": dict,
                "required": False,
                "validator": self._validate_text_size_tiers,
            },
            "operation_ttls": {
                "type": dict,
                "required": False,
                "validator": self._validate_operation_ttls,
            },
        }

        logger.info(
            f"CacheParameterMapper initialized with {len(self._generic_parameters)} generic, "
            f"{len(self._ai_specific_parameters)} AI-specific, and {len(self._parameter_mappings)} mapped parameters"
        )

    def map_ai_to_generic_params(
        self, ai_params: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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
        logger.debug(
            f"Mapping AI parameters to generic parameters: {list(ai_params.keys())}"
        )

        try:
            generic_params: Dict[str, Any] = {}
            ai_specific_params: Dict[str, Any] = {}

            for param_name, param_value in ai_params.items():
                logger.debug(f"Processing parameter: {param_name} = {param_value}")

                # Check if parameter should be mapped to a different generic parameter name
                if param_name in self._parameter_mappings:
                    generic_param_name = self._parameter_mappings[param_name]
                    generic_params[generic_param_name] = param_value
                    logger.debug(f"Mapped {param_name} -> {generic_param_name}")

                # Check if it's a direct generic parameter
                elif param_name in self._generic_parameters:
                    generic_params[param_name] = param_value
                    logger.debug(f"Direct generic parameter: {param_name}")

                # Check if it's an AI-specific parameter
                elif param_name in self._ai_specific_parameters:
                    ai_specific_params[param_name] = param_value
                    logger.debug(f"AI-specific parameter: {param_name}")

                # Unknown parameter - log warning but don't fail
                else:
                    logger.warning(
                        f"Unknown parameter '{param_name}' - treating as AI-specific"
                    )
                    ai_specific_params[param_name] = param_value

            # Ensure L1 cache is enabled if l1_cache_size is provided
            if (
                "l1_cache_size" in generic_params
                and "enable_l1_cache" not in generic_params
            ):
                generic_params["enable_l1_cache"] = True
                logger.debug("Auto-enabled L1 cache due to l1_cache_size parameter")

            logger.info(
                f"Parameter mapping complete: {len(generic_params)} generic, "
                f"{len(ai_specific_params)} AI-specific"
            )

            return generic_params, ai_specific_params

        except Exception as e:
            error_msg = f"Failed to map AI parameters to generic parameters: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(
                error_msg,
                context={
                    "ai_params": list(ai_params.keys()),
                    "error_type": type(e).__name__,
                },
            )

    def validate_parameter_compatibility(
        self, ai_params: Dict[str, Any]
    ) -> ValidationResult:
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
        logger.debug(
            f"Validating parameter compatibility for {len(ai_params)} parameters"
        )

        result = ValidationResult()
        result.context = {
            "total_parameters": len(ai_params),
            "validation_timestamp": logger.name,  # Using logger name as placeholder for timestamp
            "parameter_names": list(ai_params.keys()),
        }

        try:
            # Classify parameters for the result
            for param_name in ai_params.keys():
                if (
                    param_name in self._generic_parameters
                    or param_name in self._parameter_mappings
                ):
                    result.generic_params.add(param_name)
                elif param_name in self._ai_specific_parameters:
                    result.ai_specific_params.add(param_name)

            # Validate individual parameters
            for param_name, param_value in ai_params.items():
                self._validate_single_parameter(param_name, param_value, result)

            # Check for parameter conflicts
            self._check_parameter_conflicts(ai_params, result)

            # Add configuration recommendations
            self._add_configuration_recommendations(ai_params, result)

            # Final validation summary
            if result.is_valid:
                logger.info(
                    f"Parameter validation passed for {len(ai_params)} parameters"
                )
            else:
                logger.warning(
                    f"Parameter validation failed with {len(result.errors)} errors "
                    f"and {len(result.warnings)} warnings"
                )

            return result

        except Exception as e:
            error_msg = f"Parameter validation failed with exception: {e}"
            logger.error(error_msg, exc_info=True)
            result.add_error(error_msg)
            result.context["validation_exception"] = str(e)
            return result

    def _validate_single_parameter(
        self, param_name: str, param_value: Any, result: ValidationResult
    ) -> None:
        """Validate a single parameter against its validation rules."""
        if param_name not in self._parameter_validators:
            logger.debug(f"No validation rules for parameter '{param_name}' - skipping")
            return

        validator_config = self._parameter_validators[param_name]

        # Type validation
        expected_type = validator_config.get("type")
        if expected_type and not isinstance(param_value, expected_type):
            result.add_error(
                f"Parameter '{param_name}' must be {expected_type.__name__}, got {type(param_value).__name__}"
            )
            return  # Skip further validation if type is wrong

        # Required validation
        if validator_config.get("required", False) and param_value is None:
            result.add_error(f"Parameter '{param_name}' is required but not provided")
            return

        # Skip validation if value is None and parameter is not required
        if param_value is None:
            return

        # Range validation for numeric parameters
        min_value = validator_config.get("min_value")
        max_value = validator_config.get("max_value")

        if (
            min_value is not None
            and isinstance(param_value, (int, float))
            and param_value < min_value
        ):
            result.add_error(
                f"Parameter '{param_name}' must be >= {min_value}, got {param_value}"
            )

        if (
            max_value is not None
            and isinstance(param_value, (int, float))
            and param_value > max_value
        ):
            result.add_error(
                f"Parameter '{param_name}' must be <= {max_value}, got {param_value}"
            )

        # Custom validator function
        custom_validator = validator_config.get("validator")
        if custom_validator:
            try:
                custom_validator(param_value, result, param_name)
            except Exception as e:
                result.add_error(f"Custom validation failed for '{param_name}': {e}")

    def _validate_redis_url(
        self, redis_url: str, result: ValidationResult, param_name: str
    ) -> None:
        """Custom validator for Redis URL format."""
        if not redis_url.startswith(("redis://", "rediss://", "unix://")):
            result.add_error(
                f"Parameter '{param_name}' must be a valid Redis URL "
                f"(redis://, rediss://, or unix://), got: {redis_url}"
            )

    def _validate_text_size_tiers(
        self, text_size_tiers: Dict[str, int], result: ValidationResult, param_name: str
    ) -> None:
        """Custom validator for text size tiers configuration."""
        required_tiers = {"small", "medium", "large"}
        provided_tiers = set(text_size_tiers.keys())

        missing_tiers = required_tiers - provided_tiers
        if missing_tiers:
            result.add_error(
                f"Parameter '{param_name}' missing required tiers: {missing_tiers}"
            )

        # Validate tier values are positive integers
        for tier_name, tier_value in text_size_tiers.items():
            if not isinstance(tier_value, int) or tier_value <= 0:
                result.add_error(
                    f"Text size tier '{tier_name}' must be a positive integer, got: {tier_value}"
                )

        # Validate tier ordering: small < medium < large
        if all(tier in text_size_tiers for tier in required_tiers):
            if not (
                text_size_tiers["small"]
                < text_size_tiers["medium"]
                < text_size_tiers["large"]
            ):
                result.add_error(
                    f"Text size tiers must be ordered: small < medium < large, "
                    f"got: small={text_size_tiers['small']}, medium={text_size_tiers['medium']}, "
                    f"large={text_size_tiers['large']}"
                )

    def _validate_operation_ttls(
        self, operation_ttls: Dict[str, int], result: ValidationResult, param_name: str
    ) -> None:
        """Custom validator for operation TTL configuration."""
        valid_operations = {"summarize", "sentiment", "key_points", "questions", "qa"}

        for operation, ttl in operation_ttls.items():
            # Validate TTL is positive integer
            if not isinstance(ttl, int) or ttl <= 0:
                result.add_error(
                    f"Operation TTL for '{operation}' must be a positive integer, got: {ttl}"
                )

            # Validate TTL is reasonable (not more than 1 year)
            if isinstance(ttl, int) and ttl > 86400 * 365:
                result.add_warning(
                    f"Operation TTL for '{operation}' is very large ({ttl} seconds = {ttl // 86400} days). "
                    f"Consider if this is intentional."
                )

            # Warn about unknown operations
            if operation not in valid_operations:
                result.add_warning(
                    f"Unknown operation '{operation}' in operation_ttls. "
                    f"Valid operations: {valid_operations}"
                )

    def _check_parameter_conflicts(
        self, ai_params: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Check for parameter conflicts and inconsistencies."""

        # Check for memory_cache_size vs l1_cache_size conflict
        if "memory_cache_size" in ai_params and "l1_cache_size" in ai_params:
            memory_size = ai_params["memory_cache_size"]
            l1_size = ai_params["l1_cache_size"]
            if memory_size != l1_size:
                result.add_conflict(
                    "memory_cache_size",
                    f"memory_cache_size ({memory_size}) conflicts with l1_cache_size ({l1_size}). "
                    f"These parameters map to the same GenericRedisCache parameter.",
                )

        # Check L1 cache consistency
        if "enable_l1_cache" in ai_params and not ai_params["enable_l1_cache"]:
            if "l1_cache_size" in ai_params or "memory_cache_size" in ai_params:
                result.add_warning(
                    "L1 cache is disabled but cache size is specified. "
                    "The size parameter will be ignored."
                )

        # Check compression configuration consistency
        if "compression_level" in ai_params and "compression_threshold" in ai_params:
            threshold = ai_params["compression_threshold"]
            level = ai_params["compression_level"]

            if threshold == 0 and level > 1:
                result.add_warning(
                    "Compression threshold is 0 (compression disabled) but compression level is > 1. "
                    "Consider setting compression_level to 1 or increasing compression_threshold."
                )

    def _add_configuration_recommendations(
        self, ai_params: Dict[str, Any], result: ValidationResult
    ) -> None:
        """Add configuration recommendations based on parameter analysis."""

        # Recommend enabling L1 cache for performance
        if (
            "l1_cache_size" in ai_params or "memory_cache_size" in ai_params
        ) and ai_params.get("enable_l1_cache") is False:
            result.add_recommendation(
                "Consider enabling L1 cache (enable_l1_cache=True) for better performance "
                "when cache size is specified"
            )

        # Recommend reasonable compression settings
        compression_threshold = ai_params.get("compression_threshold", 1000)
        compression_level = ai_params.get("compression_level", 6)

        if compression_threshold > 10000:
            result.add_recommendation(
                f"Compression threshold ({compression_threshold}) is quite high. "
                f"Consider lowering it to compress more responses and save memory."
            )

        if compression_level > 7:
            result.add_recommendation(
                f"Compression level ({compression_level}) is high, which uses more CPU. "
                f"Consider level 6 for balanced performance and compression."
            )

        # Recommend text hash threshold consistency
        text_hash_threshold = ai_params.get("text_hash_threshold", 1000)
        if text_hash_threshold != compression_threshold:
            result.add_recommendation(
                f"Text hash threshold ({text_hash_threshold}) differs from compression threshold "
                f"({compression_threshold}). Consider aligning these values for consistency."
            )

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
        return {
            "generic_parameters": sorted(self._generic_parameters),
            "ai_specific_parameters": sorted(self._ai_specific_parameters),
            "parameter_mappings": dict(self._parameter_mappings),
            "parameter_conflicts": dict(self._parameter_conflicts),
            "validation_rules": {
                param: {k: v for k, v in rules.items() if k != "validator"}
                for param, rules in self._parameter_validators.items()
            },
            "total_parameters": len(self._generic_parameters)
            + len(self._ai_specific_parameters),
        }


# Public exports
__all__ = [
    "ValidationResult",
    "CacheParameterMapper",
]
