---
sidebar_label: generate_code_docs
---

# Public Contract and Documentation Generator

  file_path: `scripts/generate_code_docs.py`
===========================================

Generates a "public contract" type-stub and Markdown documentation from Python
source, suitable for tests, type checking, and documentation platforms like
Docusaurus. The output is designed to be stable and readable, preserving public
API shape (signatures, docstrings, inheritance) while omitting implementation
details.

Features
--------
- **Dual Output**: Generates both ``.pyi`` contract stubs and ``.md``
  documentation files.
- **Robust signature builder**: Handles positional-only, keyword-only, varargs,
  kwargs, defaults, annotations, and async functions.
- **Class method emission**: Emits methods nested within classes; nested classes
  are supported.
- **Empty class handling**: Emits a configurable placeholder when a class body
  would otherwise be empty.
- **Docstrings**: Preserves and indents module, class, and function docstrings
  as multi-line blocks.
- **Imports**: Collects and emits only top-level imports (deduplicated, order
  preserved) near the module top.
- **Stable ordering**: Module docstring → imports → classes → functions.
- **Filtering**: Control inclusion of private names and dunder methods.
- **Directory mode**: Recursively process a directory tree, mirroring structure
  into an output directory and generating ``.pyi`` and ``.md`` files.

Usage
-----
Single file:
```bash
python generate_code_docs.py backend/app/main.py --pyi-output-dir backend/contracts --md-output-dir docs/api
```

Directory (smart detection or explicit flags):
```bash
python generate_code_docs.py backend/app --pyi-output-dir backend/contracts --md-output-dir docs/api
# or
python generate_code_docs.py --input-dir backend/app --pyi-output-dir backend/contracts --md-output-dir docs/api
```

CLI Options
-----------
- ``input_path``: Positional path to a source ``.py`` file or a directory
  (smart-detected). If ``--input-dir`` is supplied, it takes precedence.
- ``--pyi-output-dir``: Output directory for ``.pyi`` files.
- ``--md-output-dir``: Output directory for ``.md`` files.
- ``--include-private``: Include names starting with a single underscore.
- ``--exclude-dunder``: Exclude ``__dunder__`` names (keeps ``__init__`` for methods).
- ``--body-placeholder {ellipsis,pass}``: Placeholder for generated bodies.
  Defaults to ``ellipsis`` (``...``), recommended for ``.pyi`` stubs.
- ``--encoding``: File encoding for reading source (default: ``utf-8``).

Behavior
--------
- Generates type stubs (``.pyi``) and uses ``...`` by default.
- Creates intermediate directories as needed.
- Skips hidden directories and ``__pycache__`` when processing trees.
- Prints a summary in directory mode (``Processed X/Y files``).

Exit Codes
----------
- ``1``: Failed to read input file
- ``2``: Syntax error while parsing
- ``3``: Unexpected generation error
- ``4``: Directory mode without a valid output directory

Notes
-----
- For contract snapshots used in tests and static analysis, prefer ``.pyi`` with
  ``...`` bodies. Use ``pass`` only if you truly need executable skeletons.
- The generator targets Python 3.9+ (uses ``ast.unparse``).

## PublicContractGenerator

Traverses a Python AST and generates a public contract file.

### __init__()

```python
def __init__(self, *, include_private: bool = False, exclude_dunder: bool = False, body_placeholder: str = '...', public_object_types: Optional[List[str]] = None):
```

### visit_Assign()

```python
def visit_Assign(self, node: ast.Assign):
```

Captures public module-level constants AND common public objects
like FastAPI Routers, Blueprints, etc.

### visit_Import()

```python
def visit_Import(self, node: ast.Import):
```

### visit_ImportFrom()

```python
def visit_ImportFrom(self, node: ast.ImportFrom):
```

### visit_AnnAssign()

```python
def visit_AnnAssign(self, node: ast.AnnAssign):
```

Capture top-level annotated assignments if they look public/constant objects and pass filters.

### visit_ClassDef()

```python
def visit_ClassDef(self, node: ast.ClassDef):
```

### visit_FunctionDef()

```python
def visit_FunctionDef(self, node: ast.FunctionDef):
```

### visit_AsyncFunctionDef()

```python
def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
```

### generate()

```python
def generate(self, source_code: str, source_path: Path, is_init_file: bool = False) -> str:
```

Parses source code and returns the public contract.

## MarkdownContractGenerator

Traverses a Python AST and generates Markdown documentation.

### generate()

```python
def generate(self, source_code: str, source_path: Path, is_init_file: bool = False) -> str:
```

### visit_ClassDef()

```python
def visit_ClassDef(self, node: ast.ClassDef):
```

### visit_FunctionDef()

```python
def visit_FunctionDef(self, node: ast.FunctionDef):
```

### visit_AsyncFunctionDef()

```python
def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
```

## main()

```python
def main():
```
