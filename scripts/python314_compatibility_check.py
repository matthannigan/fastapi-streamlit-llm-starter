#!/usr/bin/env python3
"""
Python 3.14 Compatibility Assessment Script

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
"""

import ast
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass, asdict
import re


@dataclass
class CompatibilityIssue:
    """Represents a potential Python 3.14 compatibility issue."""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    severity: str  # 'error', 'warning', 'info'
    recommendation: str
    code_snippet: str


class Python314CompatibilityChecker:
    """
    Python 3.14 compatibility checker for the FastAPI-Streamlit-LLM-Starter project.

    This checker identifies code patterns that may break or behave differently
    in Python 3.14 based on known upcoming changes and deprecations.
    """

    def __init__(self, project_root: Path):
        """
        Initialize compatibility checker.

        Args:
            project_root: Root directory of the project to analyze
        """
        self.project_root = Path(project_root)
        self.issues: List[CompatibilityIssue] = []

        # Patterns to exclude from analysis
        self.exclude_patterns = {
            '*.pyc', '__pycache__', '.git', '.venv', 'node_modules',
            'htmlcov', '*.egg-info', 'dist', 'build'
        }

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []

        for path in self.project_root.rglob("*.py"):
            # Skip excluded directories
            if any(exclude in str(path) for exclude in self.exclude_patterns):
                continue
            python_files.append(path)

        return python_files

    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file for compatibility issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST for structural analysis
            try:
                tree = ast.parse(content, filename=str(file_path))
                self._analyze_ast(file_path, tree, content.splitlines())
            except SyntaxError as e:
                self.issues.append(CompatibilityIssue(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=e.lineno or 0,
                    issue_type="syntax_error",
                    description=f"Syntax error prevents analysis: {e.msg}",
                    severity="error",
                    recommendation="Fix syntax error before Python 3.14 migration",
                    code_snippet=content.splitlines()[e.lineno - 1] if e.lineno else "Unknown"
                ))

            # Text-based analysis for patterns not easily caught by AST
            self._analyze_text_patterns(file_path, content)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _analyze_ast(self, file_path: Path, tree: ast.AST, lines: List[str]) -> None:
        """Analyze AST for Python 3.14 compatibility issues."""

        class CompatibilityVisitor(ast.NodeVisitor):
            def __init__(self, checker, file_path, lines):
                self.checker = checker
                self.file_path = file_path
                self.lines = lines
                self.in_finally = False

            def visit_Try(self, node):
                """Check finally clauses for PEP 765 violations."""
                if node.finalbody:
                    old_in_finally = self.in_finally
                    self.in_finally = True

                    for stmt in node.finalbody:
                        self.visit(stmt)

                    self.in_finally = old_in_finally

                # Visit other parts normally
                for handler in node.handlers:
                    self.visit(handler)
                for stmt in node.body:
                    self.visit(stmt)
                for stmt in node.orelse:
                    self.visit(stmt)

            def visit_Return(self, node):
                """Check for return statements in finally clauses (PEP 765)."""
                if self.in_finally:
                    self._add_issue(
                        node, "finally_return", "error",
                        "Return statement in finally clause will raise SyntaxError in Python 3.14",
                        "Remove return statement from finally clause or restructure exception handling"
                    )
                self.generic_visit(node)

            def visit_Break(self, node):
                """Check for break statements in finally clauses (PEP 765)."""
                if self.in_finally:
                    self._add_issue(
                        node, "finally_break", "error",
                        "Break statement in finally clause will raise SyntaxError in Python 3.14",
                        "Remove break statement from finally clause or restructure loop logic"
                    )
                self.generic_visit(node)

            def visit_Continue(self, node):
                """Check for continue statements in finally clauses (PEP 765)."""
                if self.in_finally:
                    self._add_issue(
                        node, "finally_continue", "error",
                        "Continue statement in finally clause will raise SyntaxError in Python 3.14",
                        "Remove continue statement from finally clause or restructure loop logic"
                    )
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                """Check for __future__ import annotations (PEP 649)."""
                if (node.module == "__future__" and
                    any(alias.name == "annotations" for alias in node.names)):
                    self._add_issue(
                        node, "future_annotations", "warning",
                        "from __future__ import annotations will be deprecated in Python 3.14",
                        "This import will become unnecessary as deferred evaluation becomes default"
                    )
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                """Check function annotations for PEP 649 compatibility."""
                # Check if function uses complex annotation patterns that might break
                if node.returns and isinstance(node.returns, ast.Subscript):
                    # Complex return type annotations may need adjustment
                    self._add_issue(
                        node, "complex_annotation", "info",
                        f"Complex return annotation in function '{node.name}' may need review for PEP 649",
                        "Verify that complex type annotations work correctly with deferred evaluation"
                    )
                self.generic_visit(node)

            def _add_issue(self, node, issue_type, severity, description, recommendation):
                """Add a compatibility issue."""
                line_num = getattr(node, 'lineno', 0)
                code_snippet = self.lines[line_num - 1] if line_num <= len(self.lines) else "Unknown"

                self.checker.issues.append(CompatibilityIssue(
                    file_path=str(self.file_path.relative_to(self.checker.project_root)),
                    line_number=line_num,
                    issue_type=issue_type,
                    description=description,
                    severity=severity,
                    recommendation=recommendation,
                    code_snippet=code_snippet.strip()
                ))

        visitor = CompatibilityVisitor(self, file_path, lines)
        visitor.visit(tree)

    def _analyze_text_patterns(self, file_path: Path, content: str) -> None:
        """Analyze text patterns that might cause Python 3.14 issues."""
        lines = content.splitlines()

        # Check for potential annotation evaluation timing issues
        annotation_runtime_pattern = re.compile(r'getattr\s*\(\s*\w+\s*,\s*["\']__annotations__["\']')
        for i, line in enumerate(lines, 1):
            if annotation_runtime_pattern.search(line):
                self.issues.append(CompatibilityIssue(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=i,
                    issue_type="annotation_runtime_access",
                    description="Runtime access to __annotations__ may behave differently with PEP 649",
                    severity="warning",
                    recommendation="Review runtime annotation access patterns for PEP 649 compatibility",
                    code_snippet=line.strip()
                ))

        # Check for deprecated string formatting patterns
        old_format_pattern = re.compile(r'%\s*[sd]')
        for i, line in enumerate(lines, 1):
            if old_format_pattern.search(line) and 'f"' not in line:
                self.issues.append(CompatibilityIssue(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=i,
                    issue_type="old_string_format",
                    description="Old-style string formatting may have performance implications",
                    severity="info",
                    recommendation="Consider migrating to f-strings for better Python 3.14 performance",
                    code_snippet=line.strip()
                ))

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete compatibility analysis."""
        print("Starting Python 3.14 compatibility analysis...")
        print(f"Analyzing project: {self.project_root}")

        python_files = self.find_python_files()
        print(f"Found {len(python_files)} Python files to analyze")

        # Analyze each file
        for i, file_path in enumerate(python_files, 1):
            if i % 50 == 0 or i == len(python_files):
                print(f"Progress: {i}/{len(python_files)} files analyzed")

            self.analyze_file(file_path)

        # Generate summary
        summary = self._generate_summary()
        print(f"\nAnalysis complete. Found {len(self.issues)} potential issues.")

        return summary

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate analysis summary."""
        issues_by_severity = {"error": [], "warning": [], "info": []}
        issues_by_type = {}
        files_with_issues = set()

        for issue in self.issues:
            issues_by_severity[issue.severity].append(issue)
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
            files_with_issues.add(issue.file_path)

        return {
            "total_issues": len(self.issues),
            "issues_by_severity": {k: len(v) for k, v in issues_by_severity.items()},
            "issues_by_type": {k: len(v) for k, v in issues_by_type.items()},
            "files_with_issues": len(files_with_issues),
            "critical_issues": len(issues_by_severity["error"]),
            "issues": [asdict(issue) for issue in self.issues]
        }

    def check_specific_pattern(self, pattern_type: str) -> List[CompatibilityIssue]:
        """Check for specific compatibility pattern."""
        python_files = self.find_python_files()
        pattern_issues = []

        for file_path in python_files:
            self.analyze_file(file_path)

        # Filter issues by pattern type
        pattern_issues = [issue for issue in self.issues if issue.issue_type.startswith(pattern_type)]
        return pattern_issues

    def generate_report(self, output_file: Optional[str] = None) -> None:
        """Generate detailed compatibility report."""
        summary = self._generate_summary()

        print("\n" + "=" * 80)
        print("PYTHON 3.14 COMPATIBILITY REPORT")
        print("=" * 80)

        print(f"\nSummary:")
        print(f"  Total issues found: {summary['total_issues']}")
        print(f"  Files with issues: {summary['files_with_issues']}")
        print(f"  Critical errors: {summary['critical_issues']}")

        print(f"\nIssues by severity:")
        for severity, count in summary['issues_by_severity'].items():
            icon = "🔴" if severity == "error" else "🟡" if severity == "warning" else "🔵"
            print(f"  {icon} {severity.title()}: {count}")

        print(f"\nIssues by type:")
        for issue_type, count in summary['issues_by_type'].items():
            print(f"  {issue_type}: {count}")

        # Detailed issue listing
        if self.issues:
            print(f"\nDetailed Issues:")
            print("-" * 80)

            # Group by severity for display
            for severity in ["error", "warning", "info"]:
                severity_issues = [issue for issue in self.issues if issue.severity == severity]
                if severity_issues:
                    print(f"\n{severity.upper()} ISSUES:")
                    for issue in severity_issues[:10]:  # Limit display
                        print(f"\n📁 {issue.file_path}:{issue.line_number}")
                        print(f"   Issue: {issue.description}")
                        print(f"   Code:  {issue.code_snippet}")
                        print(f"   Fix:   {issue.recommendation}")

                    if len(severity_issues) > 10:
                        print(f"   ... and {len(severity_issues) - 10} more {severity} issues")

        # Recommendations
        print(f"\nPython 3.14 Migration Recommendations:")
        print("1. Address all ERROR-level issues immediately")
        print("2. Review WARNING-level issues for compatibility impact")
        print("3. Consider INFO-level suggestions for performance improvements")
        print("4. Test with Python 3.14 release candidates when available")
        print("5. Update CI/CD to include Python 3.14 testing")

        # Save detailed report if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"\nDetailed JSON report saved to: {output_file}")


def main():
    """Main compatibility check execution."""
    parser = argparse.ArgumentParser(description="Python 3.14 Compatibility Checker")
    parser.add_argument("--project-root", type=str, default=".",
                       help="Project root directory (default: current directory)")
    parser.add_argument("--check", choices=["finally_clauses", "annotations", "imports", "all"],
                       default="all", help="Specific compatibility check to run")
    parser.add_argument("--report", type=str,
                       help="Save detailed JSON report to file")

    args = parser.parse_args()

    # Initialize checker
    project_root = Path(args.project_root).resolve()
    checker = Python314CompatibilityChecker(project_root)

    # Run requested analysis
    if args.check == "all":
        summary = checker.run_full_analysis()
    else:
        print(f"Running specific check: {args.check}")
        issues = checker.check_specific_pattern(args.check)
        print(f"Found {len(issues)} issues related to {args.check}")

    # Generate report
    checker.generate_report(output_file=args.report)

    # Exit with appropriate code
    critical_issues = sum(1 for issue in checker.issues if issue.severity == "error")
    if critical_issues > 0:
        print(f"\n⚠️  Found {critical_issues} critical compatibility issues!")
        print("These MUST be fixed before upgrading to Python 3.14")
        sys.exit(1)
    else:
        print(f"\n✅ No critical compatibility issues found!")
        print("Project appears ready for Python 3.14 migration")
        sys.exit(0)


if __name__ == "__main__":
    main()