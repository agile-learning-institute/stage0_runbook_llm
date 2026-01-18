# stage0_runbook_llm

Container-friendly CLI that executes LLM-powered code transformations against a mounted repository. Produces deterministic patches and commit messages for automated workflows.

## Architecture

```
Caller → [Mounts repo + context] → Executor → [stdout: patch + message] → Caller
```

The executor is a pure function: reads inputs, executes one task, writes patch output, exits. Git operations (clone, pull, checkout, patch, etc.) handled by the caller.

## Usage

### Developer Commands

```bash
# Quick Start - run the simple_readme task 
# Using the test/repo and test/context folders
# And LLM Services hosed on the Dev Spark
pipenv install
export TASK_NAME=simple_readme
make spark

# Setup Environment
export TASK_NAME=example
export LLM_PROVIDER=ollama
export LLM_MODEL=codellama
export LLM_BASE_URL=http://localhost:11434
export REPO_ROOT=/path/to/repo
export CONTEXT_ROOT=/path/to/context  # Optional

# Execute a Task as configured in the environment
pipenv run task

# Run unit tests
pipenv run test

# Run end-to-end tests
pipenv run e2e
```

### Container Related Commands
```sh
# Build the Docker Container
make container

# Run E2E tests using the Docker Container
make e2e

# Run the configured script using the container
make deploy

# Run the configured script using the NVIDIA Spark LLM backing service
make spark

# Show the current configuration values
make show-config

# Get a command to clear all env config values
make clear-config
```

### Output Format

```
---COMMIT_MSG---
feat(api): generate OpenAPI specification

- Adds openapi.yaml using org-standard conventions
- Includes pagination, error envelope, and auth scheme
---PATCH---
diff --git a/openapi.yaml b/openapi.yaml
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/openapi.yaml
@@ -0,0 +1,10 @@
+openapi: 3.1.0
+...
```

### Container Execution

```bash
docker run --rm \
  -v /path/to/repo:/workspace/repo \
  # -v /path/to/context:/workspace/context \  # Optional: only needed if tasks use context files
  -e TASK_NAME=example \
  -e LLM_PROVIDER=ollama \
  -e LLM_MODEL=codellama \
  -e LLM_BASE_URL=http://localhost:11434 \
  ghcr.io/agile-learning-institute/stage0_runbook_llm:latest
```

## Configuration

Configuration is managed by the `Config` class in `src/config.py`. See that file for:
- All available configuration options
- Default values
- Environment variable names
- Configuration priority system

The Config class automatically configures logging based on `LOG_LEVEL`.

## Task Definitions

See [TASKS.md](TASKS.md) for complete documentation on task file format, fields, and examples.

## LLM Providers

### Null (Testing)
```bash
export LLM_PROVIDER=null
```
Returns mock patch output for testing.

### Ollama (Local/Remote)
```bash
export LLM_PROVIDER=ollama
export LLM_MODEL=codellama
export LLM_BASE_URL=http://localhost:11434
```

### OpenAI / Azure

**Note:** OpenAI and Azure configurations have not been tested and are not currently supported. The provider interface exists for future extensibility, but these examples are provided for reference only.

```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_API_KEY=sk-...
```

Provider interface is extensible via `LLMClient` protocol in `src/llm_provider.py`.

## Project Structure

```
src/
├── command.py          # CLI entry point
├── config.py           # Configuration management
├── executor.py         # Task orchestration
├── llm_provider.py     # LLM abstraction & adapters
├── task_loader.py      # Task definition loader
├── repo_reader.py      # Repository file access
└── patch_generator.py  # Patch output generation

test/
├── unit/               # Unit tests
├── e2e/                # End-to-end tests
├── context/            # Test context files
│   └── tasks/          # Example task definitions
├── repo/               # Test repository
└── expected/           # Expected test outputs
```

## Design Principles

- **Deterministic**: One task, one run, one patch
- **Container-first**: Designed for `docker run` with mounted volumes
- **Provider-agnostic**: LLM backend via protocol interface
- **Non-interactive**: All configuration via env vars
- **Auditable**: Explicit task definitions, path allowlists, output contracts

## Security

Designed to run with:
- `--network=none` (unless LLM provider requires network)
- Non-root user
- No git credentials
- Limited CPU/memory
- Access only to mounted volumes

Container hardening is the caller's responsibility.
