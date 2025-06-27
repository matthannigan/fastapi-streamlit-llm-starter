"""Resilience configuration security validation REST API endpoints.

This module provides specialized REST API endpoints for security-focused
validation of resilience configurations. It implements comprehensive security
checks including field whitelisting, rate limiting, content filtering, and
threat detection to ensure configuration safety and system security.

The module offers multi-layered security validation with configurable limits,
real-time rate limiting monitoring, and detailed security policy enforcement.
All endpoints provide extensive security analysis and protection against
configuration-based attacks and system abuse.

Endpoints:
    POST /resilience/validate/security: Comprehensive security validation with rate limiting
    GET /resilience/validate/security-config: Security configuration and limits information
    POST /resilience/validate/field-whitelist: Field whitelist validation and analysis
    GET /resilience/validate/rate-limit-status: Current rate limiting status and quotas

Security Validation Features:
    - Multi-layered security checks with threat detection
    - Field whitelisting with type and constraint validation
    - Content filtering for malicious patterns and payloads
    - Rate limiting with client-based quota management
    - Size limits and nesting depth protection
    - Unicode validation and character encoding checks

Field Whitelisting:
    - Comprehensive field validation against security whitelist
    - Type checking and constraint enforcement for allowed fields
    - Detailed analysis of field compliance and violations
    - Security recommendations for non-whitelisted fields
    - Configuration sanitization and cleanup suggestions

Rate Limiting:
    - Client-based rate limiting with configurable quotas
    - Real-time rate limit monitoring and status reporting
    - Quota exhaustion detection and prevention
    - Time-based rate limit reset mechanisms
    - Security event logging for rate limit violations

Content Security:
    - Malicious pattern detection and filtering
    - Injection attack prevention mechanisms
    - Size-based security limits and enforcement
    - Nesting depth protection against denial-of-service attacks
    - Unicode and encoding validation for security compliance

Dependencies:
    - ConfigValidator: Core security validation engine with threat detection
    - SecurityConfig: Configurable security policies and limits
    - Security: API key verification for all security endpoints
    - RateLimiter: Client-based rate limiting and quota management

Authentication:
    All security validation endpoints require API key authentication to
    ensure secure access and prevent unauthorized security analysis.

Example:
    Comprehensive security validation:
        POST /api/internal/resilience/validate/security
        {
            "configuration": {
                "retry_attempts": 3,
                "circuit_breaker_threshold": 5
            }
        }
        
    Field whitelist validation:
        POST /api/internal/resilience/validate/field-whitelist
        {
            "configuration": {
                "retry_attempts": 3,
                "invalid_field": "value"
            }
        }
        
    Rate limit status check:
        GET /api/internal/resilience/validate/rate-limit-status?client_ip=192.168.1.1

Note:
    Security validation includes comprehensive threat detection and should
    be used for all production configurations. Rate limiting helps prevent
    abuse and ensures fair access to validation services across all clients.
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
    SecurityValidationRequest,
    ValidationRequest
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resilience", tags=["resilience"])

@router.post("/validate/security")
async def validate_configuration_security(
    request: SecurityValidationRequest,
    client_ip: str = "unknown",
    api_key: str = Depends(verify_api_key)
):
    """
    Validate configuration with enhanced security checks.
    
    Args:
        request: Configuration validation request
        client_ip: Client IP address for rate limiting
    
    Returns:
        Comprehensive security validation results
    """
    try:
        # Use client IP as identifier for rate limiting
        result = config_validator.validate_with_security_checks(
            request.configuration, 
            client_identifier=client_ip
        )
        
        return {
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "suggestions": result.suggestions,
            "security_info": {
                "size_bytes": len(str(request.configuration)),
                "max_size_bytes": 4096,
                "field_count": len(request.configuration) if isinstance(request.configuration, dict) else 0,
                "validation_timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate configuration security: {str(e)}"
        )


@router.get("/validate/security-config")
async def get_security_configuration(
    api_key: str = Depends(verify_api_key)
):
    """
    Get current security validation configuration and limits.
    
    Returns:
        Security validation configuration details
    """
    try:
        from app.infrastructure.resilience.config_validator import SECURITY_CONFIG
        
        return {
            "security_limits": {
                "max_config_size_bytes": SECURITY_CONFIG["max_config_size"],
                "max_string_length": SECURITY_CONFIG["max_string_length"],
                "max_array_items": SECURITY_CONFIG["max_array_items"],
                "max_object_properties": SECURITY_CONFIG["max_object_properties"],
                "max_nesting_depth": SECURITY_CONFIG["max_nesting_depth"]
            },
            "rate_limiting": SECURITY_CONFIG["rate_limiting"],
            "content_filtering": SECURITY_CONFIG["content_filtering"],
            "allowed_fields": list(SECURITY_CONFIG["allowed_field_whitelist"].keys()),
            "forbidden_pattern_count": len(SECURITY_CONFIG["forbidden_patterns"]),
            "validation_features": [
                "Size limits",
                "Field whitelisting", 
                "Content filtering",
                "Rate limiting",
                "Unicode validation",
                "Nesting depth limits",
                "Pattern detection"
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security configuration: {str(e)}"
        )


@router.post("/validate/field-whitelist")
async def validate_against_field_whitelist(
    request: ValidationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Validate configuration specifically against field whitelist.
    
    Args:
        request: Configuration validation request
    
    Returns:
        Field whitelist validation results
    """
    try:
        if not isinstance(request.configuration, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configuration must be a JSON object for field validation"
            )
        
        # Perform only field whitelist validation
        errors, suggestions = config_validator._validate_field_whitelist(request.configuration)
        
        from app.infrastructure.resilience.config_validator import SECURITY_CONFIG
        whitelist = SECURITY_CONFIG["allowed_field_whitelist"]
        
        field_analysis = {}
        for field_name, field_value in request.configuration.items():
            if field_name in whitelist:
                field_spec = whitelist[field_name]
                field_analysis[field_name] = {
                    "allowed": True,
                    "type": field_spec["type"],
                    "constraints": {k: v for k, v in field_spec.items() if k != "type"},
                    "current_value": field_value,
                    "current_type": type(field_value).__name__
                }
            else:
                field_analysis[field_name] = {
                    "allowed": False,
                    "current_value": field_value,
                    "current_type": type(field_value).__name__
                }
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "suggestions": suggestions,
            "field_analysis": field_analysis,
            "allowed_fields": list(whitelist.keys()),
            "validation_timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate field whitelist: {str(e)}"
        )
    

@router.get("/validate/rate-limit-status")
async def get_validation_rate_limit_status(
    client_ip: str = "unknown",
    api_key: str = Depends(verify_api_key)
):
    """
    Get current rate limit status for validation requests.
    
    Args:
        client_ip: Client IP address
    
    Returns:
        Current rate limit status and quotas
    """
    try:
        status_info = config_validator.get_rate_limit_info(client_ip)
        
        return {
            "client_identifier": client_ip,
            "current_status": status_info,
            "limits": {
                "max_validations_per_minute": 60,
                "max_validations_per_hour": 1000,
                "cooldown_seconds": 1
            },
            "check_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit status: {str(e)}"
        )
