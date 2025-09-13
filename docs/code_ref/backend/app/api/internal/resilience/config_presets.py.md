---
sidebar_label: config_presets
---

# Infrastructure Service: Resilience Preset Management API

  file_path: `backend/app/api/internal/resilience/config_presets.py`

🏗️ **STABLE API** - Changes affect all template users  
📋 **Minimum test coverage**: 90%  
🔧 **Configuration-driven behavior**

This module provides comprehensive REST API endpoints for managing and querying
resilience configuration presets. It includes functionality for listing presets,
retrieving detailed preset configurations, generating environment-specific
recommendations, and providing auto-detection capabilities for optimal preset
selection based on deployment contexts.

The module implements intelligent preset recommendation algorithms that analyze
deployment environments and provide confidence scores and reasoning for optimal
resilience configurations. All endpoints require API key authentication for
secure access to configuration data.

Endpoints:
    GET /internal/resilience/config/presets: List all available resilience presets with summaries
    GET /internal/resilience/config/presets/{preset_name}: Get detailed configuration for a specific preset
    GET /internal/resilience/config/presets-summary: Get comprehensive summary of all presets
    GET /internal/resilience/config/recommend-preset/{environment}: Get preset recommendation for specific environment
    GET /internal/resilience/config/recommend-preset-auto: Auto-detect environment and recommend optimal preset

Preset Management Features:
    - Complete preset catalog with descriptions and configurations
    - Environment-specific preset recommendations (dev, test, staging, prod)
    - Confidence scoring for recommendation quality assessment
    - Auto-detection of deployment environments for intelligent recommendations
    - Detailed reasoning for recommended configurations
    - Support for custom environment contexts and deployment scenarios

Recommendation Algorithm:
    - Environment pattern matching against preset specifications
    - Confidence scoring based on configuration alignment
    - Fallback recommendations for unknown environments
    - Support for both explicit environment specification and auto-detection
    - Comprehensive reasoning explanations for recommendation decisions

Dependencies:
    - PresetManager: Core preset management and recommendation engine
    - Settings: Configuration access for preset customization
    - Security: API key verification for all endpoints
    - Pydantic Models: Structured response validation and documentation

Authentication:
    All endpoints require API key authentication to protect configuration
    data and ensure secure access to resilience preset information.

Example:
    To get a recommendation for production environment:
        GET /internal/resilience/recommend/prod
        
    To auto-detect environment and get recommendation:
        GET /internal/resilience/recommend-auto
        
    To list all available presets:
        GET /internal/resilience/presets

Note:
    Preset recommendations include confidence scores to help administrators
    make informed decisions about resilience configurations. The auto-detection
    feature analyzes deployment context to provide intelligent recommendations
    without requiring explicit environment specification.

## get_preset_manager()

```python
def get_preset_manager() -> PresetManager:
```

Get the global preset manager instance.

## list_presets()

```python
async def list_presets(preset_mgr: PresetManager = Depends(get_preset_manager), api_key: str = Depends(verify_api_key)) -> List[PresetSummary]:
```

List all available resilience configuration presets with summary information.

This endpoint provides a comprehensive list of all available resilience presets,
including basic configuration parameters and environment contexts for each preset.

Args:
    preset_mgr: Preset manager dependency for accessing preset data
    api_key: API key for authentication (injected via dependency)
    
Returns:
    List[PresetSummary]: List of preset summaries, each containing:
        - name: Preset name identifier
        - description: Human-readable preset description
        - retry_attempts: Number of retry attempts configured
        - circuit_breaker_threshold: Failure threshold for circuit breaker
        - recovery_timeout: Circuit breaker recovery timeout
        - default_strategy: Default resilience strategy
        - environment_contexts: List of suitable deployment environments
        
Raises:
    HTTPException: 500 Internal Server Error if preset listing fails
    
Example:
    >>> response = await list_presets()
    >>> [
    ...     PresetSummary(
    ...         name="production",
    ...         description="High-reliability configuration for production",
    ...         retry_attempts=3,
    ...         circuit_breaker_threshold=5,
    ...         default_strategy="conservative"
    ...     ),
    ...     PresetSummary(name="development", ...)
    ... ]

## get_preset_details()

```python
async def get_preset_details(preset_name: str, preset_mgr: PresetManager = Depends(get_preset_manager), api_key: str = Depends(verify_api_key)) -> PresetDetails:
```

Get comprehensive detailed information about a specific resilience preset.

This endpoint provides complete configuration details for a specific preset,
including all parameters, strategies, and configuration values needed for
implementation and decision-making.

Args:
    preset_name: Name of the specific preset to retrieve details for
    preset_mgr: Preset manager dependency for accessing preset data
    api_key: API key for authentication (injected via dependency)
    
Returns:
    PresetDetails: Comprehensive preset information containing:
        - Complete configuration parameters
        - Retry and circuit breaker settings
        - Strategy configurations
        - Environment suitability information
        - Performance characteristics
        - Usage recommendations
        
Raises:
    HTTPException: 404 Not Found if preset doesn't exist
    HTTPException: 500 Internal Server Error if preset details retrieval fails
    
Example:
    >>> response = await get_preset_details("production")
    >>> PresetDetails(
    ...     name="production",
    ...     description="High-reliability configuration",
    ...     retry_config={...},
    ...     circuit_breaker_config={...},
    ...     strategies={...}
    ... )

## get_all_presets_summary()

```python
async def get_all_presets_summary(preset_mgr: PresetManager = Depends(get_preset_manager), api_key: str = Depends(verify_api_key)) -> Dict[str, PresetDetails]:
```

Get comprehensive summary of all presets with detailed configuration information.

This endpoint provides a complete overview of all available presets with
detailed configuration information, useful for comparison and selection
of appropriate resilience configurations.

Args:
    preset_mgr: Preset manager dependency for accessing preset data
    api_key: API key for authentication (injected via dependency)
    
Returns:
    Dict[str, PresetDetails]: Dictionary mapping preset names to detailed information:
        - Keys: Preset names (e.g., "production", "development", "testing")
        - Values: PresetDetails objects containing complete configuration
        - Each preset includes retry configs, circuit breaker settings,
          strategies, and environment suitability information
        
Raises:
    HTTPException: 500 Internal Server Error if presets summary retrieval fails
    
Example:
    >>> response = await get_all_presets_summary()
    >>> {
    ...     "production": PresetDetails(
    ...         name="production",
    ...         retry_attempts=3,
    ...         circuit_breaker_threshold=5,
    ...         strategies={...}
    ...     ),
    ...     "development": PresetDetails(...),
    ...     "testing": PresetDetails(...)
    ... }

## recommend_preset()

```python
async def recommend_preset(environment: str, preset_mgr: PresetManager = Depends(get_preset_manager), api_key: str = Depends(verify_api_key)) -> DetailedRecommendationResponse:
```

Get intelligent preset recommendation for a specific deployment environment.

This endpoint analyzes the specified environment and provides a detailed
recommendation for the most suitable resilience preset, including confidence
scoring and comprehensive reasoning for the recommendation decision.

Args:
    environment: Target deployment environment name 
                (e.g., "dev", "test", "staging", "prod", "production")
    preset_mgr: Preset manager dependency for accessing preset data
    api_key: API key for authentication (injected via dependency)
    
Returns:
    DetailedRecommendationResponse: Comprehensive recommendation containing:
        - recommended_preset: Name of the recommended preset
        - confidence_score: Numerical confidence (0.0-1.0) in recommendation
        - reasoning: Detailed explanation for the recommendation
        - alternative_presets: List of alternative preset options
        - environment_analysis: Analysis of environment characteristics
        - configuration_highlights: Key configuration aspects
        
Raises:
    HTTPException: 500 Internal Server Error if recommendation generation fails
    
Example:
    >>> response = await recommend_preset("production")
    >>> DetailedRecommendationResponse(
    ...     recommended_preset="production",
    ...     confidence_score=0.95,
    ...     reasoning="High-reliability requirements detected...",
    ...     alternative_presets=["high_performance", "enterprise"],
    ...     environment_analysis={...}
    ... )

## auto_recommend_preset()

```python
async def auto_recommend_preset(preset_mgr: PresetManager = Depends(get_preset_manager), api_key: str = Depends(verify_api_key)) -> AutoDetectResponse:
```

Auto-detect deployment environment and recommend appropriate resilience preset.

This endpoint intelligently analyzes environment variables and system context
to automatically determine the deployment environment and recommend the most
suitable resilience preset without requiring explicit environment specification.

Args:
    preset_mgr: Preset manager dependency for accessing preset data
    api_key: API key for authentication (injected via dependency)
    
Returns:
    AutoDetectResponse: Auto-detection results containing:
        - environment_detected: Detected environment name with detection method
        - recommended_preset: Name of the recommended preset
        - confidence: Confidence score (0.0-1.0) in the recommendation
        - reasoning: Detailed explanation for the recommendation decision
        - detection_method: Method used for environment detection
        
Raises:
    HTTPException: 500 Internal Server Error if auto-detection or recommendation fails
    
Note:
    The auto-detection analyzes environment variables, system properties,
    and deployment context to intelligently determine the appropriate
    environment and corresponding resilience configuration.
    
Example:
    >>> response = await auto_recommend_preset()
    >>> AutoDetectResponse(
    ...     environment_detected="production (auto-detected)",
    ...     recommended_preset="production",
    ...     confidence=0.85,
    ...     reasoning="Detected production indicators in environment...",
    ...     detection_method="environment_variables_and_context"
    ... )
