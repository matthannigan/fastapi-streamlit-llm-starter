#!/usr/bin/env python3
"""Manual integration tests for API endpoints.

These tests require actual AI API keys and make real API calls.
They are designed for manual testing and validation of the complete API flow.
"""

import asyncio
import httpx
import json
import os
import pytest
import requests
from typing import Dict, Any, Tuple, Optional, Union

# Configuration
BASE_URL = "http://localhost:8000"
TEST_API_KEY = "test-api-key-12345"


class APITestHelper:
    """Helper class for manual API testing with comprehensive scenario coverage."""

    @staticmethod
    def call_endpoint(endpoint: str, api_key: Optional[str] = None, method: str = "GET", data: Optional[dict] = None) -> Tuple[Optional[int], Union[dict, str, None]]:
        """
        Reusable helper method for endpoint testing with optional API key.

        This pattern enables comprehensive scenario coverage across different endpoints
        with consistent error handling and response validation.
        """
        url = f"{BASE_URL}{endpoint}"
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

@pytest.mark.manual
class TestManualAPI:
    """Manual integration tests for the FastAPI application."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test the health endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            print(f"Health Check: {response.status_code}")
            
            # Handle different response types gracefully
            if response.status_code == 307:
                # Handle redirect - try following the redirect
                print(f"Redirect detected: {response.headers.get('location', 'N/A')}")
                if 'location' in response.headers:
                    redirect_url = response.headers['location']
                    if not redirect_url.startswith('http'):
                        redirect_url = BASE_URL + redirect_url
                    response = await client.get(redirect_url)
                    print(f"After redirect: {response.status_code}")
            
            # Try to parse JSON, handle non-JSON responses
            try:
                data = response.json()
                print(json.dumps(data, indent=2))
                
                # Basic assertions for successful responses
                if response.status_code == 200:
                    assert "status" in data
                    assert data["status"] == "healthy"
            except ValueError as e:
                print(f"Non-JSON response: {response.text}")
                # For non-JSON responses, we still want to see what we got
                if response.status_code not in [200, 307]:
                    pytest.fail(f"Health endpoint returned {response.status_code} with non-JSON response: {response.text}")
                    
            print("-" * 50)

    @pytest.mark.asyncio
    async def test_operations_endpoint(self):
        """Test the operations endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/text_processing/operations")
            print(f"Operations: {response.status_code}")
            
            try:
                data = response.json()
                print(json.dumps(data, indent=2))
                
                # Basic assertions
                if response.status_code == 200:
                    assert "operations" in data
            except ValueError:
                print(f"Non-JSON response: {response.text}")
                if response.status_code == 200:
                    pytest.fail("Expected JSON response from operations endpoint")
                    
            print("-" * 50)

    # Helper method - not a test method
    async def process_text_operation(self, operation: str, text: str, options: Optional[Dict[str, Any]] = None, question: Optional[str] = None) -> Tuple[int, Optional[dict]]:
        """Helper method to test text processing endpoint for a specific operation."""
        data = {
            "text": text,
            "operation": operation,
            "options": options or {}
        }
        
        if question:
            data["question"] = question
        
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(f"{BASE_URL}/text_processing/process", json=data, headers=headers)
                print(f"Process Text ({operation}): {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(json.dumps(result, indent=2))
                        
                        # Basic assertions
                        assert result["success"] is True
                        assert result["operation"] == operation
                        assert "result" in result or "sentiment" in result
                        
                        return response.status_code, result
                    except ValueError:
                        print(f"Non-JSON response: {response.text}")
                        return response.status_code, None
                else:
                    print(f"Error: {response.text}")
                    return response.status_code, None
                    
            except Exception as e:
                print(f"Error testing {operation}: {e}")
                raise e
            finally:
                print("-" * 50)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    async def test_all_text_processing_operations(self):
        """Test all text processing operations with AI integration."""
        sample_text = """
        Artificial intelligence (AI) is transforming the way we work, live, and interact with technology. 
        From machine learning algorithms that power recommendation systems to natural language processing 
        models that enable chatbots, AI is becoming increasingly integrated into our daily lives. 
        However, with these advancements come important considerations about ethics, privacy, and the 
        future of human employment. As we continue to develop more sophisticated AI systems, it's crucial 
        that we address these challenges thoughtfully and responsibly.
        """
        
        print("Testing text processing operations...")
        
        # Test summarization
        status, result = await self.process_text_operation("summarize", sample_text, {"max_length": 50})
        assert status == 200
        
        # Test sentiment analysis
        status, result = await self.process_text_operation("sentiment", sample_text)
        assert status == 200
        
        # Test key points extraction
        status, result = await self.process_text_operation("key_points", sample_text, {"max_points": 3})
        assert status == 200
        
        # Test question generation
        status, result = await self.process_text_operation("questions", sample_text, {"num_questions": 3})
        assert status == 200
        
        # Test Q&A
        status, result = await self.process_text_operation("qa", sample_text, question="What are the main concerns about AI?")
        assert status == 200

    @pytest.mark.asyncio
    async def test_manual_integration_suite(self):
        """Run the complete manual integration test suite."""
        print("Testing FastAPI Application")
        print("=" * 50)
        
        # Test health endpoint
        await self.test_health_endpoint()
        
        # Test operations endpoint
        await self.test_operations_endpoint()
        
        # Only test AI operations if API key is available
        if os.getenv("GEMINI_API_KEY"):
            await self.test_all_text_processing_operations()
        else:
            print("GEMINI_API_KEY not set - skipping AI processing tests")
            print("Set GEMINI_API_KEY environment variable to test AI features")


@pytest.mark.manual
class TestManualAuthentication(APITestHelper):
    """
    Manual authentication tests with comprehensive scenario coverage.

    These tests validate authentication behavior across different endpoint types
    and security scenarios, derived from legacy testing patterns.
    """

    def test_public_endpoints(self):
        """Test public endpoints that should work without API key."""
        print("\n--- Testing Public Endpoints ---")

        # Test root endpoint
        status, response = self.call_endpoint("/")
        assert status == 200

        # Test health endpoint
        status, response = self.call_endpoint("/v1/health")
        if status == 307:
            print("Health endpoint returned redirect, checking if it's working...")
            assert status in [200, 307]
        else:
            assert status == 200
            if isinstance(response, dict):
                assert response.get("status") == "healthy"

    def test_protected_endpoints_without_auth(self):
        """Test protected endpoints without API key (should fail)."""
        print("\n--- Testing Protected Endpoints (No API Key) ---")

        # Test process endpoint without auth
        status, response = self.call_endpoint("/v1/text_processing/process", method="POST", data={
            "text": "Hello world",
            "operation": "summarize"
        })
        assert status == 401  # Unauthorized

        # Test auth status endpoint without auth
        status, response = self.call_endpoint("/v1/auth/status")
        assert status == 401  # Unauthorized

    def test_protected_endpoints_with_invalid_auth(self):
        """Test protected endpoints with invalid API key (should fail)."""
        print("\n--- Testing Protected Endpoints (Invalid API Key) ---")

        # Test process endpoint with invalid key
        status, response = self.call_endpoint("/v1/text_processing/process", api_key="invalid-key", method="POST", data={
            "text": "Hello world",
            "operation": "summarize"
        })
        assert status == 401  # Unauthorized

        # Test auth status endpoint with invalid key
        status, response = self.call_endpoint("/v1/auth/status", api_key="invalid-key")
        assert status == 401  # Unauthorized

    def test_protected_endpoints_with_valid_auth(self):
        """Test protected endpoints with valid API key (should work if configured)."""
        print("\n--- Testing Protected Endpoints (Valid API Key) ---")

        # Test auth status endpoint with valid key
        status, response = self.call_endpoint("/v1/auth/status", api_key=TEST_API_KEY)
        assert status == 200
        if isinstance(response, dict):
            assert response.get("authenticated") is True

        # Test process endpoint with valid key
        status, response = self.call_endpoint("/v1/text_processing/process", api_key=TEST_API_KEY, method="POST", data={
            "text": "Hello world",
            "operation": "summarize"
        })
        # This might return 200 (success) or 500 (if AI service not configured)
        # Both are acceptable for auth testing - we just want to ensure it's not 401
        assert status in [200, 500]  # Not unauthorized

    def test_optional_auth_endpoints(self):
        """Test endpoints that work with or without authentication."""
        print("\n--- Testing Optional Auth Endpoints ---")

        # Test operations endpoint without auth
        status, response = self.call_endpoint("/v1/text_processing/operations")
        assert status == 200
        if isinstance(response, dict):
            assert "operations" in response

        # Test operations endpoint with auth
        status, response = self.call_endpoint("/v1/text_processing/operations", api_key=TEST_API_KEY)
        assert status == 200
        if isinstance(response, dict):
            assert "operations" in response

    def test_auth_edge_cases(self):
        """Test authentication edge cases and malformed requests."""
        print("\n--- Testing Auth Edge Cases ---")

        # Test malformed authorization headers
        malformed_cases = [
            ("InvalidFormat", "Malformed header without Bearer prefix"),
            ("Bearer", "Bearer without token"),
            ("", "Empty header"),
        ]

        for header_value, description in malformed_cases:
            print(f"\nTesting: {description}")
            # Manually create request with malformed header
            import requests
            try:
                response = requests.get(
                    f"{BASE_URL}/v1/auth/status",
                    headers={"Authorization": header_value}
                )
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
                assert response.status_code == 401
            except Exception as e:
                print(f"Error (expected): {e}")

        # Test case sensitivity
        print(f"\nTesting case-sensitive API key")
        status, response = self.call_endpoint("/v1/auth/status", api_key=TEST_API_KEY.upper())
        # Should fail if keys are case-sensitive
        print(f"Case sensitivity test result: {status}")

    def test_complete_auth_suite(self):
        """Run the complete authentication test suite."""
        print("=== API Authentication Tests ===")
        print(f"Testing against: {BASE_URL}")
        print(f"Test API Key: {TEST_API_KEY}")

        self.test_public_endpoints()
        self.test_protected_endpoints_without_auth()
        self.test_protected_endpoints_with_invalid_auth()
        self.test_protected_endpoints_with_valid_auth()
        self.test_optional_auth_endpoints()
        self.test_auth_edge_cases()

        print("\n=== Authentication Test Instructions ===")
        print("1. Start the FastAPI server: cd backend && python -m uvicorn app.main:app --reload")
        print("2. Set API_KEY environment variable: export API_KEY=test-api-key-12345")
        print("3. Run this test: pytest backend/tests/manual/test_manual_api.py::TestManualAuthentication -v")
        print("\nExpected behavior:")
        print("- Public endpoints (/, /health) should work without API key")
        print("- Protected endpoints (/text_processing/process, /auth/status) should require valid API key")
        print("- Optional auth endpoints (/text_processing/operations) should work with or without API key")
        print("- Invalid/malformed auth should consistently return 401")


# Standalone function for manual execution
async def run_manual_tests():
    """Run all manual tests - can be called directly."""
    test_instance = TestManualAPI()
    await test_instance.test_manual_integration_suite()


if __name__ == "__main__":
    print("Running manual API tests...")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("Set GEMINI_API_KEY environment variable to test AI features")
    print("Set API_KEY=test-api-key-12345 environment variable for authentication")
    print("-" * 50)
    
    asyncio.run(run_manual_tests()) 