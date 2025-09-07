---
sidebar_label: update_tests_progress_w_failures
---

# Scans a directory of Python files to generate statistics about classes, methods,

  file_path: `scripts/update_tests_progress_w_failures.py`
and standalone test functions.

This script uses Python's `ast` module to parse Python source files without
executing them. It counts total methods/functions, items marked with
`@pytest.mark.skip`, and items with an actual implementation (i.e., more
than just a `pass` statement or a docstring).

It can optionally process a file containing pytest failure summaries to enrich
the report with test pass/fail status. It supports both plain text summaries
and structured JSON reports from the `pytest-json-report` plugin.

The output is a Markdown table, which can be printed to the console or saved
to a file.

## ClassMethodAnalyzer

An AST visitor that traverses a Python file's AST, collecting and
aggregating statistics about all classes and standalone test functions.

### __init__()

```python
def __init__(self, file_path: str):
```

### visit_ClassDef()

```python
def visit_ClassDef(self, node: ast.ClassDef):
```

Called when visiting a class. Pushes the class onto a stack to handle
nested classes correctly.

### visit_FunctionDef()

```python
def visit_FunctionDef(self, node: ast.FunctionDef):
```

Called for sync functions/methods.

### visit_AsyncFunctionDef()

```python
def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
```

Called for async functions/methods.

### get_final_stats()

```python
def get_final_stats(self) -> List[Dict[str, Any]]:
```

Converts the aggregated stats dictionary into the final list format
for the report.

## get_decorator_name()

```python
def get_decorator_name(decorator_node: ast.expr) -> str:
```

Recursively constructs the full decorator name from an AST node.
Handles simple names (`@mydecorator`), attributes (`@pytest.mark.skip`),
and calls (`@mydecorator(arg)`).

## analyze_file()

```python
def analyze_file(file_path: str) -> List[Dict[str, Any]]:
```

Parses a single Python file and returns statistics for its classes
and standalone test functions.

## scan_directory()

```python
def scan_directory(directory: str) -> List[Dict[str, Any]]:
```

Recursively scans a directory for `test_*.py` files and analyzes them.
Ensures all test files are accounted for in the output.

## parse_text_failures_file()

```python
def parse_text_failures_file(file_path: str, base_dir: str) -> Dict[tuple, int]:
```

Parses a pytest plain text summary file and counts failures per class or
for standalone functions in a file.

## parse_json_failures_file()

```python
def parse_json_failures_file(file_path: str, base_dir: str) -> Dict[tuple, int]:
```

Parses a pytest JSON report file and counts failures per class or for
standalone functions in a file.

## generate_markdown_table()

```python
def generate_markdown_table(stats: List[Dict[str, Any]], failure_counts: Optional[Dict[tuple, int]]) -> str:
```

Generates a formatted Markdown table from the collected statistics.

## main()

```python
def main():
```

Main function to parse command-line arguments and run the analysis.
