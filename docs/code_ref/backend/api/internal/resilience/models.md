# Pydantic models for resilience API request and response validation.

This module defines comprehensive Pydantic models for all resilience API
endpoints, providing structured data validation, serialization, and
documentation for requests and responses. The models ensure data integrity,
type safety, and consistent API documentation across all resilience
service endpoints.

The module implements a complete set of data models that cover configuration
validation, template management, performance benchmarking, monitoring, and
security validation, providing a unified approach to data structure
management across the resilience infrastructure.

## Model Categories

## Request Models

- TemplateBasedConfigRequest: Template-based configuration with overrides
- CustomConfigRequest: Custom configuration validation requests
- BenchmarkRunRequest: Performance benchmark execution parameters
- ValidationRequest: Generic configuration validation requests
- TemplateValidationRequest: Template validation with override support

## Response Models

- ResilienceMetricsResponse: Comprehensive resilience service metrics
- TemplateListResponse: Available configuration templates catalog
- TemplateSuggestionResponse: Template recommendation with confidence scoring
- ValidationResponse: Configuration validation results with detailed feedback
- CurrentConfigResponse: Current resilience configuration state and strategies

## Data Validation Features

- Type safety with Pydantic field validation
- Optional and required field specification
- Default value management and fallback handling
- Nested model support for complex data structures
- Field documentation with descriptions and examples
- Validation constraints and business rule enforcement

## Configuration Models

- Support for both legacy and modern configuration formats
- Template-based configuration with override mechanisms
- Custom configuration validation with security checks
- Operation strategy mapping and preset management
- Environment-specific configuration handling

## Performance and Monitoring Models

- Benchmark configuration with iteration and operation selection
- Metrics aggregation with operational and circuit breaker data
- Performance thresholds and target specification
- Historical data representation and trend analysis

## Security Models

- Security validation with threat detection support
- Field whitelisting and constraint validation
- Rate limiting and quota management
- Content filtering and pattern detection

## Dependencies

- Pydantic: Core data validation and serialization framework
- Typing: Type hints and generic type support for complex structures
- Field: Pydantic field configuration with defaults and validation

## Usage

These models are used throughout the resilience API endpoints to ensure
consistent data validation, serialization, and documentation. They
provide automatic OpenAPI schema generation and interactive documentation.

## Example

### Request validation

request = CustomConfigRequest(
configuration={
"retry_attempts": 3,
"circuit_breaker_threshold": 5
}
)

### Response serialization

response = ValidationResponse(
is_valid=True,
errors=[],
warnings=["Consider increasing retry attempts"],
suggestions=["Use exponential backoff for retries"]
)

## Note

All models include comprehensive field documentation and validation
constraints to ensure data integrity and provide clear API documentation.
The models support both simple and complex validation scenarios with
appropriate error handling and user feedback.
