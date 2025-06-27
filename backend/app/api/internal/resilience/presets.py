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
    GET /resilience/presets: List all available resilience presets with summaries
    GET /resilience/presets/{preset_name}: Get detailed configuration for a specific preset
    GET /resilience/presets-summary: Get comprehensive summary of all presets
    GET /resilience/recommend/{environment}: Get preset recommendation for specific environment
    GET /resilience/recommend-auto: Auto-detect environment and recommend optimal preset
    GET /resilience/recommend: Legacy preset recommendation endpoint with query parameter

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

from app.config import Settings, settings
from app.infrastructure.security.auth import verify_api_key, optional_verify_api_key
from app.infrastructure.resilience.orchestrator import ai_resilience
from app.services.text_processor import TextProcessorService
from app.api.v1.deps import get_text_processor
from app.infrastructure.resilience.presets import preset_manager, PresetManager
from app.infrastructure.resilience.performance_benchmarks import performance_benchmark
from app.infrastructure.resilience.config_validator import config_validator, ValidationResult


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resilience", tags=["resilience"])

# Dependency for getting preset manager
def get_preset_manager() -> PresetManager:
    """Get the global preset manager instance."""
    return preset_manager

# Pydantic models for API responses
class PresetSummary(BaseModel):
    """Summary information about a resilience preset."""
    name: str
    description: str
    retry_attempts: int
    circuit_breaker_threshold: int
    recovery_timeout: int
    default_strategy: str
    environment_contexts: List[str]


class PresetDetails(BaseModel):
    """Detailed information about a resilience preset."""
    name: str
    description: str
    configuration: Dict[str, Any]
    environment_contexts: List[str]


class RecommendationResponse(BaseModel):
    """Preset recommendation response."""
    environment: str
    recommended_preset: str
    reason: str
    available_presets: List[str]


class DetailedRecommendationResponse(BaseModel):
    """Enhanced preset recommendation response with confidence and reasoning."""
    environment_detected: str
    recommended_preset: str
    confidence: float
    reasoning: str
    available_presets: List[str]
    auto_detected: bool


class AutoDetectResponse(BaseModel):
    """Auto-detection response for environment-aware recommendations."""
    environment_detected: str
    recommended_preset: str
    confidence: float
    reasoning: str
    detection_method: str


@router.get("/presets", response_model=List[PresetSummary])
async def list_presets(
    preset_mgr: PresetManager = Depends(get_preset_manager),
    api_key: str = Depends(verify_api_key)
) -> List[PresetSummary]:
    """
    List all available resilience presets.
    
    Returns:
        List of preset summaries with basic information
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
    """
    Get detailed information about a specific preset.
    
    Args:
        preset_name: Name of the preset to retrieve
        
    Returns:
        Detailed preset information
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
    """
    Get summary of all presets with detailed information.
    
    Returns:
        Dictionary mapping preset names to their detailed information
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


@router.get("/recommend/{environment}", response_model=DetailedRecommendationResponse)
async def recommend_preset(
    environment: str,
    preset_mgr: PresetManager = Depends(get_preset_manager),
    api_key: str = Depends(verify_api_key)
) -> DetailedRecommendationResponse:
    """
    Get detailed preset recommendation for a specific environment.
    
    Args:
        environment: Environment name (dev, test, staging, prod, etc.)
        
    Returns:
        Detailed recommendation with confidence and reasoning
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


@router.get("/recommend-auto", response_model=AutoDetectResponse)
async def auto_recommend_preset(
    preset_mgr: PresetManager = Depends(get_preset_manager),
    api_key: str = Depends(verify_api_key)
) -> AutoDetectResponse:
    """
    Auto-detect environment and recommend appropriate preset.
    
    Analyzes environment variables and system context to recommend
    the most suitable resilience preset.
    
    Returns:
        Auto-detected environment and recommended preset with confidence
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


@router.get("/recommend", response_model=RecommendationResponse)
async def recommend_preset_legacy(
    environment: str = Query(..., description="Environment name to get recommendation for"),
    preset_mgr: PresetManager = Depends(get_preset_manager),
    api_key: str = Depends(verify_api_key)
) -> RecommendationResponse:
    """
    Legacy endpoint: Get preset recommendation for a specific environment.
    
    This endpoint maintains backward compatibility with the original
    recommendation format.
    
    Args:
        environment: Environment name (dev, test, staging, prod, etc.)
        
    Returns:
        Recommended preset with basic reasoning
    """
    try:
        recommended = preset_mgr.recommend_preset(environment)
        available = preset_mgr.list_presets()
        
        # Generate simple reasoning based on environment
        env_lower = environment.lower()
        if env_lower in ["development", "dev", "testing", "test"]:
            reason = "Development environments benefit from fast-fail strategies for quick feedback"
        elif env_lower in ["staging", "stage", "production", "prod"]:
            reason = "Production environments require high reliability and comprehensive error handling"
        else:
            reason = "Using balanced approach for unrecognized environment"
        
        return RecommendationResponse(
            environment=environment,
            recommended_preset=recommended,
            reason=reason,
            available_presets=available
        )
        
    except Exception as e:
        logger.error(f"Error recommending preset for environment '{environment}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to recommend preset: {str(e)}")
