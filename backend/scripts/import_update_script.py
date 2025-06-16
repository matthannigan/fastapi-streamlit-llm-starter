#!/usr/bin/env python3
"""
Import Update Script for Backend Refactoring

This script automatically updates import statements throughout the codebase
to reflect the new directory structure while maintaining a mapping of old
to new paths.

Usage:
    python import_update_script.py [--dry-run] [--verbose]
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict

# Import mapping from old structure to new structure
IMPORT_MAPPINGS = {
    # Core migrations
    "from app.config import": "from app.core.config import",
    "from .config import": "from .core.config import",
    "import app.config": "import app.core.config",
    
    # Infrastructure services
    "from app.services.cache import": "from app.infrastructure.cache.redis import",
    "from .services.cache import": "from ..infrastructure.cache.redis import",
    "from app.services.resilience import": "from app.infrastructure.resilience import",
    "from .services.resilience import": "from ..infrastructure.resilience import",
    "from app.services.monitoring import": "from app.infrastructure.monitoring.cache_monitor import",
    "from .services.monitoring import": "from ..infrastructure.monitoring.cache_monitor import",
    "from app.services.prompt_builder import": "from app.infrastructure.ai.prompt_builder import",
    "from .services.prompt_builder import": "from ..infrastructure.ai.prompt_builder import",
    
    # Security migrations
    "from app.auth import": "from app.infrastructure.security.auth import",
    "from .auth import": "from ..infrastructure.security.auth import",
    "from app.security.response_validator import": "from app.infrastructure.security.response_validator import",
    "from .security.response_validator import": "from ..infrastructure.security.response_validator import",
    "from app.utils.sanitization import": "from app.infrastructure.security.sanitization import",
    "from .utils.sanitization import": "from ..infrastructure.security.sanitization import",
    
    # Domain services
    "from app.services.text_processor import": "from app.services.text_processing import",
    "from .services.text_processor import": "from .services.text_processing import",
    
    # API layer
    "from app.routers.monitoring import": "from app.api.internal.monitoring import",
    "from .routers.monitoring import": "from ..api.internal.monitoring import",
    "from app.routers.resilience import": "from app.api.internal.admin import",
    "from .routers.resilience import": "from ..api.internal.admin import",
    
    # Exception handling
    "from app.validation_schemas import": "from app.core.exceptions import",
    "from .validation_schemas import": "from .core.exceptions import",
}

# File movement mapping (old path -> new path)
FILE_MOVEMENTS = {
    "app/config.py": "app/core/config.py",
    "app/services/cache.py": "app/infrastructure/cache/redis.py",
    "app/services/resilience.py": "app/infrastructure/resilience/service.py",
    "app/services/monitoring.py": "app/infrastructure/monitoring/cache_monitor.py",
    "app/config_monitoring.py": "app/infrastructure/monitoring/config_monitor.py",
    "app/services/prompt_builder.py": "app/infrastructure/ai/prompt_builder.py",
    "app/auth.py": "app/infrastructure/security/auth.py",
    "app/security/response_validator.py": "app/infrastructure/security/response_validator.py",
    "app/utils/sanitization.py": "app/infrastructure/security/sanitization.py",
    "app/services/text_processor.py": "app/services/text_processing.py",
    "app/routers/monitoring.py": "app/api/internal/monitoring.py",
    "app/routers/resilience.py": "app/api/internal/admin.py",
    "app/resilience_presets.py": "app/infrastructure/resilience/presets.py",
    "app/validation_schemas.py": "app/core/exceptions.py",
}


class ImportUpdater:
    def __init__(self, root_dir: str, dry_run: bool = False, verbose: bool = False):
        self.root_dir = Path(root_dir)
        self.dry_run = dry_run
        self.verbose = verbose
        self.updated_files = []
        self.error_files = []
        self.import_errors = defaultdict(list)
        
    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        for ext in ['*.py']:
            python_files.extend(self.root_dir.rglob(ext))
        
        # Exclude virtual environments and cache directories
        excluded_dirs = {'venv', '__pycache__', '.git', 'node_modules', '.pytest_cache'}
        python_files = [
            f for f in python_files 
            if not any(excluded in f.parts for excluded in excluded_dirs)
        ]
        
        return python_files
    
    def update_imports_in_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Update imports in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            changes = []
            
            # Apply all import mappings
            for old_import, new_import in IMPORT_MAPPINGS.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    changes.append(f"{old_import} -> {new_import}")
            
            # Update relative imports based on file location
            content = self._update_relative_imports(file_path, content, changes)
            
            # Only write if changes were made
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                return True, changes
            
            return False, []
            
        except Exception as e:
            self.error_files.append((file_path, str(e)))
            return False, []
    
    def _update_relative_imports(self, file_path: Path, content: str, changes: List[str]) -> str:
        """Update relative imports based on new file locations."""
        # Calculate relative path from backend/app
        try:
            rel_path = file_path.relative_to(self.root_dir / "backend" / "app")
            depth = len(rel_path.parts) - 1
            
            # Adjust relative imports based on new directory depth
            if "infrastructure" in rel_path.parts:
                # Files in infrastructure need different relative imports
                content = self._adjust_infrastructure_imports(content, rel_path, changes)
            elif "api" in rel_path.parts:
                # Files in API layer need different relative imports
                content = self._adjust_api_imports(content, rel_path, changes)
                
        except ValueError:
            # File is not in backend/app, skip relative import updates
            pass
            
        return content
    
    def _adjust_infrastructure_imports(self, content: str, rel_path: Path, changes: List[str]) -> str:
        """Adjust imports for files moved to infrastructure directory."""
        # Example adjustments for infrastructure files
        if "from ..services" in content:
            old = "from ..services"
            new = "from ..domain"
            content = content.replace(old, new)
            changes.append(f"{old} -> {new}")
            
        return content
    
    def _adjust_api_imports(self, content: str, rel_path: Path, changes: List[str]) -> str:
        """Adjust imports for files in API directory."""
        # Example adjustments for API files
        if "from ...services" in content:
            old = "from ...services"
            new = "from ...domain"
            content = content.replace(old, new)
            changes.append(f"{old} -> {new}")
            
        return content
    
    def validate_imports(self, file_path: Path) -> List[str]:
        """Validate that all imports in a file can be resolved."""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract all import statements
            import_pattern = re.compile(r'^\s*(?:from|import)\s+([^\s]+)', re.MULTILINE)
            imports = import_pattern.findall(content)
            
            for imp in imports:
                # Skip built-in and third-party imports
                if imp.startswith('.') or imp.startswith('app'):
                    # Validate local imports
                    if not self._can_resolve_import(file_path, imp):
                        errors.append(f"Cannot resolve import: {imp}")
                        
        except Exception as e:
            errors.append(f"Error validating file: {str(e)}")
            
        return errors
    
    def _can_resolve_import(self, file_path: Path, import_str: str) -> bool:
        """Check if an import can be resolved."""
        # Simple validation - check if the imported module exists
        # This is a basic check and might need enhancement
        if import_str.startswith('app.'):
            module_path = import_str.replace('.', '/') + '.py'
            full_path = self.root_dir / "backend" / module_path
            return full_path.exists() or full_path.with_suffix('').is_dir()
        
        # For relative imports, this would need more complex resolution
        return True
    
    def run(self):
        """Run the import update process."""
        print(f"Scanning for Python files in {self.root_dir}")
        python_files = self.find_python_files()
        print(f"Found {len(python_files)} Python files")
        
        if self.dry_run:
            print("\n=== DRY RUN MODE - No files will be modified ===\n")
        
        for file_path in python_files:
            updated, changes = self.update_imports_in_file(file_path)
            
            if updated:
                self.updated_files.append((file_path, changes))
                if self.verbose:
                    print(f"\n{file_path}:")
                    for change in changes:
                        print(f"  {change}")
            
            # Validate imports after update
            if not self.dry_run:
                errors = self.validate_imports(file_path)
                if errors:
                    self.import_errors[file_path] = errors
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print summary of changes."""
        print("\n" + "="*60)
        print("IMPORT UPDATE SUMMARY")
        print("="*60)
        
        print(f"\nFiles updated: {len(self.updated_files)}")
        if self.updated_files and not self.verbose:
            print("\nUpdated files:")
            for file_path, changes in self.updated_files[:10]:
                print(f"  - {file_path} ({len(changes)} changes)")
            if len(self.updated_files) > 10:
                print(f"  ... and {len(self.updated_files) - 10} more files")
        
        if self.error_files:
            print(f"\nFiles with errors: {len(self.error_files)}")
            for file_path, error in self.error_files:
                print(f"  - {file_path}: {error}")
        
        if self.import_errors:
            print(f"\nFiles with unresolved imports: {len(self.import_errors)}")
            for file_path, errors in list(self.import_errors.items())[:5]:
                print(f"  - {file_path}:")
                for error in errors[:3]:
                    print(f"    {error}")
        
        if self.dry_run:
            print("\n*** This was a dry run. No files were modified. ***")
            print("*** Run without --dry-run to apply changes. ***")


def main():
    parser = argparse.ArgumentParser(
        description="Update imports for backend refactoring"
    )
    parser.add_argument(
        "--root-dir",
        default=".",
        help="Root directory of the project (default: current directory)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information about changes"
    )
    
    args = parser.parse_args()
    
    updater = ImportUpdater(
        root_dir=args.root_dir,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    try:
        updater.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()