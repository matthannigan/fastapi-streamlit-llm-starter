---
sidebar_label: test_reporting
---

# Tests for benchmark reporting system.

  file_path: `backend/tests.old/infrastructure/cache/benchmarks/test_reporting.py`

This module tests all reporter classes including TextReporter, CIReporter,
JSONReporter, MarkdownReporter, and the ReporterFactory.

## TestBenchmarkReporter

Test cases for base BenchmarkReporter class.

### test_base_reporter_initialization()

```python
def test_base_reporter_initialization(self):
```

Test base reporter initialization.

### test_base_reporter_with_thresholds()

```python
def test_base_reporter_with_thresholds(self, default_thresholds):
```

Test base reporter initialization with custom thresholds.

### test_analyze_performance_insights()

```python
def test_analyze_performance_insights(self, sample_benchmark_suite):
```

Test performance insights analysis.

### test_generate_recommendations()

```python
def test_generate_recommendations(self, sample_benchmark_suite):
```

Test recommendations generation.

## TestTextReporter

Test cases for TextReporter class.

### test_text_reporter_initialization()

```python
def test_text_reporter_initialization(self):
```

Test TextReporter initialization with default parameters.

### test_text_reporter_custom_verbosity()

```python
def test_text_reporter_custom_verbosity(self):
```

Test TextReporter with custom verbosity levels.

### test_text_reporter_section_filtering()

```python
def test_text_reporter_section_filtering(self):
```

Test TextReporter with section filtering.

### test_generate_report_basic()

```python
def test_generate_report_basic(self, sample_benchmark_suite):
```

Test basic report generation.

### test_generate_report_verbosity_levels()

```python
def test_generate_report_verbosity_levels(self, sample_benchmark_suite):
```

Test report generation with different verbosity levels.

### test_generate_report_with_failures()

```python
def test_generate_report_with_failures(self):
```

Test report generation with failed benchmarks.

### test_section_filtering_functionality()

```python
def test_section_filtering_functionality(self, sample_benchmark_suite):
```

Test that section filtering actually works.

### test_performance_status_indicators()

```python
def test_performance_status_indicators(self, sample_benchmark_suite):
```

Test performance status indicators in report.

## TestCIReporter

Test cases for CIReporter class.

### test_ci_reporter_initialization()

```python
def test_ci_reporter_initialization(self):
```

Test CIReporter initialization.

### test_generate_report_basic()

```python
def test_generate_report_basic(self, sample_benchmark_suite):
```

Test basic CI report generation.

### test_performance_badges_suite()

```python
def test_performance_badges_suite(self, sample_benchmark_suite):
```

Test performance badge generation for suite.

### test_performance_badges_individual_result()

```python
def test_performance_badges_individual_result(self, sample_benchmark_result):
```

Test performance badge generation for individual result.

### test_ci_insights_generation()

```python
def test_ci_insights_generation(self, sample_benchmark_suite):
```

Test CI-specific insights generation.

### test_github_actions_format()

```python
def test_github_actions_format(self, sample_benchmark_suite):
```

Test that report format is suitable for GitHub Actions.

## TestJSONReporter

Test cases for JSONReporter class.

### test_json_reporter_initialization()

```python
def test_json_reporter_initialization(self):
```

Test JSONReporter initialization with default parameters.

### test_json_reporter_custom_options()

```python
def test_json_reporter_custom_options(self):
```

Test JSONReporter with custom options.

### test_generate_report_basic()

```python
def test_generate_report_basic(self, sample_benchmark_suite):
```

Test basic JSON report generation.

### test_generate_report_with_metadata()

```python
def test_generate_report_with_metadata(self, sample_benchmark_suite):
```

Test JSON report generation with metadata.

### test_generate_report_without_metadata()

```python
def test_generate_report_without_metadata(self, sample_benchmark_suite):
```

Test JSON report generation without metadata.

### test_json_schema_validation()

```python
def test_json_schema_validation(self, sample_benchmark_suite):
```

Test that JSON output follows expected schema.

### test_json_serialization_edge_cases()

```python
def test_json_serialization_edge_cases(self):
```

Test JSON serialization with edge cases.

## TestMarkdownReporter

Test cases for MarkdownReporter class.

### test_markdown_reporter_initialization()

```python
def test_markdown_reporter_initialization(self):
```

Test MarkdownReporter initialization.

### test_generate_report_basic()

```python
def test_generate_report_basic(self, sample_benchmark_suite):
```

Test basic markdown report generation.

### test_markdown_table_formatting()

```python
def test_markdown_table_formatting(self, sample_benchmark_suite):
```

Test markdown table formatting.

### test_collapsible_sections()

```python
def test_collapsible_sections(self, sample_benchmark_suite):
```

Test collapsible sections in markdown.

### test_github_flavored_markdown()

```python
def test_github_flavored_markdown(self, sample_benchmark_suite):
```

Test GitHub-flavored markdown features.

### test_environment_info_section()

```python
def test_environment_info_section(self, sample_benchmark_suite):
```

Test environment information section.

## TestReporterFactory

Test cases for ReporterFactory class.

### test_get_reporter_text()

```python
def test_get_reporter_text(self):
```

Test getting text reporter from factory.

### test_get_reporter_ci()

```python
def test_get_reporter_ci(self):
```

Test getting CI reporter from factory.

### test_get_reporter_json()

```python
def test_get_reporter_json(self):
```

Test getting JSON reporter from factory.

### test_get_reporter_markdown()

```python
def test_get_reporter_markdown(self):
```

Test getting markdown reporter from factory.

### test_get_reporter_with_kwargs()

```python
def test_get_reporter_with_kwargs(self):
```

Test getting reporter with custom arguments.

### test_get_reporter_unsupported_format()

```python
def test_get_reporter_unsupported_format(self):
```

Test getting reporter with unsupported format.

### test_generate_all_reports()

```python
def test_generate_all_reports(self, sample_benchmark_suite):
```

Test generating all report formats.

### test_generate_all_reports_with_thresholds()

```python
def test_generate_all_reports_with_thresholds(self, sample_benchmark_suite, strict_thresholds):
```

Test generating all reports with custom thresholds.

### test_detect_format_from_environment_ci()

```python
def test_detect_format_from_environment_ci(self):
```

Test format detection in CI environment.

### test_detect_format_from_environment_github()

```python
def test_detect_format_from_environment_github(self):
```

Test format detection in GitHub Actions.

### test_detect_format_from_environment_preference()

```python
def test_detect_format_from_environment_preference(self):
```

Test format detection with explicit preference.

### test_detect_format_from_environment_default()

```python
def test_detect_format_from_environment_default(self):
```

Test format detection with no environment indicators.

### test_error_handling_in_generate_all_reports()

```python
def test_error_handling_in_generate_all_reports(self):
```

Test error handling when report generation fails.
