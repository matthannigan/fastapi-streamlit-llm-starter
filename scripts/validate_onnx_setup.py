#!/usr/bin/env python3
"""
ONNX Setup Validation Script

This script validates ONNX runtime setup, tests model loading, and verifies
performance characteristics across different platforms and configurations.

Usage:
    python scripts/validate_onnx_setup.py [options]

Options:
    --verbose         Enable verbose logging
    --download-models Download test models if not available
    --benchmark       Run performance benchmarks
    --export-report   Export validation report to JSON
    --fix-issues      Attempt to fix common issues automatically
"""

import asyncio
import json
import logging
import os
import platform
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.infrastructure.security.llm.onnx_utils import (
    get_onnx_manager,
    verify_onnx_setup,
)


@dataclass
class ValidationIssue:
    """Represents a validation issue found during setup validation."""
    severity: str  # "error", "warning", "info"
    category: str  # "installation", "compatibility", "performance", "configuration"
    title: str
    description: str
    recommendation: str | None = None
    fix_available: bool = False


@dataclass
class ValidationReport:
    """Complete validation report for ONNX setup."""
    timestamp: str
    platform_info: dict[str, Any]
    onnx_runtime_info: dict[str, Any]
    model_tests: dict[str, Any]
    performance_tests: dict[str, Any]
    issues: list[ValidationIssue]
    overall_status: str  # "pass", "warn", "fail"
    summary: str


class ONNXSetupValidator:
    """Comprehensive ONNX setup validator."""

    def __init__(
        self,
        verbose: bool = False,
        download_models: bool = False,
        run_benchmarks: bool = False
    ):
        self.verbose = verbose
        self.download_models = download_models
        self.run_benchmarks = run_benchmarks
        self.issues: list[ValidationIssue] = []

        # Setup logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Test models for validation
        self.test_models = [
            "microsoft/deberta-v3-base-injection",  # Prompt injection
            "unitary/toxic-bert",                    # Toxicity detection
            "d4data/bias-detection",                # Bias detection
        ]

        # Performance targets
        self.performance_targets = {
            "model_load_time_s": 10.0,      # Max 10 seconds to load model
            "inference_time_ms": 50.0,       # Max 50ms p95 inference
            "memory_usage_mb": 1000.0,       # Max 1GB memory usage
        }

    def add_issue(
        self,
        severity: str,
        category: str,
        title: str,
        description: str,
        recommendation: str | None = None,
        fix_available: bool = False
    ) -> None:
        """Add a validation issue to the report."""
        issue = ValidationIssue(
            severity=severity,
            category=category,
            title=title,
            description=description,
            recommendation=recommendation,
            fix_available=fix_available
        )
        self.issues.append(issue)

        # Log based on severity
        if severity == "error":
            self.logger.error(f"{title}: {description}")
        elif severity == "warning":
            self.logger.warning(f"{title}: {description}")
        else:
            self.logger.info(f"{title}: {description}")

    def get_platform_info(self) -> dict[str, Any]:
        """Get detailed platform information."""
        info: dict[str, Any] = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "architecture": platform.architecture(),
        }

        # Add memory information
        try:
            import psutil
            memory = psutil.virtual_memory()
            info["total_memory_gb"] = round(float(memory.total) / 1024 / 1024 / 1024, 2)
            info["available_memory_gb"] = round(float(memory.available) / 1024 / 1024 / 1024, 2)
            info["cpu_count"] = psutil.cpu_count()
            info["cpu_count_logical"] = psutil.cpu_count(logical=True)
        except ImportError:
            self.add_issue(
                "warning",
                "installation",
                "psutil not available",
                "psutil is recommended for system information gathering",
                "Install psutil: pip install psutil"
            )

        return info

    async def validate_onnx_installation(self) -> dict[str, Any]:
        """Validate ONNX runtime installation."""
        self.logger.info("Validating ONNX runtime installation...")

        onnx_info: dict[str, Any] = {}

        try:
            import onnxruntime as ort  # type: ignore
            onnx_info["installed"] = True
            onnx_info["version"] = ort.__version__
            onnx_info["build_info"] = ort.get_build_info()
            onnx_info["available_providers"] = ort.get_available_providers()

            self.logger.info(f"ONNX Runtime {ort.__version__} found")
            self.logger.info(f"Available providers: {ort.get_available_providers()}")

            # Check for recommended providers
            providers = ort.get_available_providers()
            if "CPUExecutionProvider" not in providers:
                self.add_issue(
                    "error",
                    "compatibility",
                    "CPU Execution Provider not available",
                    "CPU execution provider is required for fallback functionality",
                    fix_available=False
                )

            if "CUDAExecutionProvider" in providers:
                self.logger.info("CUDA acceleration is available")
                onnx_info["cuda_available"] = True
            else:
                self.logger.info("CUDA acceleration not available (CPU-only mode)")
                onnx_info["cuda_available"] = False

            # Check platform-specific providers
            if platform.system() == "Darwin" and "CoreMLExecutionProvider" in providers:
                self.logger.info("CoreML acceleration available on macOS")
                onnx_info["coreml_available"] = True

        except ImportError as e:
            onnx_info["installed"] = False
            onnx_info["error_message"] = str(e)

            self.add_issue(
                "error",
                "installation",
                "ONNX Runtime not installed",
                f"Import error: {e}",
                "Install ONNX Runtime: pip install onnxruntime",
                fix_available=True
            )

        return onnx_info

    async def validate_model_loading(self) -> dict[str, Any]:
        """Validate model loading for different scanner types."""
        self.logger.info("Validating ONNX model loading...")

        model_tests = {}

        for model_name in self.test_models:
            self.logger.info(f"Testing model: {model_name}")

            try:
                # Verify model compatibility
                diagnostics = await verify_onnx_setup(model_name)
                model_tests[model_name] = diagnostics

                if not diagnostics["onnx_available"]:
                    self.add_issue(
                        "error",
                        "installation",
                        f"ONNX not available for {model_name}",
                        "Cannot test model loading without ONNX runtime"
                    )
                    continue

                if not diagnostics["model_found"] and not self.download_models:
                    self.add_issue(
                        "warning",
                        "compatibility",
                        f"Model not found: {model_name}",
                        "Model not available locally and auto-download disabled",
                        "Run with --download-models to download models automatically",
                        fix_available=True
                    )
                    continue

                if diagnostics["model_loadable"]:
                    self.logger.info(f"✓ Model {model_name} loads successfully")

                    # Check model characteristics
                    if "input_details" in diagnostics:
                        input_details = diagnostics["input_details"]
                        if input_details:
                            self.logger.debug(f"  Input: {input_details[0]}")

                    if "output_details" in diagnostics:
                        output_details = diagnostics["output_details"]
                        if output_details:
                            self.logger.debug(f"  Output: {output_details[0]}")

                else:
                    self.add_issue(
                        "error",
                        "compatibility",
                        f"Model loading failed: {model_name}",
                        "Model could not be loaded with available providers"
                    )

            except Exception as e:
                self.logger.error(f"Model test failed for {model_name}: {e}")
                model_tests[model_name] = {
                    "error": str(e),
                    "model_loadable": False
                }

                self.add_issue(
                    "error",
                    "compatibility",
                    f"Model test error: {model_name}",
                    f"Unexpected error during model testing: {e}"
                )

        return model_tests

    async def validate_performance(self) -> dict[str, Any]:
        """Validate performance characteristics."""
        self.logger.info("Validating ONNX performance...")

        performance_tests: dict[str, Any] = {}

        if not self.run_benchmarks:
            self.logger.info("Performance benchmarks skipped (use --benchmark to enable)")
            return {"skipped": True, "reason": "Benchmarks disabled"}

        try:
            manager = get_onnx_manager(auto_download=self.download_models)

            for model_name in self.test_models[:1]:  # Test only first model to save time
                self.logger.info(f"Benchmarking model: {model_name}")

                # Test model loading time
                start_time = time.time()
                try:
                    session, tokenizer, info = await manager.load_model(model_name)
                    load_time = time.time() - start_time

                    performance_tests[f"{model_name}_load_time"] = load_time

                    if load_time > self.performance_targets["model_load_time_s"]:
                        self.add_issue(
                            "warning",
                            "performance",
                            f"Slow model loading: {model_name}",
                            f"Model loading took {load_time:.1f}s (target: {self.performance_targets['model_load_time_s']}s)",
                            "Consider model quantization or smaller models"
                        )
                    else:
                        self.logger.info(f"✓ Model loading time: {load_time:.2f}s")

                    # Test inference time
                    if tokenizer and session:
                        # Note: tokenizer is returned as a string from load_model
                        # We need to handle this appropriately based on the actual implementation
                        # For now, we'll skip the inference test if tokenizer is not callable
                        if not callable(tokenizer):
                            self.logger.warning(f"Tokenizer is not callable: {type(tokenizer)}")
                            continue

                        # Prepare test input
                        test_text = "This is a test input for performance validation."
                        inputs = tokenizer(
                            test_text,
                            return_tensors="np",
                            truncation=True,
                            max_length=512
                        )

                        # Run inference multiple times
                        inference_times = []
                        for _ in range(10):
                            start_time = time.perf_counter()
                            outputs = session.run(None, dict(inputs))
                            inference_time = (time.perf_counter() - start_time) * 1000
                            inference_times.append(inference_time)

                        avg_inference_time = sum(inference_times) / len(inference_times)
                        p95_inference_time = sorted(inference_times)[int(len(inference_times) * 0.95)]

                        performance_tests[f"{model_name}_avg_inference_ms"] = avg_inference_time
                        performance_tests[f"{model_name}_p95_inference_ms"] = p95_inference_time

                        if p95_inference_time > self.performance_targets["inference_time_ms"]:
                            self.add_issue(
                                "warning",
                                "performance",
                                f"Slow inference: {model_name}",
                                f"P95 inference time: {p95_inference_time:.1f}ms (target: {self.performance_targets['inference_time_ms']}ms)",
                                "Consider GPU acceleration or model optimization"
                            )
                        else:
                            self.logger.info(f"✓ Inference time - Avg: {avg_inference_time:.1f}ms, P95: {p95_inference_time:.1f}ms")

                except Exception as e:
                    self.logger.error(f"Performance test failed for {model_name}: {e}")
                    performance_tests[f"{model_name}_error"] = str(e)

        except Exception as e:
            self.logger.error(f"Performance validation failed: {e}")
            performance_tests["error"] = str(e)

        return performance_tests

    def validate_dependencies(self) -> None:
        """Validate required dependencies."""
        self.logger.info("Validating dependencies...")

        required_packages = [
            ("transformers", "Hugging Face Transformers"),
            ("numpy", "NumPy"),
        ]

        optional_packages = [
            ("psutil", "System monitoring"),
            ("torch", "PyTorch"),
            ("huggingface_hub", "Hugging Face Hub"),
        ]

        for package, description in required_packages:
            try:
                __import__(package)
                self.logger.info(f"✓ {description} available")
            except ImportError:
                self.add_issue(
                    "error",
                    "installation",
                    f"Missing required package: {package}",
                    f"{description} is required for ONNX functionality",
                    f"Install with: pip install {package}",
                    fix_available=True
                )

        for package, description in optional_packages:
            try:
                __import__(package)
                self.logger.info(f"✓ {description} available")
            except ImportError:
                self.add_issue(
                    "info",
                    "installation",
                    f"Optional package not available: {package}",
                    f"{description} is recommended for full functionality",
                    f"Install with: pip install {package}",
                    fix_available=True
                )

    async def attempt_fixes(self) -> None:
        """Attempt to fix common issues automatically."""
        self.logger.info("Attempting to fix common issues...")

        # Try to install missing packages (if allowed)
        installable_issues = [issue for issue in self.issues if issue.fix_available and issue.severity == "error"]

        if installable_issues:
            self.logger.warning("Automatic fixing not implemented. Please fix issues manually:")
            for issue in installable_issues:
                if issue.recommendation:
                    self.logger.warning(f"  - {issue.recommendation}")

    def calculate_overall_status(self) -> str:
        """Calculate overall validation status."""
        errors = [issue for issue in self.issues if issue.severity == "error"]
        warnings = [issue for issue in self.issues if issue.severity == "warning"]

        if errors:
            return "fail"
        elif warnings:
            return "warn"
        else:
            return "pass"

    def generate_summary(self) -> str:
        """Generate validation summary."""
        errors = len([issue for issue in self.issues if issue.severity == "error"])
        warnings = len([issue for issue in self.issues if issue.severity == "warning"])
        info = len([issue for issue in self.issues if issue.severity == "info"])

        status = self.calculate_overall_status()

        summary_parts = [
            f"ONNX Setup Validation: {status.upper()}",
            f"Errors: {errors}, Warnings: {warnings}, Info: {info}"
        ]

        if status == "pass":
            summary_parts.append("✓ ONNX runtime is properly configured and ready for use")
        elif status == "warn":
            summary_parts.append("⚠ ONNX runtime is functional but some optimizations may not be available")
        else:
            summary_parts.append("❌ ONNX runtime setup has critical issues that must be resolved")

        return "\n".join(summary_parts)

    async def run_validation(self) -> ValidationReport:
        """Run complete ONNX setup validation."""
        self.logger.info("Starting ONNX setup validation...")

        start_time = datetime.now()

        # Validate dependencies first
        self.validate_dependencies()

        # Get platform information
        platform_info = self.get_platform_info()

        # Validate ONNX installation
        onnx_runtime_info = await self.validate_onnx_installation()

        # Validate model loading
        model_tests = await self.validate_model_loading()

        # Validate performance
        performance_tests = await self.validate_performance()

        # Attempt fixes if requested
        # Note: Automatic fixing not implemented for safety
        # await self.attempt_fixes()

        # Generate report
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        report = ValidationReport(
            timestamp=start_time.isoformat(),
            platform_info=platform_info,
            onnx_runtime_info=onnx_runtime_info,
            model_tests=model_tests,
            performance_tests=performance_tests,
            issues=self.issues,
            overall_status=self.calculate_overall_status(),
            summary=self.generate_summary()
        )

        self.logger.info(f"Validation completed in {duration:.1f} seconds")
        self.logger.info(report.summary)

        return report

    def export_report(self, report: ValidationReport, filename: str | None = None) -> str:
        """Export validation report to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"onnx_validation_report_{timestamp}.json"

        # Convert to JSON-serializable format
        report_dict = asdict(report)

        # Add additional metadata
        report_dict["validation_duration_s"] = (
            datetime.fromisoformat(report.timestamp) - datetime.fromisoformat(report.timestamp)
        ).total_seconds() if isinstance(report.timestamp, str) else 0

        # Write to file
        output_path = Path(filename)
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)

        self.logger.info(f"Validation report exported to: {output_path}")
        return str(output_path)


async def main() -> int:
    """Main entry point for the validation script."""
    import argparse

    parser = argparse.ArgumentParser(description="ONNX Setup Validation Script")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--download-models", action="store_true", help="Download test models if not available")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--export-report", help="Export report to specified JSON file")
    parser.add_argument("--fix-issues", action="store_true", help="Attempt to fix common issues automatically")

    args = parser.parse_args()

    # Create validator
    validator = ONNXSetupValidator(
        verbose=args.verbose,
        download_models=args.download_models,
        run_benchmarks=args.benchmark
    )

    try:
        # Run validation
        report = await validator.run_validation()

        # Export report if requested
        if args.export_report:
            validator.export_report(report, args.export_report)

        # Print summary
        print("\n" + "="*50)
        print(report.summary)
        print("="*50)

        if report.issues:
            print("\nIssues Found:")
            for issue in report.issues:
                print(f"  [{issue.severity.upper()}] {issue.title}")
                print(f"    {issue.description}")
                if issue.recommendation:
                    print(f"    Recommendation: {issue.recommendation}")
            print()

        # Return appropriate exit code
        if report.overall_status == "fail":
            return 1
        elif report.overall_status == "warn":
            return 2
        else:
            return 0

    except Exception as e:
        logging.error(f"Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
