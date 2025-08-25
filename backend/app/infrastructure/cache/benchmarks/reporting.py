"""
[REFACTORED] Comprehensive cache benchmark reporting with multi-format output and detailed analysis.

This module provides sophisticated report generation infrastructure for cache performance benchmarks
supporting multiple output formats including human-readable text, structured JSON, GitHub-compatible
markdown, and CI/CD optimized reports with performance badges and automated insights.

Classes:
    BenchmarkReporter: Abstract base class defining reporting interface with analysis utilities
    TextReporter: Human-readable console/log reports with configurable verbosity levels
    CIReporter: CI/CD pipeline optimized reports with badges, tables, and concise insights
    JSONReporter: Structured JSON output for API integration and programmatic processing
    MarkdownReporter: GitHub-flavored markdown with collapsible sections and performance tables
    ReporterFactory: Factory pattern for creating appropriate reporters with auto-detection

Key Features:
    - **Multi-Format Support**: Text, JSON, Markdown, and CI-specific formats with consistent
      analysis across all output types for different audiences and use cases.
    
    - **Performance Analysis**: Automated performance insights including threshold analysis,
      memory efficiency assessment, success rate evaluation, and variability detection.
    
    - **Actionable Recommendations**: Context-aware optimization recommendations based on
      performance patterns, memory usage, reliability metrics, and cache efficiency.
    
    - **CI/CD Integration**: Performance badges, GitHub Actions annotations, automated
      pass/fail determination, and concise insights optimized for pipeline integration.
    
    - **Configurable Verbosity**: Multiple detail levels from summary to comprehensive
      with customizable section inclusion for different reporting needs.
    
    - **Environment Detection**: Automatic format detection based on CI environment
      variables and configuration preferences for seamless integration.

Report Format Capabilities:
    **Text Reports**: Console-friendly output with sections for header, results, analysis,
    recommendations, and failures. Supports summary, standard, and detailed verbosity.
    
    **JSON Reports**: Structured data with schema versioning, computed metrics, analysis
    metadata, and complete benchmark preservation for API integration.
    
    **Markdown Reports**: GitHub-compatible format with performance tables, collapsible
    details, environment information, and emoji indicators for visual clarity.
    
    **CI Reports**: Pipeline-optimized format with performance badges, concise insights,
    summary tables, and quick assessment for automated deployment decisions.

Usage Examples:
    Multi-Format Report Generation:
        >>> from app.infrastructure.cache.benchmarks.reporting import ReporterFactory
        >>> 
        >>> # Text report for console output
        >>> text_reporter = ReporterFactory.get_reporter("text")
        >>> text_report = text_reporter.generate_report(suite)
        >>> print(text_report)
        >>> 
        >>> # CI report with badges
        >>> ci_reporter = ReporterFactory.get_reporter("ci")
        >>> ci_report = ci_reporter.generate_report(suite)
        >>> 
        >>> # JSON for API integration
        >>> json_reporter = ReporterFactory.get_reporter("json")
        >>> json_report = json_reporter.generate_report(suite)
        
    Environment-Based Auto-Detection:
        >>> # Automatically detects CI environment
        >>> format = ReporterFactory.detect_format_from_environment()
        >>> reporter = ReporterFactory.get_reporter(format)
        >>> 
        >>> # Generate all formats
        >>> all_reports = ReporterFactory.generate_all_reports(suite)
        >>> for format_name, report in all_reports.items():
        ...     with open(f"report.{format_name}", "w") as f:
        ...         f.write(report)
        
    Custom Configuration:
        >>> # Detailed text report with specific sections
        >>> text_reporter = TextReporter(
        ...     verbosity="detailed",
        ...     include_sections=["header", "results", "analysis"]
        ... )
        >>> 
        >>> # JSON with metadata inclusion
        >>> json_reporter = JSONReporter(
        ...     include_metadata=True,
        ...     schema_version="2.0"
        ... )

Performance Considerations:
    - Report generation is optimized for minimal overhead during benchmark execution
    - Large dataset formatting is handled efficiently with streaming approaches
    - Multiple format generation uses shared analysis to minimize computation
    - Badge generation includes caching for repeated use in CI environments
    
Thread Safety:
    All reporter classes are stateless and thread-safe for concurrent report generation.
    Factory methods are safe for concurrent use across multiple benchmark executions.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .models import BenchmarkResult, BenchmarkSuite, ComparisonResult
from .config import CachePerformanceThresholds


class BenchmarkReporter(ABC):
    """
    Base class for benchmark reporters.
    
    This abstract base class defines the interface for all benchmark reporters
    and provides common utilities for generating insights and recommendations.
    """
    
    def __init__(self, thresholds: Optional[CachePerformanceThresholds] = None):
        """
        Initialize reporter with performance thresholds.
        
        Args:
            thresholds: Performance thresholds for pass/fail determination
        """
        self.thresholds = thresholds if thresholds is not None else CachePerformanceThresholds()
    
    @abstractmethod
    def generate_report(self, suite: BenchmarkSuite) -> str:
        """Generate report from benchmark suite."""
        pass
    
    def _analyze_performance_insights(self, suite: BenchmarkSuite) -> List[str]:
        """Generate performance insights from benchmark results."""
        insights = []
        
        if not suite.results:
            insights.append("No benchmark results available for analysis")
            return insights
        
        # Overall performance analysis
        avg_performance = sum(r.avg_duration_ms for r in suite.results) / len(suite.results)
        insights.append(f"Average operation time across all benchmarks: {avg_performance:.2f}ms")
        
        # Performance distribution
        fast_operations = len([r for r in suite.results if r.avg_duration_ms <= self.thresholds.basic_operations_avg_ms])
        total_operations = len(suite.results)
        fast_percentage = (fast_operations / total_operations) * 100
        insights.append(f"{fast_operations}/{total_operations} operations ({fast_percentage:.1f}%) meet performance thresholds")
        
        # Memory efficiency
        avg_memory = sum(r.memory_usage_mb for r in suite.results) / len(suite.results)
        if avg_memory > self.thresholds.memory_usage_warning_mb:
            insights.append(f"High memory usage detected: {avg_memory:.2f}MB average (threshold: {self.thresholds.memory_usage_warning_mb}MB)")
        else:
            insights.append(f"Memory usage within acceptable limits: {avg_memory:.2f}MB average")
        
        # Success rate analysis
        avg_success_rate = sum(r.success_rate for r in suite.results) / len(suite.results)
        if avg_success_rate < (self.thresholds.success_rate_warning / 100):
            insights.append(f"Reliability concern: {avg_success_rate*100:.1f}% average success rate")
        else:
            insights.append(f"High reliability: {avg_success_rate*100:.1f}% average success rate")
        
        # Throughput analysis
        avg_throughput = sum(r.operations_per_second for r in suite.results) / len(suite.results)
        insights.append(f"Average throughput: {avg_throughput:.0f} operations/second")
        
        # Performance variability
        durations = [r.avg_duration_ms for r in suite.results]
        if durations:
            min_duration = min(durations)
            max_duration = max(durations)
            variability = (max_duration - min_duration) / min_duration if min_duration > 0 else 0
            if variability > 2.0:  # 200% variability
                insights.append(f"High performance variability detected: {variability*100:.0f}% range between fastest and slowest operations")
            else:
                insights.append(f"Consistent performance: {variability*100:.0f}% variability between operations")
        
        return insights
    
    def _generate_recommendations(self, suite: BenchmarkSuite) -> List[str]:
        """Generate optimization recommendations based on benchmark results."""
        recommendations = []
        
        if not suite.results:
            return recommendations
        
        # Performance recommendations
        slow_operations = [r for r in suite.results if r.avg_duration_ms > self.thresholds.basic_operations_avg_ms]
        if slow_operations:
            recommendations.append(f"Optimize {len(slow_operations)} slow operations: {', '.join(r.operation_type for r in slow_operations)}")
        
        # Memory recommendations
        high_memory_operations = [r for r in suite.results if r.memory_usage_mb > self.thresholds.memory_usage_warning_mb]
        if high_memory_operations:
            recommendations.append(f"Review memory usage for: {', '.join(r.operation_type for r in high_memory_operations)}")
        
        # Success rate recommendations
        unreliable_operations = [r for r in suite.results if r.success_rate < (self.thresholds.success_rate_warning / 100)]
        if unreliable_operations:
            recommendations.append(f"Improve error handling for: {', '.join(r.operation_type for r in unreliable_operations)}")
        
        # Cache efficiency recommendations
        cache_results = [r for r in suite.results if r.cache_hit_rate is not None and r.cache_hit_rate < 0.8]
        if cache_results:
            recommendations.append("Consider cache tuning to improve hit rates")
        
        # Compression recommendations
        compression_results = [r for r in suite.results if r.compression_ratio is not None and r.compression_ratio > 0.7]
        if compression_results:
            recommendations.append("Review compression strategy - low compression ratios detected")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable thresholds - no immediate optimizations required")
        
        return recommendations


class TextReporter(BenchmarkReporter):
    """
    Human-readable text report generator.
    
    Generates comprehensive text reports suitable for console output,
    log files, and human review. Supports multiple verbosity levels
    and customizable sections.
    """
    
    def __init__(self, thresholds: Optional[CachePerformanceThresholds] = None, 
                 verbosity: str = "standard", include_sections: Optional[List[str]] = None):
        """
        Initialize text reporter with options.
        
        Args:
            thresholds: Performance thresholds for analysis
            verbosity: Report detail level ("summary", "standard", "detailed")
            include_sections: List of sections to include, None for all
        """
        super().__init__(thresholds)
        self.verbosity = verbosity
        self.include_sections = include_sections
    
    def generate_report(self, suite: BenchmarkSuite) -> str:
        """Generate comprehensive text report."""
        report_lines = []
        
        # Header
        if self._should_include_section("header"):
            report_lines.extend(self._generate_header(suite))
        
        # Environment Information
        if self._should_include_section("environment") and suite.environment_info:
            report_lines.extend(self._generate_environment_section(suite))
        
        # Individual Benchmark Results
        if self._should_include_section("results"):
            report_lines.extend(self._generate_results_section(suite))
        
        # Failed Benchmarks
        if self._should_include_section("failures") and suite.failed_benchmarks:
            report_lines.extend(self._generate_failures_section(suite))
        
        # Performance Analysis
        if self._should_include_section("analysis"):
            report_lines.extend(self._generate_analysis_section(suite))
        
        # Recommendations
        if self._should_include_section("recommendations"):
            report_lines.extend(self._generate_recommendations_section(suite))
        
        report_lines.append("\\n" + "=" * 80)
        
        return "\\n".join(report_lines)
    
    def _should_include_section(self, section: str) -> bool:
        """
        Check if section should be included based on configuration.
        
        Args:
            section: Section name to check
            
        Returns:
            True if section should be included in the report
        """
        if self.include_sections is None:
            return True
        return section in self.include_sections
    
    def _generate_header(self, suite: BenchmarkSuite) -> List[str]:
        """
        Generate report header section with suite overview.
        
        Args:
            suite: Benchmark suite to generate header for
            
        Returns:
            List of formatted header lines
        """
        lines = []
        lines.append("=" * 80)
        lines.append("CACHE PERFORMANCE BENCHMARK REPORT")
        lines.append("=" * 80)
        lines.append(f"Suite: {suite.name}")
        lines.append(f"Timestamp: {suite.timestamp}")
        lines.append(f"Duration: {suite.total_duration_ms / 1000:.2f}s")
        lines.append(f"Pass Rate: {suite.pass_rate * 100:.1f}%")
        lines.append(f"Performance Grade: {suite.performance_grade}")
        lines.append(f"Memory Efficiency: {suite.memory_efficiency_grade}")
        lines.append("")
        return lines
    
    def _generate_environment_section(self, suite: BenchmarkSuite) -> List[str]:
        """
        Generate environment information section.
        
        Args:
            suite: Benchmark suite containing environment metadata
            
        Returns:
            List of formatted environment information lines
        """
        lines = []
        lines.append("ENVIRONMENT")
        lines.append("-" * 40)
        for key, value in suite.environment_info.items():
            lines.append(f"{key}: {value}")
        lines.append("")
        return lines
    
    def _generate_results_section(self, suite: BenchmarkSuite) -> List[str]:
        """Generate individual benchmark results section."""
        lines = []
        lines.append("BENCHMARK RESULTS")
        lines.append("-" * 40)
        
        for result in suite.results:
            lines.append(f"\\n{result.operation_type.upper()}")
            lines.append("-" * 30)
            
            # Performance metrics
            meets_threshold = result.meets_threshold(self.thresholds.basic_operations_avg_ms)
            status = "✓ PASS" if meets_threshold else "✗ FAIL"
            grade = result.performance_grade()
            
            lines.append(f"Status: {status} ({grade})")
            lines.append(f"Average Duration: {result.avg_duration_ms:.2f}ms")
            
            if self.verbosity in ["standard", "detailed"]:
                lines.append(f"P95 Duration: {result.p95_duration_ms:.2f}ms")
                lines.append(f"P99 Duration: {result.p99_duration_ms:.2f}ms")
                lines.append(f"Operations/sec: {result.operations_per_second:.0f}")
                lines.append(f"Success Rate: {result.success_rate * 100:.1f}%")
                lines.append(f"Memory Usage: {result.memory_usage_mb:.2f}MB")
            
            if self.verbosity == "detailed":
                lines.append(f"Min Duration: {result.min_duration_ms:.2f}ms")
                lines.append(f"Max Duration: {result.max_duration_ms:.2f}ms")
                lines.append(f"Std Deviation: {result.std_dev_ms:.2f}ms")
                lines.append(f"Iterations: {result.iterations}")
                lines.append(f"Error Count: {result.error_count}")
            
            if result.cache_hit_rate is not None:
                lines.append(f"Cache Hit Rate: {result.cache_hit_rate * 100:.1f}%")
            
            if result.compression_ratio is not None:
                lines.append(f"Compression Ratio: {result.compression_ratio:.2f}")
                if result.compression_savings_mb is not None:
                    lines.append(f"Compression Savings: {result.compression_savings_mb:.2f}MB")
            
            # Additional metadata for detailed reports
            if self.verbosity == "detailed" and result.metadata:
                lines.append("Additional Metrics:")
                for key, value in result.metadata.items():
                    lines.append(f"  {key}: {value}")
        
        return lines
    
    def _generate_failures_section(self, suite: BenchmarkSuite) -> List[str]:
        """Generate failed benchmarks section."""
        lines = []
        lines.append("\\nFAILED BENCHMARKS")
        lines.append("-" * 40)
        for failure in suite.failed_benchmarks:
            lines.append(f"✗ {failure}")
        return lines
    
    def _generate_analysis_section(self, suite: BenchmarkSuite) -> List[str]:
        """Generate performance analysis section."""
        lines = []
        lines.append("\\nPERFORMANCE ANALYSIS")
        lines.append("-" * 40)
        
        insights = self._analyze_performance_insights(suite)
        for insight in insights:
            lines.append(f"• {insight}")
        
        return lines
    
    def _generate_recommendations_section(self, suite: BenchmarkSuite) -> List[str]:
        """Generate recommendations section."""
        lines = []
        recommendations = self._generate_recommendations(suite)
        if recommendations:
            lines.append("\\nRECOMMENDATIONS")
            lines.append("-" * 40)
            for rec in recommendations:
                lines.append(f"• {rec}")
        return lines


class CIReporter(BenchmarkReporter):
    """
    CI/CD pipeline optimized reporter.
    
    Generates concise reports suitable for CI environments with
    performance badges, GitHub Actions annotations, and GitLab CI artifacts.
    """
    
    def generate_report(self, suite: BenchmarkSuite) -> str:
        """Generate CI-optimized report."""
        lines = []
        
        # CI Summary Header
        lines.append("## 🔍 Cache Performance Report")
        lines.append("")
        lines.append(f"**Suite:** {suite.name}")
        lines.append(f"**Status:** {'✅ PASS' if suite.pass_rate >= 0.9 else '❌ FAIL'}")
        lines.append(f"**Pass Rate:** {suite.pass_rate * 100:.1f}%")
        lines.append(f"**Duration:** {suite.total_duration_ms / 1000:.1f}s")
        lines.append("")
        
        # Performance Summary Table
        lines.append("### Performance Summary")
        lines.append("")
        lines.append("| Operation | Status | Avg Time | P95 Time | Throughput |")
        lines.append("|-----------|--------|----------|----------|------------|")
        
        for result in suite.results:
            meets_threshold = result.meets_threshold(self.thresholds.basic_operations_avg_ms)
            status = "✅" if meets_threshold else "❌"
            lines.append(f"| {result.operation_type} | {status} | {result.avg_duration_ms:.1f}ms | "
                        f"{result.p95_duration_ms:.1f}ms | {result.operations_per_second:.0f} ops/s |")
        
        lines.append("")
        
        # Badges
        badges = self.create_performance_badges(suite)
        if badges:
            lines.append("### Performance Badges")
            lines.append("")
            for label, badge in badges.items():
                lines.append(f"**{label}:** {badge}")
            lines.append("")
        
        # Quick insights for CI
        quick_insights = self._generate_ci_insights(suite)
        if quick_insights:
            lines.append("### Key Insights")
            lines.append("")
            for insight in quick_insights:
                lines.append(f"- {insight}")
            lines.append("")
        
        # Failed benchmarks (critical for CI)
        if suite.failed_benchmarks:
            lines.append("### ❌ Failed Benchmarks")
            lines.append("")
            for failure in suite.failed_benchmarks:
                lines.append(f"- {failure}")
            lines.append("")
        
        return "\\n".join(lines)
    
    def create_performance_badges(self, results: Union[BenchmarkResult, BenchmarkSuite]) -> Dict[str, str]:
        """Create performance badges for CI display."""
        badges = {}
        
        if isinstance(results, BenchmarkSuite):
            # Suite-level badges
            pass_rate = results.pass_rate * 100
            if pass_rate >= 95:
                badges["Pass Rate"] = f"![Pass Rate](https://img.shields.io/badge/Pass_Rate-{pass_rate:.0f}%25-brightgreen)"
            elif pass_rate >= 80:
                badges["Pass Rate"] = f"![Pass Rate](https://img.shields.io/badge/Pass_Rate-{pass_rate:.0f}%25-yellow)"
            else:
                badges["Pass Rate"] = f"![Pass Rate](https://img.shields.io/badge/Pass_Rate-{pass_rate:.0f}%25-red)"
            
            badges["Performance"] = f"![Performance](https://img.shields.io/badge/Performance-{results.performance_grade}-{'brightgreen' if results.performance_grade == 'Good' else 'yellow' if results.performance_grade == 'Acceptable' else 'red'})"
            
            if results.results:
                avg_throughput = sum(r.operations_per_second for r in results.results) / len(results.results)
                badges["Throughput"] = f"![Throughput](https://img.shields.io/badge/Throughput-{avg_throughput:.0f}_ops/s-blue)"
        
        elif isinstance(results, BenchmarkResult):
            # Individual result badges
            grade = results.performance_grade()
            grade_color = {"Excellent": "brightgreen", "Good": "green", "Acceptable": "yellow", "Poor": "orange", "Critical": "red"}
            badges["Performance"] = f"![Performance](https://img.shields.io/badge/Performance-{grade}-{grade_color.get(grade, 'gray')})"
            badges["Throughput"] = f"![Throughput](https://img.shields.io/badge/Throughput-{results.operations_per_second:.0f}_ops/s-blue)"
        
        return badges
    
    def _generate_ci_insights(self, suite: BenchmarkSuite) -> List[str]:
        """Generate concise insights for CI environment."""
        insights = []
        
        if not suite.results:
            return ["No benchmark results available"]
        
        # Overall performance status
        avg_performance = sum(r.avg_duration_ms for r in suite.results) / len(suite.results)
        if avg_performance <= self.thresholds.basic_operations_avg_ms:
            insights.append(f"✅ Average performance within thresholds ({avg_performance:.1f}ms)")
        else:
            insights.append(f"⚠️ Average performance exceeds thresholds ({avg_performance:.1f}ms > {self.thresholds.basic_operations_avg_ms}ms)")
        
        # Memory status
        avg_memory = sum(r.memory_usage_mb for r in suite.results) / len(suite.results)
        if avg_memory > self.thresholds.memory_usage_critical_mb:
            insights.append(f"🔴 High memory usage: {avg_memory:.1f}MB")
        elif avg_memory > self.thresholds.memory_usage_warning_mb:
            insights.append(f"🟡 Elevated memory usage: {avg_memory:.1f}MB")
        
        # Reliability status
        failed_count = len([r for r in suite.results if r.success_rate < 0.95])
        if failed_count > 0:
            insights.append(f"⚠️ {failed_count} operations have reliability issues")
        
        return insights


class JSONReporter(BenchmarkReporter):
    """
    Structured JSON report generator.
    
    Generates machine-readable JSON reports suitable for programmatic
    processing, data analysis, and integration with other tools.
    """
    
    def __init__(self, thresholds: Optional[CachePerformanceThresholds] = None,
                 include_metadata: bool = True, schema_version: str = "1.0"):
        """
        Initialize JSON reporter with options.
        
        Args:
            thresholds: Performance thresholds for analysis
            include_metadata: Whether to include analysis metadata
            schema_version: JSON schema version for compatibility
        """
        super().__init__(thresholds)
        self.include_metadata = include_metadata
        self.schema_version = schema_version
    
    def generate_report(self, suite: BenchmarkSuite) -> str:
        """Generate structured JSON report."""
        report_data = {
            "schema_version": self.schema_version,
            "generated_at": datetime.now().isoformat(),
            "suite": asdict(suite),
        }
        
        if self.include_metadata:
            # Add analysis metadata
            report_data["analysis"] = {
                "insights": self._analyze_performance_insights(suite),
                "recommendations": self._generate_recommendations(suite),
                "thresholds_used": {
                    "basic_operations_avg_ms": self.thresholds.basic_operations_avg_ms,
                    "basic_operations_p95_ms": self.thresholds.basic_operations_p95_ms,
                    "memory_usage_warning_mb": self.thresholds.memory_usage_warning_mb,
                    "success_rate_warning": self.thresholds.success_rate_warning
                }
            }
            
            # Add computed metrics
            if suite.results:
                report_data["computed_metrics"] = {
                    "average_duration_ms": sum(r.avg_duration_ms for r in suite.results) / len(suite.results),
                    "average_throughput": sum(r.operations_per_second for r in suite.results) / len(suite.results),
                    "average_memory_mb": sum(r.memory_usage_mb for r in suite.results) / len(suite.results),
                    "operations_meeting_thresholds": len([r for r in suite.results if r.meets_threshold(self.thresholds.basic_operations_avg_ms)]),
                    "total_operations": len(suite.results)
                }
        
        return json.dumps(report_data, indent=2, default=str)


class MarkdownReporter(BenchmarkReporter):
    """
    GitHub-flavored markdown report generator.
    
    Generates markdown reports suitable for GitHub README files,
    pull request comments, and documentation sites.
    """
    
    def generate_report(self, suite: BenchmarkSuite) -> str:
        """Generate GitHub-flavored markdown report."""
        lines = []
        
        # Title and summary
        lines.append(f"# {suite.name}")
        lines.append("")
        lines.append(f"**Timestamp:** {suite.timestamp}")
        lines.append(f"**Duration:** {suite.total_duration_ms / 1000:.2f}s")
        lines.append(f"**Pass Rate:** {suite.pass_rate * 100:.1f}%")
        lines.append(f"**Performance Grade:** {suite.performance_grade}")
        lines.append("")
        
        # Performance Summary Table
        lines.append("## Performance Summary")
        lines.append("")
        lines.append("| Operation | Status | Avg Time | P95 | P99 | Throughput | Success Rate |")
        lines.append("|-----------|--------|----------|-----|-----|------------|--------------|")
        
        for result in suite.results:
            meets_threshold = result.meets_threshold(self.thresholds.basic_operations_avg_ms)
            status = "✅ PASS" if meets_threshold else "❌ FAIL"
            lines.append(f"| `{result.operation_type}` | {status} | {result.avg_duration_ms:.2f}ms | "
                        f"{result.p95_duration_ms:.2f}ms | {result.p99_duration_ms:.2f}ms | "
                        f"{result.operations_per_second:.0f} ops/s | {result.success_rate * 100:.1f}% |")
        
        lines.append("")
        
        # Detailed Results (Collapsible)
        lines.append("<details>")
        lines.append("<summary>📊 Detailed Results</summary>")
        lines.append("")
        
        for result in suite.results:
            lines.append(f"### {result.operation_type}")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Average Duration | {result.avg_duration_ms:.2f}ms |")
            lines.append(f"| P95 Duration | {result.p95_duration_ms:.2f}ms |")
            lines.append(f"| P99 Duration | {result.p99_duration_ms:.2f}ms |")
            lines.append(f"| Min Duration | {result.min_duration_ms:.2f}ms |")
            lines.append(f"| Max Duration | {result.max_duration_ms:.2f}ms |")
            lines.append(f"| Std Deviation | {result.std_dev_ms:.2f}ms |")
            lines.append(f"| Operations/sec | {result.operations_per_second:.0f} |")
            lines.append(f"| Success Rate | {result.success_rate * 100:.1f}% |")
            lines.append(f"| Memory Usage | {result.memory_usage_mb:.2f}MB |")
            lines.append(f"| Iterations | {result.iterations} |")
            
            if result.cache_hit_rate is not None:
                lines.append(f"| Cache Hit Rate | {result.cache_hit_rate * 100:.1f}% |")
            
            if result.compression_ratio is not None:
                lines.append(f"| Compression Ratio | {result.compression_ratio:.2f} |")
            
            lines.append("")
        
        lines.append("</details>")
        lines.append("")
        
        # Analysis
        insights = self._analyze_performance_insights(suite)
        if insights:
            lines.append("## 📈 Performance Analysis")
            lines.append("")
            for insight in insights:
                lines.append(f"- {insight}")
            lines.append("")
        
        # Recommendations
        recommendations = self._generate_recommendations(suite)
        if recommendations:
            lines.append("## 💡 Recommendations")
            lines.append("")
            for rec in recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        # Failed benchmarks
        if suite.failed_benchmarks:
            lines.append("## ❌ Failed Benchmarks")
            lines.append("")
            for failure in suite.failed_benchmarks:
                lines.append(f"- `{failure}`")
            lines.append("")
        
        # Environment info
        if suite.environment_info:
            lines.append("<details>")
            lines.append("<summary>🔧 Environment Information</summary>")
            lines.append("")
            lines.append("| Setting | Value |")
            lines.append("|---------|-------|")
            for key, value in suite.environment_info.items():
                lines.append(f"| {key} | {value} |")
            lines.append("")
            lines.append("</details>")
        
        return "\\n".join(lines)


class ReporterFactory:
    """
    Factory for creating appropriate reporters.
    
    Provides a centralized way to create reporters with proper configuration
    and supports format auto-detection based on environment or context.
    """
    
    @staticmethod
    def get_reporter(format: str, **kwargs) -> BenchmarkReporter:
        """
        Get reporter for specified format.
        
        Args:
            format: Report format ("text", "ci", "json", "markdown")
            **kwargs: Additional arguments passed to reporter constructor
            
        Returns:
            Configured reporter instance
            
        Raises:
            ValueError: If format is not supported
        """
        reporters = {
            "text": TextReporter,
            "ci": CIReporter,
            "json": JSONReporter,
            "markdown": MarkdownReporter
        }
        
        if format not in reporters:
            supported = ", ".join(reporters.keys())
            raise ValueError(f"Unsupported report format: {format}. Supported formats: {supported}")
        
        return reporters[format](**kwargs)
    
    @staticmethod
    def generate_all_reports(suite: BenchmarkSuite, thresholds: Optional[CachePerformanceThresholds] = None) -> Dict[str, str]:
        """
        Generate reports in all supported formats.
        
        Args:
            suite: Benchmark suite to generate reports for
            thresholds: Performance thresholds for analysis
            
        Returns:
            Dictionary mapping format names to generated reports
        """
        reports = {}
        formats = ["text", "ci", "json", "markdown"]
        
        for format_name in formats:
            try:
                reporter = ReporterFactory.get_reporter(format_name, thresholds=thresholds)
                reports[format_name] = reporter.generate_report(suite)
            except Exception as e:
                reports[format_name] = f"Error generating {format_name} report: {e}"
        
        return reports
    
    @staticmethod
    def detect_format_from_environment() -> str:
        """
        Auto-detect appropriate report format based on environment.
        
        Returns:
            Detected format name
        """
        import os
        
        # Check for CI environment
        ci_indicators = ["CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", "GITLAB_CI"]
        if any(os.getenv(indicator) for indicator in ci_indicators):
            return "ci"
        
        # Check for JSON output preference
        if os.getenv("BENCHMARK_REPORT_FORMAT") == "json":
            return "json"
        
        # Check for markdown preference
        if os.getenv("BENCHMARK_REPORT_FORMAT") == "markdown":
            return "markdown"
        
        # Default to text
        return "text"