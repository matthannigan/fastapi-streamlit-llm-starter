#!/usr/bin/env python3
"""
Concurrent Initialization Testing for LLM Security Scanner

This script tests thread safety and concurrent initialization behavior
of the lazy loading security scanner.

Usage:
    python scripts/test_concurrent_initialization.py [--concurrent-requests N] [--iterations M]
"""

import argparse
import asyncio
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.infrastructure.security.llm.config_loader import load_security_config
from app.infrastructure.security.llm.scanners.local_scanner import (
    LocalLLMSecurityScanner,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ConcurrentTestResult:
    """Result of a concurrent initialization test."""
    iteration: int
    request_id: int
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    error_message: str = ""
    scanner_count: int = 0
    initialized_scanners: int = 0


class ConcurrentInitializationTester:
    """Tester for concurrent initialization scenarios."""

    def __init__(self, max_concurrent_requests: int = 10, iterations: int = 3):
        self.max_concurrent_requests = max_concurrent_requests
        self.iterations = iterations
        self.results: list[ConcurrentTestResult] = []

    async def run_concurrent_requests(self, scanner: LocalLLMSecurityScanner,
                                    iteration: int, num_requests: int) -> list[ConcurrentTestResult]:
        """Run multiple concurrent requests against the scanner."""
        results = []

        async def single_request(request_id: int) -> ConcurrentTestResult:
            start_time = time.time()
            try:
                # Use different text for each request to avoid cache hits
                test_text = f"Test input {request_id} for iteration {iteration}"
                result = await scanner.validate_input(test_text)

                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                return ConcurrentTestResult(
                    iteration=iteration,
                    request_id=request_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    success=True,
                    scanner_count=len(scanner.scanner_configs),
                    initialized_scanners=len(scanner.scanners),
                )

            except Exception as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                return ConcurrentTestResult(
                    iteration=iteration,
                    request_id=request_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    success=False,
                    error_message=str(e),
                )

        # Create tasks for concurrent execution
        tasks = [single_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions in results
        processed_results: list[ConcurrentTestResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ConcurrentTestResult(
                    iteration=iteration,
                    request_id=i,
                    start_time=0,
                    end_time=0,
                    duration_ms=0,
                    success=False,
                    error_message=str(result),
                ))
            else:
                # Type: ignore - we've confirmed result is not an Exception above
                processed_results.append(result)  # type: ignore[arg-type]

        return processed_results

    async def test_concurrent_initialization(self) -> list[ConcurrentTestResult]:
        """Test concurrent initialization behavior."""
        logger.info(f"Testing concurrent initialization with {self.max_concurrent_requests} requests across {self.iterations} iterations")

        all_results = []

        for iteration in range(self.iterations):
            logger.info(f"Running iteration {iteration + 1}/{self.iterations}")

            # Create fresh scanner for each iteration
            config = load_security_config(environment="testing")

            # Lazy loading is controlled by the scanner implementation

            scanner = LocalLLMSecurityScanner(config=config)
            await scanner.initialize()

            # Run concurrent requests
            iteration_results = await self.run_concurrent_requests(
                scanner, iteration, self.max_concurrent_requests
            )

            all_results.extend(iteration_results)

            # Log iteration summary
            successful = [r for r in iteration_results if r.success]
            failed = [r for r in iteration_results if not r.success]

            if successful:
                avg_duration = sum(r.duration_ms for r in successful) / len(successful)
                max_duration = max(r.duration_ms for r in successful)
                min_duration = min(r.duration_ms for r in successful)

                logger.info(f"Iteration {iteration + 1} results:")
                logger.info(f"  Successful: {len(successful)}/{len(iteration_results)}")
                logger.info(f"  Average duration: {avg_duration:.1f}ms")
                logger.info(f"  Duration range: {min_duration:.1f}ms - {max_duration:.1f}ms")
                logger.info(f"  Scanners initialized: {successful[0].initialized_scanners}/{successful[0].scanner_count}" if successful else "  No successful requests")

            if failed:
                logger.warning(f"Failed requests: {len(failed)}")
                for failure in failed[:3]:  # Show first 3 failures
                    logger.warning(f"  Error: {failure.error_message}")

            # Small delay between iterations
            await asyncio.sleep(1)

        self.results = all_results
        return all_results

    async def test_scanner_isolation(self) -> list[ConcurrentTestResult]:
        """Test that different scanner instances don't interfere with each other."""
        logger.info("Testing scanner instance isolation")

        config = load_security_config(environment="testing")

        # Create multiple scanner instances
        scanners = [LocalLLMSecurityScanner(config=config) for _ in range(3)]

        # Initialize all scanners
        for i, scanner in enumerate(scanners):
            await scanner.initialize()
            logger.info(f"Scanner {i} initialized with {len(scanner.scanner_configs)} configured scanners")

        # Run concurrent requests across all scanners
        async def request_on_scanner(scanner_id: int, request_id: int) -> ConcurrentTestResult:
            start_time = time.time()
            try:
                scanner = scanners[scanner_id]
                test_text = f"Test for scanner {scanner_id}, request {request_id}"
                await scanner.validate_input(test_text)

                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                return ConcurrentTestResult(
                    iteration=99,  # Special iteration number
                    request_id=request_id * 10 + scanner_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    success=True,
                    scanner_count=len(scanner.scanner_configs),
                    initialized_scanners=len(scanner.scanners),
                )

            except Exception as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                return ConcurrentTestResult(
                    iteration=99,
                    request_id=request_id * 10 + scanner_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    success=False,
                    error_message=str(e),
                )

        # Create mixed requests across different scanners
        tasks = []
        for i in range(15):  # 15 total requests
            scanner_id = i % 3  # Round-robin between scanners
            tasks.append(request_on_scanner(scanner_id, i))

        isolation_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results: list[ConcurrentTestResult] = []
        for i, result in enumerate(isolation_results):
            if isinstance(result, Exception):
                processed_results.append(ConcurrentTestResult(
                    iteration=99,
                    request_id=i,
                    start_time=0,
                    end_time=0,
                    duration_ms=0,
                    success=False,
                    error_message=str(result),
                ))
            else:
                # Type: ignore - we've confirmed result is not an Exception above
                processed_results.append(result)  # type: ignore[arg-type]

        # Log isolation test results
        successful = [r for r in processed_results if r.success]
        logger.info(f"Isolation test results: {len(successful)}/{len(processed_results)} successful")

        return processed_results

    def analyze_results(self, results: list[ConcurrentTestResult]) -> dict[str, Any]:
        """Analyze test results and return summary statistics."""
        if not results:
            return {"error": "No results to analyze"}

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        analysis: dict[str, Any] = {
            "total_requests": len(results),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": len(successful) / len(results) * 100 if results else 0,
        }

        if successful:
            durations = [r.duration_ms for r in successful]
            analysis.update({
                "avg_duration_ms": sum(durations) / len(durations),
                "max_duration_ms": max(durations),
                "min_duration_ms": min(durations),
                "median_duration_ms": sorted(durations)[len(durations) // 2],
            })

            # Analyze initialization patterns
            init_patterns: dict[str, int] = {}
            for r in successful:
                key = f"{r.initialized_scanners}/{r.scanner_count}"
                init_patterns[key] = init_patterns.get(key, 0) + 1

            analysis["initialization_patterns"] = init_patterns

            # Check for thread safety issues (duplicate initializations)
            if len(set(r.initialized_scanners for r in successful)) > 1:
                analysis["thread_safety_warning"] = "Different scanner counts detected - possible race condition"
            else:
                analysis["thread_safety_status"] = "No thread safety issues detected"

        if failed:
            error_types: dict[str, int] = {}
            for r in failed:
                error_type = r.error_message.split(':')[0]  # Get first part of error message
                error_types[error_type] = error_types.get(error_type, 0) + 1

            analysis["error_types"] = error_types

        return analysis

    def print_report(self, analysis: dict[str, Any]) -> None:
        """Print a formatted report of the test results."""
        print("\n" + "=" * 60)
        print("CONCURRENT INITIALIZATION TEST REPORT")
        print("=" * 60)

        print("\n📊 Overall Results:")
        print(f"  Total requests: {analysis['total_requests']}")
        print(f"  Successful: {analysis['successful_requests']}")
        print(f"  Failed: {analysis['failed_requests']}")
        print(f"  Success rate: {analysis['success_rate']:.1f}%")

        if 'avg_duration_ms' in analysis:
            print("\n⏱️  Performance Metrics:")
            print(f"  Average duration: {analysis['avg_duration_ms']:.1f}ms")
            print(f"  Min duration: {analysis['min_duration_ms']:.1f}ms")
            print(f"  Max duration: {analysis['max_duration_ms']:.1f}ms")
            print(f"  Median duration: {analysis['median_duration_ms']:.1f}ms")

        if 'initialization_patterns' in analysis:
            print("\n🔧 Initialization Patterns:")
            for pattern, count in analysis['initialization_patterns'].items():
                print(f"  {pattern} scanners: {count} requests")

        if 'thread_safety_status' in analysis:
            print("\n🔒 Thread Safety:")
            status = analysis.get('thread_safety_status', analysis.get('thread_safety_warning', ''))
            icon = "✅" if "No issues" in status else "⚠️"
            print(f"  {icon} {status}")

        if 'error_types' in analysis:
            print("\n❌ Error Summary:")
            for error_type, count in analysis['error_types'].items():
                print(f"  {error_type}: {count} occurrences")

        print("\n" + "=" * 60)

    async def run_tests(self) -> dict[str, Any]:
        """Run all concurrent initialization tests."""
        logger.info("Starting concurrent initialization tests")

        # Test 1: Concurrent requests to single scanner
        logger.info("Test 1: Concurrent requests to single scanner")
        concurrent_results = await self.test_concurrent_initialization()

        # Test 2: Scanner isolation
        logger.info("Test 2: Scanner instance isolation")
        isolation_results = await self.test_scanner_isolation()

        # Combine and analyze all results
        all_results = concurrent_results + isolation_results
        analysis = self.analyze_results(all_results)

        # Print report
        self.print_report(analysis)

        return analysis


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test concurrent initialization of LLM Security Scanner")
    parser.add_argument("--concurrent-requests", "-c", type=int, default=10,
                       help="Number of concurrent requests (default: 10)")
    parser.add_argument("--iterations", "-i", type=int, default=3,
                       help="Number of test iterations (default: 3)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    tester = ConcurrentInitializationTester(
        max_concurrent_requests=args.concurrent_requests,
        iterations=args.iterations
    )

    try:
        analysis = await tester.run_tests()

        # Exit with error code if success rate is too low
        if analysis.get('success_rate', 0) < 90:
            logger.error(f"Low success rate: {analysis.get('success_rate', 0):.1f}%")
            sys.exit(1)
        else:
            logger.info("All tests passed successfully")
            sys.exit(0)

    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Tests failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
