"""
Security Scanner Configuration Models

This module provides comprehensive configuration models for security scanning services.
It supports flexible scanner configuration, performance optimization, and environment-based
configuration management.

## Configuration Overview

The configuration system supports multiple levels of configuration:
- **Scanner Configuration**: Individual scanner settings and parameters
- **Performance Configuration**: System performance and optimization settings
- **Security Configuration**: Overall security service configuration
- **Environment Configuration**: Environment-based configuration loading

## Configuration Features

### Scanner Configuration
- **Flexible Settings**: Per-scanner configuration with type-safe parameters
- **Threshold Management**: Configurable detection thresholds and sensitivity
- **Action Policies**: Configurable actions for detected violations
- **Model Selection**: Configurable model selection and parameters

### Performance Configuration
- **Caching Settings**: Model and result caching configuration
- **Concurrency Control**: Configurable concurrency limits and timeouts
- **Resource Management**: Memory and CPU usage optimization
- **Monitoring Settings**: Performance monitoring and metrics collection

### Environment Integration
- **Environment Variables**: Support for environment-based configuration
- **Presets**: Predefined configuration presets for different use cases
- **Validation**: Comprehensive configuration validation with helpful error messages
"""

from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field, validator


class ScannerType(str, Enum):
    """
    Enumeration of available security scanner types.

    Defines the categories of security analysis that can be applied to input and output text.
    Each scanner type represents a specific security or safety concern that the system can detect.

    **Input Scanners** - Analyze user-provided text for security risks:
    - PROMPT_INJECTION: Detects attempts to manipulate AI through prompt injection
    - TOXICITY_INPUT: Identifies harmful or inappropriate content in user input
    - PII_DETECTION: Finds personally identifiable information in text
    - MALICIOUS_URL: Detects potentially dangerous URLs
    - SUSPICIOUS_PATTERN: Identifies unusual patterns that may indicate attacks

    **Output Scanners** - Analyze AI-generated responses for safety concerns:
    - TOXICITY_OUTPUT: Checks AI responses for harmful content
    - BIAS_DETECTION: Identifies potential bias in AI responses
    - HARMFUL_CONTENT: Detects dangerous or inappropriate generated content
    - FACTUALITY_CHECK: Verifies accuracy of generated information
    - SENTIMENT_ANALYSIS: Analyzes emotional tone of responses

    Usage:
        >>> # Configure a specific scanner type
        scanner_type = ScannerType.PROMPT_INJECTION
        config = ScannerConfig(enabled=True, threshold=0.7)
        security_config.scanners[scanner_type] = config

        >>> # List all available input scanners
        input_scanners = [
            ScannerType.PROMPT_INJECTION,
            ScannerType.TOXICITY_INPUT,
            ScannerType.PII_DETECTION
        ]
    """

    # Input scanners
    PROMPT_INJECTION = "prompt_injection"
    TOXICITY_INPUT = "toxicity_input"
    PII_DETECTION = "pii_detection"
    MALICIOUS_URL = "malicious_url"
    SUSPICIOUS_PATTERN = "suspicious_pattern"

    # Output scanners
    TOXICITY_OUTPUT = "toxicity_output"
    BIAS_DETECTION = "bias_detection"
    HARMFUL_CONTENT = "harmful_content"
    FACTUALITY_CHECK = "factuality_check"
    SENTIMENT_ANALYSIS = "sentiment_analysis"


class ViolationAction(str, Enum):
    """
    Enumeration of actions to take when security violations are detected.

    Defines the response strategy when a scanner identifies content that violates
    security policies. Each action represents a different level of intervention
    from passive monitoring to complete blocking.

    **Available Actions:**
    - NONE: Passively log violations without blocking or modifying content
    - WARN: Allow content to proceed but include warning metadata
    - BLOCK: Completely prevent the content from being processed or delivered
    - REDACT: Remove or mask the problematic portions of the content
    - FLAG: Mark content for manual review while allowing processing

    Usage:
        >>> # Configure strict blocking for high-risk violations
        scanner_config = ScannerConfig(
            action=ViolationAction.BLOCK,
            threshold=0.5
        )

        >>> # Configure warning for moderate risk violations
        scanner_config = ScannerConfig(
            action=ViolationAction.WARN,
            threshold=0.7
        )

        >>> # Check if action requires content modification
        if scanner_config.action in [ViolationAction.BLOCK, ViolationAction.REDACT]:
            apply_content_filtering()
    """

    NONE = "none"  # No action, only log
    WARN = "warn"  # Return warning but allow content
    BLOCK = "block"  # Block the content entirely
    REDACT = "redact"  # Remove or redact problematic content
    FLAG = "flag"  # Flag for manual review


class PresetName(str, Enum):
    """
    Enumeration of predefined configuration presets for security scanning.

    Provides ready-to-use configuration templates optimized for different environments
    and security requirements. Each preset balances sensitivity, performance, and
    operational needs based on typical use cases.

    **Available Presets:**
    - STRICT: Maximum security with low thresholds, suitable for high-risk environments
    - BALANCED: Moderate security settings for general production use
    - LENIENT: Relaxed security with high thresholds, minimal false positives
    - DEVELOPMENT: Optimized for development with verbose logging and relaxed settings
    - PRODUCTION: Production-ready configuration with performance optimizations

    Usage:
        >>> # Create strict security configuration
        config = SecurityConfig.create_from_preset(PresetName.STRICT)

        >>> # Create development configuration
        dev_config = SecurityConfig.create_from_preset(
            PresetName.DEVELOPMENT,
            environment="development"
        )

        >>> # Compare preset characteristics
        if PresetName.STRICT in [PresetName.STRICT, PresetName.PRODUCTION]:
            enable_comprehensive_monitoring()
    """

    STRICT = "strict"
    BALANCED = "balanced"
    LENIENT = "lenient"
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class ScannerConfig(BaseModel):
    """
    Configuration for individual security scanners with comprehensive parameter control.

    Defines all operational parameters for a specific security scanner, including
    detection sensitivity, response actions, model selection, and performance
    constraints. Each scanner type (PROMPT_INJECTION, TOXICITY_INPUT, etc.) can
    have its own configuration instance.

    Attributes:
        enabled: Whether the scanner is active and should process content
        threshold: Detection sensitivity threshold (0.0 to 1.0, higher = more sensitive)
        action: Response action when violations are detected (BLOCK, WARN, etc.)
        model_name: Name of the ML model to use for detection (None for default)
        model_params: Model-specific parameters for tuning detection behavior
        scan_timeout: Maximum time allowed for scanning operation in seconds
        enabled_violation_types: Specific violation types to detect (empty = all)
        metadata: Additional scanner configuration and operational metadata

    State Management:
        - Configuration is immutable once created (Pydantic BaseModel)
        - All fields have sensible defaults for immediate use
        - Validation ensures thresholds and timeouts remain within operational bounds
        - Thread-safe for read operations across concurrent scanner instances

    Usage:
        >>> # Basic scanner configuration with defaults
        config = ScannerConfig()
        assert config.enabled and config.threshold == 0.7

        >>> # High-sensitivity configuration for critical security
        strict_config = ScannerConfig(
            enabled=True,
            threshold=0.3,  # Lower threshold = more sensitive
            action=ViolationAction.BLOCK,
            scan_timeout=60
        )

        >>> # Custom model configuration
        model_config = ScannerConfig(
            model_name="custom-toxicity-model-v2",
            model_params={"language": "en", "context_window": 512},
            enabled_violation_types=["harassment", "hate_speech"]
        )

        >>> # Check if scanner should process specific violation type
        if config.is_violation_type_enabled("harassment"):
            process_violation_type()
    """

    enabled: bool = True
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Detection threshold")
    action: ViolationAction = ViolationAction.BLOCK
    model_name: str | None = None
    model_params: Dict[str, Any] = Field(default_factory=dict)
    scan_timeout: int = Field(default=30, ge=1, le=300, description="Scan timeout in seconds")
    enabled_violation_types: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("threshold")
    def validate_threshold(cls, v: float) -> float:
        """
        Validate that detection threshold is within acceptable range.

        Args:
            v: Threshold value to validate

        Returns:
            Validated threshold value

        Raises:
            ValueError: If threshold is outside 0.0 to 1.0 range

        Behavior:
            - Ensures threshold values are mathematically valid for probability calculations
            - Prevents configuration errors that could cause scanner malfunction
            - Maintains consistency across all scanner configurations
        """
        if not 0.0 <= v <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        return v

    @validator("scan_timeout")
    def validate_scan_timeout(cls, v: int) -> int:
        """
        Validate that scan timeout is within operational limits.

        Args:
            v: Timeout value in seconds

        Returns:
            Validated timeout value

        Raises:
            ValueError: If timeout is less than 1 second or more than 5 minutes

        Behavior:
            - Prevents excessively short timeouts that could cause false negatives
            - Prevents excessively long timeouts that could impact system performance
            - Ensures reasonable response times for security scanning operations
        """
        if v < 1 or v > 300:
            raise ValueError("Scan timeout must be between 1 and 300 seconds")
        return v

    def get_effective_threshold(self) -> float:
        """
        Get the effective detection threshold for this scanner configuration.

        Returns:
            Current threshold value that determines detection sensitivity
            (0.0 = least sensitive, 1.0 = most sensitive)

        Behavior:
            - Returns the configured threshold value
            - Future extensions could apply environment-based adjustments
            - Used by scanning engines to determine violation detection level
        """
        return self.threshold

    def is_violation_type_enabled(self, violation_type: str) -> bool:
        """
        Check if a specific violation type is enabled for detection.

        Args:
            violation_type: String identifier of the violation type to check

        Returns:
            True if the violation type should be detected, False otherwise

        Behavior:
            - Returns True for all violation types when enabled_violation_types is empty
            - Returns True only for explicitly listed violation types when list is populated
            - Enables fine-grained control over which violations each scanner detects
            - Case-sensitive matching of violation type strings

        Examples:
            >>> # Scanner with all violation types enabled
            config = ScannerConfig(enabled_violation_types=[])
            assert config.is_violation_type_enabled("harassment")
            assert config.is_violation_type_enabled("hate_speech")

            >>> # Scanner with specific violation types enabled
            config = ScannerConfig(enabled_violation_types=["harassment"])
            assert config.is_violation_type_enabled("harassment")
            assert not config.is_violation_type_enabled("hate_speech")
        """
        if not self.enabled_violation_types:
            return True  # All types enabled if no specific list
        return violation_type in self.enabled_violation_types


class PerformanceConfig(BaseModel):
    """
    Configuration for security service performance optimization and resource management.

    Controls all performance-related aspects of the security scanning system including
    caching strategies, concurrency limits, memory usage, and monitoring. These settings
    balance security effectiveness with system performance and operational efficiency.

    Attributes:
        enable_model_caching: Whether to cache ML models in memory for faster loading
        enable_result_caching: Whether to cache scan results to avoid redundant processing
        cache_ttl_seconds: Time-to-live for cached results in seconds (1 minute to 1 hour)
        cache_redis_url: Redis connection URL for distributed result caching (None = memory-only)
        max_concurrent_scans: Maximum simultaneous scan operations (1-100)
        max_memory_mb: Maximum memory usage for security scanning in MB (512MB-8GB)
        enable_batch_processing: Whether to enable batch processing for multiple items
        batch_size: Number of items to process in each batch (1-50)
        enable_async_processing: Whether to use asynchronous processing for better throughput
        queue_size: Size of the async processing queue for pending scan requests (10-1000)
        metrics_collection_interval: Interval in seconds for collecting performance metrics (10-300)
        health_check_interval: Interval in seconds for system health checks (5-300)

    State Management:
        - Performance settings are applied globally across all scanner instances
        - Caching configurations affect both local and distributed cache behavior
        - Concurrency limits help prevent resource exhaustion under heavy load
        - All configurations validated to ensure operational stability

    Usage:
        >>> # High-performance configuration for production
        prod_config = PerformanceConfig(
            enable_model_caching=True,
            enable_result_caching=True,
            cache_ttl_seconds=1800,  # 30 minutes
            max_concurrent_scans=20,
            max_memory_mb=4096,
            enable_batch_processing=True,
            batch_size=10
        )

        >>> # Minimal configuration for development
        dev_config = PerformanceConfig(
            enable_result_caching=False,  # Fresh scans each time
            max_concurrent_scans=2,
            max_memory_mb=1024,
            enable_batch_processing=False
        )

        >>> # Memory-constrained configuration
        limited_config = PerformanceConfig(
            max_memory_mb=512,
            enable_model_caching=False,  # Reduce memory usage
            cache_ttl_seconds=60  # Short cache to limit memory
        )
    """

    enable_model_caching: bool = True
    enable_result_caching: bool = True
    cache_ttl_seconds: int = Field(default=300, ge=60, le=3600)
    cache_redis_url: str | None = None
    max_concurrent_scans: int = Field(default=10, ge=1, le=100)
    max_memory_mb: int = Field(default=2048, ge=512, le=8192)
    enable_batch_processing: bool = False
    batch_size: int = Field(default=5, ge=1, le=50)
    enable_async_processing: bool = True
    queue_size: int = Field(default=100, ge=10, le=1000)
    metrics_collection_interval: int = Field(default=60, ge=10, le=300)
    health_check_interval: int = Field(default=30, ge=5, le=300)

    @validator("cache_ttl_seconds")
    def validate_cache_ttl(cls, v: int) -> int:
        """
        Validate that cache TTL is within reasonable operational bounds.

        Args:
            v: Cache TTL in seconds

        Returns:
            Validated cache TTL value

        Raises:
            ValueError: If TTL is less than 1 minute or more than 1 hour

        Behavior:
            - Prevents excessively short TTLs that would cause cache churn
            - Prevents excessively long TTLs that could serve stale results
            - Balances performance benefits with result freshness requirements
        """
        if v < 60 or v > 3600:
            raise ValueError("Cache TTL must be between 60 and 3600 seconds")
        return v

    @validator("max_concurrent_scans")
    def validate_concurrent_scans(cls, v: int) -> int:
        """
        Validate that concurrent scans limit is within system capabilities.

        Args:
            v: Maximum number of concurrent scans

        Returns:
            Validated concurrent scans limit

        Raises:
            ValueError: If limit is less than 1 or more than 100

        Behavior:
            - Ensures minimum capacity for basic operation
            - Prevents resource exhaustion from excessive parallelism
            - Maintains system stability under varying load conditions
        """
        if v < 1 or v > 100:
            raise ValueError("Max concurrent scans must be between 1 and 100")
        return v


class LoggingConfig(BaseModel):
    """
    Configuration for security service logging and audit trail management.

    Controls comprehensive logging behavior for the security scanning system, including
    operational logs, violation reports, performance metrics, and audit trails. These
    settings balance operational visibility with privacy requirements and storage efficiency.

    Attributes:
        enable_scan_logging: Whether to log all security scan operations for audit trails
        enable_violation_logging: Whether to log all detected violations with details
        enable_performance_logging: Whether to log performance metrics and timing data
        log_level: Standard logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format for log entries (json for structured, text for readability)
        include_scanned_text: Whether to include actual scanned text in log entries
        sanitize_pii_in_logs: Whether to automatically detect and mask PII in log content
        log_retention_days: Number of days to retain log entries before rotation (1-365)

    State Management:
        - Logging configurations affect all scanner instances globally
        - Privacy settings (PII sanitization) override include_scanned_text when needed
        - Log retention policies apply to both structured and text log formats
        - Performance logging includes timing, memory usage, and scanner efficiency metrics

    Usage:
        >>> # Production configuration with privacy protection
        prod_logging = LoggingConfig(
            enable_scan_logging=True,
            enable_violation_logging=True,
            include_scanned_text=False,  # Privacy-first
            sanitize_pii_in_logs=True,
            log_level="INFO",
            log_format="json",
            log_retention_days=90
        )

        >>> # Development configuration with detailed debugging
        dev_logging = LoggingConfig(
            enable_performance_logging=True,
            include_scanned_text=True,  # For debugging
            log_level="DEBUG",
            log_format="text",
            log_retention_days=7
        )

        >>> # Minimal logging for privacy-sensitive environments
        minimal_logging = LoggingConfig(
            enable_violation_logging=True,  # Keep violations only
            enable_scan_logging=False,
            enable_performance_logging=False,
            sanitize_pii_in_logs=True,
            log_level="WARNING"
        )
    """

    enable_scan_logging: bool = True
    enable_violation_logging: bool = True
    enable_performance_logging: bool = True
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_format: str = Field(default="json", pattern="^(json|text)$")
    include_scanned_text: bool = False
    sanitize_pii_in_logs: bool = True
    log_retention_days: int = Field(default=30, ge=1, le=365)


class SecurityConfig(BaseModel):
    """
    Main configuration for the security scanning service with comprehensive control.

    Serves as the central configuration hub for the entire security scanning system,
    coordinating scanner configurations, performance settings, logging behavior,
    and environmental adaptations. Provides both programmatic configuration
    management and preset-based quick setup for common deployment scenarios.

    Attributes:
        scanners: Dictionary mapping scanner types to their individual configurations
        performance: Global performance optimization settings and resource limits
        logging: Logging configuration for audit trails and operational monitoring
        service_name: Identifier for the security service instance
        version: Configuration schema version for compatibility tracking
        preset: Optional preset name used for initial configuration
        environment: Deployment environment (development, staging, production, testing)
        debug_mode: Whether to enable debug-level logging and verbose output
        custom_settings: Additional user-defined configuration extensions

    Public Methods:
        get_scanner_config(): Retrieve configuration for a specific scanner type
        is_scanner_enabled(): Check if a scanner is currently enabled
        get_enabled_scanners(): List all scanner types that are currently active
        create_from_preset(): Factory method for creating preset-based configurations
        merge_with_environment_overrides(): Apply environment variable overrides
        to_dict(): Export configuration to dictionary format
        from_dict(): Import configuration from dictionary format

    State Management:
        - Configuration instances are immutable after creation (Pydantic BaseModel)
        - Environment overrides create new instances rather than modifying existing ones
        - Scanner configurations maintain independent state from global settings
        - Thread-safe for read operations across concurrent security scanning operations

    Usage:
        >>> # Create configuration from preset
        config = SecurityConfig.create_from_preset(
            PresetName.PRODUCTION,
            environment="production"
        )

        >>> # Configure individual scanners
        config.scanners[ScannerType.PROMPT_INJECTION] = ScannerConfig(
            enabled=True,
            threshold=0.5,
            action=ViolationAction.BLOCK
        )

        >>> # Check scanner status
        if config.is_scanner_enabled(ScannerType.TOXICITY_INPUT):
            process_toxicity_scan()

        >>> # Apply environment overrides
        overridden_config = config.merge_with_environment_overrides({
            "SECURITY_DEBUG": "true",
            "SECURITY_MAX_CONCURRENT_SCANS": "20"
        })

        >>> # Export for backup or analysis
        config_dict = config.to_dict()
        save_config(config_dict, "security_config_backup.json")
    """

    scanners: Dict[ScannerType, ScannerConfig] = Field(default_factory=dict)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    service_name: str = Field(default="security-scanner")
    version: str = Field(default="1.0.0")
    preset: PresetName | None = None
    environment: str = Field(default="development", pattern="^(development|staging|production|testing)$")
    debug_mode: bool = False
    custom_settings: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True

    def get_scanner_config(self, scanner_type: ScannerType) -> ScannerConfig | None:
        """
        Retrieve configuration for a specific scanner type.

        Args:
            scanner_type: The scanner type to retrieve configuration for

        Returns:
            ScannerConfig if the scanner is configured, None if not found

        Behavior:
            - Returns None for scanner types that haven't been configured
            - Provides access to all scanner settings including thresholds and actions
            - Used by security scanning engines to determine scanner behavior
            - Thread-safe read operation on configuration dictionary

        Examples:
            >>> config = SecurityConfig()
            >>> config.scanners[ScannerType.PROMPT_INJECTION] = ScannerConfig(enabled=True)
            >>>
            >>> scanner_config = config.get_scanner_config(ScannerType.PROMPT_INJECTION)
            >>> assert scanner_config is not None
            >>> assert scanner_config.enabled == True
            >>>
            >>> # Non-existent scanner returns None
            >>> missing_config = config.get_scanner_config(ScannerType.TOXICITY_INPUT)
            >>> assert missing_config is None
        """
        return self.scanners.get(scanner_type)

    def is_scanner_enabled(self, scanner_type: ScannerType) -> bool:
        """
        Check if a specific scanner type is currently enabled and active.

        Args:
            scanner_type: The scanner type to check status for

        Returns:
            True if the scanner is configured and enabled, False otherwise

        Behavior:
            - Returns False for scanner types that haven't been configured
            - Returns False for configured scanners that are explicitly disabled
            - Returns True only for configured and enabled scanners
            - Used by security orchestration to skip disabled scanners

        Examples:
            >>> config = SecurityConfig()
            >>> # Initially no scanners configured
            >>> assert not config.is_scanner_enabled(ScannerType.PROMPT_INJECTION)
            >>>
            >>> # Configure but disable scanner
            >>> config.scanners[ScannerType.PROMPT_INJECTION] = ScannerConfig(enabled=False)
            >>> assert not config.is_scanner_enabled(ScannerType.PROMPT_INJECTION)
            >>>
            >>> # Configure and enable scanner
            >>> config.scanners[ScannerType.PROMPT_INJECTION] = ScannerConfig(enabled=True)
            >>> assert config.is_scanner_enabled(ScannerType.PROMPT_INJECTION)
        """
        config = self.get_scanner_config(scanner_type)
        return config.enabled if config else False

    def get_enabled_scanners(self) -> List[ScannerType]:
        """
        Get list of all scanner types that are currently enabled and active.

        Returns:
            List of ScannerType enums for scanners that are configured and enabled
            Returns empty list if no scanners are configured or enabled

        Behavior:
            - Filters configured scanners to only include enabled ones
            - Returns scanner types in insertion order (dict preserves order)
            - Used by security orchestration to determine which scanners to run
            - Excludes scanners that are configured but disabled
            - Excludes scanner types that have no configuration

        Examples:
            >>> config = SecurityConfig()
            >>> config.scanners[ScannerType.PROMPT_INJECTION] = ScannerConfig(enabled=True)
            >>> config.scanners[ScannerType.TOXICITY_INPUT] = ScannerConfig(enabled=False)
            >>> config.scanners[ScannerType.PII_DETECTION] = ScannerConfig(enabled=True)
            >>>
            >>> enabled = config.get_enabled_scanners()
            >>> assert ScannerType.PROMPT_INJECTION in enabled
            >>> assert ScannerType.PII_DETECTION in enabled
            >>> assert ScannerType.TOXICITY_INPUT not in enabled  # Disabled
            >>> assert ScannerType.BIAS_DETECTION not in enabled  # Not configured
        """
        return [scanner_type for scanner_type, config in self.scanners.items() if config.enabled]

    @validator("scanners")
    def validate_scanners(cls, v: Dict[ScannerType, ScannerConfig]) -> Dict[ScannerType, ScannerConfig]:
        """
        Validate the integrity and consistency of scanner configurations.

        Args:
            v: Dictionary mapping scanner types to their configurations

        Returns:
            Validated scanner configurations dictionary

        Raises:
            ValueError: If duplicate scanner types or invalid configurations are found

        Behavior:
            - Ensures no duplicate scanner types in the configuration
            - Validates that all scanner configurations are proper ScannerConfig instances
            - Prevents configuration errors that could cause runtime failures
            - Maintains referential integrity between scanner types and their configurations
        """
        # Ensure no duplicate scanner types
        if len(v) != len(set(v.keys())):
            raise ValueError("Duplicate scanner types found")

        # Validate each scanner configuration
        for scanner_type, config in v.items():
            if not isinstance(config, ScannerConfig):
                raise ValueError(f"Invalid configuration for scanner {scanner_type}")

        return v

    @classmethod
    def create_from_preset(cls, preset: PresetName, environment: str = "development") -> "SecurityConfig":
        """
        Create a SecurityConfig instance from a predefined configuration preset.

        Factory method that provides ready-to-use configurations optimized for different
        deployment scenarios. Each preset balances security coverage, performance,
        and operational needs according to typical use case requirements.

        Args:
            preset: The preset configuration to use (STRICT, BALANCED, LENIENT, DEVELOPMENT, PRODUCTION)
            environment: Deployment environment context for configuration tuning (default: "development")

        Returns:
            SecurityConfig instance with scanners, performance settings, and logging configured
            according to the specified preset and environment

        Behavior:
            - STRICT: Maximum security coverage with low thresholds, conservative performance settings
            - BALANCED: Moderate security with balanced performance, suitable for general production
            - LENIENT: Minimal security with high thresholds, optimized for low false positives
            - DEVELOPMENT: Debug-friendly settings with verbose logging and relaxed security
            - PRODUCTION: Production-optimized settings with performance tuning and comprehensive security
            - Environment parameter fine-tunes settings for specific deployment contexts

        Examples:
            >>> # Create strict security configuration for high-risk environment
            strict_config = SecurityConfig.create_from_preset(
                PresetName.STRICT,
                environment="production"
            )
            >>> assert strict_config.get_enabled_scanners()  # Multiple scanners enabled

            >>> # Create development configuration for local testing
            dev_config = SecurityConfig.create_from_preset(PresetName.DEVELOPMENT)
            >>> assert dev_config.debug_mode
            >>> assert dev_config.logging.include_scanned_text

            >>> # Create balanced configuration for standard production
            prod_config = SecurityConfig.create_from_preset(
                PresetName.PRODUCTION,
                environment="production"
            )
            >>> assert not prod_config.debug_mode
            >>> assert prod_config.performance.enable_model_caching
        """
        config = cls(preset=preset, environment=environment)

        if preset == PresetName.STRICT:
            config.scanners = {
                ScannerType.PROMPT_INJECTION: ScannerConfig(
                    enabled=True, threshold=0.6, action=ViolationAction.BLOCK
                ),
                ScannerType.TOXICITY_INPUT: ScannerConfig(
                    enabled=True, threshold=0.5, action=ViolationAction.BLOCK
                ),
                ScannerType.PII_DETECTION: ScannerConfig(
                    enabled=True, threshold=0.7, action=ViolationAction.REDACT
                ),
                ScannerType.TOXICITY_OUTPUT: ScannerConfig(
                    enabled=True, threshold=0.5, action=ViolationAction.BLOCK
                ),
                ScannerType.BIAS_DETECTION: ScannerConfig(
                    enabled=True, threshold=0.6, action=ViolationAction.WARN
                ),
                ScannerType.HARMFUL_CONTENT: ScannerConfig(
                    enabled=True, threshold=0.5, action=ViolationAction.BLOCK
                ),
            }
            config.performance.max_concurrent_scans = 5
            config.performance.cache_ttl_seconds = 600

        elif preset == PresetName.BALANCED:
            config.scanners = {
                ScannerType.PROMPT_INJECTION: ScannerConfig(
                    enabled=True, threshold=0.7, action=ViolationAction.BLOCK
                ),
                ScannerType.TOXICITY_INPUT: ScannerConfig(
                    enabled=True, threshold=0.8, action=ViolationAction.WARN
                ),
                ScannerType.PII_DETECTION: ScannerConfig(
                    enabled=True, threshold=0.8, action=ViolationAction.REDACT
                ),
                ScannerType.TOXICITY_OUTPUT: ScannerConfig(
                    enabled=True, threshold=0.8, action=ViolationAction.WARN
                ),
                ScannerType.BIAS_DETECTION: ScannerConfig(
                    enabled=True, threshold=0.7, action=ViolationAction.FLAG
                ),
            }
            config.performance.max_concurrent_scans = 10

        elif preset == PresetName.LENIENT:
            config.scanners = {
                ScannerType.PROMPT_INJECTION: ScannerConfig(
                    enabled=True, threshold=0.8, action=ViolationAction.WARN
                ),
                ScannerType.TOXICITY_INPUT: ScannerConfig(
                    enabled=True, threshold=0.9, action=ViolationAction.WARN
                ),
                ScannerType.PII_DETECTION: ScannerConfig(
                    enabled=True, threshold=0.9, action=ViolationAction.FLAG
                ),
            }
            config.performance.max_concurrent_scans = 20

        elif preset == PresetName.DEVELOPMENT:
            config.scanners = {
                ScannerType.PROMPT_INJECTION: ScannerConfig(
                    enabled=True, threshold=0.8, action=ViolationAction.WARN
                ),
                ScannerType.TOXICITY_INPUT: ScannerConfig(
                    enabled=True, threshold=0.9, action=ViolationAction.WARN
                ),
            }
            config.debug_mode = True
            config.logging.include_scanned_text = True
            config.performance.enable_result_caching = False

        elif preset == PresetName.PRODUCTION:
            config.scanners = {
                ScannerType.PROMPT_INJECTION: ScannerConfig(
                    enabled=True, threshold=0.6, action=ViolationAction.BLOCK
                ),
                ScannerType.TOXICITY_INPUT: ScannerConfig(
                    enabled=True, threshold=0.7, action=ViolationAction.BLOCK
                ),
                ScannerType.PII_DETECTION: ScannerConfig(
                    enabled=True, threshold=0.7, action=ViolationAction.REDACT
                ),
                ScannerType.TOXICITY_OUTPUT: ScannerConfig(
                    enabled=True, threshold=0.7, action=ViolationAction.BLOCK
                ),
                ScannerType.BIAS_DETECTION: ScannerConfig(
                    enabled=True, threshold=0.6, action=ViolationAction.FLAG
                ),
            }
            config.performance.enable_model_caching = True
            config.performance.enable_result_caching = True
            config.logging.include_scanned_text = False

        return config

    def merge_with_environment_overrides(self, overrides: Dict[str, Any]) -> "SecurityConfig":
        """
        Merge current configuration with environment variable-based overrides.

        Creates a new SecurityConfig instance that combines the base configuration
        with values from environment variables. This enables runtime configuration
        adjustments without modifying the original configuration files.

        Args:
            overrides: Dictionary of environment variable overrides where keys are
                      variable names (with SECURITY_ prefix) and values are string values

        Returns:
            New SecurityConfig instance with environment overrides applied

        Behavior:
            - Creates a new instance without modifying the original configuration
            - Processes only variables starting with "SECURITY_" prefix
            - Supports boolean conversion for debug and enable_caching settings
            - Converts string values to appropriate types (int, enum, bool)
            - Applies overrides to nested configuration sections (performance, logging)
            - Handles special cases for preset configuration via environment variables

        Examples:
            >>> base_config = SecurityConfig.create_from_preset(PresetName.BALANCED)
            >>>
            >>> # Apply environment overrides
            >>> env_overrides = {
            ...     "SECURITY_DEBUG": "true",
            ...     "SECURITY_MAX_CONCURRENT_SCANS": "20",
            ...     "SECURITY_ENABLE_CACHING": "false",
            ...     "SECURITY_LOG_LEVEL": "DEBUG"
            ... }
            >>> updated_config = base_config.merge_with_environment_overrides(env_overrides)
            >>>
            >>> assert updated_config.debug_mode
            >>> assert updated_config.performance.max_concurrent_scans == 20
            >>> assert not updated_config.performance.enable_result_caching
            >>> assert updated_config.logging.log_level == "DEBUG"
        """
        # Create a copy to avoid modifying the original
        config_data = self.dict()

        # Apply environment variable overrides
        for key, value in overrides.items():
            if key.startswith("SECURITY_"):
                config_key = key[8:].lower()  # Remove "SECURITY_" prefix

                if config_key == "mode":
                    # Handle special case for security mode
                    continue
                if config_key == "preset":
                    if isinstance(value, str):
                        config_data["preset"] = PresetName(value.lower())
                elif config_key == "debug":
                    config_data["debug_mode"] = str(value).lower() in ("true", "1", "yes")
                elif config_key == "max_concurrent_scans":
                    config_data["performance"]["max_concurrent_scans"] = int(value)
                elif config_key == "enable_caching":
                    config_data["performance"]["enable_result_caching"] = str(value).lower() in ("true", "1", "yes")
                elif config_key == "log_level":
                    config_data["logging"]["log_level"] = value.upper()

        return SecurityConfig(**config_data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Export configuration to dictionary representation for serialization and storage.

        Converts the SecurityConfig instance to a dictionary format suitable for
        JSON serialization, database storage, or API responses. Includes computed
        fields like enabled_scanners for convenience.

        Returns:
            Dictionary containing all configuration values with enum values converted
            to strings. Includes computed fields and maintains nested structure
            for scanners, performance, and logging configurations.

        Behavior:
            - Converts enum values to string representations for JSON compatibility
            - Includes computed enabled_scanners list for quick reference
            - Preserves nested structure for configuration sections
            - Handles None values gracefully for optional fields
            - Includes metadata fields like service_name and version
            - Returns serializable dictionary suitable for JSON.dump()

        Examples:
            >>> config = SecurityConfig.create_from_preset(PresetName.PRODUCTION)
            >>> config_dict = config.to_dict()
            >>>
            >>> # Dictionary is JSON-serializable
            >>> import json
            >>> json_str = json.dumps(config_dict)
            >>> assert len(json_str) > 0
            >>>
            >>> # Contains expected structure
            >>> assert "service_name" in config_dict
            >>> assert "scanners" in config_dict
            >>> assert "performance" in config_dict
            >>> assert "enabled_scanners" in config_dict  # Computed field
            >>>
            >>> # Can be saved and restored
            >>> from pathlib import Path
            >>> Path("config_backup.json").write_text(json_str)
        """
        return {
            "service_name": self.service_name,
            "version": self.version,
            "preset": self.preset.value if self.preset and hasattr(self.preset, "value") else self.preset,
            "environment": self.environment,
            "debug_mode": self.debug_mode,
            "scanners": {k.value: v.dict() for k, v in self.scanners.items()},
            "performance": self.performance.dict(),
            "logging": self.logging.dict(),
            "custom_settings": self.custom_settings,
            "enabled_scanners": [scanner.value for scanner in self.get_enabled_scanners()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityConfig":
        """
        Create SecurityConfig instance from dictionary representation.

        Factory method that reconstructs a SecurityConfig instance from a dictionary
        created by to_dict() or loaded from external storage. Supports multiple
        configuration formats for backward compatibility and handles nested structures.

        Args:
            data: Dictionary containing configuration data. Supports multiple formats:
                  - Nested structure with input_scanners/output_scanners sections
                  - Legacy flat structure with scanners dictionary
                  - Partial configurations with sensible defaults for missing values

        Returns:
            SecurityConfig instance reconstructed from the dictionary data

        Behavior:
            - Handles both nested (input_scanners/output_scanners) and legacy flat formats
            - Maps string names to ScannerType enums for backward compatibility
            - Converts string action names to ViolationAction enums
            - Skips unknown scanner types rather than failing
            - Uses default configurations for missing or invalid sections
            - Maintains backward compatibility with older configuration formats
            - Gracefully handles missing or invalid configuration data

        Examples:
            >>> # Load configuration from JSON file
            >>> import json
            >>> from pathlib import Path
            >>> config_data = json.loads(Path("config.json").read_text())
            >>> config = SecurityConfig.from_dict(config_data)
            >>> assert isinstance(config, SecurityConfig)

            >>> # Handle legacy format
            >>> legacy_data = {
            ...     "scanners": {
            ...         "prompt_injection": {
            ...             "enabled": True,
            ...             "threshold": 0.7,
            ...             "action": "block"
            ...         }
            ...     },
            ...     "service": {
            ...         "name": "legacy-scanner",
            ...         "environment": "production"
            ...     }
            ... }
            >>> config = SecurityConfig.from_dict(legacy_data)
            >>> assert config.service_name == "legacy-scanner"
            >>> assert ScannerType.PROMPT_INJECTION in config.scanners

            >>> # Handle nested format
            >>> nested_data = {
            ...     "input_scanners": {
            ...         "prompt_injection": {
            ...             "enabled": True,
            ...             "threshold": 0.5,
            ...             "action": "block"
            ...         }
            ...     },
            ...     "service": {
            ...         "environment": "production"
            ...     }
            ... }
            >>> config = SecurityConfig.from_dict(nested_data)
            >>> assert config.environment == "production"
        """
        # Handle scanners dictionary - support both flat and nested structures
        scanners = {}

        # Handle input scanners
        input_scanners = data.get("input_scanners", {})
        for scanner_name, scanner_config in input_scanners.items():
            try:
                # Map YAML names to enum values
                if scanner_name == "prompt_injection":
                    scanner_type = ScannerType.PROMPT_INJECTION
                elif scanner_name == "toxicity_input":
                    scanner_type = ScannerType.TOXICITY_INPUT
                elif scanner_name == "pii_detection":
                    scanner_type = ScannerType.PII_DETECTION
                elif scanner_name == "malicious_url":
                    scanner_type = ScannerType.MALICIOUS_URL
                else:
                    # Skip unknown scanner types
                    continue

                # Convert action string to enum if needed
                if "action" in scanner_config and isinstance(scanner_config["action"], str):
                    try:
                        scanner_config["action"] = ViolationAction(scanner_config["action"])
                    except ValueError:
                        # Default to BLOCK if action is invalid
                        scanner_config["action"] = ViolationAction.BLOCK

                scanners[scanner_type] = ScannerConfig(**scanner_config)
            except ValueError:
                # Skip invalid scanner configurations
                continue

        # Handle output scanners
        output_scanners = data.get("output_scanners", {})
        for scanner_name, scanner_config in output_scanners.items():
            try:
                # Map YAML names to enum values
                if scanner_name == "toxicity_output":
                    scanner_type = ScannerType.TOXICITY_OUTPUT
                elif scanner_name == "bias_detection":
                    scanner_type = ScannerType.BIAS_DETECTION
                elif scanner_name == "harmful_content":
                    scanner_type = ScannerType.HARMFUL_CONTENT
                else:
                    # Skip unknown scanner types
                    continue

                # Convert action string to enum if needed
                if "action" in scanner_config and isinstance(scanner_config["action"], str):
                    try:
                        scanner_config["action"] = ViolationAction(scanner_config["action"])
                    except ValueError:
                        # Default to BLOCK if action is invalid
                        scanner_config["action"] = ViolationAction.BLOCK

                scanners[scanner_type] = ScannerConfig(**scanner_config)
            except ValueError:
                # Skip invalid scanner configurations
                continue

        # Handle legacy flat scanners structure for backward compatibility
        legacy_scanners_data = data.get("scanners", {})
        for scanner_name, scanner_config in legacy_scanners_data.items():
            try:
                scanner_type = ScannerType(scanner_name)
                scanners[scanner_type] = ScannerConfig(**scanner_config)
            except ValueError:
                # Skip unknown scanner types
                continue

        # Handle other configuration sections
        performance_data = data.get("performance", {})
        logging_data = data.get("logging", {})

        # Extract service configuration
        service_data = data.get("service", {})
        service_name = service_data.get("name", "security-scanner")
        version = service_data.get("version", "1.0.0")
        environment = service_data.get("environment", "development")
        debug_mode = service_data.get("debug_mode", False)

        return cls(
            service_name=service_name,
            version=version,
            preset=PresetName(data.get("preset")) if data.get("preset") else None,
            environment=environment,
            debug_mode=debug_mode,
            scanners=scanners,
            performance=PerformanceConfig(**performance_data),
            logging=LoggingConfig(**logging_data),
            custom_settings=data.get("custom_settings", {}),
        )
