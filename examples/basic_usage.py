#!/usr/bin/env python3
"""
Basic usage examples for the FastAPI-Streamlit-LLM Starter Template.

This script demonstrates how to interact with the API programmatically
and showcases all available text processing operations using standardized
patterns for imports, error handling, and sample data.
"""

# Standard library imports
import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional

# Third-party imports
import httpx

# Local application imports
from shared.sample_data import (
    STANDARD_SAMPLE_TEXTS,
    get_sample_text,
    get_medium_text,
    get_business_text
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIClient:
    """
    Simple API client for the FastAPI backend with standardized error handling.
    
    This client provides methods for interacting with the text processing API
    and follows consistent error handling patterns.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for the API endpoints
        """
        self.base_url = base_url
        self.session = None
        self.timeout = httpx.Timeout(30.0)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()
    
    async def health_check(self) -> Optional[Dict[str, Any]]:
        """
        Check API health status with error handling.
        
        Returns:
            Health status dictionary or None if error occurred
        """
        try:
            response = await self.session.get(f"{self.base_url}/v1/health")
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.error("Health check timeout")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Health check HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return None
    
    async def get_operations(self) -> Optional[Dict[str, Any]]:
        """
        Get available operations with error handling.
        
        Returns:
            Operations dictionary or None if error occurred
        """
        try:
            response = await self.session.get(f"{self.base_url}/operations")
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.error("Get operations timeout")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Get operations HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Get operations error: {str(e)}")
            return None
    
    async def process_text(
        self, 
        text: str, 
        operation: str, 
        question: Optional[str] = None, 
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process text with specified operation and standardized error handling.
        
        Args:
            text: Text to process
            operation: Processing operation to perform
            question: Optional question for Q&A operation
            options: Optional operation-specific parameters
            
        Returns:
            Processing result dictionary or None if error occurred
        """
        try:
            payload = {
                "text": text,
                "operation": operation,
                "options": options or {}
            }
            
            if question:
                payload["question"] = question
            
            response = await self.session.post(f"{self.base_url}/process", json=payload)
            response.raise_for_status()
            return response.json()
            
        except httpx.TimeoutException:
            logger.error(f"Process text timeout for operation: {operation}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Process text HTTP error: {e.response.status_code}")
            try:
                error_detail = e.response.json().get('detail', 'Unknown error')
                logger.error(f"Error detail: {error_detail}")
            except:
                pass
            return None
        except Exception as e:
            logger.error(f"Process text error: {str(e)}")
            return None

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}")

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{title}")
    print("-" * len(title))

def print_result(result: Dict[str, Any], operation: str):
    """Print formatted result based on operation type."""
    if not result.get("success", True):
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        return
    
    print(f"✅ Operation: {operation}")
    print(f"⏱️  Processing time: {result.get('processing_time', 0):.2f}s")
    
    if operation == "sentiment":
        sentiment = result.get("sentiment", {})
        print(f"📊 Sentiment: {sentiment.get('sentiment', 'Unknown')}")
        print(f"🎯 Confidence: {sentiment.get('confidence', 0):.2%}")
        print(f"💭 Explanation: {sentiment.get('explanation', 'N/A')}")
    
    elif operation == "key_points":
        points = result.get("key_points", [])
        print("📝 Key Points:")
        for i, point in enumerate(points, 1):
            print(f"   {i}. {point}")
    
    elif operation == "questions":
        questions = result.get("questions", [])
        print("❓ Generated Questions:")
        for i, question in enumerate(questions, 1):
            print(f"   {i}. {question}")
    
    else:
        # For summarize, qa, and other text results
        result_text = result.get("result", "No result")
        print(f"📄 Result: {result_text}")
    
    # Print metadata if available
    metadata = result.get("metadata", {})
    if metadata:
        print(f"📊 Metadata: {json.dumps(metadata, indent=2)}")

async def demonstrate_basic_operations():
    """Demonstrate all basic text processing operations."""
    
    print_header("FastAPI-Streamlit-LLM Starter Template - Basic Usage Examples")
    
    async with APIClient() as client:
        
        # 1. Health Check
        print_section("1️⃣ Health Check")
        try:
            health = await client.health_check()
            print(f"✅ API Status: {health.get('status', 'Unknown')}")
            print(f"🤖 AI Model Available: {health.get('ai_model_available', False)}")
            print(f"📅 Timestamp: {health.get('timestamp', 'Unknown')}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return
        
        # 2. Available Operations
        print_section("2️⃣ Available Operations")
        try:
            operations = await client.get_operations()
            print("📋 Available operations:")
            for op in operations.get("operations", []):
                options_str = f" (Options: {', '.join(op.get('options', []))})" if op.get('options') else ""
                question_req = " [Requires Question]" if op.get('requires_question') else ""
                print(f"   • {op['name']}: {op['description']}{options_str}{question_req}")
        except Exception as e:
            print(f"❌ Failed to get operations: {e}")
            return
        
        # Use standardized sample text for demonstrations
        sample_text = get_sample_text("climate_change")
        print(f"\n📖 Sample Text (first 100 chars): {sample_text[:100]}...")
        
        # 3. Text Summarization
        print_section("3️⃣ Text Summarization")
        result = await client.process_text(
            text=sample_text,
            operation="summarize",
            options={"max_length": 50}
        )
        if result:
            print_result(result, "summarize")
        else:
            print("❌ Summarization failed - check logs for details")
        
        # 4. Sentiment Analysis
        print_section("4️⃣ Sentiment Analysis")
        result = await client.process_text(
            text=sample_text,
            operation="sentiment"
        )
        if result:
            print_result(result, "sentiment")
        else:
            print("❌ Sentiment analysis failed - check logs for details")
        
        # 5. Key Points Extraction
        print_section("5️⃣ Key Points Extraction")
        result = await client.process_text(
            text=sample_text,
            operation="key_points",
            options={"max_points": 3}
        )
        if result:
            print_result(result, "key_points")
        else:
            print("❌ Key points extraction failed - check logs for details")
        
        # 6. Question Generation
        print_section("6️⃣ Question Generation")
        result = await client.process_text(
            text=sample_text,
            operation="questions",
            options={"num_questions": 3}
        )
        if result:
            print_result(result, "questions")
        else:
            print("❌ Question generation failed - check logs for details")
        
        # 7. Question & Answer
        print_section("7️⃣ Question & Answer")
        question = "What is the main cause of climate change mentioned in the text?"
        print(f"❓ Question: {question}")
        result = await client.process_text(
            text=sample_text,
            operation="qa",
            question=question
        )
        if result:
            print_result(result, "qa")
        else:
            print("❌ Q&A failed - check logs for details")

async def demonstrate_different_text_types():
    """Demonstrate processing different types of text."""
    
    print_header("Processing Different Text Types")
    
    async with APIClient() as client:
        
        for text_type, text_content in STANDARD_SAMPLE_TEXTS.items():
            print_section(f"📄 Processing {text_type.replace('_', ' ').title()} Text")
            
            # Show first 100 characters
            print(f"Text preview: {text_content[:100]}...")
            
            # Analyze sentiment for each text type
            result = await client.process_text(
                text=text_content,
                operation="sentiment"
            )
            if result:
                sentiment = result.get("sentiment", {})
                print(f"📊 Sentiment: {sentiment.get('sentiment', 'Unknown')} "
                      f"({sentiment.get('confidence', 0):.1%} confidence)")
            else:
                print(f"❌ Failed to analyze {text_type} - check logs for details")

async def demonstrate_error_handling():
    """Demonstrate error handling scenarios."""
    
    print_header("Error Handling Examples")
    
    async with APIClient() as client:
        
        # 1. Empty text
        print_section("1️⃣ Empty Text Error")
        try:
            await client.process_text(text="", operation="summarize")
        except Exception as e:
            print(f"✅ Correctly caught error: {e}")
        
        # 2. Invalid operation
        print_section("2️⃣ Invalid Operation Error")
        try:
            await client.process_text(text="Valid text", operation="invalid_op")
        except Exception as e:
            print(f"✅ Correctly caught error: {e}")
        
        # 3. Missing question for Q&A
        print_section("3️⃣ Missing Question for Q&A")
        try:
            await client.process_text(text="Valid text", operation="qa")
        except Exception as e:
            print(f"✅ Correctly caught error: {e}")
        
        # 4. Text too long
        print_section("4️⃣ Text Too Long Error")
        try:
            long_text = "A" * 15000  # Exceeds max_length of 10000
            await client.process_text(text=long_text, operation="summarize")
        except Exception as e:
            print(f"✅ Correctly caught error: {e}")

async def performance_benchmark():
    """Run a simple performance benchmark."""
    
    print_header("Performance Benchmark")
    
    async with APIClient() as client:
        
        operations = ["summarize", "sentiment", "key_points"]
        text = STANDARD_SAMPLE_TEXTS["ai_technology"]
        
        print(f"📊 Running benchmark with {len(operations)} operations...")
        print(f"📖 Text length: {len(text)} characters")
        
        total_time = 0
        results = {}
        
        for operation in operations:
            print(f"\n⏱️  Testing {operation}...")
            start_time = time.time()
            
            result = await client.process_text(text=text, operation=operation)
            if result:
                processing_time = result.get("processing_time", 0)
                total_time += processing_time
                results[operation] = {
                    "success": True,
                    "processing_time": processing_time
                }
                print(f"   ✅ Completed in {processing_time:.2f}s")
            else:
                results[operation] = {
                    "success": False,
                    "error": "Processing failed"
                }
                print(f"   ❌ Failed - check logs for details")
        
        print(f"\n📊 Benchmark Results:")
        print(f"   Total processing time: {total_time:.2f}s")
        print(f"   Average per operation: {total_time/len(operations):.2f}s")
        
        successful = sum(1 for r in results.values() if r.get("success"))
        print(f"   Success rate: {successful}/{len(operations)} ({successful/len(operations)*100:.1f}%)")

async def main():
    """Main function to run all examples."""
    
    print("🚀 Starting FastAPI-Streamlit-LLM Starter Template Examples")
    print("📋 This script will demonstrate:")
    print("   • Basic API operations")
    print("   • Different text types processing")
    print("   • Error handling")
    print("   • Performance benchmarking")
    print("\n⚠️  Make sure the FastAPI backend is running on http://localhost:8000")
    
    try:
        # Run all demonstrations
        await demonstrate_basic_operations()
        await demonstrate_different_text_types()
        await demonstrate_error_handling()
        await performance_benchmark()
        
        print_header("Examples Completed Successfully! 🎉")
        print("💡 Next steps:")
        print("   • Try the Streamlit frontend at http://localhost:8501")
        print("   • Explore the API documentation at http://localhost:8000/docs")
        print("   • Check out custom_operation.py for extending functionality")
        print("   • Review integration_test.py for testing examples")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("💡 Make sure the FastAPI backend is running and accessible")

if __name__ == "__main__":
    asyncio.run(main()) 