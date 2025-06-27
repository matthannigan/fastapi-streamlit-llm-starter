"""
REST API endpoints for resilience infrastructure.

Provides endpoints for:
- Listing and retrieving presets
- Validating custom configurations  
- Getting current resilience configuration
- Managing preset recommendations
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.config import Settings, settings
from app.infrastructure.resilience.orchestrator import ai_resilience
from app.infrastructure.resilience.presets import preset_manager, PresetManager
from app.infrastructure.resilience.config_validator import config_validator, ValidationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resilience", tags=["resilience"])


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


class ValidationResponse(BaseModel):
    """Response model for configuration validation."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CurrentConfigResponse(BaseModel):
    """Current resilience configuration response."""
    preset_name: str
    is_legacy_config: bool
    configuration: Dict[str, Any]
    operation_strategies: Dict[str, str]
    custom_overrides: Optional[Dict[str, Any]] = None


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


class CustomConfigRequest(BaseModel):
    """Request model for custom configuration validation."""
    configuration: Dict[str, Any]


class TemplateBasedConfigRequest(BaseModel):
    """Request model for template-based configuration."""
    template_name: str
    overrides: Optional[Dict[str, Any]] = None


class TemplateListResponse(BaseModel):
    """Response model for configuration templates."""
    templates: Dict[str, Dict[str, Any]]


class TemplateSuggestionResponse(BaseModel):
    """Response model for template suggestions."""
    suggested_template: Optional[str]
    confidence: float
    reasoning: str
    available_templates: List[str]


# Dependency for getting preset manager
def get_preset_manager() -> PresetManager:
    """Get the global preset manager instance."""
    return preset_manager


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


@router.get("/presets", response_model=List[PresetSummary])
async def list_presets(
    preset_mgr: PresetManager = Depends(get_preset_manager)
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
    preset_mgr: PresetManager = Depends(get_preset_manager)
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


@router.post("/validate", response_model=ValidationResponse)
async def validate_custom_config(
    request: CustomConfigRequest
) -> ValidationResponse:
    """
    Validate a custom resilience configuration.
    
    Args:
        request: Custom configuration to validate
        
    Returns:
        Validation results with errors and warnings
    """
    try:
        validation_result = config_validator.validate_custom_config(request.configuration)
        return ValidationResponse(
            is_valid=validation_result.is_valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            suggestions=validation_result.suggestions
        )
        
    except Exception as e:
        logger.error(f"Error validating custom configuration: {e}")
        return ValidationResponse(
            is_valid=False,
            errors=[f"Validation error: {str(e)}"],
            warnings=[],
            suggestions=[]
        )


@router.post("/validate-secure", response_model=ValidationResponse)
async def validate_custom_config_with_security(
    request: CustomConfigRequest
) -> ValidationResponse:
    """
    Validate a custom resilience configuration with enhanced security checks.
    
    Args:
        request: Custom configuration to validate
        
    Returns:
        Validation results with security, schema validation, errors and warnings
    """
    try:
        validation_result = config_validator.validate_with_security_checks(request.configuration)
        return ValidationResponse(
            is_valid=validation_result.is_valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            suggestions=validation_result.suggestions
        )
        
    except Exception as e:
        logger.error(f"Error validating custom configuration with security: {e}")
        return ValidationResponse(
            is_valid=False,
            errors=[f"Validation error: {str(e)}"],
            warnings=[],
            suggestions=[]
        )


@router.post("/validate-json", response_model=ValidationResponse)
async def validate_json_config(
    json_config: str = Query(..., description="JSON string of custom configuration")
) -> ValidationResponse:
    """
    Validate a JSON string configuration.
    
    Args:
        json_config: JSON string to validate
        
    Returns:
        Validation results with errors and warnings
    """
    try:
        validation_result = config_validator.validate_json_string(json_config)
        return ValidationResponse(
            is_valid=validation_result.is_valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            suggestions=validation_result.suggestions
        )
        
    except Exception as e:
        logger.error(f"Error validating JSON configuration: {e}")
        return ValidationResponse(
            is_valid=False,
            errors=[f"Validation error: {str(e)}"],
            warnings=[],
            suggestions=[]
        )


@router.get("/config", response_model=CurrentConfigResponse)
async def get_current_config(
    app_settings: Settings = Depends(get_settings)
) -> CurrentConfigResponse:
    """
    Get the current resilience configuration.
    
    Returns:
        Current configuration with preset info and operation strategies
    """
    try:
        # Get current resilience configuration
        resilience_config = app_settings.get_resilience_config()
        is_legacy = app_settings._has_legacy_resilience_config()
        
        # Get operation-specific strategies
        # Use registered operations from settings if available, fall back to common operations
        try:
            operations = app_settings.get_registered_operations()
        except Exception:
            # Fallback to common operations for compatibility
            operations = ["summarize", "sentiment", "key_points", "questions", "qa"]
        
        operation_strategies = {}
        for op in operations:
            try:
                operation_strategies[op] = app_settings.get_operation_strategy(op)
            except (AttributeError, KeyError):
                # Skip operations that don't have a strategy defined
                logger.debug(f"No strategy found for operation: {op}")
                continue
        
        # Parse custom overrides if present
        custom_overrides = None
        env_custom_config = os.getenv("RESILIENCE_CUSTOM_CONFIG")
        custom_config_json = env_custom_config if env_custom_config else app_settings.resilience_custom_config
        
        if custom_config_json:
            try:
                custom_overrides = json.loads(custom_config_json)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in resilience_custom_config")
        
        # Convert resilience config to dictionary
        config_dict = {
            "strategy": resilience_config.strategy.value,
            "retry_config": {
                "max_attempts": resilience_config.retry_config.max_attempts,
                "max_delay_seconds": resilience_config.retry_config.max_delay_seconds,
                "exponential_multiplier": resilience_config.retry_config.exponential_multiplier,
                "exponential_min": resilience_config.retry_config.exponential_min,
                "exponential_max": resilience_config.retry_config.exponential_max,
                "jitter": resilience_config.retry_config.jitter,
                "jitter_max": resilience_config.retry_config.jitter_max,
            },
            "circuit_breaker_config": {
                "failure_threshold": resilience_config.circuit_breaker_config.failure_threshold,
                "recovery_timeout": resilience_config.circuit_breaker_config.recovery_timeout,
                "half_open_max_calls": resilience_config.circuit_breaker_config.half_open_max_calls,
            },
            "enable_circuit_breaker": resilience_config.enable_circuit_breaker,
            "enable_retry": resilience_config.enable_retry,
        }
        
        return CurrentConfigResponse(
            preset_name=app_settings.resilience_preset,
            is_legacy_config=is_legacy,
            configuration=config_dict,
            operation_strategies=operation_strategies,
            custom_overrides=custom_overrides
        )
        
    except Exception as e:
        logger.error(f"Error getting current configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current configuration: {str(e)}")


@router.get("/recommend/{environment}", response_model=DetailedRecommendationResponse)
async def recommend_preset(
    environment: str,
    preset_mgr: PresetManager = Depends(get_preset_manager)
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
    preset_mgr: PresetManager = Depends(get_preset_manager)
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
    preset_mgr: PresetManager = Depends(get_preset_manager)
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


@router.post("/metrics/reset")
async def reset_resilience_metrics(
    operation_name: Optional[str] = Query(None, description="Operation name to reset (if None, resets all)")
):
    """
    Reset resilience metrics for a specific operation or all operations.
    
    Args:
        operation_name: Optional operation name to reset (if None, resets all)
        
    Returns:
        Success message
    """
    try:
        ai_resilience.reset_metrics(operation_name)
        
        if operation_name:
            message = f"Reset metrics for operation: {operation_name}"
        else:
            message = "Reset all resilience metrics"
            
        logger.info(message)
        return {"message": message}
        
    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset metrics: {str(e)}")


@router.get("/presets-summary", response_model=Dict[str, PresetDetails])
async def get_all_presets_summary(
    preset_mgr: PresetManager = Depends(get_preset_manager)
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


@router.get("/templates", response_model=TemplateListResponse)
async def get_configuration_templates() -> TemplateListResponse:
    """
    Get all available configuration templates.
    
    Returns:
        Dictionary of available configuration templates with descriptions
    """
    try:
        templates = config_validator.get_configuration_templates()
        return TemplateListResponse(templates=templates)
        
    except Exception as e:
        logger.error(f"Error getting configuration templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration templates: {str(e)}")


@router.get("/templates/{template_name}")
async def get_configuration_template(template_name: str):
    """
    Get a specific configuration template.
    
    Args:
        template_name: Name of the template to retrieve
        
    Returns:
        Template configuration with metadata
    """
    try:
        template = config_validator.get_template(template_name)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template '{template_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@router.post("/validate-template", response_model=ValidationResponse)
async def validate_template_based_config(
    request: TemplateBasedConfigRequest
) -> ValidationResponse:
    """
    Validate configuration based on a template with optional overrides.
    
    Args:
        request: Template name and optional configuration overrides
        
    Returns:
        Validation results for the template-based configuration
    """
    try:
        validation_result = config_validator.validate_template_based_config(
            request.template_name, 
            request.overrides or {}
        )
        return ValidationResponse(
            is_valid=validation_result.is_valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            suggestions=validation_result.suggestions
        )
        
    except Exception as e:
        logger.error(f"Error validating template-based configuration: {e}")
        return ValidationResponse(
            is_valid=False,
            errors=[f"Validation error: {str(e)}"],
            warnings=[],
            suggestions=[]
        )


@router.post("/suggest-template", response_model=TemplateSuggestionResponse)
async def suggest_template_for_config(
    request: CustomConfigRequest
) -> TemplateSuggestionResponse:
    """
    Suggest the most appropriate template for a given configuration.
    
    Args:
        request: Configuration to analyze for template suggestion
        
    Returns:
        Template suggestion with confidence and reasoning
    """
    try:
        suggested_template = config_validator.suggest_template_for_config(request.configuration)
        available_templates = list(config_validator.get_configuration_templates().keys())
        
        if suggested_template:
            # Calculate confidence based on how well the config matches
            template_info = config_validator.get_template(suggested_template)
            if template_info:
                template_config = template_info["config"]
                
                # Simple confidence calculation based on matching fields  
                matches = 0
                total_fields = 0
                
                for key in ["retry_attempts", "circuit_breaker_threshold", "default_strategy"]:
                    if key in request.configuration and key in template_config:
                        total_fields += 1
                        if request.configuration[key] == template_config[key]:
                            matches += 1
                
                confidence = matches / total_fields if total_fields > 0 else 0.5
                reasoning = f"Configuration closely matches '{suggested_template}' template with {matches}/{total_fields} key parameters matching"
            else:
                confidence = 0.2
                reasoning = f"Template '{suggested_template}' found but could not load its configuration"
        else:
            confidence = 0.0
            reasoning = "No template closely matches the provided configuration. Consider using a standard preset instead."
        
        return TemplateSuggestionResponse(
            suggested_template=suggested_template,
            confidence=confidence,
            reasoning=reasoning,
            available_templates=available_templates
        )
        
    except Exception as e:
        logger.error(f"Error suggesting template for configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to suggest template: {str(e)}")