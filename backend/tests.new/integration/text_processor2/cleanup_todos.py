#!/usr/bin/env python3
"""
Quick cleanup of TODO(integration) lines in migrated test files.

This script:
1. Deletes FakeCache metric assertions (get_hit_count, get_miss_count, etc.)
2. Replaces ._data.keys() with get_all_keys()
3. Creates a backup before modifying

Usage:
    python cleanup_todos.py [--dry-run] [--file FILE]
"""

import argparse
import re
from pathlib import Path
from typing import Tuple


def cleanup_todos(file_path: Path, dry_run: bool = False) -> Tuple[int, int]:
    """
    Clean up TODO(integration) comments.

    Args:
        file_path: Path to file to clean
        dry_run: If True, show changes without modifying file

    Returns:
        Tuple of (lines_deleted, lines_replaced)
    """
    content = file_path.read_text()
    original_content = content
    lines_deleted = 0
    lines_replaced = 0

    print(f"\n{'=' * 80}")
    print(f"Processing: {file_path.name}")
    print(f"{'=' * 80}\n")

    # Pattern 1: DELETE get_hit_count() lines
    pattern = r'\s*# TODO\(integration\):.*get_hit_count.*\n'
    matches = len(re.findall(pattern, content))
    if matches:
        print(f"✓ Deleting {matches} get_hit_count() lines")
        content = re.sub(pattern, '', content)
        lines_deleted += matches

    # Pattern 2: DELETE get_miss_count() lines
    pattern = r'\s*# TODO\(integration\):.*get_miss_count.*\n'
    matches = len(re.findall(pattern, content))
    if matches:
        print(f"✓ Deleting {matches} get_miss_count() lines")
        content = re.sub(pattern, '', content)
        lines_deleted += matches

    # Pattern 3: DELETE len(._data) lines
    pattern = r'\s*# TODO\(integration\):.*len\(ai_response_cache\._data\).*\n'
    matches = len(re.findall(pattern, content))
    if matches:
        print(f"✓ Deleting {matches} len(._data) lines")
        content = re.sub(pattern, '', content)
        lines_deleted += matches

    # Pattern 4: DELETE get_stored_ttl() lines
    pattern = r'\s*# TODO\(integration\):.*get_stored_ttl.*\n'
    matches = len(re.findall(pattern, content))
    if matches:
        print(f"✓ Deleting {matches} get_stored_ttl() lines")
        content = re.sub(pattern, '', content)
        lines_deleted += matches

    # Pattern 5: REPLACE ._data.keys() with get_all_keys()
    # Find all commented lines with ._data.keys()
    pattern = r'(\s*)# TODO\(integration\):.*- (.* = )list\(ai_response_cache\._data\.keys\(\)\)'

    def replace_keys(match):
        indent = match.group(1)
        assignment = match.group(2)
        return f'{indent}{assignment}await ai_response_cache.get_all_keys()'

    matches = len(re.findall(pattern, content))
    if matches:
        print(f"✓ Replacing {matches} ._data.keys() → get_all_keys()")
        content = re.sub(pattern, replace_keys, content)
        lines_replaced += matches

    # Show summary
    print(f"\n📊 Summary:")
    print(f"   Lines deleted: {lines_deleted}")
    print(f"   Lines replaced: {lines_replaced}")
    print(f"   Total changes: {lines_deleted + lines_replaced}")

    # Apply changes or show diff
    if content != original_content:
        if dry_run:
            print(f"\n{'=' * 80}")
            print("DRY RUN - Changes that would be made:")
            print(f"{'=' * 80}\n")
            _show_changes(original_content, content)
        else:
            # Create backup
            backup_path = file_path.with_suffix(file_path.suffix + '.before_cleanup')
            backup_path.write_text(original_content)
            print(f"\n💾 Backup created: {backup_path.name}")

            # Write cleaned content
            file_path.write_text(content)
            print(f"✅ File cleaned successfully!")

            # Check for remaining TODOs
            remaining = content.count('TODO(integration)')
            if remaining > 0:
                print(f"\n⚠️  {remaining} TODO(integration) lines remain - may need manual review")
    else:
        print(f"\nℹ️  No TODO(integration) lines found - file already clean")

    return lines_deleted, lines_replaced


def _show_changes(original: str, modified: str) -> None:
    """Show lines that changed."""
    original_lines = original.split('\n')
    modified_lines = modified.split('\n')

    changes_shown = 0
    max_changes_to_show = 20

    for i, (orig, mod) in enumerate(zip(original_lines, modified_lines), 1):
        if orig != mod and 'TODO(integration)' in orig:
            if changes_shown < max_changes_to_show:
                print(f"Line {i}:")
                if mod.strip():  # Replacement
                    print(f"  - {orig}")
                    print(f"  + {mod}")
                else:  # Deletion
                    print(f"  - {orig}")
                    print(f"  + (deleted)")
                print()
                changes_shown += 1

    if changes_shown >= max_changes_to_show:
        print(f"... ({changes_shown - max_changes_to_show} more changes not shown)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Clean up TODO(integration) comments in migrated tests"
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

    # Run cleanup
    lines_deleted, lines_replaced = cleanup_todos(file_path, dry_run=args.dry_run)

    # Final summary
    print(f"\n{'=' * 80}")
    if args.dry_run:
        print("DRY RUN COMPLETE - No files were modified")
        print("Run without --dry-run to apply changes")
    else:
        print("CLEANUP COMPLETE")
        print("\n✅ Next Steps:")
        print("   1. Review the changes")
        print("   2. Run tests: pytest tests/integration/text_processor/ -v")
        print("   3. If tests pass, delete backup file")
        print("   4. Update test docstrings with 'Integration Scope' sections")
    print(f"{'=' * 80}\n")

    return 0


if __name__ == '__main__':
    exit(main())
