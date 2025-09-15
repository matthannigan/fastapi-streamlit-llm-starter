---
sidebar_label: python314_compatibility_check
---

# Python 3.14 Compatibility Assessment Script

  file_path: `scripts/python314_compatibility_check.py`

This script analyzes the codebase for compatibility with Python 3.14 release candidates
and upcoming changes. It identifies potential issues and provides recommendations for
maintaining forward compatibility.

## Key Python 3.14 Changes Analyzed

1. **PEP 765**: Drop support for `return`, `break`, `continue` in `finally` clauses
2. **PEP 649**: Deferred annotation evaluation becomes default behavior
3. **Enhanced Performance**: New tail-call interpreter optimizations
4. **Deprecations**: `from __future__ import annotations` becomes unnecessary

## Usage

```bash
# Run full compatibility analysis
python scripts/python314_compatibility_check.py

# Check specific areas
python scripts/python314_compatibility_check.py --check finally_clauses
python scripts/python314_compatibility_check.py --check annotations
python scripts/python314_compatibility_check.py --check imports

# Generate detailed report
python scripts/python314_compatibility_check.py --report compatibility_report.json
```

## CompatibilityIssue

Represents a potential Python 3.14 compatibility issue.

## Python314CompatibilityChecker

Python 3.14 compatibility checker for the FastAPI-Streamlit-LLM-Starter project.

This checker identifies code patterns that may break or behave differently
in Python 3.14 based on known upcoming changes and deprecations.

### __init__()

```python
def __init__(self, project_root: Path):
```

Initialize compatibility checker.

Args:
    project_root: Root directory of the project to analyze

### find_python_files()

```python
def find_python_files(self) -> List[Path]:
```

Find all Python files in the project.

### analyze_file()

```python
def analyze_file(self, file_path: Path) -> None:
```

Analyze a single Python file for compatibility issues.

### run_full_analysis()

```python
def run_full_analysis(self) -> Dict[str, Any]:
```

Run complete compatibility analysis.

### check_specific_pattern()

```python
def check_specific_pattern(self, pattern_type: str) -> List[CompatibilityIssue]:
```

Check for specific compatibility pattern.

### generate_report()

```python
def generate_report(self, output_file: Optional[str] = None) -> None:
```

Generate detailed compatibility report.

## main()

```python
def main():
```

Main compatibility check execution.
