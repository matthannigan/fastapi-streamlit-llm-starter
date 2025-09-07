# -*- coding: utf-8 -*-
"""
Scans a directory of Python files to generate statistics about classes and methods.

This script uses Python's `ast` module to parse Python source files without
executing them. It counts the total methods, methods marked with
`@pytest.mark.skip`, and methods with an actual implementation (i.e., more
than just a `pass` statement or a docstring).

The output is a Markdown table, which can be printed to the console or saved
to a file.
"""

import ast
import os
import argparse
from typing import List, Dict, Any

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
    An AST visitor that traverses a Python file's AST to find classes
    and collect statistics about their methods.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.stats: List[Dict[str, Any]] = []
        self._current_class_name: str | None = None
        self._current_class_stats: Dict[str, int] = {}

    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Called when the visitor encounters a class definition.
        Initializes statistics for the class and then visits its body.
        """
        self._current_class_name = node.name
        self._current_class_stats = {
            "total_methods": 0,
            "skipped_methods": 0,
            "implemented_methods": 0,
        }
        
        # Visit all nodes inside the class (e.g., methods)
        self.generic_visit(node)
        
        # After visiting all methods, if any were found, save the stats
        if self._current_class_stats["total_methods"] > 0:
            self.stats.append({
                "file_path": self.file_path,
                "class_name": self._current_class_name,
                **self._current_class_stats,
            })
            
        self._current_class_name = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Called when the visitor encounters a function or method definition.
        Gathers statistics if it's inside a class.
        """
        # We only care about methods defined within a class
        if self._current_class_name is None:
            self.generic_visit(node)
            return

        self._current_class_stats["total_methods"] += 1

        # Check for @pytest.mark.skip decorator
        for decorator in node.decorator_list:
            decorator_name = get_decorator_name(decorator)
            if decorator_name == 'pytest.mark.skip':
                self._current_class_stats["skipped_methods"] += 1
                break

        # Check for an actual implementation
        # An implementation exists if there is any statement in the body
        # that is not a `pass` statement or a lone docstring.
        if node.body:
            # Check for an actual implementation. Docstrings are `Expr` nodes
            # containing a `Constant` (string). We ignore them and `pass`.
            non_trivial_statements = [
                stmt for stmt in node.body
                if not isinstance(stmt, ast.Pass) and not (
                    isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                )
            ]
            if non_trivial_statements:
                self._current_class_stats["implemented_methods"] += 1
        
        self.generic_visit(node)

def analyze_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a single Python file and returns statistics for its classes.
    Returns an empty list if the file cannot be parsed.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as source_file:
            source_code = source_file.read()
        tree = ast.parse(source_code, filename=file_path)
        analyzer = ClassMethodAnalyzer(file_path)
        analyzer.visit(tree)
        return analyzer.stats
    except (SyntaxError, FileNotFoundError, UnicodeDecodeError, TypeError) as e:
        print(f"Warning: Skipping file '{file_path}' due to an error: {e}")
        return []

def scan_directory(directory: str) -> List[Dict[str, Any]]:
    """
    Recursively scans a directory for `.py` files and analyzes them.
    """
    all_stats = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                # Make file paths relative and use forward slashes for consistency
                relative_path = os.path.relpath(file_path, directory)
                file_stats = analyze_file(file_path)
                for stat in file_stats:
                    stat['file_path'] = relative_path.replace('\\', '/')
                all_stats.extend(file_stats)
    return all_stats

def generate_markdown_table(stats: List[Dict[str, Any]]) -> str:
    """
    Generates a formatted Markdown table from the collected statistics.
    """
    header = "| Status | File Path | Class Name | Total Methods | Non-Skip Methods | Actual Implementation |\n"
    separator = "|--------|-----------|------------|---------------|------------------|----------------------|\n"
    
    rows = []
    # Sort stats for a consistent and readable output. Use `or ''` to handle potential None values.
    stats.sort(key=lambda x: (x.get('file_path') or '', x.get('class_name') or ''))

    for stat in stats:
        total_methods = stat["total_methods"]
        non_skip_methods = total_methods - stat["skipped_methods"]
        actual_implementation = stat["implemented_methods"]

        # Determine status emoji
        status = "🔴"  # Red: No implementation
        if non_skip_methods > 0:
            if actual_implementation == non_skip_methods:
                status = "🟢"  # Green: Fully implemented
            elif actual_implementation > 0:
                status = "🟡"  # Yellow: Partially implemented
        
        row = (
            f"| {status} "
            f"| `{stat['file_path']}` "
            f"| {stat['class_name']} "
            f"| {total_methods} "
            f"| {non_skip_methods} "
            f"| {actual_implementation} |"
        )
        rows.append(row)
        
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
    args = parser.parse_args()
    
    target_directory = os.path.abspath(args.directory)
    if not os.path.isdir(target_directory):
        print(f"Error: Directory not found at '{target_directory}'")
        return

    print(f"Scanning directory: {target_directory}...")
    class_stats = scan_directory(target_directory)
    
    if not class_stats:
        print("No Python files with classes were found or successfully analyzed.")
        return
        
    markdown_output = generate_markdown_table(class_stats)
    
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
