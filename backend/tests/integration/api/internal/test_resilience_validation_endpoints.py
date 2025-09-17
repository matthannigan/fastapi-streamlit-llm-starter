"""
Integration tests for resilience security validation API endpoints.

Tests the REST API endpoints for security validation including rate limiting,
field whitelisting, and comprehensive security checks.
"""

import pytest
import json
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app


class TestSecurityValidationEndpoints:
    """Test security validation API endpoints."""
    
    @pytest.fixture(autouse=True)
    def reset_rate_limiter(self):
        """Reset rate limiter before each test."""
        from app.infrastructure.resilience.config_validator import config_validator
        config_validator.reset_rate_limiter()
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_security_validation_endpoint_unauthorized(self, client):
        """Test security validation endpoint without authentication."""
        config = {"retry_attempts": 3}
        try:
            response = client.post(
                "/internal/resilience/config/validate-secure",
                json={"configuration": config}
            )
            assert response.status_code == 401
        except Exception as e:
            # If exception is thrown, it should be an authentication error
            assert "AuthenticationError" in str(type(e)) or "API key required" in str(e)
    
    def test_security_validation_endpoint_valid_config(self, client, auth_headers):
        """Test security validation with valid configuration."""
        config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "default_strategy": "balanced"
        }
        
        response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": config},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_valid" in data
        assert "errors" in data
        assert "warnings" in data
        assert "suggestions" in data
        assert "security_info" in data
        
        assert data["is_valid"] is True
        assert isinstance(data["errors"], list)
        assert isinstance(data["warnings"], list)
        assert isinstance(data["suggestions"], list)
        
        security_info = data["security_info"]
        assert "size_bytes" in security_info
        assert "max_size_bytes" in security_info
        assert "field_count" in security_info
        assert "validation_timestamp" in security_info
    
    def test_security_validation_endpoint_invalid_config(self, client, auth_headers):
        """Test security validation with invalid configuration."""
        config = {
            "retry_attempts": "not_a_number",  # Invalid type
            "malicious_field": "<script>alert('xss')</script>",  # Forbidden pattern + unknown field
            "circuit_breaker_threshold": 50  # Out of range
        }
        
        response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": config},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
        
        # Should detect multiple types of issues
        error_text = " ".join(data["errors"]).lower()
        assert "whitelist" in error_text or "forbidden" in error_text or "pattern" in error_text
    
    def test_security_validation_large_config(self, client, auth_headers):
        """Test security validation with oversized configuration."""
        # Create a config that exceeds size limits
        large_value = "x" * 5000  # Should exceed the 4KB limit when JSON serialized
        config = {"test_field": large_value}
        
        response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": config},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert any("too large" in error.lower() or "configuration too large" in error.lower() for error in data["errors"])
    
    def test_rate_limit_status_endpoint(self, client, auth_headers):
        """Test rate limit status endpoint."""
        response = client.get(
            "/internal/resilience/config/validate/rate-limit-status?client_ip=test-client",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "client_identifier" in data
        assert "current_status" in data
        assert "limits" in data
        assert "check_timestamp" in data
        
        current_status = data["current_status"]
        assert "requests_last_minute" in current_status
        assert "requests_last_hour" in current_status
        assert "max_per_minute" in current_status
        assert "max_per_hour" in current_status
        assert "cooldown_remaining" in current_status
        
        limits = data["limits"]
        assert "max_validations_per_minute" in limits
        assert "max_validations_per_hour" in limits
        assert "cooldown_seconds" in limits
    
    def test_security_config_endpoint(self, client, auth_headers):
        """Test security configuration endpoint."""
        response = client.get(
            "/internal/resilience/config/validate/security-config",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "security_limits" in data
        assert "rate_limiting" in data
        assert "content_filtering" in data
        assert "allowed_fields" in data
        assert "forbidden_pattern_count" in data
        assert "validation_features" in data
        
        security_limits = data["security_limits"]
        assert "max_config_size_bytes" in security_limits
        assert "max_string_length" in security_limits
        assert "max_array_items" in security_limits
        assert "max_object_properties" in security_limits
        assert "max_nesting_depth" in security_limits
        
        assert isinstance(data["allowed_fields"], list)
        assert len(data["allowed_fields"]) > 0
        assert isinstance(data["validation_features"], list)
        assert len(data["validation_features"]) > 0
    
    def test_field_whitelist_validation_endpoint(self, client, auth_headers):
        """Test field whitelist validation endpoint."""
        config = {
            "retry_attempts": 3,  # Valid field
            "malicious_field": "bad_value",  # Invalid field
            "circuit_breaker_threshold": 5  # Valid field
        }
        
        response = client.post(
            "/internal/resilience/config/validate/field-whitelist",
            json={"configuration": config},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_valid" in data
        assert "errors" in data
        assert "suggestions" in data
        assert "field_analysis" in data
        assert "allowed_fields" in data
        assert "validation_timestamp" in data
        
        assert data["is_valid"] is False  # Should fail due to malicious_field
        assert len(data["errors"]) > 0
        
        field_analysis = data["field_analysis"]
        assert "retry_attempts" in field_analysis
        assert "malicious_field" in field_analysis
        assert "circuit_breaker_threshold" in field_analysis
        
        # Valid fields should be marked as allowed
        assert field_analysis["retry_attempts"]["allowed"] is True
        assert field_analysis["circuit_breaker_threshold"]["allowed"] is True
        
        # Invalid field should be marked as not allowed
        assert field_analysis["malicious_field"]["allowed"] is False
        
        assert isinstance(data["allowed_fields"], list)
        assert len(data["allowed_fields"]) > 0
    
    def test_field_whitelist_validation_non_object(self, client, auth_headers):
        """Test field whitelist validation with non-object configuration."""
        response = client.post(
            "/internal/resilience/config/validate/field-whitelist",
            json={"configuration": "not_an_object"},
            headers=auth_headers
        )
        
        assert response.status_code == 422  # FastAPI validation error for invalid input type
        response_detail = response.json()["detail"]
        # The error should indicate that configuration should be a dictionary
        assert any("valid dictionary" in str(error).lower() or "dict_type" in str(error) for error in response_detail)
    
    def test_rate_limiting_integration(self, client, auth_headers):
        """Test that rate limiting works across validation endpoints."""
        config = {"retry_attempts": 3}
        
        # Clear any existing rate limit state by using unique client IP
        unique_client_ip = f"test-client-{int(time.time())}"
        
        # First request should succeed
        response1 = client.post(
            f"/internal/resilience/config/validate-secure?client_ip={unique_client_ip}",
            json={"configuration": config},
            headers=auth_headers
        )
        assert response1.status_code == 200
        assert response1.json()["is_valid"] is True
        
        # Immediate second request should be rate limited
        response2 = client.post(
            f"/internal/resilience/config/validate-secure?client_ip={unique_client_ip}",
            json={"configuration": config},
            headers=auth_headers
        )
        assert response2.status_code == 200
        assert response2.json()["is_valid"] is False
        
        # Should contain rate limit error
        errors = response2.json()["errors"]
        assert any("rate limit" in error.lower() for error in errors)
    
    def test_security_validation_endpoint_error_handling(self, client, auth_headers):
        """Test error handling in security validation endpoint."""
        # Test with malformed JSON by sending invalid configuration
        response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": None},  # Invalid configuration type
            headers=auth_headers
        )
        
        # The endpoint may return either 422 (validation error) or 200 (business logic error)
        assert response.status_code in [200, 422]
        data = response.json()
        
        if response.status_code == 200:
            assert data["is_valid"] is False
            assert any("must be a JSON object" in error for error in data["errors"])
        else:  # 422 case
            assert "detail" in data  # FastAPI validation error format
    
    def test_all_security_endpoints_require_authentication(self, client):
        """Test that all security validation endpoints require authentication."""
        security_endpoints = [
            ("/internal/resilience/config/validate-secure", "POST", {"configuration": {}}),
            ("/internal/resilience/config/validate/rate-limit-status", "GET", None),
            ("/internal/resilience/config/validate/security-config", "GET", None),
            ("/internal/resilience/config/validate/field-whitelist", "POST", {"configuration": {}}),
        ]
        
        for endpoint, method, json_data in security_endpoints:
            try:
                if method == "GET":
                    response = client.get(endpoint)
                else:
                    response = client.post(endpoint, json=json_data)
                
                assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"
            except Exception as e:
                # If exception is thrown, it should be an authentication error
                assert "AuthenticationError" in str(type(e)) or "API key required" in str(e), f"Endpoint {endpoint} should require authentication"
    
    def test_security_validation_performance(self, client, auth_headers):
        """Test that security validation endpoints respond quickly."""
        config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "recovery_timeout": 60,
            "default_strategy": "balanced"
        }
        
        start_time = time.perf_counter()
        response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": config},
            headers=auth_headers
        )
        end_time = time.perf_counter()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond in less than 1 second
    
    def test_field_analysis_details(self, client, auth_headers):
        """Test detailed field analysis in whitelist validation."""
        config = {
            "retry_attempts": 3,
            "exponential_multiplier": 1.5,
            "jitter_enabled": True,
            "default_strategy": "balanced"
        }
        
        response = client.post(
            "/internal/resilience/config/validate/field-whitelist",
            json={"configuration": config},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        field_analysis = data["field_analysis"]
        
        # Check integer field analysis
        retry_analysis = field_analysis["retry_attempts"]
        assert retry_analysis["allowed"] is True
        assert retry_analysis["type"] == "int"
        assert retry_analysis["current_value"] == 3
        assert retry_analysis["current_type"] == "int"
        assert "constraints" in retry_analysis
        
        # Check float field analysis
        multiplier_analysis = field_analysis["exponential_multiplier"]
        assert multiplier_analysis["allowed"] is True
        assert multiplier_analysis["type"] == "float"
        assert multiplier_analysis["current_value"] == 1.5
        assert multiplier_analysis["current_type"] == "float"
        
        # Check boolean field analysis
        jitter_analysis = field_analysis["jitter_enabled"]
        assert jitter_analysis["allowed"] is True
        assert jitter_analysis["type"] == "bool"
        assert jitter_analysis["current_value"] is True
        assert jitter_analysis["current_type"] == "bool"
        
        # Check string field analysis
        strategy_analysis = field_analysis["default_strategy"]
        assert strategy_analysis["allowed"] is True
        assert strategy_analysis["type"] == "string"
        assert strategy_analysis["current_value"] == "balanced"
        assert strategy_analysis["current_type"] == "str"
    
    def test_security_info_accuracy(self, client, auth_headers):
        """Test that security info in response is accurate."""
        config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5
        }
        
        response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": config},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        security_info = data["security_info"]
        
        # Verify size calculation
        expected_size = len(str(config))
        assert security_info["size_bytes"] == expected_size
        
        # Verify field count
        assert security_info["field_count"] == len(config)
        
        # Verify max size is from security config
        assert security_info["max_size_bytes"] == 4096
        
        # Verify timestamp format
        timestamp = security_info["validation_timestamp"]
        assert "T" in timestamp  # ISO format should contain 'T'


class TestSecurityValidationIntegration:
    """Test integration between security validation and other systems."""
    
    @pytest.fixture(autouse=True)
    def reset_rate_limiter(self):
        """Reset rate limiter before each test."""
        from app.infrastructure.resilience.config_validator import config_validator
        config_validator.reset_rate_limiter()
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_security_validation_with_monitoring_integration(self, client, auth_headers):
        """Test that security validation integrates with monitoring."""
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector
        
        # Clear any existing metrics
        config_metrics_collector.metrics.clear()
        config_metrics_collector.alerts.clear()
        
        config = {"retry_attempts": 3}
        
        # Perform validation
        response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": config},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Check if any validation-related metrics were recorded
        # Note: This depends on whether security validation creates monitoring events
        # For now, just verify the endpoint works correctly
        assert response.json()["is_valid"] is True
    
    def test_security_validation_consistency_with_regular_validation(self, client, auth_headers):
        """Test that security validation is consistent with regular validation."""
        config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "default_strategy": "balanced"
        }
        
        # Test security validation
        security_response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": config},
            headers=auth_headers
        )
        
        # Test regular validation
        regular_response = client.post(
            "/internal/resilience/config/validate",
            json={"configuration": config},
            headers=auth_headers
        )
        
        assert security_response.status_code == 200
        assert regular_response.status_code == 200
        
        security_data = security_response.json()
        regular_data = regular_response.json()
        
        # Both should agree on validity for a good config
        assert security_data["is_valid"] is True
        assert regular_data["is_valid"] is True
    
    def test_security_validation_stricter_than_regular(self, client, auth_headers):
        """Test that security validation is stricter than regular validation."""
        # Use a config that might pass regular validation but fail security
        potentially_problematic_config = {
            "retry_attempts": 3,
            "malicious_field": "some_value"  # Unknown field
        }
        
        # Security validation should be stricter
        security_response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": potentially_problematic_config},
            headers=auth_headers
        )
        
        assert security_response.status_code == 200
        security_data = security_response.json()
        
        # Security validation should reject unknown fields
        assert security_data["is_valid"] is False
        assert any("whitelist" in error.lower() for error in security_data["errors"])


class TestSecurityValidationEdgeCases:
    """Test edge cases for security validation."""
    
    @pytest.fixture(autouse=True)
    def reset_rate_limiter(self):
        """Reset rate limiter before each test."""
        from app.infrastructure.resilience.config_validator import config_validator
        config_validator.reset_rate_limiter()
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_empty_configuration(self, client, auth_headers):
        """Test validation with empty configuration."""
        response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": {}},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Empty config should be valid (no violations)
        assert data["is_valid"] is True
        assert data["security_info"]["field_count"] == 0
    
    def test_null_configuration(self, client, auth_headers):
        """Test validation with null configuration."""
        response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": None},
            headers=auth_headers
        )
        
        # The endpoint may return either 422 (validation error) or 200 (business logic error)
        assert response.status_code in [200, 422]
        data = response.json()
        
        if response.status_code == 200:
            # Null config should be invalid
            assert data["is_valid"] is False
            assert any("must be a JSON object" in error for error in data["errors"])
        else:  # 422 case
            assert "detail" in data  # FastAPI validation error format
    
    def test_very_large_valid_configuration(self, client, auth_headers):
        """Test validation with large but valid configuration."""
        # Create a large config that's still under limits
        large_config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "recovery_timeout": 60,
            "default_strategy": "balanced",
            "operation_overrides": {
                "summarize": "conservative",
                "sentiment": "aggressive", 
                "key_points": "balanced",
                "questions": "balanced",
                "qa": "conservative"
            },
            "exponential_multiplier": 1.5,
            "exponential_min": 1.0,
            "exponential_max": 30.0,
            "jitter_enabled": True,
            "jitter_max": 2.0,
            "max_delay_seconds": 120
        }
        
        response = client.post(
            "/internal/resilience/config/validate-secure",
            json={"configuration": large_config},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be valid since it's within all limits
        assert data["is_valid"] is True
        assert data["security_info"]["field_count"] == len(large_config)