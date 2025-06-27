"""Resilience configuration template management REST API endpoints.

This module provides REST API endpoints for managing and utilizing resilience
configuration templates. Templates serve as structured blueprints for creating
consistent resilience configurations across different use cases and deployment
scenarios, offering validation, suggestion, and customization capabilities.

The module implements template-based configuration management that allows users
to leverage predefined configuration patterns while providing flexibility for
customization through override mechanisms. All endpoints include comprehensive
validation and intelligent template suggestion features.

Endpoints:
    GET /resilience/templates: Retrieve all available configuration templates
    GET /resilience/templates/{template_name}: Get specific template configuration
    POST /resilience/validate-template: Validate template-based configuration with overrides
    POST /resilience/suggest-template: Suggest optimal template for given configuration

Template Management Features:
    - Complete template catalog with descriptions and use cases
    - Template-based configuration validation with override support
    - Intelligent template suggestion based on configuration analysis
    - Confidence scoring for template matching quality
    - Flexible override mechanism for template customization
    - Comprehensive validation with error reporting and suggestions

Template Validation:
    - Schema validation against template specifications
    - Override compatibility checking and conflict detection
    - Error reporting with detailed validation messages
    - Warning generation for potential configuration issues
    - Suggestion provision for configuration improvements

Template Suggestion Algorithm:
    - Configuration pattern analysis for template matching
    - Field-by-field comparison with available templates
    - Confidence calculation based on parameter alignment
    - Reasoning explanations for suggestion decisions
    - Fallback handling for configurations without close matches

Dependencies:
    - ConfigValidator: Template validation and suggestion engine
    - Security: API key verification for protected endpoints
    - Pydantic Models: Structured request/response validation
    - TemplateManager: Core template management functionality

Authentication:
    All endpoints require API key authentication to protect template
    configurations and ensure secure access to validation services.

Example:
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

Note:
    Template-based configurations provide consistency and best practices
    while allowing customization through overrides. The suggestion system
    helps identify appropriate templates for existing configurations.
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

from app.api.internal.resilience.models import (
    TemplateListResponse, 
    TemplateBasedConfigRequest, 
    TemplateSuggestionResponse, 
    ValidationResponse, 
    CustomConfigRequest
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resilience", tags=["resilience"])

@router.get("/templates", response_model=TemplateListResponse)
async def get_configuration_templates(
    api_key: str = Depends(verify_api_key)
) -> TemplateListResponse:
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration templates: {str(e)}"
        )


@router.get("/templates/{template_name}")
async def get_configuration_template(
    template_name: str,
    api_key: str = Depends(verify_api_key)
):
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
    request: TemplateBasedConfigRequest,
    api_key: str = Depends(verify_api_key)
) -> ValidationResponse:
    """
    Validate configuration based on a template with optional overrides.
    
    Supports both authenticated and unauthenticated access. When authenticated,
    additional metadata may be included in the response.
    
    Args:
        request: Template name and optional configuration overrides
        api_key: Optional API key for authenticated access
        
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
    request: CustomConfigRequest,
    api_key: str = Depends(verify_api_key)
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
