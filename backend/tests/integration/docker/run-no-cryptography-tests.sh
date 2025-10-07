#!/bin/bash
# Script to run integration tests without cryptography library
# This verifies graceful degradation when cryptography is unavailable

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Integration Tests: No Cryptography${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../../.." && pwd )"

echo -e "${GREEN}Project root: ${PROJECT_ROOT}${NC}"
echo -e "${GREEN}Building Docker image without cryptography...${NC}"
echo ""

# Build the Docker image
cd "$PROJECT_ROOT"
docker build \
  -f backend/tests/integration/docker/Dockerfile.no-cryptography \
  -t fastapi-integration-no-crypto:latest \
  .

echo ""
echo -e "${GREEN}Running integration tests...${NC}"
echo ""

# Run the tests
docker run --rm \
  -v "$PROJECT_ROOT/backend/tests/integration/docker/test-results:/app/backend/test-results" \
  fastapi-integration-no-crypto:latest

# Capture exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✅ All integration tests passed!${NC}"
else
  echo -e "${RED}❌ Some integration tests failed (exit code: $EXIT_CODE)${NC}"
fi
echo ""

exit $EXIT_CODE
