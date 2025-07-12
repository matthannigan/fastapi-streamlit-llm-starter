"""Resilience preset management REST API endpoints.

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
    GET /resilience/config/presets: List all available resilience presets with summaries
    GET /resilience/config/presets/{preset_name}: Get detailed configuration for a specific preset
    GET /resilience/config/presets-summary: Get comprehensive summary of all presets
    GET /resilience/config/recommend-preset/{environment}: Get preset recommendation for specific environment
    GET /resilience/config/recommend-preset-auto: Auto-detect environment and recommend optimal preset

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
        GET /api/internal/resilience/recommend/prod
        
    To auto-detect environment and get recommendation:
        GET /api/internal/resilience/recommend-auto
        
    To list all available presets:
        GET /api/internal/resilience/presets

Note:
    Preset recommendations include confidence scores to help administrators
    make informed decisions about resilience configurations. The auto-detection
    feature analyzes deployment context to provide intelligent recommendations
    without requiring explicit environment specification.
"""

import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.config import Settings, settings
from app.infrastructure.security.auth import verify_api_key, optional_verify_api_key
from app.infrastructure.resilience.orchestrator import ai_resilience
from app.services.text_processor import TextProcessorService
from app.api.v1.deps import get_text_processor
from app.infrastructure.resilience.config_presets import preset_manager, PresetManager
from app.infrastructure.resilience.performance_benchmarks import performance_benchmark
from app.infrastructure.resilience.config_validator import config_validator, ValidationResult

from app.api.internal.resilience.models import (
    PresetSummary,
    PresetDetails,
    DetailedRecommendationResponse,
    AutoDetectResponse
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resilience/config", tags=["resilience-config"])

# Dependency for getting preset manager
def get_preset_manager() -> PresetManager:
    """Get the global preset manager instance."""
    return preset_manager

@router.get("/presets", response_model=List[PresetSummary])
async def list_presets(
    preset_mgr: PresetManager = Depends(get_preset_manager),
    api_key: str = Depends(verify_api_key)
) -> List[PresetSummary]:
    """List all available resilience configuration presets with summary information.

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
    """
    try:
        preset_summaries = []
        for preset_name in preset_mgr.list_presets():
            preset = preset_mgr.get_preset(preset_name)
            preset_summaries.append(PresetSummary(
                name=preset.name,
                description=preset.description,
                retry_attempts=preset.retry_attempts,
                circuit_breaker_threshold=preset.circuit_breaker_threshold,
                recovery_timeout=preset.recovery_timeout,
                default_strategy=preset.default_strategy.value,
                environment_contexts=preset.environment_contexts
            ))
        
        return preset_summaries
        
    except Exception as e:
        logger.error(f"Error listing presets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list presets: {str(e)}")


@router.get("/presets/{preset_name}", response_model=PresetDetails)
async def get_preset_details(
    preset_name: str,
    preset_mgr: PresetManager = Depends(get_preset_manager),
    api_key: str = Depends(verify_api_key)
) -> PresetDetails:
    """Get comprehensive detailed information about a specific resilience preset.

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
    """
    try:
        details = preset_mgr.get_preset_details(preset_name)
        return PresetDetails(**details)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting preset details for '{preset_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get preset details: {str(e)}")


@router.get("/presets-summary", response_model=Dict[str, PresetDetails])
async def get_all_presets_summary(
    preset_mgr: PresetManager = Depends(get_preset_manager),
    api_key: str = Depends(verify_api_key)
) -> Dict[str, PresetDetails]:
    """Get comprehensive summary of all presets with detailed configuration information.

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
    """
    try:
        summary = preset_mgr.get_all_presets_summary()
        
        # Convert to PresetDetails format
        result = {}
        for preset_name, details in summary.items():
            result[preset_name] = PresetDetails(**details)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting presets summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get presets summary: {str(e)}")


@router.get("/recommend-preset/{environment}", response_model=DetailedRecommendationResponse)
async def recommend_preset(
    environment: str,
    preset_mgr: PresetManager = Depends(get_preset_manager),
    api_key: str = Depends(verify_api_key)
) -> DetailedRecommendationResponse:
    """Get intelligent preset recommendation for a specific deployment environment.

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
    """
    try:
        recommendation = preset_mgr.recommend_preset_with_details(environment)
        available = preset_mgr.list_presets()
        
        return DetailedRecommendationResponse(
            environment_detected=recommendation.environment_detected,
            recommended_preset=recommendation.preset_name,
            confidence=recommendation.confidence,
            reasoning=recommendation.reasoning,
            available_presets=available,
            auto_detected=False
        )
        
    except Exception as e:
        logger.error(f"Error recommending preset for environment '{environment}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to recommend preset: {str(e)}")


@router.get("/recommend-preset-auto", response_model=AutoDetectResponse)
async def auto_recommend_preset(
    preset_mgr: PresetManager = Depends(get_preset_manager),
    api_key: str = Depends(verify_api_key)
) -> AutoDetectResponse:
    """Auto-detect deployment environment and recommend appropriate resilience preset.

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
    """
    try:
        recommendation = preset_mgr.recommend_preset_with_details(None)  # None triggers auto-detection
        
        # Determine detection method based on environment detected
        if "(auto-detected)" in recommendation.environment_detected:
            detection_method = "environment_variables_and_context"
        else:
            detection_method = "environment_variable"
        
        return AutoDetectResponse(
            environment_detected=recommendation.environment_detected,
            recommended_preset=recommendation.preset_name,
            confidence=recommendation.confidence,
            reasoning=recommendation.reasoning,
            detection_method=detection_method
        )
        
    except Exception as e:
        logger.error(f"Error auto-detecting environment for preset recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to auto-detect and recommend preset: {str(e)}")
