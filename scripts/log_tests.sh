# Run backend core functionality tests with sorted summary
echo "🧪 Running backend core functionality tests..."
cd backend && $(PYTHON_CMD) -m pytest tests/core/ --tb=no --quiet > ../dev/taskplans/current/enhanced-middleware_testing.log || true

# Extract everything before the test summary
sed '/short test summary info/,$$d' dev/taskplans/current/enhanced-middleware_testing.log > dev/taskplans/current/temp_log.txt

# Add the sorted test summary header
echo "" >> dev/taskplans/current/temp_log.txt
echo "================= short test summary info ==================" >> dev/taskplans/current/temp_log.txt

# Add the sorted test results
sed -n '/short test summary info/,/failed.*passed.*warnings/p' dev/taskplans/current/enhanced-middleware_testing.log | grep -E '^(FAILED|ERROR|SKIPPED)' | sort >> dev/taskplans/current/temp_log.txt

# Add the final summary totals line
sed -n '/failed.*passed.*warnings/p' dev/taskplans/current/enhanced-middleware_testing.log >> dev/taskplans/current/temp_log.txt

# Replace the original file with the processed version
mv dev/taskplans/current/temp_log.txt dev/taskplans/current/enhanced-middleware_testing.log
cd backend && $(PYTHON_CMD) -m pytest tests/core/ --tb=no --quiet || true
echo "Generated log with sorted test summary at dev/taskplans/current/enhanced-middleware_testing.log"