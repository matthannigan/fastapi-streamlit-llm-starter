#!/bin/bash
# Backend test runner with parallel execution options
set -e

# Default values
MODE="parallel"
COVERAGE=false
VERBOSE=false
TARGET=""
WORKERS="auto"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo -e "${BLUE}Backend Test Runner${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS] [TARGET]"
    echo ""
    echo "OPTIONS:"
    echo "  -m, --mode MODE      Test execution mode: parallel, sequential, debug (default: parallel)"
    echo "  -c, --coverage       Include coverage report"
    echo "  -v, --verbose        Verbose output"
    echo "  -w, --workers NUM    Number of workers for parallel execution (default: auto)"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "TARGET:"
    echo "  Specific test file or test pattern (e.g., tests/test_specific.py or tests/test_specific.py::TestClass::test_method)"
    echo ""
    echo "MODES:"
    echo "  parallel    - Run tests in parallel with optimal worker distribution (default)"
    echo "  sequential  - Run tests sequentially (useful for debugging)"
    echo "  debug      - Run with detailed output and no parallel execution"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                                    # Run all tests in parallel"
    echo "  $0 -c                                # Run all tests with coverage"
    echo "  $0 -m debug tests/test_specific.py   # Debug specific test file"
    echo "  $0 -w 4 -c                          # Use 4 workers with coverage"
    echo "  $0 -m sequential --verbose           # Sequential execution with verbose output"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

# Validate mode
case $MODE in
    parallel|sequential|debug)
        ;;
    *)
        echo -e "${RED}Invalid mode: $MODE${NC}"
        echo "Valid modes: parallel, sequential, debug"
        exit 1
        ;;
esac

# Build pytest command
PYTEST_CMD="python -m pytest"

# Add target if specified
if [ -n "$TARGET" ]; then
    PYTEST_CMD="$PYTEST_CMD $TARGET"
fi

# Configure based on mode
case $MODE in
    parallel)
        echo -e "${GREEN}Running tests in parallel mode with $WORKERS workers${NC}"
        PYTEST_CMD="$PYTEST_CMD -n $WORKERS --dist worksteal"
        ;;
    sequential)
        echo -e "${YELLOW}Running tests sequentially${NC}"
        PYTEST_CMD="$PYTEST_CMD -n 0"
        ;;
    debug)
        echo -e "${BLUE}Running tests in debug mode${NC}"
        PYTEST_CMD="$PYTEST_CMD -s -vv --tb=long -n 0"
        VERBOSE=true  # Force verbose in debug mode
        ;;
esac

# Add coverage if requested
if [ "$COVERAGE" = true ]; then
    echo -e "${GREEN}Including coverage report${NC}"
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=html --cov-report=term-missing"
fi

# Add verbose if requested (and not already added by debug mode)
if [ "$VERBOSE" = true ] && [ "$MODE" != "debug" ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
fi

# Display command being run
echo -e "${BLUE}Command:${NC} $PYTEST_CMD"
echo ""

# Execute the command
eval $PYTEST_CMD

# Check exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo -e "${GREEN}📊 Coverage report generated: htmlcov/index.html${NC}"
    fi
else
    echo ""
    echo -e "${RED}❌ Some tests failed (exit code: $EXIT_CODE)${NC}"
    
    if [ "$MODE" = "parallel" ]; then
        echo -e "${YELLOW}💡 Try running in debug mode for more details:${NC}"
        echo "   $0 -m debug $TARGET"
    fi
fi

exit $EXIT_CODE 