#!/usr/bin/env python3
"""
Integration test examples for the FastAPI-Streamlit-LLM Starter Template.

This script provides comprehensive testing scenarios to validate the entire system
including API endpoints, error handling, performance, and edge cases.
"""

import asyncio
import httpx
import time
import json
import pytest
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TestResult:
    """Test result data structure."""
    name: str
    status: TestStatus
    duration: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class IntegrationTester:
    """Comprehensive integration tester for the FastAPI-Streamlit-LLM system."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.results: List[TestResult] = []
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=60.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    def print_header(self, title: str):
        """Print formatted test section header."""
        print(f"\n{'='*70}")
        print(f"🧪 {title}")
        print(f"{'='*70}")
    
    def print_test_start(self, test_name: str):
        """Print test start message."""
        print(f"\n🔄 Running: {test_name}")
    
    def print_test_result(self, result: TestResult):
        """Print formatted test result."""
        status_emoji = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.SKIPPED: "⏭️"
        }
        
        emoji = status_emoji.get(result.status, "❓")
        print(f"{emoji} {result.name} ({result.duration:.2f}s)")
        
        if result.error:
            print(f"   Error: {result.error}")
        
        if result.details:
            for key, value in result.details.items():
                print(f"   {key}: {value}")
    
    async def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Run a single test and capture results."""
        self.print_test_start(test_name)
        start_time = time.time()
        
        try:
            details = await test_func(*args, **kwargs)
            duration = time.time() - start_time
            result = TestResult(
                name=test_name,
                status=TestStatus.PASSED,
                duration=duration,
                details=details
            )
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult(
                name=test_name,
                status=TestStatus.FAILED,
                duration=duration,
                error=str(e)
            )
        
        self.results.append(result)
        self.print_test_result(result)
        return result
    
    async def test_api_health(self) -> Dict[str, Any]:
        """Test API health endpoint."""
        response = await self.session.get(f"{self.api_url}/v1/health")
        response.raise_for_status()
        
        health_data = response.json()
        
        # Validate response structure
        assert "status" in health_data
        assert "ai_model_available" in health_data
        assert "timestamp" in health_data
        
        return {
            "status": health_data["status"],
            "ai_available": health_data["ai_model_available"],
            "response_time": response.elapsed.total_seconds()
        }
    
    async def test_operations_endpoint(self) -> Dict[str, Any]:
        """Test operations listing endpoint."""
        response = await self.session.get(f"{self.api_url}/operations")
        response.raise_for_status()
        
        ops_data = response.json()
        
        # Validate response structure
        assert "operations" in ops_data
        assert isinstance(ops_data["operations"], list)
        assert len(ops_data["operations"]) > 0
        
        # Validate each operation has required fields
        for op in ops_data["operations"]:
            assert "id" in op
            assert "name" in op
            assert "description" in op
            assert "options" in op
        
        return {
            "operation_count": len(ops_data["operations"]),
            "operations": [op["id"] for op in ops_data["operations"]]
        }
    
    async def test_text_summarization(self) -> Dict[str, Any]:
        """Test text summarization operation."""
        test_text = """
        The rapid advancement of artificial intelligence has transformed numerous industries. 
        Machine learning algorithms now power everything from recommendation systems to 
        autonomous vehicles. Natural language processing has enabled chatbots and virtual 
        assistants to understand and respond to human queries with increasing sophistication. 
        Computer vision systems can now identify objects, faces, and even emotions with 
        remarkable accuracy. As AI continues to evolve, it promises to revolutionize 
        healthcare, education, finance, and countless other sectors.
        """
        
        payload = {
            "text": test_text.strip(),
            "operation": "summarize",
            "options": {"max_length": 50}
        }
        
        response = await self.session.post(f"{self.api_url}/process", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Validate response structure
        assert result["success"] is True
        assert "result" in result
        assert "processing_time" in result
        assert len(result["result"]) > 0
        
        return {
            "summary_length": len(result["result"]),
            "processing_time": result["processing_time"],
            "original_length": len(test_text)
        }
    
    async def test_sentiment_analysis(self) -> Dict[str, Any]:
        """Test sentiment analysis operation."""
        test_cases = [
            ("I absolutely love this new technology! It's amazing!", "positive"),
            ("This is terrible and completely useless.", "negative"),
            ("The weather is okay today.", "neutral")
        ]
        
        results = []
        
        for text, expected_sentiment in test_cases:
            payload = {
                "text": text,
                "operation": "sentiment"
            }
            
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Validate response structure
            assert result["success"] is True
            assert "sentiment" in result
            assert "sentiment" in result["sentiment"]
            assert "confidence" in result["sentiment"]
            
            sentiment_data = result["sentiment"]
            results.append({
                "text": text[:30] + "...",
                "expected": expected_sentiment,
                "actual": sentiment_data["sentiment"],
                "confidence": sentiment_data["confidence"]
            })
        
        return {"test_cases": results}
    
    async def test_key_points_extraction(self) -> Dict[str, Any]:
        """Test key points extraction operation."""
        test_text = """
        Climate change is one of the most pressing issues of our time. Rising global 
        temperatures are causing ice caps to melt, leading to rising sea levels. 
        Extreme weather events are becoming more frequent and severe. Governments 
        worldwide are implementing policies to reduce carbon emissions. Renewable 
        energy sources like solar and wind power are becoming more cost-effective. 
        Individual actions, such as reducing energy consumption and using public 
        transportation, can also make a difference.
        """
        
        payload = {
            "text": test_text.strip(),
            "operation": "key_points",
            "options": {"max_points": 4}
        }
        
        response = await self.session.post(f"{self.api_url}/process", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Validate response structure
        assert result["success"] is True
        assert "key_points" in result
        assert isinstance(result["key_points"], list)
        assert len(result["key_points"]) > 0
        
        return {
            "points_extracted": len(result["key_points"]),
            "points": result["key_points"]
        }
    
    async def test_question_generation(self) -> Dict[str, Any]:
        """Test question generation operation."""
        test_text = """
        The Internet of Things (IoT) refers to the network of physical devices 
        embedded with sensors, software, and connectivity that enables them to 
        collect and exchange data. Smart homes use IoT devices to automate lighting, 
        heating, and security systems. In healthcare, IoT devices can monitor 
        patient vital signs remotely. Industrial IoT applications help optimize 
        manufacturing processes and predict equipment failures.
        """
        
        payload = {
            "text": test_text.strip(),
            "operation": "questions",
            "options": {"num_questions": 3}
        }
        
        response = await self.session.post(f"{self.api_url}/process", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Validate response structure
        assert result["success"] is True
        assert "questions" in result
        assert isinstance(result["questions"], list)
        assert len(result["questions"]) > 0
        
        return {
            "questions_generated": len(result["questions"]),
            "questions": result["questions"]
        }
    
    async def test_question_answering(self) -> Dict[str, Any]:
        """Test question answering operation."""
        test_text = """
        Blockchain technology is a distributed ledger system that maintains a 
        continuously growing list of records, called blocks, which are linked 
        and secured using cryptography. Bitcoin was the first successful 
        implementation of blockchain technology, created by Satoshi Nakamoto 
        in 2008. Blockchain provides transparency, security, and decentralization, 
        making it useful for applications beyond cryptocurrency, including 
        supply chain management and digital identity verification.
        """
        
        test_questions = [
            "Who created Bitcoin?",
            "What year was Bitcoin created?",
            "What are the main benefits of blockchain technology?"
        ]
        
        results = []
        
        for question in test_questions:
            payload = {
                "text": test_text.strip(),
                "operation": "qa",
                "question": question
            }
            
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Validate response structure
            assert result["success"] is True
            assert "result" in result
            assert len(result["result"]) > 0
            
            results.append({
                "question": question,
                "answer": result["result"],
                "processing_time": result.get("processing_time", 0)
            })
        
        return {"qa_pairs": results}
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test various error scenarios."""
        error_tests = []
        
        # Test 1: Empty text
        try:
            payload = {"text": "", "operation": "summarize"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "empty_text",
                "status_code": response.status_code,
                "handled": response.status_code == 422
            })
        except Exception as e:
            error_tests.append({
                "test": "empty_text",
                "error": str(e),
                "handled": True
            })
        
        # Test 2: Invalid operation
        try:
            payload = {"text": "Valid text", "operation": "invalid_operation"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "invalid_operation",
                "status_code": response.status_code,
                "handled": response.status_code == 422
            })
        except Exception as e:
            error_tests.append({
                "test": "invalid_operation",
                "error": str(e),
                "handled": True
            })
        
        # Test 3: Missing question for Q&A
        try:
            payload = {"text": "Valid text", "operation": "qa"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "missing_question",
                "status_code": response.status_code,
                "handled": response.status_code == 400
            })
        except Exception as e:
            error_tests.append({
                "test": "missing_question",
                "error": str(e),
                "handled": True
            })
        
        # Test 4: Text too long
        try:
            long_text = "A" * 15000  # Exceeds max_length
            payload = {"text": long_text, "operation": "summarize"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "text_too_long",
                "status_code": response.status_code,
                "handled": response.status_code == 422
            })
        except Exception as e:
            error_tests.append({
                "test": "text_too_long",
                "error": str(e),
                "handled": True
            })
        
        handled_count = sum(1 for test in error_tests if test.get("handled", False))
        
        return {
            "total_error_tests": len(error_tests),
            "properly_handled": handled_count,
            "error_details": error_tests
        }
    
    async def test_performance_benchmark(self) -> Dict[str, Any]:
        """Test system performance with multiple operations."""
        operations = ["summarize", "sentiment", "key_points"]
        test_text = """
        Machine learning is a subset of artificial intelligence that enables 
        computers to learn and improve from experience without being explicitly 
        programmed. It uses algorithms to analyze data, identify patterns, and 
        make predictions or decisions. Common applications include image recognition, 
        natural language processing, recommendation systems, and predictive analytics.
        """
        
        performance_results = []
        total_time = 0
        
        for operation in operations:
            start_time = time.time()
            
            payload = {
                "text": test_text.strip(),
                "operation": operation
            }
            
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            response.raise_for_status()
            
            result = response.json()
            duration = time.time() - start_time
            total_time += duration
            
            performance_results.append({
                "operation": operation,
                "duration": duration,
                "processing_time": result.get("processing_time", 0),
                "success": result.get("success", False)
            })
        
        return {
            "total_time": total_time,
            "average_time": total_time / len(operations),
            "operations_tested": len(operations),
            "performance_details": performance_results
        }
    
    async def test_concurrent_requests(self) -> Dict[str, Any]:
        """Test system behavior under concurrent load."""
        concurrent_count = 5
        test_text = "This is a test for concurrent processing."
        
        async def single_request():
            payload = {
                "text": test_text,
                "operation": "sentiment"
            }
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            return response.status_code == 200
        
        start_time = time.time()
        
        # Run concurrent requests
        tasks = [single_request() for _ in range(concurrent_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        successful = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if isinstance(r, Exception))
        
        return {
            "concurrent_requests": concurrent_count,
            "successful": successful,
            "failed": failed,
            "total_duration": duration,
            "requests_per_second": concurrent_count / duration
        }
    
    async def run_all_tests(self):
        """Run the complete test suite."""
        self.print_header("FastAPI-Streamlit-LLM Integration Test Suite")
        
        print("🚀 Starting comprehensive integration tests...")
        print(f"📡 API URL: {self.api_url}")
        print(f"⏰ Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Core functionality tests
        self.print_header("Core Functionality Tests")
        await self.run_test("API Health Check", self.test_api_health)
        await self.run_test("Operations Endpoint", self.test_operations_endpoint)
        
        # Text processing operation tests
        self.print_header("Text Processing Operation Tests")
        await self.run_test("Text Summarization", self.test_text_summarization)
        await self.run_test("Sentiment Analysis", self.test_sentiment_analysis)
        await self.run_test("Key Points Extraction", self.test_key_points_extraction)
        await self.run_test("Question Generation", self.test_question_generation)
        await self.run_test("Question Answering", self.test_question_answering)
        
        # Error handling tests
        self.print_header("Error Handling Tests")
        await self.run_test("Error Handling", self.test_error_handling)
        
        # Performance tests
        self.print_header("Performance Tests")
        await self.run_test("Performance Benchmark", self.test_performance_benchmark)
        await self.run_test("Concurrent Requests", self.test_concurrent_requests)
        
        # Generate test report
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate and display comprehensive test report."""
        self.print_header("Test Report Summary")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed_tests = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        total_duration = sum(r.duration for r in self.results)
        
        print(f"📊 Test Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"   ⏱️  Total Duration: {total_duration:.2f}s")
        print(f"   🕐 Average Test Time: {total_duration/total_tests:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if result.status == TestStatus.FAILED:
                    print(f"   • {result.name}: {result.error}")
        
        print(f"\n💡 Recommendations:")
        if passed_tests == total_tests:
            print("   🎉 All tests passed! System is working correctly.")
            print("   • Consider running load tests for production readiness")
            print("   • Monitor performance metrics in production")
        else:
            print("   🔧 Some tests failed. Please review and fix issues:")
            print("   • Check API server is running and accessible")
            print("   • Verify AI model configuration and API keys")
            print("   • Review error logs for detailed diagnostics")
        
        print(f"\n📋 Next Steps:")
        print("   • Run frontend tests with Streamlit interface")
        print("   • Test with different text types and lengths")
        print("   • Validate production deployment configuration")
        print("   • Set up monitoring and alerting")

async def main():
    """Main function to run integration tests."""
    
    print("🧪 FastAPI-Streamlit-LLM Starter Template - Integration Tests")
    print("=" * 80)
    print("This script runs comprehensive integration tests to validate the entire system.")
    print("\n⚠️  Prerequisites:")
    print("   • FastAPI backend running on http://localhost:8000")
    print("   • Valid AI model configuration (Gemini API key)")
    print("   • All dependencies installed")
    
    # Allow user to confirm before starting
    try:
        input("\n🚀 Press Enter to start tests (Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\n⏹️  Tests cancelled by user")
        return
    
    try:
        async with IntegrationTester() as tester:
            await tester.run_all_tests()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        print("💡 Make sure the FastAPI backend is running and accessible")

if __name__ == "__main__":
    asyncio.run(main()) 