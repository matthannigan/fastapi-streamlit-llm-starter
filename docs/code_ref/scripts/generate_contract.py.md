---
sidebar_label: generate_contract
---

# Public Contract Generator

  file_path: `scripts/generate_contract.py`
=========================

Generates a "public contract" type-stub from Python source, suitable for tests,
type checking, and documentation. The output is designed to be stable and
readable, preserving public API shape (signatures, docstrings, inheritance) while
omitting implementation details.

Features
--------
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
into an output directory and generating ``.pyi`` files.

Usage
-----

## Single file

```bash
python generate_contract.py backend/app/main.py -o backend/contracts/main.pyi
```

Directory (smart detection or explicit flags):
```bash
python generate_contract.py backend/app -o backend/contracts
# or
python generate_contract.py --input-dir backend/app --output-dir backend/contracts
```

CLI Options
-----------
- ``input_path``: Positional path to a source ``.py`` file or a directory
(smart-detected). If ``--input-dir`` is supplied, it takes precedence.
- ``-o, --output_file``: Output file (single-file mode) or output directory
(directory mode). In single-file mode, if this points to a directory, the
output name is derived from the input and written as ``.pyi``.
- ``--input-dir``: Explicit directory mode input. Preferred for CI/scripts.
- ``--output-dir``: Explicit output directory for directory mode.
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
