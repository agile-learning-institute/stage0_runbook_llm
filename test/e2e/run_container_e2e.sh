#!/bin/bash
# E2E test script for containerized CLI execution
# This script builds the container (if needed) and runs E2E tests against it

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TEST_DIR="${SCRIPT_DIR}/.."

# Container image name
IMAGE_NAME="ghcr.io/agile-learning-institute/stage0_runbook_ai_cli:latest"

# Test directories (relative to project root)
REPO_DIR="${PROJECT_ROOT}/test/repo"
CONTEXT_DIR="${PROJECT_ROOT}/test/context"

# Ensure test directories exist
mkdir -p "${REPO_DIR}"
mkdir -p "${CONTEXT_DIR}"

echo "Building container image..."
cd "${PROJECT_ROOT}"
docker build --tag "${IMAGE_NAME}" . || {
    echo "Error: Failed to build container image"
    exit 1
}

echo ""
echo "Running E2E test in container..."
echo ""

# Run container with test environment variables
# Mount test/repo and test/context as volumes
# Set environment variables for null provider test
docker run --rm \
    -v "${REPO_DIR}:/workspace/repo" \
    -v "${CONTEXT_DIR}:/workspace/context" \
    -e "LLM_PROVIDER=null" \
    -e "TASK_NAME=simple_readme" \
    -e "REPO_ROOT=/workspace/repo" \
    -e "CONTEXT_ROOT=/workspace/context" \
    -e "LOG_LEVEL=INFO" \
    "${IMAGE_NAME}" > /tmp/container_e2e_output.txt 2>&1

CONTAINER_EXIT_CODE=$?

# Capture output
OUTPUT=$(cat /tmp/container_e2e_output.txt)

echo "Container output:"
echo "=================="
echo "${OUTPUT}"
echo "=================="
echo ""

if [ ${CONTAINER_EXIT_CODE} -ne 0 ]; then
    echo "Error: Container exited with code ${CONTAINER_EXIT_CODE}"
    exit 1
fi

# Validate output
if ! echo "${OUTPUT}" | grep -q -- "---COMMIT_MSG---"; then
    echo "Error: Output missing ---COMMIT_MSG--- marker"
    exit 1
fi

if ! echo "${OUTPUT}" | grep -q -- "---PATCH---"; then
    echo "Error: Output missing ---PATCH--- marker"
    exit 1
fi

# Extract commit message and patch sections
COMMIT_MSG=$(echo "${OUTPUT}" | sed -n '/---COMMIT_MSG---/,/---PATCH---/p' | sed '1d;$d')
PATCH=$(echo "${OUTPUT}" | sed -n '/---PATCH---/,$p' | sed '1d')

# Validate commit message
if ! echo "${COMMIT_MSG}" | grep -qi "mock change"; then
    echo "Error: Commit message does not contain 'mock change'"
    echo "Commit message: ${COMMIT_MSG}"
    exit 1
fi

# Validate patch
if ! echo "${PATCH}" | grep -q "diff --git"; then
    echo "Error: Patch missing 'diff --git' header"
    exit 1
fi

if ! echo "${PATCH}" | grep -q "test.txt"; then
    echo "Error: Patch missing 'test.txt' reference"
    exit 1
fi

if ! echo "${PATCH}" | grep -q "mock content"; then
    echo "Error: Patch missing 'mock content'"
    exit 1
fi

echo "✅ E2E container test passed!"
echo ""
