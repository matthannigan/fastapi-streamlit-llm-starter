"""
Infrastructure Service: Resilience API Data Models

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
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class TemplateValidationRequest(BaseModel):
    """
    Template-based configuration validation request with override support for flexible customization.
    
    This model represents requests for validating resilience configurations based on predefined
    templates with optional customization overrides. It enables template-driven configuration
    validation while maintaining flexibility for environment-specific customizations and testing
    scenarios with structured parameter validation.
    
    Attributes:
        template_name: Unique identifier for the base configuration template to validate against.
                      Must correspond to an available template in the resilience system's
                      template catalog for successful validation processing.
        overrides: Optional configuration overrides to apply over the base template settings.
                  Allows customization of specific template parameters while maintaining
                  template structure and validation rules (defaults to empty dictionary).
    
    Behavior:
        **Template Resolution:**
        - Validates that specified template_name exists in available template catalog
        - Applies base template configuration as validation foundation
        - Merges override parameters with template defaults for comprehensive validation
        - Maintains template structure integrity while enabling customization flexibility
        
        **Override Processing:**
        - Applies overrides on top of base template configuration using deep merge semantics
        - Validates override parameters against template schema and constraints
        - Preserves template defaults for parameters not specified in overrides
        - Enables partial customization without requiring complete configuration specification
        
        **Validation Integration:**
        - Provides structured input for template-based validation endpoints
        - Enables testing of template configurations with environment-specific modifications
        - Supports validation workflow integration with template management systems
        - Facilitates configuration testing and validation automation scenarios
    
    Examples:
        >>> # Basic template validation request
        >>> request = TemplateValidationRequest(
        ...     template_name="production",
        ...     overrides={}
        ... )
        >>> assert request.template_name == "production"
        >>> assert request.overrides == {}
        
        >>> # Template validation with custom overrides
        >>> custom_request = TemplateValidationRequest(
        ...     template_name="development",
        ...     overrides={
        ...         "retry_attempts": 5,
        ...         "circuit_breaker_threshold": 3
        ...     }
        ... )
        >>> assert custom_request.overrides["retry_attempts"] == 5
        
        >>> # API request integration
        >>> import httpx
        >>> validation_data = {
        ...     "template_name": "simple",
        ...     "overrides": {"recovery_timeout": 45}
        ... }
        >>> response = await client.post("/internal/resilience/config/validate-template",
        ...                             json=validation_data)
    
    Note:
        This model is designed for template-based configuration workflows where base templates
        provide sensible defaults while overrides enable environment-specific customization.
        The validation process ensures template integrity while supporting flexible parameter
        modification for diverse deployment scenarios and testing requirements.
    """

    ...


class CustomConfigRequest(BaseModel):
    """
    Request model for custom configuration validation.
    """

    ...


class BenchmarkRunRequest(BaseModel):
    """
    Request model for running performance benchmarks.
    """

    ...


class ValidationRequest(BaseModel):
    """
    Request model for configuration validation.
    """

    ...


class TemplateBasedConfigRequest(BaseModel):
    """
    Request model for template-based configuration.
    """

    ...


class ResilienceMetricsResponse(BaseModel):
    """
    Comprehensive resilience system metrics response with multi-dimensional monitoring data.
    
    This response model provides complete visibility into resilience infrastructure performance,
    including operation-level metrics, circuit breaker status information, and aggregated system
    summaries. It serves as the primary data structure for resilience monitoring dashboards,
    alerting systems, and performance analysis workflows with structured metric organization.
    
    Attributes:
        operations: Operation-level metrics and performance data organized by operation identifier.
                   Each operation entry contains detailed metrics including success rates, failure
                   counts, response times, and resilience pattern effectiveness measurements.
        circuit_breakers: Circuit breaker status and operational metrics organized by breaker name.
                         Each circuit breaker entry includes state information, failure thresholds,
                         recovery timers, and historical failure/recovery event data.
        summary: Aggregated system-wide metrics providing overall resilience system health status,
                performance indicators, and high-level operational statistics for dashboard display
                and alerting integration purposes.
    
    Behavior:
        **Comprehensive Metrics Collection:**
        - Aggregates operation-level performance metrics across all monitored operations
        - Provides circuit breaker state and performance information for failure detection
        - Includes system-wide summary statistics for high-level health assessment
        - Maintains temporal metric data for trend analysis and performance monitoring
        
        **Monitoring Integration:**
        - Structures metrics data for integration with monitoring and alerting systems
        - Provides hierarchical metric organization from system-level to operation-specific details
        - Enables performance trend analysis and capacity planning through historical data
        - Supports dashboard visualization and operational monitoring workflow integration
        
        **Operational Visibility:**
        - Exposes resilience pattern effectiveness and system health indicators
        - Provides detailed failure analysis data and recovery pattern information
        - Enables performance optimization through comprehensive metric exposure
        - Supports troubleshooting and operational analysis with detailed metric breakdowns
    
    Examples:
        >>> # Comprehensive metrics response structure
        >>> metrics = ResilienceMetricsResponse(
        ...     operations={
        ...         "text_processing": {
        ...             "success_rate": 98.5,
        ...             "failure_count": 12,
        ...             "avg_response_time": 250.0,
        ...             "circuit_breaker_trips": 2
        ...         }
        ...     },
        ...     circuit_breakers={
        ...         "gemini_api": {
        ...             "state": "closed",
        ...             "failure_threshold": 5,
        ...             "current_failures": 0,
        ...             "last_failure_time": None
        ...         }
        ...     },
        ...     summary={
        ...         "overall_health": "healthy",
        ...         "total_operations": 10000,
        ...         "system_uptime": "99.8%"
        ...     }
        ... )
        
        >>> # Operational monitoring integration
        >>> def analyze_resilience_health(metrics: ResilienceMetricsResponse):
        ...     health_indicators = []
        ...     
        ...     # Check operation performance
        ...     for op_name, op_metrics in metrics.operations.items():
        ...         if op_metrics.get("success_rate", 0) < 95.0:
        ...             health_indicators.append(f"low_success_rate_{op_name}")
        ...     
        ...     # Check circuit breaker status
        ...     for cb_name, cb_metrics in metrics.circuit_breakers.items():
        ...         if cb_metrics.get("state") == "open":
        ...             health_indicators.append(f"circuit_breaker_open_{cb_name}")
        ...     
        ...     return {
        ...         "healthy": len(health_indicators) == 0,
        ...         "issues": health_indicators,
        ...         "overall_status": metrics.summary.get("overall_health")
        ...     }
        
        >>> # Dashboard data preparation
        >>> def prepare_dashboard_metrics(metrics: ResilienceMetricsResponse):
        ...     return {
        ...         "system_health": metrics.summary.get("overall_health", "unknown"),
        ...         "operation_count": len(metrics.operations),
        ...         "active_circuit_breakers": len(metrics.circuit_breakers),
        ...         "avg_success_rate": sum(
        ...             op.get("success_rate", 0) 
        ...             for op in metrics.operations.values()
        ...         ) / max(len(metrics.operations), 1)
        ...     }
    
    Note:
        This response model provides comprehensive resilience system visibility and is designed
        for integration with monitoring systems, operational dashboards, and alerting platforms.
        The structured metric organization enables both high-level system health assessment and
        detailed operational analysis for performance optimization and troubleshooting workflows.
    """

    ...


class PresetSummary(BaseModel):
    """
    Summary information about a resilience preset.
    """

    ...


class PresetDetails(BaseModel):
    """
    Detailed information about a resilience preset.
    """

    ...


class RecommendationResponse(BaseModel):
    """
    Preset recommendation response.
    """

    ...


class DetailedRecommendationResponse(BaseModel):
    """
    Enhanced preset recommendation response with confidence and reasoning.
    """

    ...


class AutoDetectResponse(BaseModel):
    """
    Auto-detection response for environment-aware recommendations.
    """

    ...


class TemplateListResponse(BaseModel):
    """
    Response model for configuration templates.
    """

    ...


class TemplateSuggestionResponse(BaseModel):
    """
    Response model for template suggestions.
    """

    ...


class ValidationResponse(BaseModel):
    """
    Response model for configuration validation.
    """

    ...


class CurrentConfigResponse(BaseModel):
    """
    Current resilience configuration response.
    """

    ...
