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
from typing import Dict, Any, Tuple, Optional

# Configuration
BASE_URL = "http://localhost:8000"
TEST_API_KEY = "test-api-key-12345"

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