"""
Unified Environment Detection Service

This module provides centralized environment detection capabilities for all backend
infrastructure services, eliminating code duplication and providing consistent
environment classification across cache, resilience, security, and monitoring systems.

## Architecture Position

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Services                     │
├─────────────────────────────────────────────────────────────┤
│  Security Auth  │  Cache Presets  │  Resilience Config      │
│   (INFRA)       │   (INFRA)       │    (INFRA)              │
├─────────────────────────────────────────────────────────────┤
│           Unified Environment Detection Service             │
│                   (INFRASTRUCTURE SERVICE)                  │
├─────────────────────────────────────────────────────────────┤
│              Environment Variables & System                 │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Environment Classifications
- **DEVELOPMENT**: Local development and testing environments
- **TESTING**: Automated testing and CI environments
- **STAGING**: Pre-production integration testing environments
- **PRODUCTION**: Live production environments serving real users
- **UNKNOWN**: Fallback when environment cannot be determined

### Feature Contexts
- **AI_ENABLED**: AI-powered features requiring model access and cache optimization
- **SECURITY_ENFORCEMENT**: Security-critical features with stricter requirements
- **CACHE_OPTIMIZATION**: Cache-intensive operations with performance tuning
- **RESILIENCE_STRATEGY**: Resilience pattern selection and configuration
- **DEFAULT**: Standard environment detection without feature context

### Detection Results
- **EnvironmentInfo**: Comprehensive detection with confidence scoring and reasoning
- **EnvironmentSignal**: Individual detection evidence with confidence levels
- **DetectionConfig**: Customizable patterns and detection behavior

## Key Features

- **Centralized Detection**: Single source of truth for environment classification
- **Confidence Scoring**: Provides confidence levels (0.0-1.0) and reasoning for decisions
- **Extensible Patterns**: Configurable regex patterns for custom deployment scenarios
- **Context-Aware**: Supports feature-specific context with specialized detection logic
- **Signal Collection**: Multi-source detection from environment variables, patterns, and system indicators
- **Fallback Strategies**: Robust fallback detection with development environment default
- **Thread-Safe**: Concurrent access support for infrastructure services
- **Performance Optimized**: Signal caching and efficient detection algorithms

## Usage Examples

### Basic Environment Detection
```python
from app.core.environment import get_environment_info, is_production_environment

# Quick environment check
if is_production_environment():
    configure_production_logging()
    enable_performance_monitoring()

# Detailed environment information
env_info = get_environment_info()
print(f"Environment: {env_info.environment} (confidence: {env_info.confidence})")
print(f"Reasoning: {env_info.reasoning}")
```

### Feature-Aware Detection
```python
from app.core.environment import get_environment_info, FeatureContext

# AI context for cache optimization
ai_env = get_environment_info(FeatureContext.AI_ENABLED)
if ai_env.metadata.get('ai_prefix'):
    cache_prefix = ai_env.metadata['ai_prefix']
    cache_key = f"{cache_prefix}summarize:{text_hash}"

# Security context may override to production
security_env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
if security_env.environment == Environment.PRODUCTION:
    enforce_authentication_requirements()
    enable_audit_logging()

# Cache optimization context
cache_env = get_environment_info(FeatureContext.CACHE_OPTIMIZATION)
if cache_env.environment == Environment.DEVELOPMENT:
    use_memory_cache_only()
    set_short_cache_ttls()
```

### Infrastructure Service Integration
```python
from app.core.environment import EnvironmentDetector, get_environment_info

# Custom detector for specialized deployment
detector = EnvironmentDetector()
env_info = detector.detect_environment()

# Integration with existing infrastructure services
cache_preset = cache_manager.recommend_preset(env_info.environment)
resilience_preset = resilience_manager.recommend_preset(env_info.environment)
auth_config = security_auth.configure_for_environment(env_info)

# Debugging and troubleshooting
summary = detector.get_environment_summary()
for signal in summary['all_signals']:
    print(f"  - {signal['source']}: {signal['reasoning']}")
```

## Public API

### Convenience Functions
- `get_environment_info(feature_context)`: Get environment detection results
- `is_production_environment(feature_context)`: Production check with confidence threshold
- `is_development_environment(feature_context)`: Development check with confidence threshold

### EnvironmentDetector Class
- `detect_environment(feature_context)`: Primary detection method
- `detect_with_context(feature_context)`: Feature-specific detection
- `get_environment_summary()`: Comprehensive detection summary for debugging

## Thread Safety and Performance

- **Thread-Safe**: Safe for concurrent access across infrastructure services
- **Signal Caching**: Optimized performance with cached detection signals
- **Immutable Configuration**: Thread-safe configuration after initialization
- **Graceful Degradation**: Continues operation when individual detection sources fail

## Integration Guidelines

### Infrastructure Services
```python
# In cache infrastructure
env_info = get_environment_info(FeatureContext.CACHE_OPTIMIZATION)
return get_cache_config(env_info.environment)

# In resilience infrastructure
env_info = get_environment_info(FeatureContext.RESILIENCE_STRATEGY)
return get_resilience_preset(env_info.environment)

# In security infrastructure
env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
return configure_auth_mode(env_info)
```

### Configuration Management
```python
# Use environment variables for highest confidence
export ENVIRONMENT=production
export NODE_ENV=production

# Feature-specific configuration
export ENABLE_AI_CACHE=true      # AI context metadata
export ENFORCE_AUTH=true         # Security context override
```

This service serves as the foundation for environment-aware infrastructure configuration,
providing consistent, reliable environment detection across all backend services.
"""

# Re-export all public APIs
from .enums import Environment, FeatureContext
from .models import EnvironmentSignal, EnvironmentInfo, DetectionConfig
from .detector import EnvironmentDetector
from .api import (
    environment_detector,
    get_environment_info,
    is_production_environment,
    is_development_environment
)

__all__ = [
    "DetectionConfig",
    "Environment",
    "EnvironmentDetector",
    "EnvironmentInfo",
    "EnvironmentSignal",
    "FeatureContext",
    "environment_detector",
    "get_environment_info",
    "is_development_environment",
    "is_production_environment",
]
