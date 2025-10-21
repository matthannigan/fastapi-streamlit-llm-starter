#!/bin/bash

# A script to run pytest on a specified directory, capture the output,
# and categorize the failures into predefined groups.
#
# Usage:
#   ./run_and_group_tests.sh [path_to_test_directory]
#
# Examples:
#   ./run_and_group_tests.sh ./unit/llm_security/
#   ./run_and_group_tests.sh ./unit/resilience/
#   KEEP_RAW_OUTPUT=1 ./run_and_group_tests.sh ./unit/
#
# Environment Variables:
#   KEEP_RAW_OUTPUT - Set to 1 to preserve the raw pytest output file for debugging

# --- Configuration ---
TARGET_DIR=${1:-"./unit/"} # Default to ./unit/ if no directory is provided
OUTPUT_FILE="./pytest_failures.log"
REPORT_FILE="./categorized_test_report.txt"

# --- Main Logic ---

# 1. Check if the target directory exists
if [ ! -d "$TARGET_DIR" ]; then
  echo "Error: Directory '$TARGET_DIR' not found."
  exit 1
fi

echo "Running pytest on '$TARGET_DIR' and capturing failures..."

# 2. Run pytest and save the output to a log file.
# The `-v` flag provides verbose output with test names.
# The `--tb=short` flag provides concise tracebacks with error types.
# `|| true` ensures the script doesn't exit immediately if tests fail.
../.venv/bin/python -m pytest -v --tb=short "$TARGET_DIR" > "$OUTPUT_FILE" 2>&1 || true

# 3. Check if any tests failed by looking for FAILED in the output.
if ! grep -q "^FAILED" "$OUTPUT_FILE"; then
  echo "Success! No test failures were found in '$TARGET_DIR'."
  rm "$OUTPUT_FILE"
  exit 0
fi

echo "Pytest run complete. Analyzing failures..."

# 4. Initialize the report file
# This clears any previous report content
> "$REPORT_FILE"

# 5. Extract and categorize failures
# Extract the short test summary section and analyze each failure's traceback

{
  echo "# Categorized Pytest Failure Report"
  echo "Generated on: $(date)"
  echo "Test Directory: $TARGET_DIR"
  echo "---"

  # Extract all FAILED test lines from short test summary
  echo -e "\n## Summary"
  TOTAL_FAILURES=$(grep "^FAILED" "$OUTPUT_FILE" | wc -l | tr -d ' ')
  echo "Total Failures: $TOTAL_FAILURES"
  echo "---"

  # Create a mapping of test names to full paths for grouping
  TEMP_TEST_MAP=$(mktemp)
  grep "^FAILED" "$OUTPUT_FILE" | ../.venv/bin/python -c '
import sys
import os

for line in sys.stdin:
    line = line.strip()
    if line.startswith("FAILED "):
        # Format: FAILED path/to/file.py::TestClass::test_method
        full_path = line.replace("FAILED ", "")
        parts = full_path.split("::")
        if len(parts) >= 3:
            filepath = parts[0]
            filename = os.path.basename(filepath)
            test_class = parts[1]
            test_method = parts[2]
            # Output: TestClass.test_method|filename|full_path
            print(f"{test_class}.{test_method}|{filename}|{full_path}")
' > "$TEMP_TEST_MAP"

  # Category 1: Assertion Errors
  echo -e "\n## 1. Assertion Errors"
  echo "These tests failed due to an unmet condition or value comparison."
  echo ""

  # Find test sections with AssertionError and group by filename
  TEMP_TESTS=$(mktemp)
  grep -B 20 "AssertionError" "$OUTPUT_FILE" | \
    grep "^_.*_$" | \
    sed 's/^_* //' | \
    sed 's/ _*$//' | \
    sort -u > "$TEMP_TESTS"

  if [ -s "$TEMP_TESTS" ]; then
    ../.venv/bin/python -c '
import sys
from collections import defaultdict

# Read test name to file mapping
test_map_file = sys.argv[1]
test_to_file = {}
with open(test_map_file, "r") as f:
    for line in f:
        parts = line.strip().split("|")
        if len(parts) == 3:
            test_name, filename, full_path = parts
            test_to_file[test_name] = (filename, full_path)

# Read tests in this category
tests_file = sys.argv[2]
tests_by_file = defaultdict(list)

with open(tests_file, "r") as f:
    for line in f:
        test_name = line.strip()
        if test_name in test_to_file:
            filename, full_path = test_to_file[test_name]
            tests_by_file[filename].append((test_name, full_path))

# Output grouped by filename
if tests_by_file:
    for filename in sorted(tests_by_file.keys()):
        print(f"**{filename}:**")
        for test_name, full_path in sorted(tests_by_file[filename]):
            print(f"  - {test_name}")
        print()
else:
    print("  No matches found.")
' "$TEMP_TEST_MAP" "$TEMP_TESTS"
  else
    echo "  No assertion errors found."
  fi
  rm -f "$TEMP_TESTS"

  # Helper function (embedded Python) for grouping tests by filename
  GROUP_BY_FILE='
import sys
from collections import defaultdict

# Read test name to file mapping
test_map_file = sys.argv[1]
test_to_file = {}
with open(test_map_file, "r") as f:
    for line in f:
        parts = line.strip().split("|")
        if len(parts) == 3:
            test_name, filename, full_path = parts
            test_to_file[test_name] = (filename, full_path)

# Read tests in this category
tests_file = sys.argv[2]
tests_by_file = defaultdict(list)

with open(tests_file, "r") as f:
    for line in f:
        test_name = line.strip()
        if test_name in test_to_file:
            filename, full_path = test_to_file[test_name]
            tests_by_file[filename].append((test_name, full_path))

# Output grouped by filename
if tests_by_file:
    for filename in sorted(tests_by_file.keys()):
        print(f"**{filename}:**")
        for test_name, full_path in sorted(tests_by_file[filename]):
            print(f"  - {test_name}")
        print()
'

  # Category 2: Expected Exception Not Raised
  echo -e "\n## 2. Expected Exception Not Raised"
  echo "These tests expected a specific error that was not thrown."
  echo ""

  TEMP_TESTS=$(mktemp)
  grep -B 20 "DID NOT RAISE\|Did not raise" "$OUTPUT_FILE" | \
    grep "^_.*_$" | \
    sed 's/^_* //' | \
    sed 's/ _*$//' | \
    sort -u > "$TEMP_TESTS"

  if [ -s "$TEMP_TESTS" ]; then
    ../.venv/bin/python -c "$GROUP_BY_FILE" "$TEMP_TEST_MAP" "$TEMP_TESTS"
  else
    echo "  No 'DID NOT RAISE' failures found."
  fi
  rm -f "$TEMP_TESTS"

  # Category 3: Validation Errors (Pydantic)
  echo -e "\n## 3. Validation Errors"
  echo "These tests failed due to data validation issues (e.g., Pydantic ValidationError)."
  echo ""

  TEMP_TESTS=$(mktemp)
  grep -B 20 "ValidationError" "$OUTPUT_FILE" | \
    grep -v "AssertionError" | \
    grep "^_.*_$" | \
    sed 's/^_* //' | \
    sed 's/ _*$//' | \
    sort -u > "$TEMP_TESTS"

  if [ -s "$TEMP_TESTS" ]; then
    ../.venv/bin/python -c "$GROUP_BY_FILE" "$TEMP_TEST_MAP" "$TEMP_TESTS"
  else
    echo "  No validation errors found."
  fi
  rm -f "$TEMP_TESTS"

  # Category 4: Configuration/Infrastructure Errors
  echo -e "\n## 4. Configuration & Infrastructure Errors"
  echo "These tests failed due to ConfigurationError, InfrastructureError, or setup issues."
  echo ""

  TEMP_TESTS=$(mktemp)
  grep -B 20 -E "ConfigurationError|InfrastructureError|RuntimeError|TypeError|KeyError" "$OUTPUT_FILE" | \
    grep -v "AssertionError" | \
    grep -v "NameError" | \
    grep -v "AttributeError" | \
    grep "^_.*_$" | \
    sed 's/^_* //' | \
    sed 's/ _*$//' | \
    sort -u > "$TEMP_TESTS"

  if [ -s "$TEMP_TESTS" ]; then
    ../.venv/bin/python -c "$GROUP_BY_FILE" "$TEMP_TEST_MAP" "$TEMP_TESTS"
  else
    echo "  No configuration/infrastructure errors found."
  fi
  rm -f "$TEMP_TESTS"

  # Category 5: NameError
  echo -e "\n## 5. NameError"
  echo "These tests failed due to undefined names or missing imports."
  echo ""

  TEMP_TESTS=$(mktemp)
  grep -B 20 "NameError" "$OUTPUT_FILE" | \
    grep -v "AssertionError" | \
    grep "^_.*_$" | \
    sed 's/^_* //' | \
    sed 's/ _*$//' | \
    sort -u > "$TEMP_TESTS"

  if [ -s "$TEMP_TESTS" ]; then
    ../.venv/bin/python -c "$GROUP_BY_FILE" "$TEMP_TEST_MAP" "$TEMP_TESTS"
  else
    echo "  No NameError failures found."
  fi
  rm -f "$TEMP_TESTS"

  # Category 6: AttributeError
  echo -e "\n## 6. AttributeError"
  echo "These tests failed due to missing attributes or incorrect object references."
  echo ""

  TEMP_TESTS=$(mktemp)
  grep -B 20 "AttributeError" "$OUTPUT_FILE" | \
    grep -v "AssertionError" | \
    grep "^_.*_$" | \
    sed 's/^_* //' | \
    sed 's/ _*$//' | \
    sort -u > "$TEMP_TESTS"

  if [ -s "$TEMP_TESTS" ]; then
    ../.venv/bin/python -c "$GROUP_BY_FILE" "$TEMP_TEST_MAP" "$TEMP_TESTS"
  else
    echo "  No AttributeError failures found."
  fi
  rm -f "$TEMP_TESTS"

  # Category 7: Common Error Patterns
  echo -e "\n## 7. Common Error Patterns"
  echo "Errors that appear in 2 or more tests (indicating systematic issues):"
  echo ""

  # Create temporary files for processing
  TEMP_ERROR_MAP=$(mktemp)
  TEMP_ERROR_SORTED=$(mktemp)
  TEMP_ERROR_GROUPS=$(mktemp)

  # Extract error messages for each test
  # Strategy: Find all "E   " lines and associate them with their preceding test name

  # Use Python with file argument (TAB-delimited output)
  ../.venv/bin/python -c '
import sys
import re

filepath = sys.argv[1]
current_test = None
current_error = []

with open(filepath, "r") as f:
    for line in f:
        # Detect test section header (line with underscores surrounding text)
        if re.match(r"^_+ .+ _+$", line):
            # Save previous test if we have one
            if current_test and current_error:
                error_msg = " ".join(current_error)
                print(f"{current_test}\t{error_msg}")

            # Extract test name (remove underscores and whitespace)
            test_name = line.strip("_").strip()
            current_test = test_name
            current_error = []

        # Detect error lines
        elif line.startswith("E   "):
            error_text = line[4:].strip()
            current_error.append(error_text)

        # End of test section
        elif re.match(r"^=+ ", line) and current_test:
            if current_error:
                error_msg = " ".join(current_error)
                print(f"{current_test}\t{error_msg}")
            current_test = None
            current_error = []

# Handle last test if needed
if current_test and current_error:
    error_msg = " ".join(current_error)
    print(f"{current_test}\t{error_msg}")
' "$OUTPUT_FILE" > "$TEMP_ERROR_MAP"

  # Group errors and count occurrences
  if [ -s "$TEMP_ERROR_MAP" ]; then
    # Just copy to sorted file (we'll group in Python)
    cp "$TEMP_ERROR_MAP" "$TEMP_ERROR_SORTED"

    # Use Python to group, count, AND format output with filename grouping
    ../.venv/bin/python -c '
import sys
from collections import defaultdict

# Read error map
error_map_file = sys.argv[1]
error_to_tests = defaultdict(list)

with open(error_map_file, "r") as f:
    for line in f:
        line = line.strip()
        if "\t" in line:
            test, error = line.split("\t", 1)
            # Strip trailing underscores and spaces from test names
            test = test.rstrip("_ ")
            error_to_tests[error].append(test)

# Read test name to filename mapping
test_map_file = sys.argv[2]
test_to_file = {}
with open(test_map_file, "r") as f:
    for line in f:
        parts = line.strip().split("|")
        if len(parts) == 3:
            test_name, filename, full_path = parts
            test_to_file[test_name] = (filename, full_path)

# Output errors that appear 2+ times with filename grouping
has_output = False
for error, tests in sorted(error_to_tests.items(), key=lambda x: len(x[1]), reverse=True):
    if len(tests) >= 2:
        has_output = True
        count = len(tests)
        print(f"### Error appearing in {count} tests:")
        print("```")
        print(error)
        print("```")
        print()
        print("**Affected tests:**")

        # Group tests by filename
        tests_by_file = defaultdict(list)
        for test in tests:
            if test in test_to_file:
                filename, full_path = test_to_file[test]
                tests_by_file[filename].append(test)

        # Output grouped by filename
        for filename in sorted(tests_by_file.keys()):
            print(f"**{filename}:**")
            for test in sorted(tests_by_file[filename]):
                print(f"  - {test}")
            print()

if not has_output:
    print("  No common error patterns found (all errors are unique).")
' "$TEMP_ERROR_SORTED" "$TEMP_TEST_MAP"
  else
    echo "  No common error patterns found (all errors are unique)."
  fi

  # Cleanup temp files
  rm -f "$TEMP_ERROR_MAP" "$TEMP_ERROR_SORTED" "$TEMP_ERROR_GROUPS"

  # Category 8: All Failed Tests (Complete List) - Grouped by filename
  echo -e "\n## 8. Complete List of Failed Tests"
  echo "All failed tests grouped by filename:"
  echo ""

  # Get all test names from the map and group by filename
  TEMP_ALL_TESTS=$(mktemp)
  cut -d'|' -f1 "$TEMP_TEST_MAP" > "$TEMP_ALL_TESTS"

  if [ -s "$TEMP_ALL_TESTS" ]; then
    ../.venv/bin/python -c "$GROUP_BY_FILE" "$TEMP_TEST_MAP" "$TEMP_ALL_TESTS"
  else
    echo "  No failures found."
  fi
  rm -f "$TEMP_ALL_TESTS"

  # Cleanup test map
  rm -f "$TEMP_TEST_MAP"

} >> "$REPORT_FILE"

# --- Cleanup ---
# Keep the raw output file for debugging if KEEP_RAW_OUTPUT is set
if [ -z "$KEEP_RAW_OUTPUT" ]; then
  rm "$OUTPUT_FILE"
else
  echo "Raw pytest output saved to '$OUTPUT_FILE' for debugging."
fi

echo ""
echo "=========================================="
echo "Analysis complete. Report saved to '$REPORT_FILE'."
echo "=========================================="
echo ""
cat "$REPORT_FILE"
echo ""
echo "=========================================="
echo "To keep the raw pytest output, run with:"
echo "  KEEP_RAW_OUTPUT=1 $0 $TARGET_DIR"
echo "=========================================="
