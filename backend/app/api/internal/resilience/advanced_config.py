"""Advanced resilience configuration validation REST API endpoints.

This module provides sophisticated REST API endpoints for validating custom
resilience configurations with multiple validation strategies and security
levels. It supports standard validation, enhanced security validation, and
direct JSON string validation, offering comprehensive error detection and
configuration optimization suggestions.

The module implements multi-layered validation approaches that ensure
configuration correctness, security compliance, and performance optimization.
Each validation endpoint provides detailed feedback including errors, warnings,
and actionable suggestions for configuration improvements.

Endpoints:
    POST /resilience/validate: Standard custom configuration validation
    POST /resilience/validate-secure: Enhanced security validation with additional checks
    POST /resilience/validate-json: Direct JSON string configuration validation

Validation Features:
    - Multi-tier validation with standard and enhanced security modes
    - Comprehensive error detection and reporting
    - Security-focused validation with threat detection
    - JSON string parsing and validation capabilities
    - Detailed warning systems for potential issues
    - Actionable suggestions for configuration optimization

Standard Validation:
    - Schema compliance checking against resilience configuration standards
    - Parameter range validation and constraint verification
    - Logical consistency checks for configuration coherence
    - Performance impact assessment and recommendations
    - Best practice compliance verification

Enhanced Security Validation:
    - Advanced security threat detection and prevention
    - Input sanitization and injection attack prevention
    - Configuration tampering detection mechanisms
    - Security policy compliance verification
    - Risk assessment for configuration parameters

JSON Validation:
    - Direct JSON string parsing and validation
    - Syntax error detection and reporting
    - Format compliance checking
    - Type validation for configuration parameters
    - Structure verification against expected schemas

Dependencies:
    - ConfigValidator: Core validation engine with multiple validation strategies
    - Security: API key verification for all validation endpoints
    - Pydantic Models: Structured request/response validation and documentation
    - ValidationResult: Comprehensive validation result aggregation

Authentication:
    All validation endpoints require API key authentication to ensure
    secure access to validation services and protect against abuse.

Example:
    Standard configuration validation:
        POST /api/internal/resilience/validate
        {
            "configuration": {
                "retry_attempts": 3,
                "circuit_breaker_threshold": 5,
                "timeout_seconds": 30
            }
        }
        
    Enhanced security validation:
        POST /api/internal/resilience/validate-secure
        {
            "configuration": {
                "retry_attempts": 3,
                "circuit_breaker_threshold": 5
            }
        }

Note:
    Enhanced security validation includes additional checks for potential
    security vulnerabilities and should be used for production configurations.
    All validation endpoints provide comprehensive feedback for configuration
    improvement and optimization.
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
    ValidationResponse,
    CustomConfigRequest
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resilience", tags=["resilience"])

@router.post("/validate", response_model=ValidationResponse)
async def validate_custom_config(
    request: CustomConfigRequest,
    api_key: str = Depends(verify_api_key)
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
    request: CustomConfigRequest,
    api_key: str = Depends(verify_api_key)
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
    json_config: str = Query(..., description="JSON string of custom configuration"),
    api_key: str = Depends(verify_api_key)
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

