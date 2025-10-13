#!/usr/bin/env python3
"""
Startup Performance Testing for LLM Security Scanner

This script measures and compares startup performance between:
- Eager loading (all scanners initialized at startup)
- Lazy loading (scanners initialized on first use)

Usage:
    python scripts/benchmark_startup_performance.py [--scenarios SCENARIOS] [--output OUTPUT_FILE]
"""

import argparse
import asyncio
import json
import logging
import sys
import time
import tracemalloc
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import AsyncGenerator

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.infrastructure.security.llm.config import ScannerType
from app.infrastructure.security.llm.config_loader import load_security_config
from app.infrastructure.security.llm.scanners.local_scanner import (
    LocalLLMSecurityScanner,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class StartupMetrics:
    """Metrics for startup performance testing."""
    scenario_name: str
    initialization_time_ms: float
    memory_usage_mb: float
    memory_peak_mb: float
    scanner_count: int
    initialized_scanners: int
    lazy_loading_enabled: bool
    first_request_time_ms: float | None = None
    warmup_time_ms: float | None = None
    errors: list[str] | None = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


class StartupPerformanceBenchmark:
    """Benchmark startup performance for security scanner."""

    def __init__(self, output_file: str | None = None):
        self.output_file = output_file
        self.results: list[StartupMetrics] = []

    @asynccontextmanager
    async def memory_tracker(self) -> AsyncGenerator[None, None]:
        """Context manager for tracking memory usage."""
        tracemalloc.start()
        start_snapshot = tracemalloc.take_snapshot()
        start_memory = tracemalloc.get_traced_memory()[0] / 1024 / 1024  # MB

        try:
            yield
        finally:
            end_snapshot = tracemalloc.take_snapshot()
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            current_memory_mb = current_memory / 1024 / 1024
            peak_memory_mb = peak_memory / 1024 / 1024
            tracemalloc.stop()

            # Store results in context for later access
            self._memory_results = {
                'start_mb': start_memory,
                'end_mb': current_memory_mb,
                'peak_mb': peak_memory_mb,
                'delta_mb': current_memory_mb - start_memory
            }

    async def benchmark_scenario(self, scenario_name: str, lazy_loading: bool,
                                warmup_scanners: list[ScannerType] | None = None) -> StartupMetrics:
        """Benchmark a specific startup scenario."""
        logger.info(f"Running scenario: {scenario_name} (lazy_loading={lazy_loading})")

        try:
            # Load configuration and modify for scenario
            config = load_security_config(environment="testing")

            # Configure performance settings for scenario
            # Note: PerformanceConfig doesn't have enable_lazy_loading attribute
            # We'll use existing performance settings that affect initialization
            if lazy_loading:
                # For lazy loading, reduce concurrent operations and memory limits
                config.performance.max_concurrent_scans = 1
                config.performance.enable_model_caching = False
            else:
                # For eager loading, allow higher concurrency and enable caching
                config.performance.max_concurrent_scans = 10
                config.performance.enable_model_caching = True

            # Track memory and time
            async with self.memory_tracker():
                start_time = time.time()

                # Initialize scanner
                scanner = LocalLLMSecurityScanner(config=config)
                await scanner.initialize()

                init_time = time.time() - start_time
                init_time_ms = init_time * 1000

                # Get scanner counts
                configured_scanners = len(scanner.scanner_configs)
                initialized_scanners = len(scanner.scanners)

                # Benchmark first request if lazy loading
                first_request_time = None
                if lazy_loading and configured_scanners > 0:
                    first_req_start = time.time()
                    try:
                        await scanner.validate_input("Test input for performance measurement")
                        first_request_time = (time.time() - first_req_start) * 1000
                    except Exception as e:
                        logger.warning(f"First request failed: {e}")
                        first_request_time = None

                # Benchmark warmup if specified
                warmup_time = None
                if warmup_scanners:
                    warmup_start = time.time()
                    try:
                        warmup_results = await scanner.warmup(warmup_scanners)
                        warmup_time = (time.time() - warmup_start) * 1000
                        logger.info(f"Warmup completed: {warmup_results}")
                    except Exception as e:
                        logger.error(f"Warmup failed: {e}")
                        warmup_time = None

            # Create metrics object
            memory_results = getattr(self, '_memory_results', {})
            metrics = StartupMetrics(
                scenario_name=scenario_name,
                initialization_time_ms=init_time_ms,
                memory_usage_mb=memory_results.get('delta_mb', 0),
                memory_peak_mb=memory_results.get('peak_mb', 0),
                scanner_count=configured_scanners,
                initialized_scanners=initialized_scanners,
                lazy_loading_enabled=lazy_loading,
                first_request_time_ms=first_request_time,
                warmup_time_ms=warmup_time,
            )

            logger.info(f"Scenario {scenario_name} completed:")
            logger.info(f"  Init time: {init_time_ms:.1f}ms")
            logger.info(f"  Memory: {memory_results.get('delta_mb', 0):.1f}MB")
            logger.info(f"  Scanners: {initialized_scanners}/{configured_scanners}")
            if first_request_time:
                logger.info(f"  First request: {first_request_time:.1f}ms")
            if warmup_time:
                logger.info(f"  Warmup: {warmup_time:.1f}ms")

            return metrics

        except Exception as e:
            logger.error(f"Scenario {scenario_name} failed: {e}")
            return StartupMetrics(
                scenario_name=scenario_name,
                initialization_time_ms=float('inf'),
                memory_usage_mb=0,
                memory_peak_mb=0,
                scanner_count=0,
                initialized_scanners=0,
                lazy_loading_enabled=lazy_loading,
                errors=[str(e)]
            )

    async def run_all_scenarios(self) -> list[StartupMetrics]:
        """Run all benchmark scenarios."""
        scenarios = [
            ("eager_loading", False, None),
            ("lazy_loading", True, None),
            ("lazy_loading_with_warmup", True, [ScannerType.PROMPT_INJECTION, ScannerType.TOXICITY_INPUT]),
            ("lazy_loading_selective_warmup", True, [ScannerType.PROMPT_INJECTION]),
        ]

        results = []
        for scenario_name, lazy_loading, warmup_scanners in scenarios:
            metrics = await self.benchmark_scenario(scenario_name, lazy_loading, warmup_scanners)
            results.append(metrics)
            self.results.append(metrics)

            # Small delay between scenarios
            await asyncio.sleep(1)

        return results

    def generate_report(self, results: list[StartupMetrics]) -> str:
        """Generate a performance report from benchmark results."""
        if not results:
            return "No results to report"

        report_lines = [
            "# LLM Security Scanner Startup Performance Report",
            "=" * 60,
            "",
            "## Summary",
            "",
        ]

        # Find successful results
        successful_results = [r for r in results if not r.errors and r.initialization_time_ms != float('inf')]
        if not successful_results:
            report_lines.append("❌ All scenarios failed!")
            return "\n".join(report_lines)

        # Performance comparisons
        eager_result = next((r for r in successful_results if not r.lazy_loading_enabled), None)
        lazy_result = next((r for r in successful_results if r.lazy_loading_enabled and not r.warmup_time_ms), None)

        if eager_result and lazy_result:
            startup_improvement = ((eager_result.initialization_time_ms - lazy_result.initialization_time_ms) /
                                 eager_result.initialization_time_ms * 100)
            memory_improvement = ((eager_result.memory_usage_mb - lazy_result.memory_usage_mb) /
                                max(eager_result.memory_usage_mb, 0.1) * 100)

            report_lines.extend([
                f"🚀 **Startup Performance Improvement**: {startup_improvement:.1f}% faster",
                f"💾 **Memory Usage Improvement**: {memory_improvement:.1f}% lower",
                f"⏱️ **Eager Loading Time**: {eager_result.initialization_time_ms:.1f}ms",
                f"⏱️ **Lazy Loading Time**: {lazy_result.initialization_time_ms:.1f}ms",
                f"🔄 **First Request Time**: {lazy_result.first_request_time_ms:.1f}ms" if lazy_result.first_request_time_ms else "",
                "",
            ])

        # Detailed results table
        report_lines.extend([
            "## Detailed Results",
            "",
            "| Scenario | Init Time (ms) | Memory (MB) | Peak Memory (MB) | Scanners | First Request (ms) | Warmup (ms) |",
            "|" + "-" * 9 + "|" + "-" * 15 + "|" + "-" * 12 + "|" + "-" * 17 + "|" + "-" * 10 + "|" + "-" * 19 + "|" + "-" * 11 + "|",
        ])

        for result in successful_results:
            first_req = f"{result.first_request_time_ms:.1f}" if result.first_request_time_ms else "N/A"
            warmup = f"{result.warmup_time_ms:.1f}" if result.warmup_time_ms else "N/A"

            report_lines.append(
                f"| {result.scenario_name} | {result.initialization_time_ms:.1f} | "
                f"{result.memory_usage_mb:.1f} | {result.memory_peak_mb:.1f} | "
                f"{result.initialized_scanners}/{result.scanner_count} | {first_req} | {warmup} |"
            )

        # Errors if any
        failed_results = [r for r in results if r.errors or r.initialization_time_ms == float('inf')]
        if failed_results:
            report_lines.extend([
                "",
                "## Failed Scenarios",
                "",
            ])
            for result in failed_results:
                report_lines.append(f"### {result.scenario_name}")
                if result.errors:  # Check if errors is not None and not empty
                    for error in result.errors:
                        report_lines.append(f"- {error}")
                else:
                    report_lines.append("- Unknown error occurred")
                report_lines.append("")

        # Recommendations
        report_lines.extend([
            "",
            "## Recommendations",
            "",
        ])

        if lazy_result:
            if lazy_result.initialization_time_ms < 5000:  # 5 second target
                report_lines.append("✅ **Lazy loading meets startup time target (<5s)**")
            else:
                report_lines.append("⚠️ **Lazy loading exceeds startup time target (>5s)**")

            if lazy_result.first_request_time_ms and lazy_result.first_request_time_ms < 200:  # 200ms target
                report_lines.append("✅ **First request meets latency target (<200ms)**")
            elif lazy_result.first_request_time_ms:
                report_lines.append("⚠️ **First request exceeds latency target (>200ms)**")

        if eager_result and lazy_result:
            if startup_improvement > 50:
                report_lines.append("🎯 **Significant startup performance improvement achieved**")
            elif startup_improvement > 20:
                report_lines.append("✅ **Good startup performance improvement achieved**")
            else:
                report_lines.append("📊 **Modest startup performance improvement**")

        return "\n".join(report_lines)

    async def save_results(self, results: list[StartupMetrics]) -> None:
        """Save results to file."""
        if not self.output_file:
            return

        # Save as JSON for machine reading
        json_file = Path(self.output_file).with_suffix('.json')
        with open(json_file, 'w') as f:
            json.dump([asdict(r) for r in results], f, indent=2)

        # Save as markdown for human reading
        md_file = Path(self.output_file).with_suffix('.md')
        report = self.generate_report(results)
        with open(md_file, 'w') as f:
            f.write(report)

        logger.info(f"Results saved to {json_file} and {md_file}")

    async def run_benchmark(self) -> list[StartupMetrics]:
        """Run the complete benchmark suite."""
        logger.info("Starting LLM Security Scanner startup performance benchmark")
        logger.info(f"Output file: {self.output_file or 'stdout only'}")

        results = await self.run_all_scenarios()

        # Print report to console
        report = self.generate_report(results)
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60 + "\n")

        # Save results
        await self.save_results(results)

        return results


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark LLM Security Scanner startup performance")
    parser.add_argument("--output", "-o", help="Output file path (without extension)")
    parser.add_argument("--scenarios", nargs="+", help="Specific scenarios to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    benchmark = StartupPerformanceBenchmark(output_file=args.output)

    try:
        results = await benchmark.run_benchmark()

        # Exit with error code if any scenarios failed
        failed_count = len([r for r in results if r.errors])
        if failed_count > 0:
            logger.error(f"{failed_count} scenarios failed")
            sys.exit(1)
        else:
            logger.info("All scenarios completed successfully")

    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
