#!/usr/bin/env python3
"""
Basic usage examples for the FastAPI-Streamlit-LLM Starter Template.

This script demonstrates how to interact with the API programmatically
and showcases all available text processing operations.
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

# Sample texts for different use cases
SAMPLE_TEXTS = {
    "climate_change": """
    Climate change represents one of the most significant challenges facing humanity today. 
    Rising global temperatures, caused primarily by increased greenhouse gas emissions, 
    are leading to more frequent extreme weather events, rising sea levels, and 
    disruptions to ecosystems worldwide. Scientists agree that immediate action is 
    required to mitigate these effects and transition to sustainable energy sources.
    The Paris Agreement, signed by nearly 200 countries, aims to limit global warming 
    to well below 2 degrees Celsius above pre-industrial levels.
    """,
    
    "technology": """
    Artificial intelligence is revolutionizing industries across the globe. From healthcare 
    diagnostics to autonomous vehicles, AI systems are becoming increasingly sophisticated 
    and capable. Machine learning algorithms can now process vast amounts of data to 
    identify patterns and make predictions with remarkable accuracy. However, this rapid 
    advancement also raises important questions about ethics, privacy, and the future 
    of human employment in an AI-driven world.
    """,
    
    "business": """
    The quarterly earnings report shows strong performance across all business units. 
    Revenue increased by 15% compared to the same period last year, driven primarily 
    by growth in our digital services division. Customer satisfaction scores have 
    improved significantly, and we've successfully launched three new products. 
    Looking ahead, we remain optimistic about market conditions and expect continued 
    growth in the coming quarters.
    """
}

class APIClient:
    """Simple API client for the FastAPI backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = await self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    async def get_operations(self) -> Dict[str, Any]:
        """Get available operations."""
        response = await self.session.get(f"{self.base_url}/operations")
        response.raise_for_status()
        return response.json()
    
    async def process_text(self, text: str, operation: str, question: str = None, 
                          options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process text with specified operation."""
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
        
        # Use climate change text for demonstrations
        sample_text = SAMPLE_TEXTS["climate_change"]
        print(f"\n📖 Sample Text (first 100 chars): {sample_text[:100]}...")
        
        # 3. Text Summarization
        print_section("3️⃣ Text Summarization")
        try:
            result = await client.process_text(
                text=sample_text,
                operation="summarize",
                options={"max_length": 50}
            )
            print_result(result, "summarize")
        except Exception as e:
            print(f"❌ Summarization failed: {e}")
        
        # 4. Sentiment Analysis
        print_section("4️⃣ Sentiment Analysis")
        try:
            result = await client.process_text(
                text=sample_text,
                operation="sentiment"
            )
            print_result(result, "sentiment")
        except Exception as e:
            print(f"❌ Sentiment analysis failed: {e}")
        
        # 5. Key Points Extraction
        print_section("5️⃣ Key Points Extraction")
        try:
            result = await client.process_text(
                text=sample_text,
                operation="key_points",
                options={"max_points": 4}
            )
            print_result(result, "key_points")
        except Exception as e:
            print(f"❌ Key points extraction failed: {e}")
        
        # 6. Question Generation
        print_section("6️⃣ Question Generation")
        try:
            result = await client.process_text(
                text=sample_text,
                operation="questions",
                options={"num_questions": 3}
            )
            print_result(result, "questions")
        except Exception as e:
            print(f"❌ Question generation failed: {e}")
        
        # 7. Question & Answer
        print_section("7️⃣ Question & Answer")
        try:
            question = "What is the main cause of climate change mentioned in the text?"
            print(f"❓ Question: {question}")
            result = await client.process_text(
                text=sample_text,
                operation="qa",
                question=question
            )
            print_result(result, "qa")
        except Exception as e:
            print(f"❌ Q&A failed: {e}")

async def demonstrate_different_text_types():
    """Demonstrate processing different types of text."""
    
    print_header("Processing Different Text Types")
    
    async with APIClient() as client:
        
        for text_type, text_content in SAMPLE_TEXTS.items():
            print_section(f"📄 Processing {text_type.replace('_', ' ').title()} Text")
            
            # Show first 100 characters
            print(f"Text preview: {text_content[:100]}...")
            
            # Analyze sentiment for each text type
            try:
                result = await client.process_text(
                    text=text_content,
                    operation="sentiment"
                )
                sentiment = result.get("sentiment", {})
                print(f"📊 Sentiment: {sentiment.get('sentiment', 'Unknown')} "
                      f"({sentiment.get('confidence', 0):.1%} confidence)")
            except Exception as e:
                print(f"❌ Failed to analyze {text_type}: {e}")

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
        text = SAMPLE_TEXTS["technology"]
        
        print(f"📊 Running benchmark with {len(operations)} operations...")
        print(f"📖 Text length: {len(text)} characters")
        
        total_time = 0
        results = {}
        
        for operation in operations:
            print(f"\n⏱️  Testing {operation}...")
            start_time = time.time()
            
            try:
                result = await client.process_text(text=text, operation=operation)
                processing_time = result.get("processing_time", 0)
                total_time += processing_time
                results[operation] = {
                    "success": True,
                    "processing_time": processing_time
                }
                print(f"   ✅ Completed in {processing_time:.2f}s")
            except Exception as e:
                results[operation] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"   ❌ Failed: {e}")
        
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