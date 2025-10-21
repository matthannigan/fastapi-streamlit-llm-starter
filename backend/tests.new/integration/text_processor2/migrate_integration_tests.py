#!/usr/bin/env python3
"""
Batch migration script for text_processor integration tests.

Automates the migration from unit test patterns to integration test patterns:
- Replaces fixture parameters (fake_cache → ai_response_cache)
- Updates cache usage patterns
- Updates helper function signatures
- Adds integration test markers

Usage:
    python migrate_integration_tests.py [--dry-run] [--file FILE]

    --dry-run: Show changes without modifying files
    --file FILE: Process specific file (default: text_processor_cache_integration.py)
"""

import argparse
import re
from pathlib import Path
from typing import List, Tuple


class IntegrationTestMigrator:
    """Migrates unit test patterns to integration test patterns."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.changes_made: List[Tuple[int, str, str]] = []

    def migrate_file(self, file_path: Path) -> None:
        """Migrate a single test file."""
        print(f"\n{'=' * 80}")
        print(f"Processing: {file_path}")
        print(f"{'=' * 80}\n")

        # Read file
        content = file_path.read_text()
        original_content = content

        # Apply migrations
        content = self._migrate_imports(content)
        content = self._migrate_fixture_parameters(content)
        content = self._migrate_cache_usage(content)
        content = self._migrate_helper_functions(content)
        content = self._remove_fake_cache_metrics(content)
        content = self._update_module_docstring(content)

        # Show changes
        if content != original_content:
            if self.dry_run:
                print(f"\n{'=' * 80}")
                print(f"DRY RUN - Changes that would be made:")
                print(f"{'=' * 80}\n")
                self._show_diff(original_content, content)
            else:
                file_path.write_text(content)
                print(f"\n✅ File updated successfully!")

            print(f"\n📊 Changes Summary:")
            print(f"   - {len(self.changes_made)} total changes")
        else:
            print("\nℹ️  No changes needed.")

        # Print change details
        if self.changes_made:
            print(f"\n📝 Detailed Changes:")
            for line_num, old, new in self.changes_made:
                print(f"   Line {line_num}:")
                print(f"      - {old}")
                print(f"      + {new}")

    def _migrate_imports(self, content: str) -> str:
        """Add integration test imports."""
        # Check if we need to add imports
        if "from app.infrastructure.cache.redis_ai import AIResponseCache" not in content:
            # Find first import or after module docstring
            import_pattern = r'("""[\s\S]*?"""\n\n|\'\'\'[\s\S]*?\'\'\'\n\n)'
            match = re.search(import_pattern, content)

            if match:
                insert_pos = match.end()
                new_imports = (
                    "# Integration test imports\n"
                    "from app.infrastructure.cache.redis_ai import AIResponseCache\n\n"
                )
                content = content[:insert_pos] + new_imports + content[insert_pos:]
                self.changes_made.append((1, "No integration imports", "Added AIResponseCache import"))

        return content

    def _migrate_fixture_parameters(self, content: str) -> str:
        """Replace unit test fixtures with integration fixtures in parameters."""
        replacements = [
            # fake_cache → ai_response_cache
            (
                r'\bfake_cache\b(?!_with_hit)',
                'ai_response_cache',
                'fake_cache → ai_response_cache'
            ),
            # fake_cache_with_hit → ai_response_cache_with_data
            (
                r'\bfake_cache_with_hit\b',
                'ai_response_cache_with_data',
                'fake_cache_with_hit → ai_response_cache_with_data'
            ),
        ]

        for pattern, replacement, description in replacements:
            matches = list(re.finditer(pattern, content))
            if matches:
                # Count replacements by line
                lines = content.split('\n')
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    old_text = lines[line_num - 1].strip()[:50]
                    self.changes_made.append((line_num, description, old_text))

                content = re.sub(pattern, replacement, content)

        return content

    def _migrate_cache_usage(self, content: str) -> str:
        """Update cache variable usage in test bodies."""
        # Replace fake_cache variable references
        lines = content.split('\n')
        new_lines = []

        for i, line in enumerate(lines, 1):
            original_line = line

            # Replace fake_cache when used as variable (not in params)
            if 'def ' not in line and 'import' not in line:
                # Replace standalone fake_cache references
                line = re.sub(r'\bfake_cache\b(?!_with_hit)', 'ai_response_cache', line)

                # Replace fake_cache_with_hit references
                line = re.sub(r'\bfake_cache_with_hit\b', 'ai_response_cache_with_data', line)

            if line != original_line:
                self.changes_made.append((i, "Variable reference", original_line.strip()[:50]))

            new_lines.append(line)

        return '\n'.join(new_lines)

    def _migrate_helper_functions(self, content: str) -> str:
        """Update helper function signatures and calls."""
        # Update _create_text_processor_with_mock_agent signature
        old_sig = r'def _create_text_processor_with_mock_agent\(test_settings, cache_service, mock_pydantic_agent\)'
        new_sig = 'def _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent)'

        if re.search(old_sig, content):
            content = re.sub(old_sig, new_sig, content)
            self.changes_made.append((0, "Helper function signature", "cache_service → ai_response_cache"))

        # Update docstring in helper function
        content = re.sub(
            r'cache_service',
            'ai_response_cache',
            content,
            flags=re.MULTILINE
        )

        return content

    def _remove_fake_cache_metrics(self, content: str) -> str:
        """Comment out FakeCache-specific metric assertions."""
        lines = content.split('\n')
        new_lines = []

        metrics_patterns = [
            r'\.get_hit_count\(\)',
            r'\.get_miss_count\(\)',
            r'\.get_stored_ttl\(',
            r'\._data\b',
            r'\._ttls\b',
        ]

        for i, line in enumerate(lines, 1):
            original_line = line

            # Check if line contains fake cache metrics
            for pattern in metrics_patterns:
                if re.search(pattern, line) and not line.strip().startswith('#'):
                    # Comment out the line
                    indent = len(line) - len(line.lstrip())
                    line = ' ' * indent + '# TODO(integration): Remove FakeCache metric - ' + line.strip()
                    self.changes_made.append((i, "Commented FakeCache metric", original_line.strip()[:50]))
                    break

            new_lines.append(line)

        return '\n'.join(new_lines)

    def _update_module_docstring(self, content: str) -> str:
        """Update module docstring to reflect integration testing."""
        # Update first docstring
        old_pattern = r'"""[\s\S]*?Test skeletons for TextProcessorService caching behavior\.'
        new_text = '"""Integration tests for TextProcessorService + AIResponseCache collaboration.'

        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_text, content, count=1)
            self.changes_made.append((1, "Module docstring", "Updated to integration test"))

        # Update "Test Strategy" to "Integration Strategy"
        content = re.sub(r'\bTest Strategy:', 'Integration Strategy:', content)

        return content

    def _show_diff(self, original: str, modified: str) -> None:
        """Show a simple diff between original and modified content."""
        original_lines = original.split('\n')
        modified_lines = modified.split('\n')

        print("\nShowing first 50 changed lines...\n")

        changes_shown = 0
        for i, (orig, mod) in enumerate(zip(original_lines, modified_lines), 1):
            if orig != mod and changes_shown < 50:
                print(f"Line {i}:")
                print(f"  - {orig}")
                print(f"  + {mod}")
                print()
                changes_shown += 1

        if changes_shown == 50:
            print("... (more changes not shown)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate text_processor unit tests to integration tests"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show changes without modifying files'
    )
    parser.add_argument(
        '--file',
        type=str,
        default='text_processor_cache_integration.py',
        help='File to process (default: text_processor_cache_integration.py)'
    )

    args = parser.parse_args()

    # Get file path
    script_dir = Path(__file__).parent
    file_path = script_dir / args.file

    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        return 1

    # Run migration
    migrator = IntegrationTestMigrator(dry_run=args.dry_run)
    migrator.migrate_file(file_path)

    # Summary
    print(f"\n{'=' * 80}")
    if args.dry_run:
        print("DRY RUN COMPLETE - No files were modified")
        print("Run without --dry-run to apply changes")
    else:
        print("MIGRATION COMPLETE")
        print("\n⚠️  MANUAL REVIEW REQUIRED:")
        print("   1. Review commented lines marked with 'TODO(integration)'")
        print("   2. Update test docstrings with 'Integration Scope' sections")
        print("   3. Remove FakeCache metric assertions")
        print("   4. Add new fixtures to conftest.py if not already present")
        print("   5. Run tests: pytest tests/integration/text_processor/ -v")
    print(f"{'=' * 80}\n")

    return 0


if __name__ == '__main__':
    exit(main())
