#!/usr/bin/env python3
"""
Structure Validation Script for Backend Refactoring

This script validates the project structure to ensure:
- No circular dependencies between modules
- Proper layer separation (Domain -> Infrastructure -> External)
- File size limits are respected
- Proper separation of concerns

Usage:
    python structure_validation.py [--max-file-lines 500] [--verbose]
"""

import os
import ast
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque
import json

# Layer definitions and allowed dependencies
LAYER_HIERARCHY = {
    "api": ["services", "infrastructure", "core", "schemas"],
    "services": ["infrastructure", "core", "schemas"],
    "infrastructure": ["core", "schemas"],
    "core": ["schemas"],
    "schemas": [],
    "examples": ["api", "services", "infrastructure", "core", "schemas"]  # Examples can import anything
}

# Infrastructure vs Domain classification
INFRASTRUCTURE_MODULES = {
    "infrastructure.cache",
    "infrastructure.resilience",
    "infrastructure.ai",
    "infrastructure.security",
    "infrastructure.monitoring"
}

DOMAIN_MODULES = {
    "services.text_processing",
    "services"  # Any service not in infrastructure
}


class DependencyGraph:
    """Represents the dependency graph of the project."""
    
    def __init__(self):
        self.graph = defaultdict(set)
        self.modules = set()
        
    def add_dependency(self, from_module: str, to_module: str):
        """Add a dependency from one module to another."""
        self.graph[from_module].add(to_module)
        self.modules.add(from_module)
        self.modules.add(to_module)
    
    def find_cycles(self) -> List[List[str]]:
        """Find all circular dependencies using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for module in self.modules:
            if module not in visited:
                dfs(module)
        
        return cycles
    
    def get_layer_violations(self) -> List[Tuple[str, str, str]]:
        """Find dependencies that violate layer hierarchy."""
        violations = []
        
        for from_module, to_modules in self.graph.items():
            from_layer = self._get_layer(from_module)
            
            if from_layer and from_layer in LAYER_HIERARCHY:
                allowed_layers = LAYER_HIERARCHY[from_layer]
                
                for to_module in to_modules:
                    to_layer = self._get_layer(to_module)
                    
                    if to_layer and to_layer not in allowed_layers:
                        violations.append((from_module, to_module, 
                                         f"{from_layer} cannot depend on {to_layer}"))
        
        return violations
    
    def _get_layer(self, module: str) -> Optional[str]:
        """Get the layer name from a module path."""
        parts = module.split('.')
        if len(parts) >= 2 and parts[0] == "app":
            return parts[1]
        return None


class StructureValidator:
    def __init__(self, root_dir: str, max_file_lines: int = 500, verbose: bool = False):
        self.root_dir = Path(root_dir)
        self.max_file_lines = max_file_lines
        self.verbose = verbose
        self.dependency_graph = DependencyGraph()
        self.validation_errors = defaultdict(list)
        self.validation_warnings = defaultdict(list)
        self.metrics = {
            "total_files": 0,
            "total_lines": 0,
            "oversized_files": [],
            "max_import_depth": 0,
            "infrastructure_files": 0,
            "domain_files": 0
        }
    
    def validate(self):
        """Run all validation checks."""
        print("Starting structure validation...")
        
        # Find all Python files
        python_files = self.find_python_files()
        self.metrics["total_files"] = len(python_files)
        
        # Validate each file
        for file_path in python_files:
            self.validate_file(file_path)
        
        # Check for circular dependencies
        self.check_circular_dependencies()
        
        # Check layer violations
        self.check_layer_violations()
        
        # Check infrastructure vs domain separation
        self.check_infrastructure_domain_separation()
        
        # Print results
        self.print_results()
    
    def find_python_files(self) -> List[Path]:
        """Find all Python files in the backend/app directory."""
        app_dir = self.root_dir / "backend" / "app"
        if not app_dir.exists():
            print(f"Warning: {app_dir} does not exist")
            return []
        
        python_files = []
        for ext in ['*.py']:
            python_files.extend(app_dir.rglob(ext))
        
        # Exclude test files and cache
        excluded_dirs = {'__pycache__', 'tests', '.pytest_cache'}
        python_files = [
            f for f in python_files 
            if not any(excluded in f.parts for excluded in excluded_dirs)
        ]
        
        return python_files
    
    def validate_file(self, file_path: Path):
        """Validate a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Check file size
            self.check_file_size(file_path, lines)
            
            # Analyze imports and dependencies
            self.analyze_imports(file_path, content)
            
            # Check module classification
            self.classify_module(file_path)
            
            # Update metrics
            self.metrics["total_lines"] += len(lines)
            
        except Exception as e:
            self.validation_errors[str(file_path)].append(f"Error reading file: {str(e)}")
    
    def check_file_size(self, file_path: Path, lines: List[str]):
        """Check if file exceeds size limit."""
        if len(lines) > self.max_file_lines:
            self.metrics["oversized_files"].append({
                "path": str(file_path),
                "lines": len(lines),
                "excess": len(lines) - self.max_file_lines
            })
            self.validation_warnings[str(file_path)].append(
                f"File has {len(lines)} lines (exceeds limit of {self.max_file_lines})"
            )
    
    def analyze_imports(self, file_path: Path, content: str):
        """Analyze imports in a Python file."""
        try:
            tree = ast.parse(content)
            module_path = self.get_module_path(file_path)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_module = alias.name
                        if self.is_local_import(imported_module):
                            self.dependency_graph.add_dependency(module_path, imported_module)
                            self.update_import_depth(imported_module)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and self.is_local_import(node.module):
                        # Handle relative imports
                        if node.level > 0:
                            resolved_module = self.resolve_relative_import(
                                file_path, node.module, node.level
                            )
                            if resolved_module:
                                self.dependency_graph.add_dependency(module_path, resolved_module)
                        else:
                            self.dependency_graph.add_dependency(module_path, node.module)
                            self.update_import_depth(node.module)
                        
        except SyntaxError as e:
            self.validation_errors[str(file_path)].append(f"Syntax error: {str(e)}")
    
    def get_module_path(self, file_path: Path) -> str:
        """Convert file path to module path."""
        try:
            rel_path = file_path.relative_to(self.root_dir / "backend")
            # Remove .py extension and convert to module path
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            return ".".join(module_parts)
        except ValueError:
            return str(file_path)
    
    def is_local_import(self, module_name: str) -> bool:
        """Check if an import is a local project import."""
        return module_name.startswith("app.") or module_name == "app"
    
    def resolve_relative_import(self, file_path: Path, module: Optional[str], level: int) -> Optional[str]:
        """Resolve a relative import to an absolute module path."""
        try:
            current_module = self.get_module_path(file_path)
            parts = current_module.split(".")
            
            # Go up 'level' directories
            if level <= len(parts):
                base_parts = parts[:-level]
                if module:
                    return ".".join(base_parts + module.split("."))
                else:
                    return ".".join(base_parts)
        except Exception:
            pass
        return None
    
    def update_import_depth(self, module_name: str):
        """Update maximum import depth metric."""
        depth = len(module_name.split("."))
        self.metrics["max_import_depth"] = max(self.metrics["max_import_depth"], depth)
    
    def classify_module(self, file_path: Path):
        """Classify module as infrastructure or domain."""
        module_path = self.get_module_path(file_path)
        
        for infra_module in INFRASTRUCTURE_MODULES:
            if infra_module in module_path:
                self.metrics["infrastructure_files"] += 1
                return
        
        if "services" in module_path or "domain" in module_path:
            self.metrics["domain_files"] += 1
    
    def check_circular_dependencies(self):
        """Check for circular dependencies."""
        cycles = self.dependency_graph.find_cycles()
        
        if cycles:
            for cycle in cycles:
                cycle_str = " -> ".join(cycle)
                self.validation_errors["circular_dependencies"].append(cycle_str)
    
    def check_layer_violations(self):
        """Check for layer hierarchy violations."""
        violations = self.dependency_graph.get_layer_violations()
        
        for from_module, to_module, reason in violations:
            self.validation_errors["layer_violations"].append(
                f"{from_module} -> {to_module}: {reason}"
            )
    
    def check_infrastructure_domain_separation(self):
        """Check that domain services don't import from each other."""
        for from_module, to_modules in self.dependency_graph.graph.items():
            # Check if this is a domain service
            if self.is_domain_module(from_module):
                for to_module in to_modules:
                    # Domain services shouldn't import from other domain services
                    if self.is_domain_module(to_module) and from_module != to_module:
                        base_from = from_module.split(".")[2] if len(from_module.split(".")) > 2 else ""
                        base_to = to_module.split(".")[2] if len(to_module.split(".")) > 2 else ""
                        
                        if base_from != base_to:
                            self.validation_warnings["domain_coupling"].append(
                                f"Domain service '{from_module}' imports from another domain service '{to_module}'"
                            )
    
    def is_domain_module(self, module_path: str) -> bool:
        """Check if a module is a domain service."""
        return "services" in module_path and not any(
            infra in module_path for infra in ["infrastructure", "core", "schemas"]
        )
    
    def print_results(self):
        """Print validation results."""
        print("\n" + "="*70)
        print("STRUCTURE VALIDATION RESULTS")
        print("="*70)
        
        # Print metrics
        print("\n## Project Metrics:")
        print(f"  Total files: {self.metrics['total_files']}")
        print(f"  Total lines: {self.metrics['total_lines']:,}")
        print(f"  Infrastructure files: {self.metrics['infrastructure_files']}")
        print(f"  Domain files: {self.metrics['domain_files']}")
        print(f"  Maximum import depth: {self.metrics['max_import_depth']}")
        
        # Print oversized files
        if self.metrics["oversized_files"]:
            print(f"\n## Oversized Files ({len(self.metrics['oversized_files'])}):")
            for file_info in sorted(self.metrics["oversized_files"], 
                                   key=lambda x: x["excess"], reverse=True)[:10]:
                print(f"  - {file_info['path']}: {file_info['lines']} lines "
                      f"(+{file_info['excess']} over limit)")
        
        # Print errors
        if self.validation_errors:
            print("\n## ❌ ERRORS:")
            
            if "circular_dependencies" in self.validation_errors:
                print("\n### Circular Dependencies:")
                for cycle in self.validation_errors["circular_dependencies"]:
                    print(f"  - {cycle}")
            
            if "layer_violations" in self.validation_errors:
                print("\n### Layer Violations:")
                for violation in self.validation_errors["layer_violations"]:
                    print(f"  - {violation}")
            
            # Other errors
            for category, errors in self.validation_errors.items():
                if category not in ["circular_dependencies", "layer_violations"]:
                    print(f"\n### {category}:")
                    for error in errors:
                        print(f"  - {error}")
        
        # Print warnings
        if self.validation_warnings:
            print("\n## ⚠️  WARNINGS:")
            
            for category, warnings in self.validation_warnings.items():
                print(f"\n### {category.replace('_', ' ').title()}:")
                for warning in warnings[:10]:  # Limit output
                    print(f"  - {warning}")
                if len(warnings) > 10:
                    print(f"  ... and {len(warnings) - 10} more")
        
        # Summary
        total_issues = sum(len(errors) for errors in self.validation_errors.values())
        total_warnings = sum(len(warnings) for warnings in self.validation_warnings.values())
        
        print("\n" + "-"*70)
        print(f"Total Errors: {total_issues}")
        print(f"Total Warnings: {total_warnings}")
        
        if total_issues == 0:
            print("\n✅ Structure validation PASSED!")
        else:
            print("\n❌ Structure validation FAILED!")
            print("Please fix the errors before proceeding.")
        
        # Export detailed report if verbose
        if self.verbose:
            self.export_detailed_report()
    
    def export_detailed_report(self):
        """Export detailed validation report to JSON."""
        report = {
            "metrics": self.metrics,
            "errors": dict(self.validation_errors),
            "warnings": dict(self.validation_warnings),
            "dependency_graph": {
                module: list(deps) 
                for module, deps in self.dependency_graph.graph.items()
            }
        }
        
        report_path = self.root_dir / "structure_validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report exported to: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate project structure for backend refactoring"
    )
    parser.add_argument(
        "--root-dir",
        default=".",
        help="Root directory of the project (default: current directory)"
    )
    parser.add_argument(
        "--max-file-lines",
        type=int,
        default=500,
        help="Maximum allowed lines per file (default: 500)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Export detailed validation report"
    )
    
    args = parser.parse_args()
    
    validator = StructureValidator(
        root_dir=args.root_dir,
        max_file_lines=args.max_file_lines,
        verbose=args.verbose
    )
    
    try:
        validator.validate()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()