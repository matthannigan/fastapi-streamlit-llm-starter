---
sidebar_label: integration_test
---

# Integration test examples for the FastAPI-Streamlit-LLM Starter Template.

  file_path: `examples/integration_test.py`

This script provides comprehensive testing scenarios to validate the entire system
including API endpoints, error handling, performance, and edge cases.

## TestStatus

Test execution status.

## TestResult

Test result data structure.

## IntegrationTester

Comprehensive integration tester for the FastAPI-Streamlit-LLM system.

### __init__()

```python
def __init__(self, api_url: str = 'http://localhost:8000'):
```

### session()

```python
def session(self) -> httpx.AsyncClient:
```

Get the HTTP session, ensuring it's available.

### __aenter__()

```python
async def __aenter__(self):
```

### __aexit__()

```python
async def __aexit__(self, exc_type, exc_val, exc_tb):
```

### print_header()

```python
def print_header(self, title: str):
```

Print formatted test section header.

### print_test_start()

```python
def print_test_start(self, test_name: str):
```

Print test start message.

### print_test_result()

```python
def print_test_result(self, result: TestResult):
```

Print formatted test result.

### run_test()

```python
async def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
```

Run a single test and capture results.

### test_api_health()

```python
async def test_api_health(self) -> Dict[str, Any]:
```

Test API health endpoint.

### test_operations_endpoint()

```python
async def test_operations_endpoint(self) -> Dict[str, Any]:
```

Test operations listing endpoint.

### test_text_summarization()

```python
async def test_text_summarization(self) -> Dict[str, Any]:
```

Test text summarization operation.

### test_sentiment_analysis()

```python
async def test_sentiment_analysis(self) -> Dict[str, Any]:
```

Test sentiment analysis operation.

### test_key_points_extraction()

```python
async def test_key_points_extraction(self) -> Dict[str, Any]:
```

Test key points extraction operation.

### test_question_generation()

```python
async def test_question_generation(self) -> Dict[str, Any]:
```

Test question generation operation.

### test_question_answering()

```python
async def test_question_answering(self) -> Dict[str, Any]:
```

Test question answering operation.

### test_error_handling()

```python
async def test_error_handling(self) -> Dict[str, Any]:
```

Test various error scenarios.

### test_performance_benchmark()

```python
async def test_performance_benchmark(self) -> Dict[str, Any]:
```

Test system performance with multiple operations.

### test_concurrent_requests()

```python
async def test_concurrent_requests(self) -> Dict[str, Any]:
```

Test system behavior under concurrent load.

### run_all_tests()

```python
async def run_all_tests(self):
```

Run the complete test suite.

### generate_test_report()

```python
def generate_test_report(self):
```

Generate and display comprehensive test report.

## main()

```python
async def main():
```

Main function to run integration tests.
