"""
Resilience Infrastructure Service

This module provides comprehensive fault tolerance and resilience patterns for AI services,
including circuit breakers, retry logic, and intelligent failure handling. It implements
industry-standard resilience patterns with intelligent configuration management.

## Architecture

The resilience system follows a layered architecture:
- **Pattern Layer**: Circuit breakers, retry logic, and failure classification
- **Configuration Layer**: Preset management and intelligent configuration
- **Orchestration Layer**: High-level decorators and service integration
- **Monitoring Layer**: Metrics, validation, and performance tracking

## Key Components

### Core Patterns
- **Circuit Breaker**: Prevents cascade failures with automatic recovery
- **Retry Logic**: Intelligent retry with exponential backoff and jitter
- **Exception Classification**: Smart categorization of transient vs permanent failures

### Configuration Management
- **Preset System**: Pre-configured resilience strategies (simple, development, production)
- **Dynamic Configuration**: Runtime configuration updates with validation
- **Migration Tools**: Legacy configuration analysis and migration utilities

### Monitoring & Analytics
- **Performance Metrics**: Operation timing, success rates, and failure patterns
- **Configuration Monitoring**: Preset usage tracking and change auditing
- **Alerting System**: Threshold-based alerts for configuration issues

## Usage Patterns

### Quick Start with Presets
```python
from app.infrastructure.resilience import with_operation_resilience

@with_operation_resilience("summarize")
async def summarize_text(text: str) -> Dict[str, Any]:
    # Your AI service call here
    return await ai_service.summarize(text)
```

### Custom Configuration
```python
from app.infrastructure.resilience import (
    AIServiceResilience,
    ResilienceConfig,
    ResilienceStrategy
)

config = ResilienceConfig(
    strategy=ResilienceStrategy.BALANCED,
    retry_attempts=3,
    circuit_breaker_threshold=5,
    circuit_breaker_recovery_timeout=60
)

resilience = AIServiceResilience(config)
result = await resilience.execute_with_resilience(your_ai_function, text)
```

### Monitoring Integration
```python
from app.infrastructure.resilience import config_metrics_collector

# Metrics are automatically collected
stats = config_metrics_collector.get_usage_stats()
alerts = config_metrics_collector.get_active_alerts()
```

## Design Principles

- **Fail Fast**: Quick detection and handling of permanent failures
- **Graceful Degradation**: Maintaining service availability during partial failures
- **Intelligent Recovery**: Automatic recovery with backoff strategies
- **Configuration-Driven**: Behavior controlled through presets and environment variables
- **Observable**: Comprehensive metrics and monitoring for operational visibility
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
