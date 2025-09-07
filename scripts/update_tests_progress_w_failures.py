# -*- coding: utf-8 -*-
"""
Scans a directory of Python files to generate statistics about classes, methods,
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
"""

import ast
import os
import argparse
import re
import json
from collections import Counter
from typing import List, Dict, Any, Optional, Union

def get_decorator_name(decorator_node: ast.expr) -> str:
    """
    Recursively constructs the full decorator name from an AST node.
    Handles simple names (`@mydecorator`), attributes (`@pytest.mark.skip`),
    and calls (`@mydecorator(arg)`).
    """
    if isinstance(decorator_node, ast.Name):
        return decorator_node.id
    elif isinstance(decorator_node, ast.Attribute):
        # Recursively build the name, e.g., "pytest.mark.skip"
        return f"{get_decorator_name(decorator_node.value)}.{decorator_node.attr}"
    elif isinstance(decorator_node, ast.Call):
        # Handle decorators that are calls, e.g., @patch('__main__.x')
        return get_decorator_name(decorator_node.func)
    return ""

class ClassMethodAnalyzer(ast.NodeVisitor):
    """
    An AST visitor that traverses a Python file's AST, collecting and
    aggregating statistics about all classes and standalone test functions.
    """
    STANDALONE_KEY = "[Standalone Functions]"

    def __init__(self, file_path: str):
        self.file_path = file_path
        # Use a dictionary for aggregation to prevent duplicates.
        self.class_stats: Dict[str, Dict[str, int]] = {}
        self._class_name_stack: List[str] = []

    def _get_stats_dict(self, class_name: str) -> Dict[str, int]:
        """Initializes or retrieves the stats dictionary for a given class name."""
        if class_name not in self.class_stats:
            self.class_stats[class_name] = {
                "total_methods": 0,
                "skipped_methods": 0,
                "implemented_methods": 0,
            }
        return self.class_stats[class_name]

    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Called when visiting a class. Pushes the class onto a stack to handle
        nested classes correctly.
        """
        self._class_name_stack.append(node.name)
        self._get_stats_dict(node.name) # Ensure class exists in stats
        self.generic_visit(node)
        self._class_name_stack.pop()

    def _process_function_node(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        """Helper to process both sync and async function/method nodes."""
        stats_dict = None
        if self._class_name_stack:
            # We are inside a class
            current_class_name = self._class_name_stack[-1]
            stats_dict = self._get_stats_dict(current_class_name)
        elif node.name.startswith('test_'):
            # This is a standalone test function
            stats_dict = self._get_stats_dict(self.STANDALONE_KEY)
        else:
            # Not a method in a tracked class or a standalone test, so skip.
            self.generic_visit(node)
            return

        stats_dict["total_methods"] += 1

        for decorator in node.decorator_list:
            decorator_name = get_decorator_name(decorator)
            if decorator_name == 'pytest.mark.skip':
                stats_dict["skipped_methods"] += 1
                break

        if node.body:
            non_trivial_statements = [
                stmt for stmt in node.body
                if not isinstance(stmt, ast.Pass) and not (
                    isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                )
            ]
            if non_trivial_statements:
                stats_dict["implemented_methods"] += 1
        
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Called for sync functions/methods."""
        self._process_function_node(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Called for async functions/methods."""
        self._process_function_node(node)

    def get_final_stats(self) -> List[Dict[str, Any]]:
        """
        Converts the aggregated stats dictionary into the final list format
        for the report.
        """
        final_list = []
        for class_name, stats in self.class_stats.items():
            # Only include classes/groups that actually have methods
            if stats["total_methods"] > 0:
                final_list.append({
                    "file_path": self.file_path,
                    "class_name": class_name,
                    **stats
                })
        return final_list

def analyze_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a single Python file and returns statistics for its classes
    and standalone test functions.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as source_file:
            source_code = source_file.read()
        tree = ast.parse(source_code, filename=file_path)
        analyzer = ClassMethodAnalyzer(file_path)
        analyzer.visit(tree)
        return analyzer.get_final_stats()
    except (SyntaxError, FileNotFoundError, UnicodeDecodeError, TypeError) as e:
        print(f"Warning: Skipping file '{file_path}' due to an error: {e}")
        return []

def scan_directory(directory: str) -> List[Dict[str, Any]]:
    """
    Recursively scans a directory for `test_*.py` files and analyzes them.
    Ensures all test files are accounted for in the output.
    """
    all_stats = []
    
    # Inventory all test files first
    test_files_to_process = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files_to_process.append(os.path.join(root, file))

    # Analyze each inventoried file
    for file_path in test_files_to_process:
        relative_path = os.path.relpath(file_path, directory).replace('\\', '/')
        file_stats = analyze_file(file_path)
        
        if file_stats:
            for stat in file_stats:
                stat['file_path'] = relative_path
            all_stats.extend(file_stats)
        else:
            # Add a placeholder if a test file has no discoverable tests
            all_stats.append({
                "file_path": relative_path,
                "class_name": "[No Tests Found]",
                "total_methods": 0,
                "skipped_methods": 0,
                "implemented_methods": 0,
            })
            
    return all_stats


def parse_text_failures_file(file_path: str, base_dir: str) -> Dict[tuple, int]:
    """
    Parses a pytest plain text summary file and counts failures per class or
    for standalone functions in a file.
    """
    failure_counts = Counter()
    pattern = re.compile(r"FAILED\s+([^:]+)::([^\s:]+)(::.*)?")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    log_path, name, is_method_part = match.groups()
                    
                    abs_log_path = os.path.abspath(log_path)
                    relative_path = os.path.relpath(abs_log_path, base_dir).replace('\\', '/')
                    
                    # If it's a method, name is the class. If standalone, it's the func name.
                    if is_method_part:
                        class_name = name
                    else:
                        class_name = "[Standalone Functions]"
                    
                    failure_counts[(relative_path, class_name)] += 1
    except FileNotFoundError:
        print(f"Warning: Failures file not found at '{file_path}'")
        return {}
    except Exception as e:
        print(f"Warning: An error occurred while parsing text failures file '{file_path}': {e}")
        return {}
        
    return dict(failure_counts)

def parse_json_failures_file(file_path: str, base_dir: str) -> Dict[tuple, int]:
    """
    Parses a pytest JSON report file and counts failures per class or for
    standalone functions in a file.
    """
    failure_counts = Counter()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        if 'tests' not in report:
            print(f"Warning: JSON report '{file_path}' has no 'tests' key.")
            return {}

        for test in report['tests']:
            if test.get('outcome') == 'failed':
                nodeid = test.get('nodeid', '')
                parts = nodeid.split('::')
                
                if len(parts) >= 1:
                    log_path = parts[0]
                    class_name = "[Standalone Functions]"
                    if len(parts) > 2: # Format: file.py::Class::method
                        class_name = parts[1]
                    
                    abs_log_path = os.path.abspath(log_path)
                    relative_path = os.path.relpath(abs_log_path, base_dir).replace('\\', '/')
                    
                    failure_counts[(relative_path, class_name)] += 1

    except FileNotFoundError:
        print(f"Warning: Failures file not found at '{file_path}'")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from '{file_path}'.")
        return {}
    except Exception as e:
        print(f"Warning: An error occurred while parsing JSON failures file '{file_path}': {e}")
        return {}
        
    return dict(failure_counts)


def generate_markdown_table(stats: List[Dict[str, Any]], failure_counts: Optional[Dict[tuple, int]]) -> str:
    """
    Generates a formatted Markdown table from the collected statistics.
    """
    has_failures_info = failure_counts is not None

    if has_failures_info:
        header = "| Status | File Path | Class Name | Total Methods | Non-Skip Methods | Actual Implementation | Passing Implemented Tests |\n"
        separator = "|--------|-----------|------------|---------------|------------------|-----------------------|---------------------------|\n"
    else:
        header = "| Status | File Path | Class Name | Total Methods | Non-Skip Methods | Actual Implementation |\n"
        separator = "|--------|-----------|------------|---------------|------------------|----------------------|\n"
    
    rows = []
    stats.sort(key=lambda x: (x.get('file_path') or '', x.get('class_name') or ''))

    for stat in stats:
        total_methods = stat["total_methods"]
        non_skip_methods = total_methods - stat["skipped_methods"]
        actual_implementation = stat["implemented_methods"]

        failures = 0
        if has_failures_info:
            key = (stat['file_path'], stat['class_name'])
            failures = failure_counts.get(key, 0)
        
        # Determine status emoji
        if stat['class_name'] == "[No Tests Found]":
            status = "⚪"  # White/Gray for no tests
        else:
            is_fully_implemented = non_skip_methods > 0 and actual_implementation >= non_skip_methods
            is_partially_implemented = actual_implementation > 0 and actual_implementation < non_skip_methods
            
            status = "🔴" # Default to Red
            if is_fully_implemented:
                status = "🟢" if failures == 0 else "🟡"
            elif is_partially_implemented:
                status = "🟠"
        
        passing_tests_str = f"| {actual_implementation - failures} |" if has_failures_info else ""
        
        row_str = (
            f"| {status} "
            f"| `{stat.get('file_path', 'N/A')}` "
            f"| {stat.get('class_name', 'N/A')} "
            f"| {total_methods} "
            f"| {non_skip_methods} "
            f"| {actual_implementation} "
        )
        
        if has_failures_info:
            row_str += f"| {actual_implementation - failures} |"
        else:
            row_str += "|"
            
        rows.append(row_str)
        
    return header + separator + "\n".join(rows)

def main():
    """
    Main function to parse command-line arguments and run the analysis.
    """
    parser = argparse.ArgumentParser(
        description="Scan a directory of Python files and generate statistics about classes and methods.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "directory", 
        nargs='?', 
        default='.', 
        help="The target directory to scan (default: current directory)."
    )
    parser.add_argument(
        "-o", "--output",
        help="The file to write the Markdown table to (default: print to stdout)."
    )
    parser.add_argument(
        "-f", "--failures",
        help="Path to a pytest failure summary (text or .json from pytest-json-report)."
    )
    args = parser.parse_args()
    
    target_directory = os.path.abspath(args.directory)
    if not os.path.isdir(target_directory):
        print(f"Error: Directory not found at '{target_directory}'")
        return

    failure_counts = None
    if args.failures:
        print(f"Parsing failures file: {args.failures}...")
        if args.failures.endswith('.json'):
            failure_counts = parse_json_failures_file(args.failures, target_directory)
        else:
            failure_counts = parse_text_failures_file(args.failures, target_directory)

    print(f"Scanning directory: {target_directory}...")
    class_stats = scan_directory(target_directory)
    
    if not class_stats:
        print("No Python test files were found or successfully analyzed.")
        return
        
    markdown_output = generate_markdown_table(class_stats, failure_counts)
    
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(markdown_output)
            print(f"Successfully wrote statistics to {args.output}")
        except IOError as e:
            print(f"Error writing to file {args.output}: {e}")
    else:
        print("\n--- Analysis Complete ---\n")
        print(markdown_output)

if __name__ == "__main__":
    main()
