---
sidebar_label: update_tests_progress
---

# Scans a directory of Python files to generate statistics about classes and methods.

  file_path: `scripts/update_tests_progress.py`

This script uses Python's `ast` module to parse Python source files without
executing them. It counts the total methods, methods marked with
`@pytest.mark.skip`, and methods with an actual implementation (i.e., more
than just a `pass` statement or a docstring).

The output is a Markdown table, which can be printed to the console or saved
to a file.

## ClassMethodAnalyzer

An AST visitor that traverses a Python file's AST to find classes
and collect statistics about their methods.

### __init__()

```python
def __init__(self, file_path: str):
```

### visit_ClassDef()

```python
def visit_ClassDef(self, node: ast.ClassDef):
```

Called when the visitor encounters a class definition.
Initializes statistics for the class and then visits its body.

### visit_FunctionDef()

```python
def visit_FunctionDef(self, node: ast.FunctionDef):
```

Called when the visitor encounters a function or method definition.
Gathers statistics if it's inside a class.

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

Parses a single Python file and returns statistics for its classes.
Returns an empty list if the file cannot be parsed.

## scan_directory()

```python
def scan_directory(directory: str) -> List[Dict[str, Any]]:
```

Recursively scans a directory for `.py` files and analyzes them.

## generate_markdown_table()

```python
def generate_markdown_table(stats: List[Dict[str, Any]]) -> str:
```

Generates a formatted Markdown table from the collected statistics.

## main()

```python
def main():
```

Main function to parse command-line arguments and run the analysis.
