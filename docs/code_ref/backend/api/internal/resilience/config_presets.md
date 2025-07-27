# Resilience preset management REST API endpoints.

This module provides comprehensive REST API endpoints for managing and querying
resilience configuration presets. It includes functionality for listing presets,
retrieving detailed preset configurations, generating environment-specific
recommendations, and providing auto-detection capabilities for optimal preset
selection based on deployment contexts.

The module implements intelligent preset recommendation algorithms that analyze
deployment environments and provide confidence scores and reasoning for optimal
resilience configurations. All endpoints require API key authentication for
secure access to configuration data.

## Endpoints

GET /internal/resilience/config/presets: List all available resilience presets with summaries
GET /internal/resilience/config/presets/{preset_name}: Get detailed configuration for a specific preset
GET /internal/resilience/config/presets-summary: Get comprehensive summary of all presets
GET /internal/resilience/config/recommend-preset/{environment}: Get preset recommendation for specific environment
GET /internal/resilience/config/recommend-preset-auto: Auto-detect environment and recommend optimal preset

## Preset Management Features

- Complete preset catalog with descriptions and configurations
- Environment-specific preset recommendations (dev, test, staging, prod)
- Confidence scoring for recommendation quality assessment
- Auto-detection of deployment environments for intelligent recommendations
- Detailed reasoning for recommended configurations
- Support for custom environment contexts and deployment scenarios

## Recommendation Algorithm

- Environment pattern matching against preset specifications
- Confidence scoring based on configuration alignment
- Fallback recommendations for unknown environments
- Support for both explicit environment specification and auto-detection
- Comprehensive reasoning explanations for recommendation decisions

## Dependencies

- PresetManager: Core preset management and recommendation engine
- Settings: Configuration access for preset customization
- Security: API key verification for all endpoints
- Pydantic Models: Structured response validation and documentation

## Authentication

All endpoints require API key authentication to protect configuration
data and ensure secure access to resilience preset information.

## Example

To get a recommendation for production environment:
GET /internal/resilience/recommend/prod

To auto-detect environment and get recommendation:
GET /internal/resilience/recommend-auto

To list all available presets:
GET /internal/resilience/presets

## Note

Preset recommendations include confidence scores to help administrators
make informed decisions about resilience configurations. The auto-detection
feature analyzes deployment context to provide intelligent recommendations
without requiring explicit environment specification.
