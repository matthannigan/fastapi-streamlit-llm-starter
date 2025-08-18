---
sidebar_label: reporting
---

# Cache Benchmark Reporting

  file_path: `backend/app/infrastructure/cache/benchmarks/reporting.py`

This module provides comprehensive report generation capabilities for cache performance benchmarks.
Multiple report formats are supported including text, JSON, markdown, and CI-specific formats.

## Classes

BenchmarkReporter: Base class for all reporters
TextReporter: Human-readable text reports
CIReporter: CI/CD pipeline optimized reports with badges
JSONReporter: Structured JSON output for programmatic use
MarkdownReporter: GitHub-flavored markdown reports
ReporterFactory: Factory for creating appropriate reporters

The reporting system provides detailed analysis, recommendations, and insights
for cache performance optimization.
