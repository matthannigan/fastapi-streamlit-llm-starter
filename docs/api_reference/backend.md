# Backend API Reference

## Main Application

::: app.main
    options:
        members:
            - root
            - health_check
            - auth_status
            - cache_status
            - invalidate_cache
            - get_invalidation_stats
            - get_invalidation_recommendations
            - process_text
            - get_operations
            - batch_process_text
            - get_batch_status

## Authentication

::: app.auth
    options:
        show_root_heading: true
        show_source: false

## Configuration

::: app.config
    options:
        show_root_heading: true
        show_source: false

## Services

### Text Processor Service

::: app.services.text_processor
    options:
        show_root_heading: true
        show_source: false

### Cache Service

::: app.services.cache
    options:
        show_root_heading: true
        show_source: false

### Monitoring Service

::: app.services.monitoring
    options:
        show_root_heading: true
        show_source: false

## Utilities

::: app.utils.prompt_utils
    options:
        show_root_heading: true
        show_source: false

::: app.utils.sanitization
    options:
        show_root_heading: true
        show_source: false

## Security

::: app.security.response_validator
    options:
        show_root_heading: true
        show_source: false