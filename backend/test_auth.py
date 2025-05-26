"""Test script for API authentication."""

import os
import requests
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
TEST_API_KEY = "test-api-key-12345"

def test_endpoint(endpoint: str, api_key: Optional[str] = None, method: str = "GET", data: dict = None):
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
        return None, None
    except Exception as e:
        print(f"\n{method} {endpoint}")
        print(f"Error: {str(e)}")
        return None, None

def main():
    """Run authentication tests."""
    print("=== API Authentication Tests ===")
    print(f"Testing against: {BASE_URL}")
    print(f"Test API Key: {TEST_API_KEY}")
    
    # Test public endpoints (should work without API key)
    print("\n--- Testing Public Endpoints ---")
    test_endpoint("/")
    test_endpoint("/health")
    
    # Test protected endpoints without API key (should fail)
    print("\n--- Testing Protected Endpoints (No API Key) ---")
    test_endpoint("/process", method="POST", data={
        "text": "Hello world",
        "operation": "summarize"
    })
    test_endpoint("/auth/status")
    
    # Test protected endpoints with invalid API key (should fail)
    print("\n--- Testing Protected Endpoints (Invalid API Key) ---")
    test_endpoint("/process", api_key="invalid-key", method="POST", data={
        "text": "Hello world",
        "operation": "summarize"
    })
    test_endpoint("/auth/status", api_key="invalid-key")
    
    # Test protected endpoints with valid API key (should work if configured)
    print("\n--- Testing Protected Endpoints (Valid API Key) ---")
    test_endpoint("/auth/status", api_key=TEST_API_KEY)
    test_endpoint("/process", api_key=TEST_API_KEY, method="POST", data={
        "text": "Hello world",
        "operation": "summarize"
    })
    
    # Test optional auth endpoint
    print("\n--- Testing Optional Auth Endpoints ---")
    test_endpoint("/operations")
    test_endpoint("/operations", api_key=TEST_API_KEY)
    
    print("\n=== Test Instructions ===")
    print("1. Start the FastAPI server: cd backend && python -m uvicorn app.main:app --reload")
    print("2. Set API_KEY environment variable: export API_KEY=test-api-key-12345")
    print("3. Run this test: python test_auth.py")
    print("\nExpected behavior:")
    print("- Public endpoints (/, /health) should work without API key")
    print("- Protected endpoints (/process, /auth/status) should require valid API key")
    print("- Optional auth endpoints (/operations) should work with or without API key")

if __name__ == "__main__":
    main() 