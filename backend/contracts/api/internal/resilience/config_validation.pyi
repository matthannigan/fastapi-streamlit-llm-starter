"""
Infrastructure Service: Resilience Configuration Validation API

🏗️ **STABLE API** - Changes affect all template users  
📋 **Minimum test coverage**: 90%  
🔧 **Configuration-driven behavior**

This module provides sophisticated REST API endpoints for validating custom
resilience configurations with multiple validation strategies and security
levels. It supports standard validation, enhanced security validation, and
direct JSON string validation, offering comprehensive error detection and
configuration optimization suggestions.

The module consolidates all configuration validation functionality into a
single, cohesive API that ensures configuration correctness, security
compliance, and performance optimization. Each validation endpoint provides
detailed feedback including errors, warnings, and actionable suggestions
for configuration improvements.

Endpoints:
    POST /internal/resilience/config/validate: Standard custom configuration validation
    POST /internal/resilience/config/validate-secure: Enhanced security validation with security metadata
    POST /internal/resilience/config/validate-json: Direct JSON string configuration validation
    POST /internal/resilience/config/validate/field-whitelist: Validate configuration against field whitelist
    GET  /internal/resilience/config/validate/security-config: Get security validation configuration and limits
    GET  /internal/resilience/config/validate/rate-limit-status: Get current rate limiting status and quotas

Validation Features:
    - Multi-tier validation with standard and enhanced security modes
    - Comprehensive error detection and reporting
    - Security-focused validation with threat detection and rate limiting
    - JSON string parsing and validation capabilities
    - Field whitelisting with detailed analysis and recommendations
    - Detailed warning systems for potential issues
    - Actionable suggestions for configuration optimization
    - Security metadata including size limits and validation timestamps

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
    - Rate limiting with client IP tracking
    - Security metadata in response for audit trails

Field Whitelist Validation:
    - Comprehensive field validation against security whitelist
    - Type checking and constraint enforcement for allowed fields
    - Detailed field-by-field analysis with compliance status
    - Security recommendations for non-whitelisted fields
    - Configuration sanitization and cleanup suggestions

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
        POST /internal/resilience/config/validate
        {
            "configuration": {
                "retry_attempts": 3,
                "circuit_breaker_threshold": 5,
                "timeout_seconds": 30
            }
        }
        
    Enhanced security validation with metadata:
        POST /internal/resilience/config/validate-secure
        {
            "configuration": {
                "retry_attempts": 3,
                "circuit_breaker_threshold": 5
            }
        }
        
    Field whitelist validation:
        POST /internal/resilience/config/validate/field-whitelist
        {
            "configuration": {
                "retry_attempts": 3,
                "invalid_field": "value"
            }
        }

Note:
    Enhanced security validation includes additional checks for potential
    security vulnerabilities and should be used for production configurations.
    All validation endpoints provide comprehensive feedback for configuration
    improvement and optimization. Security validation includes rate limiting
    and detailed security metadata for compliance and audit purposes.
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
from app.api.internal.resilience.models import ValidationRequest, ValidationResponse, CustomConfigRequest

router = APIRouter(prefix='/resilience/config', tags=['Resilience Configuration'])


@router.post('/validate', response_model=ValidationResponse)
async def validate_custom_config(request: CustomConfigRequest, api_key: str = Depends(verify_api_key)) -> ValidationResponse:
    """
    Validate a custom resilience configuration against standard requirements.
    
    This endpoint performs comprehensive validation of custom resilience configurations,
    checking for correctness, best practices, and potential issues with detailed
    feedback and suggestions for improvement.
    
    Args:
        request: Custom configuration validation request containing the configuration
                to validate
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        ValidationResponse: Validation results containing:
            - is_valid: Boolean indicating if configuration is valid
            - errors: List of validation errors that must be fixed
            - warnings: List of warnings about potential issues
            - suggestions: List of suggestions for improvement
            
    Raises:
        HTTPException: 500 Internal Server Error if validation process fails
        
    Example:
        >>> request = CustomConfigRequest(
        ...     configuration={
        ...         "retry_attempts": 3,
        ...         "circuit_breaker_threshold": 5
        ...     }
        ... )
        >>> response = await validate_custom_config(request)
        >>> ValidationResponse(
        ...     is_valid=True,
        ...     errors=[],
        ...     warnings=["Consider adding timeout configuration"],
        ...     suggestions=["Use exponential backoff for retries"]
        ... )
    """
    ...


@router.post('/validate-secure', response_model=ValidationResponse)
async def validate_custom_config_with_security(request: CustomConfigRequest, client_ip: str = 'unknown', api_key: str = Depends(verify_api_key)) -> ValidationResponse:
    """
    Validate custom resilience configuration with enhanced security checks.
    
    This endpoint performs comprehensive validation with additional security-focused
    checks including threat detection, rate limiting, and security metadata collection.
    Provides enhanced protection against malicious configurations and abuse.
    
    Args:
        request: Custom configuration validation request containing the configuration
                to validate with security checks
        client_ip: Client IP address for rate limiting and security tracking
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        ValidationResponse: Enhanced validation results containing:
            - is_valid: Boolean indicating if configuration is valid
            - errors: List of validation errors that must be fixed
            - warnings: List of warnings about potential issues
            - suggestions: List of suggestions for improvement
            - security_info: Additional security metadata including:
                - size_bytes: Configuration size in bytes
                - max_size_bytes: Maximum allowed size
                - field_count: Number of configuration fields
                - validation_timestamp: Security validation timestamp
            
    Raises:
        HTTPException: 500 Internal Server Error if security validation fails
        
    Example:
        >>> request = CustomConfigRequest(
        ...     configuration={"retry_attempts": 3, "circuit_breaker_threshold": 5}
        ... )
        >>> response = await validate_custom_config_with_security(request, "192.168.1.1")
        >>> ValidationResponse(
        ...     is_valid=True,
        ...     errors=[],
        ...     warnings=[],
        ...     suggestions=["Consider timeout configuration"],
        ...     security_info={
        ...         "size_bytes": 64,
        ...         "field_count": 2,
        ...         "validation_timestamp": "2023-12-01T10:30:00Z"
        ...     }
        ... )
    """
    ...


@router.post('/validate-json', response_model=ValidationResponse)
async def validate_json_config(json_config: str = Query(..., description='JSON string of custom configuration'), api_key: str = Depends(verify_api_key)) -> ValidationResponse:
    """
    Validate a resilience configuration provided as a JSON string.
    
    This endpoint accepts configurations as JSON strings and performs comprehensive
    validation including JSON parsing, schema validation, and configuration
    correctness checks with detailed error reporting.
    
    Args:
        json_config: JSON string containing the resilience configuration to validate
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        ValidationResponse: Validation results containing:
            - is_valid: Boolean indicating if the JSON configuration is valid
            - errors: List of validation errors including JSON parsing errors
            - warnings: List of warnings about potential configuration issues
            - suggestions: List of suggestions for configuration improvement
            
    Raises:
        HTTPException: 500 Internal Server Error if validation process fails
        
    Example:
        >>> json_config = '{"retry_attempts": 3, "circuit_breaker_threshold": 5}'
        >>> response = await validate_json_config(json_config)
        >>> ValidationResponse(
        ...     is_valid=True,
        ...     errors=[],
        ...     warnings=["Consider adding timeout configuration"],
        ...     suggestions=["Add strategy specification for completeness"]
        ... )
        
        >>> invalid_json = '{"retry_attempts": "invalid"}'
        >>> response = await validate_json_config(invalid_json)
        >>> ValidationResponse(
        ...     is_valid=False,
        ...     errors=["retry_attempts must be a number, not string"],
        ...     warnings=[],
        ...     suggestions=["Use integer values for retry_attempts"]
        ... )
    """
    ...


@router.post('/validate/field-whitelist')
async def validate_against_field_whitelist(request: ValidationRequest, api_key: str = Depends(verify_api_key)):
    """
    Validate configuration against security field whitelist with detailed analysis.
    
    This endpoint performs field-by-field validation against a security whitelist,
    providing detailed analysis of allowed vs. disallowed fields, type checking,
    and constraint validation for enhanced security compliance.
    
    Args:
        request: Validation request containing the configuration to validate
                against the field whitelist
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Detailed field whitelist validation results containing:
            - is_valid: Boolean indicating if all fields pass whitelist validation
            - errors: List of field validation errors
            - suggestions: List of suggestions for non-whitelisted fields
            - field_analysis: Field-by-field analysis including:
                - allowed: Whether each field is in the whitelist
                - type: Expected field type and constraints
                - current_value: Current field value
                - current_type: Current field type
            - allowed_fields: List of all whitelisted field names
            - validation_timestamp: Validation timestamp
            
    Raises:
        HTTPException: 400 Bad Request if configuration is not a JSON object
        HTTPException: 500 Internal Server Error if field validation fails
        
    Example:
        >>> request = ValidationRequest(
        ...     configuration={
        ...         "retry_attempts": 3,
        ...         "invalid_field": "not_allowed"
        ...     }
        ... )
        >>> response = await validate_against_field_whitelist(request)
        >>> {
        ...     "is_valid": False,
        ...     "errors": ["Field 'invalid_field' is not in the allowed whitelist"],
        ...     "field_analysis": {
        ...         "retry_attempts": {"allowed": True, "type": "int"},
        ...         "invalid_field": {"allowed": False, "current_value": "not_allowed"}
        ...     },
        ...     "allowed_fields": ["retry_attempts", "circuit_breaker_threshold", ...]
        ... }
    """
    ...


@router.get('/validate/security-config')
async def get_security_configuration(api_key: str = Depends(verify_api_key)):
    """
    Get current security validation configuration and operational limits.
    
    This endpoint provides comprehensive information about the security validation
    system configuration, including limits, constraints, and security features
    that are applied during configuration validation.
    
    Args:
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Security configuration information containing:
            - security_limits: Configuration size and complexity limits including:
                - max_config_size_bytes: Maximum configuration size
                - max_string_length: Maximum string field length
                - max_array_items: Maximum array size
                - max_object_properties: Maximum object property count
                - max_nesting_depth: Maximum JSON nesting depth
            - rate_limiting: Rate limiting configuration
            - content_filtering: Content filtering settings
            - allowed_fields: List of whitelisted field names
            - forbidden_pattern_count: Number of forbidden patterns detected
            - validation_features: List of enabled security features
            
    Raises:
        HTTPException: 500 Internal Server Error if security configuration retrieval fails
        
    Example:
        >>> response = await get_security_configuration()
        >>> {
        ...     "security_limits": {
        ...         "max_config_size_bytes": 4096,
        ...         "max_string_length": 256,
        ...         "max_nesting_depth": 10
        ...     },
        ...     "allowed_fields": ["retry_attempts", "circuit_breaker_threshold"],
        ...     "validation_features": ["Size limits", "Field whitelisting", ...]
        ... }
    """
    ...


@router.get('/validate/rate-limit-status')
async def get_validation_rate_limit_status(client_ip: str = 'unknown', api_key: str = Depends(verify_api_key)):
    """
    Get current rate limiting status and quotas for validation requests.
    
    This endpoint provides real-time information about rate limiting status,
    including current usage, remaining quotas, and rate limit configuration
    for validation operations from a specific client.
    
    Args:
        client_ip: Client IP address for rate limit tracking (default: "unknown")
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Rate limit status information containing:
            - client_identifier: Client IP address used for tracking
            - current_status: Current rate limit status and remaining quotas
            - limits: Rate limiting configuration including:
                - max_validations_per_minute: Maximum validations per minute
                - max_validations_per_hour: Maximum validations per hour
                - cooldown_seconds: Cooldown period between requests
            - check_timestamp: Current timestamp of the status check
            
    Raises:
        HTTPException: 500 Internal Server Error if rate limit status retrieval fails
        
    Example:
        >>> response = await get_validation_rate_limit_status("192.168.1.1")
        >>> {
        ...     "client_identifier": "192.168.1.1",
        ...     "current_status": {
        ...         "requests_this_minute": 15,
        ...         "requests_this_hour": 450,
        ...         "remaining_minute": 45,
        ...         "remaining_hour": 550
        ...     },
        ...     "limits": {
        ...         "max_validations_per_minute": 60,
        ...         "max_validations_per_hour": 1000,
        ...         "cooldown_seconds": 1
        ...     },
        ...     "check_timestamp": "2023-12-01T10:30:00Z"
        ... }
    """
    ...
