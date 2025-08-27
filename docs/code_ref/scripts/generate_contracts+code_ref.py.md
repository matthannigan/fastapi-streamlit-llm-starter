---
sidebar_label: generate_contracts+code_ref
---

# Public Contract and Documentation Generator

  file_path: `scripts/generate_contracts+code_ref.py`
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

## Single file

```bash
python generate_docs.py backend/app/main.py --pyi-output-dir backend/contracts --md-output-dir docs/api
```

Directory (smart detection or explicit flags):
```bash
python generate_docs.py backend/app --pyi-output-dir backend/contracts --md-output-dir docs/api
# or
python generate_docs.py --input-dir backend/app --pyi-output-dir backend/contracts --md-output-dir docs/api
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
