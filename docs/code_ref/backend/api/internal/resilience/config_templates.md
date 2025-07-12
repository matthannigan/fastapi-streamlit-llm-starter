# Resilience configuration template management REST API endpoints.

This module provides REST API endpoints for managing and utilizing resilience
configuration templates. Templates serve as structured blueprints for creating
consistent resilience configurations across different use cases and deployment
scenarios, offering validation, suggestion, and customization capabilities.

The module implements template-based configuration management that allows users
to leverage predefined configuration patterns while providing flexibility for
customization through override mechanisms. All endpoints include comprehensive
validation and intelligent template suggestion features.

## Endpoints

GET  /resilience/config/templates: Retrieve all available configuration templates
GET  /resilience/config/templates/{template_name}: Get specific template configuration
POST /resilience/config/validate-template: Validate template-based configuration with overrides
POST /resilience/config/recommend-template: Suggest optimal template for given configuration

## Template Management Features

- Complete template catalog with descriptions and use cases
- Template-based configuration validation with override support
- Intelligent template suggestion based on configuration analysis
- Confidence scoring for template matching quality
- Flexible override mechanism for template customization
- Comprehensive validation with error reporting and suggestions

## Template Validation

- Schema validation against template specifications
- Override compatibility checking and conflict detection
- Error reporting with detailed validation messages
- Warning generation for potential configuration issues
- Suggestion provision for configuration improvements

## Template Suggestion Algorithm

- Configuration pattern analysis for template matching
- Field-by-field comparison with available templates
- Confidence calculation based on parameter alignment
- Reasoning explanations for suggestion decisions
- Fallback handling for configurations without close matches

## Dependencies

- ConfigValidator: Template validation and suggestion engine
- Security: API key verification for protected endpoints
- Pydantic Models: Structured request/response validation
- TemplateManager: Core template management functionality

## Authentication

All endpoints require API key authentication to protect template
configurations and ensure secure access to validation services.

## Example

To validate a configuration using a template:
POST /api/internal/resilience/validate-template
{
"template_name": "production",
"overrides": {"retry_attempts": 5}
}

To get template suggestions for a configuration:
POST /api/internal/resilience/suggest-template
{
"configuration": {"retry_attempts": 3, "circuit_breaker_threshold": 10}
}

## Note

Template-based configurations provide consistency and best practices
while allowing customization through overrides. The suggestion system
helps identify appropriate templates for existing configurations.
