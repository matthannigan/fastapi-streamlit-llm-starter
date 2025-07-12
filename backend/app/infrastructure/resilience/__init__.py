"""
Resilience Infrastructure Service

Re-exports all resilience components including circuit breaker, retry logic,
presets, orchestrator, configuration validation, monitoring, migration utilities,
and performance benchmarking for ease of use.

This module serves as the single point of entry for all resilience functionality.
"""

# Core exceptions (imported from centralized location)
from app.core.exceptions import (
    AIServiceException,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError,
)

# Core components
from .circuit_breaker import (
    CircuitBreakerConfig,
    ResilienceMetrics,
    EnhancedCircuitBreaker
)

from .retry import (
    RetryConfig,
    classify_exception,
    should_retry_on_exception
)

from .config_presets import (
    ResilienceStrategy,
    ResilienceConfig,
    get_default_presets,
    DEFAULT_PRESETS,
    preset_manager
)

from .orchestrator import (
    AIServiceResilience,
    ai_resilience,
    with_operation_resilience,
    with_aggressive_resilience,
    with_balanced_resilience,
    with_conservative_resilience,
    with_critical_resilience
)

# Configuration validation and security
from .config_validator import (
    ResilienceConfigValidator,
    ValidationResult,
    ValidationRateLimiter,
    RESILIENCE_CONFIG_SCHEMA,
    CONFIGURATION_TEMPLATES,
    SECURITY_CONFIG
)

# Configuration monitoring and metrics
from .config_monitoring import (
    ConfigurationMetricsCollector,
    ConfigurationMetric,
    ConfigurationUsageStats,
    ConfigurationAlert,
    MetricType,
    AlertLevel
)

# Migration utilities for legacy configurations
from .migration_utils import (
    LegacyConfigAnalyzer,
    ConfigurationMigrator,
    MigrationRecommendation,
    MigrationConfidence
)

# Performance benchmarking
from .performance_benchmarks import (
    ConfigurationPerformanceBenchmark,
    BenchmarkResult,
    BenchmarkSuite,
    PerformanceThreshold
)

__all__ = [
    # Core exceptions
    "AIServiceException",
    "TransientAIError", 
    "PermanentAIError",
    "RateLimitError",
    "ServiceUnavailableError",
    
    # Configuration classes
    "RetryConfig",
    "CircuitBreakerConfig", 
    "ResilienceConfig",
    "ResilienceStrategy",
    
    # Core components
    "EnhancedCircuitBreaker",
    "ResilienceMetrics",
    "AIServiceResilience",
    
    # Utility functions
    "classify_exception",
    "should_retry_on_exception",
    "get_default_presets",
    
    # Presets and defaults
    "DEFAULT_PRESETS",
    "preset_manager",
    
    # Global instance and decorators
    "ai_resilience",
    "with_operation_resilience",
    "with_aggressive_resilience",
    "with_balanced_resilience", 
    "with_conservative_resilience",
    "with_critical_resilience",
    
    # Configuration validation
    "ResilienceConfigValidator",
    "ValidationResult",
    "ValidationRateLimiter",
    "RESILIENCE_CONFIG_SCHEMA",
    "CONFIGURATION_TEMPLATES",
    "SECURITY_CONFIG",
    
    # Configuration monitoring
    "ConfigurationMetricsCollector",
    "ConfigurationMetric",
    "ConfigurationUsageStats",
    "ConfigurationAlert",
    "MetricType",
    "AlertLevel",
    
    # Migration utilities
    "LegacyConfigAnalyzer",
    "ConfigurationMigrator",
    "MigrationRecommendation",
    "MigrationConfidence",
    
    # Performance benchmarking
    "ConfigurationPerformanceBenchmark",
    "BenchmarkResult",
    "BenchmarkSuite",
    "PerformanceThreshold",
    
    # Backward compatibility
    "preset_manager",
    #"PRESETS"
]
