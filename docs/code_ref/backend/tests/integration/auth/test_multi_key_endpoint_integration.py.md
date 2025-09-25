---
sidebar_label: test_multi_key_endpoint_integration
---

# Integration tests for multi-key authentication with real protected endpoints.

  file_path: `backend/tests/integration/auth/test_multi_key_endpoint_integration.py`

Tests multiple API key authentication scenarios using actual API endpoints
to validate key management and endpoint protection integration.

Seam Under Test:
    Protected Endpoints → FastAPI Dependencies → APIKeyAuth → Environment Variables

Critical Paths:
    - Primary API_KEY grants access to all protected endpoints
    - ADDITIONAL_API_KEYS work identically to primary key
    - Invalid keys are rejected with proper HTTP error responses

## TestMultiKeyEndpointIntegration

Integration tests for multi-key authentication with real endpoints.

Seam Under Test:
    HTTP Request → Protected Endpoints → FastAPI DI → APIKeyAuth → Key Validation → Response
    
Critical Paths:
    - Multiple API keys provide equivalent access to protected resources
    - Key format and validation work consistently across different keys
    - Error handling provides clear feedback for invalid authentication attempts

### test_primary_api_key_grants_access_to_auth_status_endpoint()

```python
def test_primary_api_key_grants_access_to_auth_status_endpoint(self, client, production_environment):
```

Test primary API_KEY provides access to protected auth status endpoint.

Integration Scope:
    Tests complete flow from HTTP request through primary key validation
    to successful endpoint response generation.
    
Business Impact:
    Ensures users with primary API key can access all protected
    functionality including system status monitoring.
    
Test Strategy:
    - Configure primary API key in environment
    - Make authenticated request to auth status endpoint
    - Verify successful authentication and proper response content
    
Success Criteria:
    - Returns 200 status code for successful authentication
    - Response includes authenticated user context
    - API key prefix matches primary key (truncated for security)
    - Endpoint functions normally with primary key authentication

### test_additional_api_keys_provide_equivalent_access()

```python
def test_additional_api_keys_provide_equivalent_access(self, client, multiple_api_keys_environment):
```

Test ADDITIONAL_API_KEYS work identically to primary key.

Integration Scope:
    Tests multi-key configuration loading, validation, and endpoint
    access using secondary keys from ADDITIONAL_API_KEYS.
    
Business Impact:
    Enables organizations to distribute multiple API keys while
    maintaining equivalent access rights and functionality.
    
Test Strategy:
    - Configure multiple keys via ADDITIONAL_API_KEYS
    - Test each additional key provides identical access
    - Verify response content consistent across all keys
    
Success Criteria:
    - Secondary keys return 200 status identical to primary
    - Response format consistent regardless of key used
    - All additional keys provide equivalent endpoint access
    - Key prefixes correctly identify the key used

### test_whitespace_handling_in_additional_api_keys()

```python
def test_whitespace_handling_in_additional_api_keys(self, client, multiple_api_keys_environment):
```

Test API keys with whitespace are handled correctly.

Integration Scope:
    Tests environment variable parsing, whitespace trimming,
    and key validation for keys with formatting variations.
    
Business Impact:
    Ensures configuration flexibility and prevents authentication
    failures due to formatting issues in environment variables.
    
Test Strategy:
    - Configure ADDITIONAL_API_KEYS with leading/trailing whitespace
    - Attempt authentication with keys as they appear in config
    - Verify whitespace is properly handled during validation
    
Success Criteria:
    - Keys work regardless of whitespace in configuration
    - Authentication succeeds using exact key values
    - No whitespace-related authentication failures
    - Configuration parsing handles various formatting correctly

### test_invalid_api_key_format_rejected_with_structured_error()

```python
def test_invalid_api_key_format_rejected_with_structured_error(self, client, production_environment):
```

Test invalid API key format returns proper structured error response.

Integration Scope:
    Tests invalid key handling through authentication validation,
    exception generation, and HTTP error response formatting.
    
Business Impact:
    Provides clear error messages to developers debugging
    authentication issues while maintaining security.
    
Test Strategy:
    - Attempt authentication with malformed API key
    - Verify proper 401 response with detailed error context
    - Ensure error message aids debugging without exposing secrets
    
Success Criteria:
    - Returns 401 Unauthorized for invalid key format
    - Error response includes specific validation failure reason
    - Response context includes environment and authentication method
    - No sensitive system information exposed in error

### test_unknown_valid_format_key_rejected_with_debugging_context()

```python
def test_unknown_valid_format_key_rejected_with_debugging_context(self, client, production_environment):
```

Test unknown but valid-format key provides helpful debugging context.

Integration Scope:
    Tests key validation against configured key set with proper
    error context generation for valid-format unknown keys.
    
Business Impact:
    Helps developers distinguish between format errors and
    configuration errors when debugging authentication issues.
    
Test Strategy:
    - Use valid key format that's not in configured key set
    - Verify proper error response with debugging information
    - Ensure error context helps identify configuration issues
    
Success Criteria:
    - Returns 401 for unknown but valid-format key
    - Error message clearly indicates key not found (vs format error)
    - Debugging context includes relevant authentication metadata
    - Response helps distinguish config vs format issues

### test_x_api_key_header_authentication_works_equivalently()

```python
def test_x_api_key_header_authentication_works_equivalently(self, client, production_environment):
```

Test X-API-Key header provides equivalent authentication to Bearer token.

Integration Scope:
    Tests alternative authentication header handling through
    FastAPI security schemes and authentication dependency validation.
    
Business Impact:
    Provides authentication flexibility for clients that prefer
    X-API-Key header over Bearer token authentication.
    
Test Strategy:
    - Configure valid API key in environment
    - Authenticate using X-API-Key header instead of Authorization
    - Verify equivalent functionality and response format
    
Success Criteria:
    - X-API-Key header provides identical authentication results
    - Response format consistent between authentication methods
    - Both header types provide equivalent endpoint access
    - Authentication metadata correctly identifies header method used
