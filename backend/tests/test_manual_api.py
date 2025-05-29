#!/usr/bin/env python3
"""Manual integration tests for the FastAPI application.

These tests are designed to run against a live server instance
and can be used for manual testing and validation.
"""

import asyncio
import httpx
import json
import os
import pytest
import sys
from typing import Dict, Any

# Add the root directory to Python path so we can import app modules and shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configuration
BASE_URL = "http://localhost:8000"
TEST_API_KEY = "test-api-key-12345"

class TestManualAPI:
    """Manual integration tests for the FastAPI application."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test the health endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            print(f"Health Check: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
            print("-" * 50)
            
            # Basic assertions
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_operations_endpoint(self):
        """Test the operations endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/operations")
            print(f"Operations: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
            print("-" * 50)
            
            # Basic assertions
            assert response.status_code == 200
            data = response.json()
            assert "operations" in data

    @pytest.mark.asyncio
    async def test_process_text_operation(self, operation: str, text: str, options: Dict[str, Any] = None, question: str = None):
        """Test text processing endpoint for a specific operation."""
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
                response = await client.post(f"{BASE_URL}/process", json=data, headers=headers)
                print(f"Process Text ({operation}): {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(json.dumps(result, indent=2))
                    
                    # Basic assertions
                    assert result["success"] is True
                    assert result["operation"] == operation
                    assert "result" in result or "sentiment" in result
                else:
                    print(f"Error: {response.text}")
                print("-" * 50)
                
                return response.status_code, response.json() if response.status_code == 200 else None
                
            except Exception as e:
                print(f"Error testing {operation}: {e}")
                print("-" * 50)
                pytest.fail(f"Exception during {operation} test: {e}")

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
        status, result = await self.test_process_text_operation("summarize", sample_text, {"max_length": 50})
        assert status == 200
        
        # Test sentiment analysis
        status, result = await self.test_process_text_operation("sentiment", sample_text)
        assert status == 200
        
        # Test key points extraction
        status, result = await self.test_process_text_operation("key_points", sample_text, {"max_points": 3})
        assert status == 200
        
        # Test question generation
        status, result = await self.test_process_text_operation("questions", sample_text, {"num_questions": 3})
        assert status == 200
        
        # Test Q&A
        status, result = await self.test_process_text_operation("qa", sample_text, question="What are the main concerns about AI?")
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