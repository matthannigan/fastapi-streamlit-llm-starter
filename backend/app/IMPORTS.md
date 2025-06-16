# Import Strategy and Path Aliases for Refactored Backend

## Import Conventions
- **Absolute imports** should be used throughout the codebase, always starting from the `backend.app` root.
  - Example: `from backend.app.core import config`
  - Example: `from backend.app.infrastructure.cache import base`
- **Relative imports** should be avoided except for intra-package imports within the same submodule.
- All new code and refactored modules should follow this convention to ensure clarity and avoid import errors during migration.

## PYTHONPATH Guidance
- For development and running scripts, ensure the project root is in your `PYTHONPATH`.
  - Example: `export PYTHONPATH=$(pwd)` (from the project root)
- This allows you to run modules and tests using absolute imports as intended.

## Path Aliases for Tools
- For static analysis and testing tools (e.g., mypy, pytest), configure path aliases to recognize the `backend` directory as a source root.
- Example `pyproject.toml` settings:

```toml
[tool.mypy]
mypy_path = "backend"

[tool.pytest.ini_options]
pythonpath = [".", "backend"]
```
- If using Poetry or PEP 621 tools, ensure the `backend` directory is included in the source paths.

## Migration Tooling
- The `import_update_script.py` will use these conventions to update imports during the migration.
- Developers should follow these patterns for any new modules or manual import changes.

## Summary
- **Always use absolute imports from `backend.app` root.**
- **Set `PYTHONPATH` to project root for development and testing.**
- **Configure static analysis tools to recognize `backend` as a source root.** 