#!/usr/bin/env python3
"""
Extract test skeleton code from markdown export and save to filesystem.

This utility reads a markdown file containing test skeletons exported from
a coding assistant and extracts Python code blocks to their designated file paths.

Usage:
    python extract_test_skeletons.py <markdown_file>
    python extract_test_skeletons.py test_skeletons.md --dry-run
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def parse_markdown_for_test_files(markdown_content: str) -> List[Tuple[str, str]]:
    """
    Parse markdown content and extract file paths with their Python code.

    Args:
        markdown_content: The full markdown file content

    Returns:
        List of tuples containing (file_path, python_code)
    """
    # Pattern to match: ## File: `path/to/file.py`
    # followed by ```python code block
    file_pattern = r'^##\s+File:\s+`([^`]+\.py)`'
    code_block_pattern = r'```python\n(.*?)```'

    files = []
    lines = markdown_content.split('\n')

    current_file_path = None
    in_code_block = False
    code_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for file header
        file_match = re.match(file_pattern, line)
        if file_match:
            # Save previous file if exists
            if current_file_path and code_lines:
                code = '\n'.join(code_lines)
                files.append((current_file_path, code))
                code_lines = []

            current_file_path = file_match.group(1)
            in_code_block = False
            i += 1
            continue

        # Check for code block start
        if line.strip() == '```python':
            in_code_block = True
            code_lines = []
            i += 1
            continue

        # Check for code block end
        if line.strip() == '```' and in_code_block:
            in_code_block = False
            # Don't save yet - wait for next file header or EOF
            i += 1
            continue

        # Collect code lines
        if in_code_block:
            code_lines.append(line)

        i += 1

    # Save the last file if exists
    if current_file_path and code_lines:
        code = '\n'.join(code_lines)
        files.append((current_file_path, code))

    return files


def save_test_file(file_path: str, content: str, base_dir: Path, dry_run: bool = False) -> bool:
    """
    Save test file content to filesystem.

    Args:
        file_path: Relative path to the test file
        content: Python code content
        base_dir: Base directory to resolve relative paths from
        dry_run: If True, only print what would be done

    Returns:
        True if successful, False otherwise
    """
    # Resolve the full path
    full_path = base_dir / file_path

    if dry_run:
        print(f"[DRY RUN] Would create: {full_path}")
        print(f"[DRY RUN] Content length: {len(content)} characters")
        return True

    # Create parent directories if they don't exist
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the file
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Created: {full_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to create {full_path}: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract test skeletons from markdown export to filesystem'
    )
    parser.add_argument(
        'markdown_file',
        help='Path to the markdown file containing test skeletons'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually creating files'
    )
    parser.add_argument(
        '--base-dir',
        type=Path,
        default=None,
        help='Base directory for resolving relative paths (default: project root)'
    )

    args = parser.parse_args()

    # Determine base directory
    if args.base_dir:
        base_dir = args.base_dir
    else:
        # Default to project root (two levels up from scripts/)
        script_dir = Path(__file__).parent
        base_dir = script_dir.parent

    markdown_file = Path(args.markdown_file)

    # Validate markdown file exists
    if not markdown_file.exists():
        print(f"Error: Markdown file not found: {markdown_file}", file=sys.stderr)
        sys.exit(1)

    # Read markdown content
    print(f"Reading markdown from: {markdown_file}")
    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except Exception as e:
        print(f"Error reading markdown file: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse markdown for test files
    print("Parsing markdown for test files...")
    test_files = parse_markdown_for_test_files(markdown_content)

    if not test_files:
        print("No test files found in markdown.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(test_files)} test file(s)")

    if args.dry_run:
        print("\n=== DRY RUN MODE ===\n")

    # Save each test file
    success_count = 0
    for file_path, content in test_files:
        if save_test_file(file_path, content, base_dir, args.dry_run):
            success_count += 1

    # Summary
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary:")
    print(f"  Total files: {len(test_files)}")
    print(f"  {'Would create' if args.dry_run else 'Successfully created'}: {success_count}")

    if success_count < len(test_files):
        print(f"  Failed: {len(test_files) - success_count}")
        sys.exit(1)

    if not args.dry_run:
        print("\n✓ All test skeleton files created successfully!")


if __name__ == '__main__':
    main()
