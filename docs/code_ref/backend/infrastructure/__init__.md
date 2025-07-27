# Infrastructure Services Package

This package contains business-agnostic, reusable technical capabilities that form
the foundation of the FastAPI backend application. These services are designed to be
stable, well-tested, and configuration-driven.

## Architecture

Infrastructure services follow the principle of **dependency inversion**, where:
- Domain services depend on infrastructure services
- Infrastructure services depend only on external libraries
- All dependencies flow inward toward business logic

## Modules

- `ai/`: AI model interaction utilities
- Input sanitization and prompt injection protection
- Safe prompt building with template system
- `cache/`: Caching infrastructure with Redis backend
- Memory and Redis-based caching with graceful degradation
- Cache monitoring and health checks
- `monitoring/`: Application observability
- Health checks and system metrics collection
- `resilience/`: Fault tolerance patterns
- Circuit breakers, retry logic, and configuration management
- `security/`: Authentication and authorization
- API key-based authentication with multi-key support

## Design Principles

- **Stability**: Infrastructure APIs should remain stable across application changes
- **Reusability**: Components should be usable across different business domains
- **Configuration-driven**: Behavior controlled through environment variables and presets
- **High test coverage**: Infrastructure services target >90% test coverage
- **Graceful degradation**: Services should continue operating when dependencies fail

## Usage

Infrastructure services are typically injected as dependencies:

```python
from app.infrastructure.cache import get_cache_service
from app.infrastructure.resilience import get_resilience_service

# Services are configured via dependency injection
cache = get_cache_service()
resilience = get_resilience_service()
```
