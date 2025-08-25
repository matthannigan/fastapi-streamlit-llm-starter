"""
Resilience Infrastructure Service Package

This package provides comprehensive fault tolerance and resilience patterns for AI services,
implementing industry-standard resilience patterns with intelligent configuration management,
performance monitoring, and seamless integration across the application infrastructure.

## Package Architecture

The resilience system follows a sophisticated layered architecture designed for maximum
flexibility and operational visibility:

- **Pattern Layer**: Core resilience patterns (circuit breakers, retry logic, failure classification)
- **Configuration Layer**: Intelligent preset management with dynamic configuration and validation
- **Orchestration Layer**: High-level decorators and service integration for seamless adoption
- **Monitoring Layer**: Comprehensive metrics, performance tracking, and alerting system
- **Migration Layer**: Legacy configuration analysis and automated migration utilities

## Core Components

### Circuit Breaker Pattern (`circuit_breaker.py`)
Advanced circuit breaker implementation with intelligent failure detection:
- **Failure Threshold Detection**: Configurable failure rate and count thresholds
- **Automatic Recovery**: Time-based recovery with exponential backoff
- **State Management**: Open/Closed/Half-Open states with proper state transitions
- **Performance Metrics**: Real-time monitoring of operation success/failure rates
- **Custom Strategies**: Configurable strategies for different operation types

### Retry Logic (`retry.py`)
Intelligent retry mechanisms with failure classification:
- **Exponential Backoff**: Configurable backoff with jitter to prevent thundering herd
- **Exception Classification**: Smart categorization of transient vs permanent failures
- **Retry Strategies**: Different strategies (conservative, balanced, aggressive) per operation
- **Timeout Management**: Configurable timeouts with graceful degradation
- **Success Rate Tracking**: Monitoring of retry success patterns

### Configuration Management (`config_presets.py`)
Simplified configuration system with intelligent defaults:
- **Preset System**: Pre-configured strategies (simple, development, production)
- **Environment Detection**: Automatic environment-specific configuration
- **Dynamic Updates**: Runtime configuration changes with validation
- **Legacy Migration**: Automated migration from complex legacy configurations
- **Validation**: Comprehensive configuration validation with detailed error reporting

### Orchestration (`orchestrator.py`)
High-level integration layer for seamless resilience adoption:
- **Operation Decorators**: Easy-to-use decorators for different resilience strategies
- **Service Integration**: Unified resilience interface for AI service operations
- **Context Management**: Automatic context preservation across retry attempts
- **Metrics Integration**: Automatic performance tracking and monitoring
- **Error Handling**: Comprehensive error handling with proper exception propagation

### Performance Monitoring (`performance_benchmarks.py`)
Advanced performance monitoring and benchmarking system:
- **Operation Timing**: Detailed timing analysis with percentile calculations
- **Success Rate Analysis**: Success/failure rate tracking with trend analysis
- **Performance Regression Detection**: Automatic detection of performance degradations
- **Benchmark Suites**: Comprehensive benchmark testing for configuration validation
- **Threshold Alerting**: Configurable performance thresholds with alerting

### Configuration Validation (`config_validator.py`)
Robust validation system with security and performance considerations:
- **Schema Validation**: Comprehensive JSON schema validation with detailed error reporting
- **Security Features**: Rate limiting and abuse protection for validation endpoints
- **Performance Optimization**: Efficient validation with caching and optimization
- **Template System**: Pre-defined configuration templates for common use cases
- **Migration Support**: Validation of migrated configurations with compatibility checking

## Design Principles & Standards

### Reliability & Fault Tolerance
- **Fail Fast**: Quick detection and handling of permanent failures
- **Graceful Degradation**: Maintaining service availability during partial failures
- **Intelligent Recovery**: Automatic recovery with adaptive backoff strategies
- **Isolation**: Failure isolation to prevent cascade failures across services

### Performance & Efficiency
- **Minimal Overhead**: < 0.1ms overhead per resilience operation
- **Async-First Design**: Full async/await support for optimal concurrency
- **Resource Efficient**: Minimal memory and CPU overhead
- **High Throughput**: Supports thousands of operations per second

### Configuration & Operations
- **Preset-Driven**: Simplified configuration through intelligent presets
- **Environment-Aware**: Automatic adaptation to different environments
- **Monitoring Integration**: Built-in metrics collection and performance tracking
- **DevOps Ready**: Comprehensive operational visibility and control

### Security & Compliance
- **Secure Defaults**: Security-first configuration with safe defaults
- **Validation Security**: Rate limiting and abuse protection for configuration endpoints
- **Audit Trails**: Complete audit trails for configuration changes and failures
- **Compliance Ready**: Supports compliance requirements with comprehensive logging

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

from app.core.exceptions import AIServiceException, TransientAIError, PermanentAIError, RateLimitError, ServiceUnavailableError
from .circuit_breaker import CircuitBreakerConfig, ResilienceMetrics, EnhancedCircuitBreaker
from .retry import RetryConfig, classify_exception, should_retry_on_exception
from .config_presets import ResilienceStrategy, ResilienceConfig, get_default_presets, DEFAULT_PRESETS, preset_manager
from .orchestrator import AIServiceResilience, ai_resilience, with_operation_resilience, with_aggressive_resilience, with_balanced_resilience, with_conservative_resilience, with_critical_resilience
from .config_validator import ResilienceConfigValidator, ValidationResult, ValidationRateLimiter, RESILIENCE_CONFIG_SCHEMA, CONFIGURATION_TEMPLATES, SECURITY_CONFIG
from .config_monitoring import ConfigurationMetricsCollector, ConfigurationMetric, ConfigurationUsageStats, ConfigurationAlert, MetricType, AlertLevel
from .migration_utils import LegacyConfigAnalyzer, ConfigurationMigrator, MigrationRecommendation, MigrationConfidence
from .performance_benchmarks import ConfigurationPerformanceBenchmark, BenchmarkResult, BenchmarkSuite, PerformanceThreshold

__all__ = ['AIServiceException', 'TransientAIError', 'PermanentAIError', 'RateLimitError', 'ServiceUnavailableError', 'RetryConfig', 'CircuitBreakerConfig', 'ResilienceConfig', 'ResilienceStrategy', 'EnhancedCircuitBreaker', 'ResilienceMetrics', 'AIServiceResilience', 'classify_exception', 'should_retry_on_exception', 'get_default_presets', 'DEFAULT_PRESETS', 'preset_manager', 'ai_resilience', 'with_operation_resilience', 'with_aggressive_resilience', 'with_balanced_resilience', 'with_conservative_resilience', 'with_critical_resilience', 'ResilienceConfigValidator', 'ValidationResult', 'ValidationRateLimiter', 'RESILIENCE_CONFIG_SCHEMA', 'CONFIGURATION_TEMPLATES', 'SECURITY_CONFIG', 'ConfigurationMetricsCollector', 'ConfigurationMetric', 'ConfigurationUsageStats', 'ConfigurationAlert', 'MetricType', 'AlertLevel', 'LegacyConfigAnalyzer', 'ConfigurationMigrator', 'MigrationRecommendation', 'MigrationConfidence', 'ConfigurationPerformanceBenchmark', 'BenchmarkResult', 'BenchmarkSuite', 'PerformanceThreshold', 'preset_manager']
