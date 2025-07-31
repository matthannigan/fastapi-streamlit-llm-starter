---
sidebar_label: config_validation
---

# Infrastructure Service: Resilience Configuration Validation API

  file_path: `backend/app/api/internal/resilience/config_validation.py`

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

## Endpoints

POST /internal/resilience/config/validate: Standard custom configuration validation
POST /internal/resilience/config/validate-secure: Enhanced security validation with security metadata
POST /internal/resilience/config/validate-json: Direct JSON string configuration validation
POST /internal/resilience/config/validate/field-whitelist: Validate configuration against field whitelist
GET  /internal/resilience/config/validate/security-config: Get security validation configuration and limits
GET  /internal/resilience/config/validate/rate-limit-status: Get current rate limiting status and quotas

## Validation Features

- Multi-tier validation with standard and enhanced security modes
- Comprehensive error detection and reporting
- Security-focused validation with threat detection and rate limiting
- JSON string parsing and validation capabilities
- Field whitelisting with detailed analysis and recommendations
- Detailed warning systems for potential issues
- Actionable suggestions for configuration optimization
- Security metadata including size limits and validation timestamps

## Standard Validation

- Schema compliance checking against resilience configuration standards
- Parameter range validation and constraint verification
- Logical consistency checks for configuration coherence
- Performance impact assessment and recommendations
- Best practice compliance verification

## Enhanced Security Validation

- Advanced security threat detection and prevention
- Input sanitization and injection attack prevention
- Configuration tampering detection mechanisms
- Security policy compliance verification
- Risk assessment for configuration parameters
- Rate limiting with client IP tracking
- Security metadata in response for audit trails

## Field Whitelist Validation

- Comprehensive field validation against security whitelist
- Type checking and constraint enforcement for allowed fields
- Detailed field-by-field analysis with compliance status
- Security recommendations for non-whitelisted fields
- Configuration sanitization and cleanup suggestions

## Dependencies

- ConfigValidator: Core validation engine with multiple validation strategies
- Security: API key verification for all validation endpoints
- Pydantic Models: Structured request/response validation and documentation
- ValidationResult: Comprehensive validation result aggregation

## Authentication

All validation endpoints require API key authentication to ensure
secure access to validation services and protect against abuse.

## Example

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

## Note

Enhanced security validation includes additional checks for potential
security vulnerabilities and should be used for production configurations.
All validation endpoints provide comprehensive feedback for configuration
improvement and optimization. Security validation includes rate limiting
and detailed security metadata for compliance and audit purposes.
