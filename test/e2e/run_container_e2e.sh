#!/bin/bash
# E2E test script for containerized CLI execution
# This script validates that the containerized CLI works correctly

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Container image name (must match Makefile)
IMAGE_NAME="ghcr.io/agile-learning-institute/stage0_runbook_llm:latest"

# Test directories
REPO_DIR="${PROJECT_ROOT}/test/repo"
CONTEXT_DIR="${PROJECT_ROOT}/test/context"

# Ensure test directories exist
mkdir -p "${REPO_DIR}"
mkdir -p "${CONTEXT_DIR}"

echo "Running E2E test in container..."
echo ""

# Run container with test environment variables
# Using default E2E test values (null provider, simple_readme task)
docker run --rm \
    -v "${REPO_DIR}:/workspace/repo" \
    -v "${CONTEXT_DIR}:/workspace/context" \
    -e "REPO_ROOT=/workspace/repo" \
    -e "CONTEXT_ROOT=/workspace/context" \
    -e "TASK_NAME=simple_readme" \
    -e "LLM_PROVIDER=null" \
    -e "LLM_MODEL=codellama" \
    -e "LLM_BASE_URL=http://localhost:11434" \
    -e "LLM_TEMPERATURE=7" \
    -e "LLM_MAX_TOKENS=8192" \
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

# Validate exit code
if [ ${CONTAINER_EXIT_CODE} -ne 0 ]; then
    echo "Error: Container exited with code ${CONTAINER_EXIT_CODE}"
    exit 1
fi

# Validate output markers
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
