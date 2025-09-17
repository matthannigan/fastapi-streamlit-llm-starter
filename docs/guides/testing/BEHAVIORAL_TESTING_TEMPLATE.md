# Behavioral Testing Template

This template demonstrates the enhanced behavioral testing patterns established during the Phase 1 & 2 test reorganization.

## Contract-Driven Integration Test Template

```python
"""
Integration tests for [Component Name] with [External Dependencies].

This module tests the integration between [Component] and [Dependencies]
following contract-driven, behavior-focused testing principles.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class Test[ComponentName]Integration:
    """Test [Component] integration with [Dependencies]."""

    def test_[operation]_success_with_valid_input(self, client, auth_headers):
        """
        Test [operation] successfully processes valid input with expected behavior.

        Business Impact: Ensures [business value] is delivered reliably to users,
        enabling [specific business capability] without [business risk].

        Observable Behavior: Valid input should result in [expected outcome]
        with proper [response structure/status/side effects].

        Success Criteria:
        - Returns [expected status] for valid input
        - Provides [expected response structure]
        - Maintains [consistency/security/performance requirements]
        - Enables [follow-up actions/workflows]
        """
        # Arrange: Set up test data and expectations
        valid_input = {
            "required_field": "valid_value",
            "optional_field": "test_value"
        }

        # Act: Execute the operation
        response = client.post(
            "/endpoint/path",
            json=valid_input,
            headers=auth_headers
        )

        # Assert: Verify observable behavior
        assert response.status_code == 200, "Valid input should be accepted"
        data = response.json()

        # Observable outcome: Response structure validation
        required_fields = ["field1", "field2", "field3"]
        for field in required_fields:
            assert field in data, f"Response must include '{field}' for [business reason]"

        # Observable outcome: Business logic validation
        assert data["field1"] == expected_value, "Business rule enforcement"
        assert data["success"] is True, "Operation should succeed with valid input"

        # Observable outcome: Side effects verification
        assert "timestamp" in data, "Audit trail requirement"

    def test_[operation]_handles_invalid_input_gracefully(self, client, auth_headers):
        """
        Test [operation] handles invalid input with appropriate error response.

        Business Impact: Prevents [business risk] by rejecting invalid input
        and providing actionable feedback to users.

        Observable Behavior: Invalid input should result in structured error
        response with specific guidance for correction.
        """
        # Arrange: Invalid input scenarios
        invalid_inputs = [
            ({"missing_required": "value"}, "missing required field"),
            ({"required_field": ""}, "empty required field"),
            ({"required_field": "invalid_format"}, "invalid format"),
        ]

        for invalid_input, scenario in invalid_inputs:
            with self.subTest(scenario=scenario):
                # Act: Submit invalid input
                response = client.post(
                    "/endpoint/path",
                    json=invalid_input,
                    headers=auth_headers
                )

                # Assert: Graceful error handling
                assert response.status_code == 422, f"Should reject {scenario}"
                error_data = response.json()

                # Observable outcome: Structured error response
                assert "detail" in error_data, "Error should provide details"
                assert "message" in error_data["detail"], "Error should be actionable"

    def test_[operation]_concurrent_access_consistency(self, client, auth_headers):
        """
        Test [operation] maintains consistency under concurrent access.

        Business Impact: Ensures system reliability under normal load conditions,
        preventing data corruption or inconsistent responses.

        Observable Behavior: Concurrent requests should receive consistent
        responses without interference between operations.
        """
        import threading
        import queue

        results = queue.Queue()
        test_input = {"required_field": "concurrent_test"}

        def make_request():
            """Execute request in separate thread."""
            try:
                response = client.post(
                    "/endpoint/path",
                    json=test_input,
                    headers=auth_headers
                )
                results.put(("success", response.status_code, response.json()))
            except Exception as e:
                results.put(("error", str(e), None))

        # Execute concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify consistent behavior
        response_count = 0
        while not results.empty():
            result_type, status_code, data = results.get()
            response_count += 1

            # Observable outcome: Consistent response behavior
            assert result_type == "success", "Concurrent requests should not fail"
            assert status_code in [200, 422], "Should return consistent status codes"

        assert response_count == 5, "All concurrent requests should complete"


class Test[ComponentName]ErrorScenarios:
    """Test error scenarios and edge cases with observable outcomes."""

    def test_[operation]_graceful_degradation_when_dependency_fails(self, client, auth_headers):
        """
        Test [operation] handles dependency failure with graceful degradation.

        Business Impact: Maintains service availability during dependency outages,
        providing [fallback capability] to minimize business disruption.

        Observable Behavior: Dependency failure should result in [degraded service]
        rather than complete failure, with appropriate status indication.
        """
        with patch('app.dependencies.dependency_service') as mock_service:
            # Arrange: Simulate dependency failure
            mock_service.side_effect = ConnectionError("Service unavailable")

            test_input = {"required_field": "test_value"}

            # Act: Execute operation with failed dependency
            response = client.post(
                "/endpoint/path",
                json=test_input,
                headers=auth_headers
            )

            # Assert: Graceful degradation behavior
            # Option 1: Return partial results
            if response.status_code == 200:
                data = response.json()
                assert "degraded" in data or "partial" in data, \
                    "Should indicate degraded service"

            # Option 2: Return service unavailable with retry info
            elif response.status_code == 503:
                error_data = response.json()
                assert "retry_after" in error_data or "service_status" in error_data, \
                    "Should provide retry guidance"

            else:
                pytest.fail(f"Unexpected response {response.status_code} for dependency failure")

    def test_[operation]_authentication_boundary_enforcement(self, client):
        """
        Test [operation] enforces authentication boundaries correctly.

        Business Impact: Protects sensitive data and operations from unauthorized
        access, maintaining security compliance and user trust.

        Observable Behavior: Unauthenticated requests should be consistently
        rejected with proper error structure and security headers.
        """
        test_input = {"required_field": "test_value"}

        # Act: Request without authentication
        response = client.post("/endpoint/path", json=test_input)

        # Assert: Security boundary enforcement
        assert response.status_code == 401, "Should reject unauthenticated requests"

        # Observable outcome: Security response structure
        if response.headers.get('content-type', '').startswith('application/json'):
            error_data = response.json()
            assert "detail" in error_data, "Security error should include details"

        # Observable outcome: Security headers
        assert "www-authenticate" in response.headers, \
            "Should include authentication challenge"
```

## API Endpoint Testing Template

```python
"""
API endpoint tests for [Endpoint Name].

Tests HTTP contract compliance, request/response validation,
and proper error handling for [endpoint description].
"""

import pytest
from fastapi.testclient import TestClient


class Test[EndpointName]Contract:
    """Test API contract compliance for [endpoint]."""

    def test_[endpoint]_request_schema_validation(self, client):
        """
        Test [endpoint] validates request schema correctly.

        Business Impact: Ensures data integrity by rejecting malformed requests
        before processing, preventing downstream errors and data corruption.

        Observable Behavior: Invalid request schemas should return 422 with
        detailed validation errors for each field violation.
        """
        # Test various schema violations
        schema_violations = [
            ({}, "empty request body"),
            ({"wrong_field": "value"}, "unexpected fields"),
            ({"required_field": None}, "null required field"),
            ({"required_field": 123}, "wrong data type"),
            ({"required_field": "a" * 1000}, "field too long"),
        ]

        for invalid_request, scenario in schema_violations:
            with self.subTest(scenario=scenario):
                response = client.post("/endpoint", json=invalid_request)

                # Observable outcome: Schema validation
                assert response.status_code == 422, f"Should reject {scenario}"
                error_data = response.json()

                # Observable outcome: Detailed validation errors
                assert "detail" in error_data, "Should provide validation details"
                if isinstance(error_data["detail"], list):
                    # FastAPI validation error format
                    assert len(error_data["detail"]) > 0, "Should specify validation errors"
                    for error in error_data["detail"]:
                        assert "loc" in error and "msg" in error, \
                            "Should provide field location and message"

    def test_[endpoint]_response_schema_consistency(self, client, valid_request):
        """
        Test [endpoint] returns consistent response schema.

        Business Impact: Ensures API consumers can reliably parse responses,
        enabling stable integration and preventing client application failures.

        Observable Behavior: All successful responses should follow the same
        schema structure regardless of input variations.
        """
        # Test multiple valid requests for schema consistency
        test_cases = [
            valid_request,
            {**valid_request, "optional_field": "additional_value"},
            {**valid_request, "array_field": ["item1", "item2"]},
        ]

        response_schemas = []
        for test_input in test_cases:
            response = client.post("/endpoint", json=test_input)
            assert response.status_code == 200, "Valid request should succeed"

            data = response.json()
            response_schemas.append(set(data.keys()))

        # Observable outcome: Schema consistency
        first_schema = response_schemas[0]
        for schema in response_schemas[1:]:
            assert schema == first_schema, \
                "Response schema should be consistent across requests"

    def test_[endpoint]_http_method_compliance(self, client):
        """
        Test [endpoint] responds correctly to different HTTP methods.

        Business Impact: Ensures proper HTTP semantics compliance for
        API standards and client library compatibility.

        Observable Behavior: Should only accept intended HTTP methods
        and return 405 Method Not Allowed for others.
        """
        test_data = {"required_field": "test_value"}

        # Test unsupported methods
        unsupported_methods = ["GET", "PUT", "PATCH", "DELETE"]
        for method in unsupported_methods:
            response = client.request(method, "/endpoint", json=test_data)

            # Observable outcome: HTTP method compliance
            assert response.status_code == 405, \
                f"Should not allow {method} method"
            assert "allow" in response.headers, \
                "Should specify allowed methods in headers"
```

## Manual Testing Template

```python
"""
Manual tests for [Feature Name] requiring live server validation.

These tests verify real-world behavior against a running server instance
with actual external dependencies and API keys.
"""

import requests
import pytest
from typing import Dict, Any, Tuple, Optional, Union


@pytest.mark.manual
class TestManual[FeatureName]:
    """Manual tests for [feature] with live server."""

    BASE_URL = "http://localhost:8000"
    TEST_API_KEY = "test-api-key-12345"

    def call_endpoint(self, endpoint: str, api_key: Optional[str] = None,
                     method: str = "GET", data: Optional[dict] = None) -> Tuple[Optional[int], Union[dict, str, None]]:
        """
        Helper method for consistent endpoint testing with optional API key.

        This pattern enables comprehensive scenario coverage across different endpoints
        with consistent error handling and response validation.
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {}

        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            print(f"\n{method} {endpoint}")
            print(f"API Key: {'Yes' if api_key else 'No'}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

            # Parse JSON response with graceful fallback
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    return response.status_code, response.json()
                else:
                    return response.status_code, response.text
            except ValueError:
                return response.status_code, response.text

        except requests.exceptions.ConnectionError:
            print(f"\n{method} {endpoint}")
            print("Error: Could not connect to server. Make sure the FastAPI server is running.")
            pytest.skip("Server not running - skipping test")
        except Exception as e:
            print(f"\n{method} {endpoint}")
            print(f"Error: {str(e)}")
            return None, None

    def test_[feature]_end_to_end_workflow(self):
        """
        Test complete [feature] workflow from start to finish.

        Business Impact: Validates that users can complete [business process]
        successfully in real-world conditions with actual dependencies.

        Observable Behavior: Complete workflow should succeed with expected
        results and proper state transitions.

        Manual Setup Required:
        1. Start FastAPI server: uvicorn app.main:app --reload --port 8000
        2. Set environment variables: export API_KEY=test-api-key-12345
        3. Ensure [external dependencies] are available
        """
        print("\n=== Testing [Feature] End-to-End Workflow ===")

        # Step 1: Initial operation
        status, response = self.call_endpoint(
            "/endpoint/initialize",
            api_key=self.TEST_API_KEY,
            method="POST",
            data={"initialization_data": "test_value"}
        )
        assert status == 200, "Initialization should succeed"
        assert isinstance(response, dict), "Should return structured response"

        # Step 2: Follow-up operation
        operation_id = response.get("operation_id")
        assert operation_id, "Should provide operation ID for tracking"

        status, response = self.call_endpoint(
            f"/endpoint/status/{operation_id}",
            api_key=self.TEST_API_KEY
        )
        assert status == 200, "Status check should succeed"

        # Step 3: Completion verification
        if response.get("status") == "completed":
            final_status, final_response = self.call_endpoint(
                f"/endpoint/result/{operation_id}",
                api_key=self.TEST_API_KEY
            )
            assert final_status == 200, "Result retrieval should succeed"
            assert "result" in final_response, "Should provide final result"

    def test_[feature]_error_recovery_scenarios(self):
        """
        Test [feature] handles real-world error scenarios gracefully.

        Business Impact: Ensures system resilience during actual failure
        conditions that may not be perfectly reproducible in unit tests.

        Observable Behavior: Errors should result in clear feedback and
        recovery guidance without system instability.
        """
        print("\n=== Testing Error Recovery Scenarios ===")

        # Test various error conditions
        error_scenarios = [
            ("/endpoint/invalid", "invalid endpoint"),
            ("/endpoint/test", "unauthorized access"),
            ("/endpoint/overload", "rate limiting"),
        ]

        for endpoint, scenario in error_scenarios:
            print(f"\nTesting scenario: {scenario}")
            status, response = self.call_endpoint(endpoint, api_key=self.TEST_API_KEY)

            # Verify appropriate error handling
            assert status in [400, 401, 404, 429, 500], \
                f"Should return appropriate error status for {scenario}"

            if isinstance(response, dict) and "detail" in response:
                assert "message" in response["detail"], \
                    f"Should provide actionable error message for {scenario}"
```

## Best Practices Summary

### Behavioral Testing Principles
1. **Test Observable Behavior**: Focus on what users and systems can observe
2. **Document Business Impact**: Explain why the test matters
3. **Define Success Criteria**: Clear expectations for pass/fail
4. **Include Error Scenarios**: Test graceful degradation and error handling
5. **Verify Consistency**: Ensure behavior is consistent across scenarios

### Enhanced Docstring Pattern
```python
def test_feature_behavior(self):
    """
    [One-line summary of what is being tested]

    Business Impact: [Why this test matters for the business]

    Observable Behavior: [What should happen from external perspective]

    Success Criteria: (optional, for complex tests)
    - [Specific expectation 1]
    - [Specific expectation 2]
    - [Specific expectation 3]
    """
```

### Anti-Patterns to Avoid
- Testing implementation details instead of behavior
- Mocking everything (prefer real dependencies when possible)
- Tests that pass regardless of behavior changes
- Vague assertions without business context
- Tests that don't specify expected observable outcomes

## See Also
- [Testing Guide](../../docs/guides/testing/TESTING.md) - Comprehensive testing philosophy
- [Integration Tests](../../docs/guides/testing/INTEGRATION_TESTS.md) - Integration testing patterns
- [Test Structure](../../docs/guides/testing/TEST_STRUCTURE.md) - Test organization guidelines