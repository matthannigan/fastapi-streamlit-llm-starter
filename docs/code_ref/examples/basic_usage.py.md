---
sidebar_label: basic_usage
---

# Basic usage examples for the FastAPI-Streamlit-LLM Starter Template.

  file_path: `examples/basic_usage.py`

This script demonstrates how to interact with the API programmatically
and showcases all available text processing operations using standardized
patterns for imports, error handling, and sample data.

## APIClient

Simple API client for the FastAPI backend with standardized error handling.

This client provides methods for interacting with the text processing API
and follows consistent error handling patterns.

### __init__()

```python
def __init__(self, base_url: str = 'http://localhost:8000'):
```

Initialize the API client.

Args:
    base_url: Base URL for the API endpoints

### __aenter__()

```python
async def __aenter__(self):
```

Async context manager entry.

### __aexit__()

```python
async def __aexit__(self, exc_type, exc_val, exc_tb):
```

Async context manager exit.

### health_check()

```python
async def health_check(self) -> Optional[Dict[str, Any]]:
```

Check API health status with error handling.

Returns:
    Health status dictionary or None if error occurred

### get_operations()

```python
async def get_operations(self) -> Optional[Dict[str, Any]]:
```

Get available operations with error handling.

Returns:
    Operations dictionary or None if error occurred

### process_text()

```python
async def process_text(self, text: str, operation: str, question: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
```

Process text with specified operation and standardized error handling.

Args:
    text: Text to process
    operation: Processing operation to perform
    question: Optional question for Q&A operation
    options: Optional operation-specific parameters
    
Returns:
    Processing result dictionary or None if error occurred

## print_header()

```python
def print_header(title: str):
```

Print a formatted header.

## print_section()

```python
def print_section(title: str):
```

Print a formatted section header.

## print_result()

```python
def print_result(result: Dict[str, Any], operation: str):
```

Print formatted result based on operation type.

## demonstrate_basic_operations()

```python
async def demonstrate_basic_operations():
```

Demonstrate all basic text processing operations.

## demonstrate_different_text_types()

```python
async def demonstrate_different_text_types():
```

Demonstrate processing different types of text.

## demonstrate_error_handling()

```python
async def demonstrate_error_handling():
```

Demonstrate error handling scenarios.

## performance_benchmark()

```python
async def performance_benchmark():
```

Run a simple performance benchmark.

## main()

```python
async def main():
```

Main function to run all examples.
