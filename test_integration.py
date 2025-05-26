#!/usr/bin/env python3
"""
Simple integration test to verify frontend-backend communication.
"""

import asyncio
import sys
import httpx
from shared.models import TextProcessingRequest, ProcessingOperation

async def test_integration():
    """Test the integration between frontend and backend."""
    
    print("🧪 Testing FastAPI-Streamlit Integration...")
    
    # Test backend health
    print("\n1. Testing backend health...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ Backend health check passed")
                health_data = response.json()
                print(f"   Status: {health_data['status']}")
                print(f"   AI Model Available: {health_data['ai_model_available']}")
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False
    
    # Test operations endpoint
    print("\n2. Testing operations endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/operations")
            if response.status_code == 200:
                print("✅ Operations endpoint working")
                ops_data = response.json()
                print(f"   Available operations: {len(ops_data['operations'])}")
                for op in ops_data['operations']:
                    print(f"   - {op['name']}: {op['description']}")
            else:
                print(f"❌ Operations endpoint failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Operations endpoint failed: {e}")
        return False
    
    # Test text processing
    print("\n3. Testing text processing...")
    try:
        request = TextProcessingRequest(
            text="This is a test text for integration testing. It should be processed successfully by the AI model.",
            operation=ProcessingOperation.SUMMARIZE,
            options={"max_length": 50}
        )
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/process",
                json=request.dict()
            )
            if response.status_code == 200:
                print("✅ Text processing successful")
                result = response.json()
                print(f"   Operation: {result['operation']}")
                print(f"   Success: {result['success']}")
                if result.get('result'):
                    print(f"   Result: {result['result'][:100]}...")
            else:
                print(f"❌ Text processing failed: {response.status_code}")
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                return False
    except Exception as e:
        print(f"❌ Text processing failed: {e}")
        return False
    
    # Test Streamlit health
    print("\n4. Testing Streamlit frontend...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8501/_stcore/health")
            if response.status_code == 200:
                print("✅ Streamlit frontend accessible")
            else:
                print(f"❌ Streamlit frontend failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Streamlit frontend failed: {e}")
        return False
    
    print("\n🎉 All integration tests passed!")
    print("\n📱 Access the application:")
    print("   Frontend (Streamlit): http://localhost:8501")
    print("   Backend (FastAPI):    http://localhost:8000")
    print("   API Docs:             http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1) 