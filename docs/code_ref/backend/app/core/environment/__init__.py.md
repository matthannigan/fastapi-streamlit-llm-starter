---
sidebar_label: __init__
---

# Unified Environment Detection Service

  file_path: `backend/app/core/environment/__init__.py`

This module provides centralized environment detection capabilities for all backend
infrastructure services, eliminating code duplication and providing consistent
environment classification across cache, resilience, security, and other systems.

## Architecture Position

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Services                     │
├─────────────────────────────────────────────────────────────┤
│  Security Auth  │  Cache Presets  │  Resilience Config      │
│     (NEW)       │   (EXISTING)    │    (EXISTING)           │
├─────────────────────────────────────────────────────────────┤
│           Unified Environment Detection Service             │
│                        (NEW)                                │
├─────────────────────────────────────────────────────────────┤
│              Environment Variables & System                 │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

- **Centralized Detection**: Single source of truth for environment classification
- **Confidence Scoring**: Provides confidence levels and reasoning for decisions  
- **Extensible Patterns**: Configurable patterns for custom deployment scenarios
- **Context-Aware**: Supports feature-specific context (AI, security, cache)
- **Fallback Strategies**: Robust fallback detection for edge cases
- **Integration Ready**: Drop-in replacement for existing detection logic

## Usage Examples

```python
# Basic environment detection
detector = EnvironmentDetector()
env_info = detector.detect_environment()
print(f"Environment: {env_info.environment} (confidence: {env_info.confidence})")

# Feature-specific detection
ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)
security_env = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)

# Integration with existing systems
cache_preset = cache_manager.recommend_preset(env_info.environment)
resilience_preset = resilience_manager.recommend_preset(env_info.environment)
auth_config = security_auth.configure_for_environment(env_info)
```

Re-exports for backward compatibility while organizing into submodules.
