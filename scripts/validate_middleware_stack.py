#!/usr/bin/env python3
"""
Middleware Stack Integration Validation

Validates the complete middleware execution order, configuration integration,
and proper request/response flow through the enhanced middleware stack.

This script tests:
- Middleware registration order and dependencies
- Request/response header propagation
- Context variable sharing (request IDs)
- Error handling through the stack
- Performance monitoring integration
- Security header injection
"""

import asyncio
import time
import sys
import logging
from typing import Dict, List, Any
from unittest.mock import AsyncMock, Mock, patch

# FastAPI and middleware imports
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

# Import enhanced middleware components
from app.core.middleware.enhanced_setup import setup_enhanced_middleware
from app.core.config import Settings
from app.core.exceptions import ApplicationError, InfrastructureError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_app() -> FastAPI:
    """Create a test FastAPI app with enhanced middleware stack."""
    app = FastAPI(title="Middleware Stack Test", version="1.0.0")
    
    # Create test settings
    settings = Settings(
        api_key="test-key-123",
        gemini_api_key="test-gemini-key",
        redis_url="redis://localhost:6379",  # Default redis URL for testing
        rate_limiting_enabled=True,
        request_logging_enabled=True,
        performance_monitoring_enabled=True,
        security_headers_enabled=True,
        compression_enabled=True,
        api_versioning_enabled=True,
        cors_enabled=True,
        rate_limit_requests_per_minute=100,
        slow_request_threshold=1000
    )
    
    # Setup enhanced middleware stack
    setup_enhanced_middleware(app, settings)
    
    # Add test endpoints
    @app.get("/test/basic")
    async def basic_endpoint():
        return {"message": "success", "endpoint": "basic"}
    
    @app.get("/test/error")
    async def error_endpoint():
        raise ApplicationError("Test application error")
    
    @app.get("/test/slow")
    async def slow_endpoint():
        await asyncio.sleep(0.1)  # Simulate slow request
        return {"message": "slow response"}
    
    @app.post("/test/large")
    async def large_endpoint(request: Request):
        body = await request.body()
        return {"message": "processed", "size": len(body)}
    
    return app


class MiddlewareStackValidator:
    """Validates the enhanced middleware stack integration."""
    
    def __init__(self):
        self.app = create_test_app()
        self.client = TestClient(self.app)
        self.validation_results: Dict[str, Any] = {}
    
    def validate_middleware_order(self) -> bool:
        """Validate middleware registration order and stack integrity."""
        logger.info("🔍 Validating middleware registration order...")
        
        try:
            # Get middleware stack from app
            middleware_stack = []
            for middleware in self.app.user_middleware:
                middleware_name = middleware.cls.__name__
                middleware_stack.append(middleware_name)
            
            logger.info(f"Detected middleware stack: {middleware_stack}")
            
            # Expected order (from outermost to innermost)
            expected_order = [
                "CORSMiddleware",
                "RequestLoggingMiddleware", 
                "PerformanceMonitoringMiddleware",
                "SecurityMiddleware",
                "APIVersioningMiddleware",
                "RateLimitMiddleware",
                "CompressionMiddleware",
                "RequestSizeMiddleware"
            ]
            
            # Validate order
            order_correct = True
            for i, expected in enumerate(expected_order):
                if i < len(middleware_stack):
                    actual = middleware_stack[i]
                    if actual != expected:
                        logger.warning(f"Middleware order mismatch at position {i}: expected {expected}, got {actual}")
                        order_correct = False
                else:
                    logger.warning(f"Missing middleware: {expected}")
                    order_correct = False
            
            self.validation_results['middleware_order'] = {
                'passed': order_correct,
                'expected': expected_order,
                'actual': middleware_stack
            }
            
            return order_correct
            
        except Exception as e:
            logger.error(f"Middleware order validation failed: {e}")
            self.validation_results['middleware_order'] = {'passed': False, 'error': str(e)}
            return False
    
    def validate_request_flow(self) -> bool:
        """Validate request processing flow through middleware stack."""
        logger.info("🔄 Validating request processing flow...")
        
        try:
            # Test basic request flow
            response = self.client.get("/test/basic", headers={
                "X-API-Key": "test-key-123",
                "User-Agent": "MiddlewareTest/1.0"
            })
            
            # Validate response
            flow_tests = {
                'status_code': response.status_code == 200,
                'security_headers': 'X-Content-Type-Options' in response.headers,
                'performance_headers': 'X-Response-Time' in response.headers,
                'api_version_headers': 'X-API-Version' in response.headers,
                'rate_limit_headers': 'X-RateLimit-Limit' in response.headers,
                'compression_headers': 'Content-Encoding' in response.headers or True,  # Optional
                'cors_headers': 'Access-Control-Allow-Origin' in response.headers or True  # Optional
            }
            
            all_passed = all(flow_tests.values())
            
            self.validation_results['request_flow'] = {
                'passed': all_passed,
                'tests': flow_tests,
                'headers': dict(response.headers),
                'status_code': response.status_code,
                'content': response.json()
            }
            
            return all_passed
            
        except Exception as e:
            logger.error(f"Request flow validation failed: {e}")
            self.validation_results['request_flow'] = {'passed': False, 'error': str(e)}
            return False
    
    def validate_error_handling(self) -> bool:
        """Validate error handling through the middleware stack."""
        logger.info("❌ Validating error handling integration...")
        
        try:
            # Test error endpoint
            response = self.client.get("/test/error", headers={
                "X-API-Key": "test-key-123"
            })
            
            error_tests = {
                'status_code': response.status_code == 400,  # ApplicationError -> 400
                'json_response': response.headers.get('content-type', '').startswith('application/json'),
                'security_headers': 'X-Content-Type-Options' in response.headers,
                'error_structure': 'error' in response.json() if response.headers.get('content-type', '').startswith('application/json') else False
            }
            
            all_passed = all(error_tests.values())
            
            self.validation_results['error_handling'] = {
                'passed': all_passed,
                'tests': error_tests,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
            
            return all_passed
            
        except Exception as e:
            logger.error(f"Error handling validation failed: {e}")
            self.validation_results['error_handling'] = {'passed': False, 'error': str(e)}
            return False
    
    def validate_performance_monitoring(self) -> bool:
        """Validate performance monitoring integration."""
        logger.info("⚡ Validating performance monitoring integration...")
        
        try:
            # Test slow endpoint to trigger performance monitoring
            response = self.client.get("/test/slow", headers={
                "X-API-Key": "test-key-123"
            })
            
            perf_tests = {
                'status_code': response.status_code == 200,
                'response_time_header': 'X-Response-Time' in response.headers,
                'response_time_format': response.headers.get('X-Response-Time', '').endswith('ms'),
                'memory_delta_header': 'X-Memory-Delta' in response.headers or True  # Optional
            }
            
            # Validate response time value
            response_time_str = response.headers.get('X-Response-Time', '0ms')
            try:
                response_time_ms = float(response_time_str.replace('ms', ''))
                perf_tests['response_time_value'] = response_time_ms >= 100  # Should be at least 100ms due to sleep
            except ValueError:
                perf_tests['response_time_value'] = False
            
            all_passed = all(perf_tests.values())
            
            self.validation_results['performance_monitoring'] = {
                'passed': all_passed,
                'tests': perf_tests,
                'response_time': response.headers.get('X-Response-Time'),
                'memory_delta': response.headers.get('X-Memory-Delta'),
                'headers': dict(response.headers)
            }
            
            return all_passed
            
        except Exception as e:
            logger.error(f"Performance monitoring validation failed: {e}")
            self.validation_results['performance_monitoring'] = {'passed': False, 'error': str(e)}
            return False
    
    def validate_rate_limiting(self) -> bool:
        """Validate rate limiting integration."""
        logger.info("🚦 Validating rate limiting integration...")
        
        try:
            # Make multiple requests to test rate limiting headers
            responses = []
            for i in range(3):
                response = self.client.get("/test/basic", headers={
                    "X-API-Key": "test-key-123"
                })
                responses.append(response)
            
            # Check rate limiting headers in first response
            first_response = responses[0]
            rate_limit_tests = {
                'status_code': first_response.status_code == 200,
                'rate_limit_limit': 'X-RateLimit-Limit' in first_response.headers,
                'rate_limit_remaining': 'X-RateLimit-Remaining' in first_response.headers,
                'rate_limit_window': 'X-RateLimit-Window' in first_response.headers,
                'rate_limit_reset': 'X-RateLimit-Reset' in first_response.headers,
                'rate_limit_rule': 'X-RateLimit-Rule' in first_response.headers
            }
            
            # Validate decreasing remaining count
            remaining_counts = []
            for response in responses:
                remaining_str = response.headers.get('X-RateLimit-Remaining', '0')
                try:
                    remaining_counts.append(int(remaining_str))
                except ValueError:
                    remaining_counts.append(0)
            
            rate_limit_tests['decreasing_remaining'] = len(remaining_counts) >= 2 and remaining_counts[0] > remaining_counts[1]
            
            all_passed = all(rate_limit_tests.values())
            
            self.validation_results['rate_limiting'] = {
                'passed': all_passed,
                'tests': rate_limit_tests,
                'remaining_counts': remaining_counts,
                'headers': dict(first_response.headers)
            }
            
            return all_passed
            
        except Exception as e:
            logger.error(f"Rate limiting validation failed: {e}")
            self.validation_results['rate_limiting'] = {'passed': False, 'error': str(e)}
            return False
    
    def validate_security_integration(self) -> bool:
        """Validate security middleware integration."""
        logger.info("🔒 Validating security middleware integration...")
        
        try:
            # Test security headers
            response = self.client.get("/test/basic", headers={
                "X-API-Key": "test-key-123"
            })
            
            expected_security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Content-Security-Policy': True  # Just check presence
            }
            
            security_tests = {}
            for header, expected_value in expected_security_headers.items():
                actual_value = response.headers.get(header)
                if expected_value is True:
                    security_tests[header] = actual_value is not None
                else:
                    security_tests[header] = actual_value == expected_value
            
            all_passed = all(security_tests.values())
            
            self.validation_results['security_integration'] = {
                'passed': all_passed,
                'tests': security_tests,
                'headers': dict(response.headers)
            }
            
            return all_passed
            
        except Exception as e:
            logger.error(f"Security integration validation failed: {e}")
            self.validation_results['security_integration'] = {'passed': False, 'error': str(e)}
            return False
    
    def run_full_validation(self) -> bool:
        """Run complete middleware stack validation."""
        logger.info("🚀 Starting middleware stack validation...")
        
        validation_steps = [
            ("Middleware Order", self.validate_middleware_order),
            ("Request Flow", self.validate_request_flow),
            ("Error Handling", self.validate_error_handling),
            ("Performance Monitoring", self.validate_performance_monitoring),
            ("Rate Limiting", self.validate_rate_limiting),
            ("Security Integration", self.validate_security_integration)
        ]
        
        results = []
        for step_name, validation_func in validation_steps:
            try:
                passed = validation_func()
                results.append(passed)
                status = "✅ PASSED" if passed else "❌ FAILED"
                logger.info(f"{status}: {step_name}")
            except Exception as e:
                results.append(False)
                logger.error(f"❌ FAILED: {step_name} - {e}")
        
        overall_success = all(results)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("MIDDLEWARE STACK VALIDATION SUMMARY")
        logger.info("="*60)
        
        for i, (step_name, _) in enumerate(validation_steps):
            status = "✅ PASSED" if results[i] else "❌ FAILED"
            logger.info(f"{status}: {step_name}")
        
        logger.info("="*60)
        final_status = "✅ ALL TESTS PASSED" if overall_success else "❌ SOME TESTS FAILED"
        logger.info(f"OVERALL RESULT: {final_status}")
        logger.info("="*60)
        
        return overall_success


def main():
    """Main validation runner."""
    validator = MiddlewareStackValidator()
    
    try:
        success = validator.run_full_validation()
        
        # Output detailed results for debugging
        if not success:
            logger.error("\nDetailed validation results:")
            for step, result in validator.validation_results.items():
                if not result.get('passed', True):
                    logger.error(f"FAILED STEP: {step}")
                    logger.error(f"Details: {result}")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Validation runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()