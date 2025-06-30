# Backend API Reference

## Main Application

::: app.main
    options:
        members:
            - root
            - health_check
            - auth_status
            - global_exception_handler
            - lifespan

## Configuration

::: app.config
    options:
        show_root_heading: true
        show_source: false

## Dependencies

::: app.dependencies
    options:
        show_root_heading: true
        show_source: false

## API Endpoints

### V1 API

::: app.api.v1.text_processing
    options:
        show_root_heading: true
        show_source: false

::: app.api.v1.deps  
    options:
        show_root_heading: true
        show_source: false

### Internal API

::: app.api.internal.cache
    options:
        show_root_heading: true
        show_source: false

::: app.api.internal.monitoring
    options:
        show_root_heading: true
        show_source: false

#### Resilience API

::: app.api.internal.resilience.circuit_breakers
    options:
        show_root_heading: true
        show_source: false

::: app.api.internal.resilience.health
    options:
        show_root_heading: true
        show_source: false

::: app.api.internal.resilience.monitoring
    options:
        show_root_heading: true
        show_source: false

::: app.api.internal.resilience.performance
    options:
        show_root_heading: true
        show_source: false

::: app.api.internal.resilience.config_presets
    options:
        show_root_heading: true
        show_source: false

::: app.api.internal.resilience.config_templates
    options:
        show_root_heading: true
        show_source: false

::: app.api.internal.resilience.config_validation
    options:
        show_root_heading: true
        show_source: false

## Services

### Text Processor Service

::: app.services.text_processor
    options:
        show_root_heading: true
        show_source: false

### Response Validator Service

::: app.services.response_validator
    options:
        show_root_heading: true
        show_source: false

## Infrastructure

### AI Infrastructure

::: app.infrastructure.ai.input_sanitizer
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.ai.prompt_builder
    options:
        show_root_heading: true
        show_source: false

### Cache Infrastructure

::: app.infrastructure.cache.base
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.cache.memory
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.cache.redis
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.cache.monitoring
    options:
        show_root_heading: true
        show_source: false

### Security Infrastructure

::: app.infrastructure.security.auth
    options:
        show_root_heading: true
        show_source: false

### Resilience Infrastructure

::: app.infrastructure.resilience.circuit_breaker
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.resilience.retry
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.resilience.orchestrator
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.resilience.config_monitoring
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.resilience.config_validator
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.resilience.performance_benchmarks
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.resilience.presets
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.resilience.migration_utils
    options:
        show_root_heading: true
        show_source: false

### Monitoring Infrastructure

::: app.infrastructure.monitoring.health
    options:
        show_root_heading: true
        show_source: false

::: app.infrastructure.monitoring.metrics
    options:
        show_root_heading: true
        show_source: false

## Schemas

::: app.schemas
    options:
        show_root_heading: true
        show_source: false