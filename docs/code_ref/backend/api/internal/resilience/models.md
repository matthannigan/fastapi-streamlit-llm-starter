# Infrastructure Service: Resilience API Data Models

🏗️ **STABLE API** - Changes affect all template users
📋 **Minimum test coverage**: 90%
🔧 **Configuration-driven behavior**

This module defines comprehensive Pydantic models for all resilience API
endpoints, providing structured data validation, serialization, and
documentation for requests and responses. These models ensure data integrity,
type safety, and consistent API documentation across the resilience
infrastructure, serving as the foundation for configuration management,
validation, and monitoring capabilities.

## Core Components

### Request Models (5 models)

#### Configuration Management
- `TemplateValidationRequest`: Template-based validation with override support
- `template_name` (str): Template identifier for validation
- `overrides` (Dict[str, Any]): Custom overrides to template defaults (default: {})

- `CustomConfigRequest`: Custom configuration validation requests
- `configuration` (Dict[str, Any]): Complete custom configuration object

- `TemplateBasedConfigRequest`: Template-based configuration with overrides
- `template_name` (str): Template identifier
- `overrides` (Optional[Dict[str, Any]]): Optional configuration overrides

- `ValidationRequest`: Generic configuration validation requests
- `configuration` (Dict[str, Any]): Configuration object for validation

#### Performance Testing
- `BenchmarkRunRequest`: Performance benchmark execution parameters
- `iterations` (int): Number of benchmark iterations (default: 50)
- `include_slow` (bool): Include slow operations in benchmarks (default: False)
- `operations` (Optional[List[str]]): Specific operations to benchmark (default: None for all)

### Response Models (11 models)

#### Metrics and Monitoring
- `ResilienceMetricsResponse`: Comprehensive resilience service metrics
- `operations` (Dict[str, Dict[str, Any]]): Operation-level metrics and statistics
- `circuit_breakers` (Dict[str, Dict[str, Any]]): Circuit breaker status and metrics
- `summary` (Dict[str, Any]): Aggregated metrics summary

#### Preset Management
- `PresetSummary`: Summary information about resilience presets
- `name` (str): Preset identifier
- `description` (str): Human-readable preset description
- `retry_attempts` (int): Number of retry attempts configured
- `circuit_breaker_threshold` (int): Circuit breaker failure threshold
- `recovery_timeout` (int): Recovery timeout in seconds
- `default_strategy` (str): Default resilience strategy name
- `environment_contexts` (List[str]): Applicable environment contexts

- `PresetDetails`: Detailed preset information with full configuration
- `name` (str): Preset identifier
- `description` (str): Human-readable preset description
- `configuration` (Dict[str, Any]): Complete preset configuration object
- `environment_contexts` (List[str]): Applicable environment contexts

#### Recommendation System
- `RecommendationResponse`: Basic preset recommendation response
- `environment` (str): Target environment context
- `recommended_preset` (str): Recommended preset name
- `reason` (str): Human-readable recommendation reasoning
- `available_presets` (List[str]): All available preset options

- `DetailedRecommendationResponse`: Enhanced recommendation with confidence scoring
- `environment_detected` (str): Detected environment context
- `recommended_preset` (str): Recommended preset name
- `confidence` (float): Recommendation confidence score (0.0-1.0)
- `reasoning` (str): Detailed recommendation reasoning
- `available_presets` (List[str]): All available preset options
- `auto_detected` (bool): Whether environment was auto-detected

- `AutoDetectResponse`: Environment auto-detection results
- `environment_detected` (str): Detected environment context
- `recommended_preset` (str): Recommended preset for detected environment
- `confidence` (float): Detection confidence score (0.0-1.0)
- `reasoning` (str): Detection reasoning and methodology
- `detection_method` (str): Method used for environment detection

#### Template Management
- `TemplateListResponse`: Available configuration templates catalog
- `templates` (Dict[str, Dict[str, Any]]): Complete templates mapping

- `TemplateSuggestionResponse`: Template recommendation with confidence scoring
- `suggested_template` (Optional[str]): Recommended template name (None if no suggestion)
- `confidence` (float): Suggestion confidence score (0.0-1.0)
- `reasoning` (str): Human-readable suggestion reasoning
- `available_templates` (List[str]): All available template options

#### Validation and Configuration
- `ValidationResponse`: Configuration validation results with detailed feedback
- `is_valid` (bool): Whether configuration passed validation
- `errors` (List[str]): Validation error messages (default: empty list)
- `warnings` (List[str]): Validation warning messages (default: empty list)
- `suggestions` (List[str]): Optimization suggestions (default: empty list)
- `security_info` (Optional[Dict[str, Any]]): Security validation metadata (default: None)

- `CurrentConfigResponse`: Current resilience configuration state
- `preset_name` (str): Active preset identifier
- `is_legacy_config` (bool): Whether using legacy configuration format
- `configuration` (Dict[str, Any]): Complete active configuration
- `operation_strategies` (Dict[str, str]): Operation-to-strategy mappings
- `custom_overrides` (Optional[Dict[str, Any]]): Custom configuration overrides
- `strategies` (Optional[Dict[str, Dict[str, Any]]]): Complete strategies mapping (backward compatibility)

## Data Validation Features

### Pydantic Integration
- **Type Safety**: Automatic type validation and conversion for all fields
- **Field Constraints**: Built-in validation with descriptive error messages
- **Default Values**: Intelligent default value management with fallback handling
- **Optional Fields**: Clear distinction between required and optional parameters
- **Nested Models**: Support for complex nested data structures with validation

### Validation Patterns
- **Configuration Validation**: Security checks and constraint validation for configurations
- **Template Validation**: Template existence and compatibility verification
- **Performance Validation**: Benchmark parameter validation with safety limits
- **Environment Validation**: Environment context validation and auto-detection

## Model Architecture

### Request/Response Pairing
Models are designed with clear request/response pairing for API endpoints:
- Template operations: `TemplateValidationRequest` → `ValidationResponse`
- Custom config: `CustomConfigRequest` → `ValidationResponse`
- Benchmarking: `BenchmarkRunRequest` → performance metrics data
- Recommendations: environment context → `RecommendationResponse` variants

### Extensibility Design
- **Backward Compatibility**: Support for legacy configuration formats
- **Forward Compatibility**: Flexible Dict fields for future extensions
- **Version Migration**: Graceful handling of configuration format evolution

## Usage Examples

### Configuration Validation
```python
# Template-based validation with overrides
request = TemplateValidationRequest(
template_name="production",
overrides={"retry_attempts": 5}
)

# Custom configuration validation
request = CustomConfigRequest(
configuration={
"retry_attempts": 3,
"circuit_breaker_threshold": 5,
"recovery_timeout": 60
}
)
```

### Response Handling
```python
# Validation response with feedback
response = ValidationResponse(
is_valid=True,
errors=[],
warnings=["Consider increasing retry attempts for production"],
suggestions=["Use exponential backoff for better performance"],
security_info={"validation_level": "strict"}
)

# Recommendation with confidence scoring
response = DetailedRecommendationResponse(
environment_detected="production",
recommended_preset="production",
confidence=0.95,
reasoning="Production indicators detected: PROD=true, production URLs",
available_presets=["simple", "development", "production"],
auto_detected=True
)
```

### Performance Benchmarking
```python
# Benchmark configuration
request = BenchmarkRunRequest(
iterations=100,
include_slow=True,
operations=["summarize", "sentiment"]
)
```

## Dependencies

### Core Dependencies
- `pydantic.BaseModel`: Base class for all model definitions
- `pydantic.Field`: Advanced field configuration with defaults and validation
- `typing`: Type hints and generic type support for complex structures

### Integration Points
- **FastAPI Integration**: Automatic OpenAPI schema generation and documentation
- **API Endpoints**: Used across all resilience API endpoints for validation
- **Configuration System**: Validates resilience configuration presets and custom configs
- **Monitoring System**: Structures metrics and monitoring data responses

## Model Organization

### Functional Groupings
1. **Configuration Models**: Template and custom configuration handling
2. **Validation Models**: Request/response pairs for validation workflows
3. **Preset Models**: Resilience preset management and recommendations
4. **Metrics Models**: Performance and monitoring data structures
5. **Recommendation Models**: Environment detection and preset suggestions

### Design Principles
- **Single Responsibility**: Each model serves a specific API use case
- **Composition Over Inheritance**: Models compose functionality rather than inherit
- **Validation First**: All fields include appropriate validation constraints
- **Documentation Complete**: Every field includes description and usage context

**Change with caution** - These models define the stable API contracts used
throughout the resilience infrastructure. Ensure backward compatibility and
comprehensive testing for any modifications.
