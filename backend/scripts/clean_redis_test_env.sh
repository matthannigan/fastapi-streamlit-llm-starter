#!/bin/bash

# Redis Test Environment Cleanup Script
# This script helps clean up stale Redis processes and temporary files
# that may cause test failures due to port conflicts or stale data.

echo "🧹 Redis Test Environment Cleanup"
echo "================================="

# Check for running Redis processes started by pytest
echo "Checking for pytest-redis processes..."
REDIS_PROCS=$(pgrep -f "redis-server.*pytest" | wc -l | tr -d ' ')

if [ "$REDIS_PROCS" -gt 0 ]; then
    echo "Found $REDIS_PROCS pytest-redis process(es)"
    echo "Stopping pytest-redis processes..."
    pkill -f "redis-server.*pytest"
    sleep 1
    
    # Force kill if still running
    if pgrep -f "redis-server.*pytest" > /dev/null; then
        echo "Force stopping stubborn processes..."
        pkill -9 -f "redis-server.*pytest"
    fi
    echo "✓ Redis processes stopped"
else
    echo "✓ No pytest-redis processes found"
fi

# Clean up pytest temporary directories
echo ""
echo "Cleaning pytest temporary directories..."
PYTEST_DIRS=("/private/tmp/pytest" "/tmp/pytest" "$HOME/.pytest_cache/redis")

for dir in "${PYTEST_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  Removing $dir..."
        rm -rf "$dir"
    fi
done
echo "✓ Temporary directories cleaned"

# Check for any remaining Redis servers on common test ports
# echo ""
# echo "Checking for Redis servers on common test ports..."
# TEST_PORTS=(6379 6380 $(seq 33000 33100) $(seq 22000 22300) $(seq 29000 29400))

# FOUND_PORTS=()
# for port in "${TEST_PORTS[@]}"; do
#     if lsof -i :$port 2>/dev/null | grep -q redis; then
#         FOUND_PORTS+=($port)
#     fi
# done

# if [ ${#FOUND_PORTS[@]} -gt 0 ]; then
#     echo "⚠️  Found Redis on ports: ${FOUND_PORTS[*]}"
#     echo "   These may be legitimate Redis instances."
#     echo "   To stop a specific instance: redis-cli -p PORT shutdown"
# else
#     echo "✓ No Redis servers found on test ports"
# fi

# echo ""
# echo "✅ Cleanup complete!"
# echo ""
# echo "Tips for running Redis tests:"
# echo "  • Run tests without parallelization: pytest -n 0"
# echo "  • Run specific test: pytest path/to/test.py::TestClass::test_method"
# echo "  • Check Redis connectivity: redis-cli ping"
# echo ""
