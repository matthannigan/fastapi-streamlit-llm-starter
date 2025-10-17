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

  # Category 1: Assertion Errors
  echo -e "\n## 1. Assertion Errors"
  echo "These tests failed due to an unmet condition or value comparison."
  echo ""

  # Find test sections with AssertionError by looking at context around AssertionError
  # Get the nearest preceding section header (line starting with _)
  grep -B 20 "AssertionError" "$OUTPUT_FILE" | \
    grep "^_.*_$" | \
    sed 's/^_* //' | \
    sed 's/ _*$//' | \
    sort -u | \
    sed 's/^/  - /' || echo "  No assertion errors found."

  # Category 2: Expected Exception Not Raised
  echo -e "\n## 2. Expected Exception Not Raised"
  echo "These tests expected a specific error that was not thrown."
  echo ""

  grep -B 20 "DID NOT RAISE\|Did not raise" "$OUTPUT_FILE" | \
    grep "^_.*_$" | \
    sed 's/^_* //' | \
    sed 's/ _*$//' | \
    sort -u | \
    sed 's/^/  - /' || echo "  No 'DID NOT RAISE' failures found."

  # Category 3: Validation Errors (Pydantic)
  echo -e "\n## 3. Validation Errors"
  echo "These tests failed due to data validation issues (e.g., Pydantic ValidationError)."
  echo ""

  # Look for ValidationError but exclude lines that also have AssertionError
  grep -B 20 "ValidationError" "$OUTPUT_FILE" | \
    grep -v "AssertionError" | \
    grep "^_.*_$" | \
    sed 's/^_* //' | \
    sed 's/ _*$//' | \
    sort -u | \
    sed 's/^/  - /' || echo "  No validation errors found."

  # Category 4: Configuration/Infrastructure Errors
  echo -e "\n## 4. Configuration & Infrastructure Errors"
  echo "These tests failed due to ConfigurationError, InfrastructureError, or setup issues."
  echo ""

  # Look for infrastructure errors but exclude AssertionError contexts
  grep -B 20 -E "ConfigurationError|InfrastructureError|AttributeError|RuntimeError|TypeError|KeyError" "$OUTPUT_FILE" | \
    grep -v "AssertionError" | \
    grep "^_.*_$" | \
    sed 's/^_* //' | \
    sed 's/ _*$//' | \
    sort -u | \
    sed 's/^/  - /' || echo "  No configuration/infrastructure errors found."

  # Category 5: All Failed Tests (Complete List)
  echo -e "\n## 5. Complete List of Failed Tests"
  echo "All failed tests from the short test summary:"
  echo ""
  grep "^FAILED" "$OUTPUT_FILE" | sed 's/^FAILED /  - /' || echo "  No failures found."

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
