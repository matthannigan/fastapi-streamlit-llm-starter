"""Manual authentication tests for the FastAPI application.

These tests are designed to run against a live server instance
and validate authentication behavior manually.
"""

import os
import pytest
import requests
import json
from typing import Optional, Tuple, Union

# Configuration
BASE_URL = "http://localhost:8000"
TEST_API_KEY = "test-api-key-12345"


@pytest.mark.manual
class TestManualAuthentication:
    """Manual authentication tests for the FastAPI application."""

    def test_endpoint(self, endpoint: str, api_key: Optional[str] = None, method: str = "GET", data: dict = None) -> Tuple[Optional[int], Union[dict, str, None]]:
        """Test an endpoint with optional API key."""
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
            
            print(f"\n{method} {endpoint}")
            print(f"API Key: {'Yes' if api_key else 'No'}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            return response.status_code, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            
        except requests.exceptions.ConnectionError:
            print(f"\n{method} {endpoint}")
            print("Error: Could not connect to server. Make sure the FastAPI server is running.")
            pytest.skip("Server not running - skipping test")
        except Exception as e:
            print(f"\n{method} {endpoint}")
            print(f"Error: {str(e)}")
            return None, None

    def test_public_endpoints(self):
        """Test public endpoints that should work without API key."""
        print("\n--- Testing Public Endpoints ---")
        
        # Test root endpoint
        status, response = self.test_endpoint("/")
        assert status == 200
        
        # Test health endpoint
        status, response = self.test_endpoint("/health")
        assert status == 200
        assert isinstance(response, dict)
        assert response.get("status") == "healthy"

    def test_protected_endpoints_without_auth(self):
        """Test protected endpoints without API key (should fail)."""
        print("\n--- Testing Protected Endpoints (No API Key) ---")
        
        # Test process endpoint without auth
        status, response = self.test_endpoint("/text_processing/process", method="POST", data={
            "text": "Hello world",
            "operation": "summarize"
        })
        assert status == 401  # Unauthorized
        
        # Test auth status endpoint without auth
        status, response = self.test_endpoint("/auth/status")
        assert status == 401  # Unauthorized

    def test_protected_endpoints_with_invalid_auth(self):
        """Test protected endpoints with invalid API key (should fail)."""
        print("\n--- Testing Protected Endpoints (Invalid API Key) ---")
        
        # Test process endpoint with invalid key
        status, response = self.test_endpoint("/text_processing/process", api_key="invalid-key", method="POST", data={
            "text": "Hello world",
            "operation": "summarize"
        })
        assert status == 401  # Unauthorized
        
        # Test auth status endpoint with invalid key
        status, response = self.test_endpoint("/auth/status", api_key="invalid-key")
        assert status == 401  # Unauthorized

    def test_protected_endpoints_with_valid_auth(self):
        """Test protected endpoints with valid API key (should work if configured)."""
        print("\n--- Testing Protected Endpoints (Valid API Key) ---")
        
        # Test auth status endpoint with valid key
        status, response = self.test_endpoint("/auth/status", api_key=TEST_API_KEY)
        assert status == 200
        assert isinstance(response, dict)
        assert response.get("authenticated") is True
        
        # Test process endpoint with valid key
        status, response = self.test_endpoint("/text_processing/process", api_key=TEST_API_KEY, method="POST", data={
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
        status, response = self.test_endpoint("/text_processing/operations")
        assert status == 200
        assert isinstance(response, dict)
        assert "operations" in response
        
        # Test operations endpoint with auth
        status, response = self.test_endpoint("/text_processing/operations", api_key=TEST_API_KEY)
        assert status == 200
        assert isinstance(response, dict)
        assert "operations" in response

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
        
        print("\n=== Test Instructions ===")
        print("1. Start the FastAPI server: cd backend && python -m uvicorn app.main:app --reload")
        print("2. Set API_KEY environment variable: export API_KEY=test-api-key-12345")
        print("3. Run this test: pytest backend/tests/test_manual_auth.py -v")
        print("\nExpected behavior:")
        print("- Public endpoints (/, /health) should work without API key")
        print("- Protected endpoints (/text_processing/process, /auth/status) should require valid API key")
        print("- Optional auth endpoints (/text_processing/operations) should work with or without API key")


# Standalone function for manual execution
def run_manual_auth_tests():
    """Run all manual auth tests - can be called directly."""
    test_instance = TestManualAuthentication()
    test_instance.test_complete_auth_suite()


if __name__ == "__main__":
    print("Running manual authentication tests...")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("Set API_KEY=test-api-key-12345 environment variable for authentication")
    print("-" * 50)
    
    run_manual_auth_tests() 