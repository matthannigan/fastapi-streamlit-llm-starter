#!/usr/bin/env python3
"""Simple script to test the FastAPI application manually."""

import asyncio
import httpx
import json
import os
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

async def test_health():
    """Test the health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        print("-" * 50)

async def test_operations():
    """Test the operations endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/operations")
        print(f"Operations: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        print("-" * 50)

async def test_process_text(operation: str, text: str, options: Dict[str, Any] = None, question: str = None):
    """Test text processing endpoint."""
    data = {
        "text": text,
        "operation": operation,
        "options": options or {}
    }
    
    if question:
        data["question"] = question
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(f"{BASE_URL}/process", json=data)
            print(f"Process Text ({operation}): {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(json.dumps(result, indent=2))
            else:
                print(f"Error: {response.text}")
            print("-" * 50)
        except Exception as e:
            print(f"Error testing {operation}: {e}")
            print("-" * 50)

async def main():
    """Run all tests."""
    print("Testing FastAPI Application")
    print("=" * 50)
    
    # Test health endpoint
    await test_health()
    
    # Test operations endpoint
    await test_operations()
    
    # Sample text for testing
    sample_text = """
    Artificial intelligence (AI) is transforming the way we work, live, and interact with technology. 
    From machine learning algorithms that power recommendation systems to natural language processing 
    models that enable chatbots, AI is becoming increasingly integrated into our daily lives. 
    However, with these advancements come important considerations about ethics, privacy, and the 
    future of human employment. As we continue to develop more sophisticated AI systems, it's crucial 
    that we address these challenges thoughtfully and responsibly.
    """
    
    # Only test if GEMINI_API_KEY is set
    if os.getenv("GEMINI_API_KEY"):
        print("Testing text processing operations...")
        
        # Test summarization
        await test_process_text("summarize", sample_text, {"max_length": 50})
        
        # Test sentiment analysis
        await test_process_text("sentiment", sample_text)
        
        # Test key points extraction
        await test_process_text("key_points", sample_text, {"max_points": 3})
        
        # Test question generation
        await test_process_text("questions", sample_text, {"num_questions": 3})
        
        # Test Q&A
        await test_process_text("qa", sample_text, question="What are the main concerns about AI?")
    else:
        print("GEMINI_API_KEY not set - skipping AI processing tests")
        print("Set GEMINI_API_KEY environment variable to test AI features")

if __name__ == "__main__":
    asyncio.run(main()) 