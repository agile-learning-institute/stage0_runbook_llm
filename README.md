# stage0_runbook_llm

Container-friendly CLI that executes LLM-powered code transformations against a mounted repository. Produces deterministic patches and commit messages for automated workflows.

## Architecture

```
Caller → [Mounts repo + context] → Executor → [stdout: patch + message] → Caller
```

The executor is a pure function: reads inputs, executes one task, writes patch output, exits. Git operations are handled by the caller.

## Usage

### Container

```bash
docker run --rm \
  -v /path/to/repo:/workspace/repo \
  -v /path/to/context:/workspace/context \
  -e LLM_PROVIDER=ollama \
  -e LLM_MODEL=codellama \
  -e LLM_BASE_URL=http://localhost:11434 \
  -e TRACKING_BREADCRUMB="user:admin,role:ci,ts:2024-01-01T00:00:00Z,corr:abc123" \
  ghcr.io/agile-learning-institute/stage0_runbook_ai_cli:latest \
  --task example
```

### Local Development

```bash
pipenv install
export LLM_PROVIDER=ollama
export LLM_MODEL=codellama
export LLM_BASE_URL=http://localhost:11434
export REPO_ROOT=/path/to/repo
export CONTEXT_ROOT=/path/to/context
export TRACKING_BREADCRUMB="user:dev,role:dev,ts:$(date -u +%Y-%m-%dT%H:%M:%SZ),corr:test"

pipenv run task --task example
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

## Configuration

Configuration is managed by the `Config` class in `src/config.py`. See that file for:
- All available configuration options
- Default values
- Environment variable names
- Configuration priority system

The Config class follows a singleton pattern and automatically configures logging based on `LOG_LEVEL`.

## Task Definitions

Tasks are markdown files with YAML frontmatter in `{CONTEXT_ROOT}/tasks/{name}.md`:

```yaml
---
description: Generate an OpenAPI spec for {SERVICE}
context:
  - /specs/api_standards.md
  - /schemas/{SERVICE}.yaml
outputs:
  - /docs/openapi.yaml
guarantees:
  - OpenAPI 3.1
  - Standard error envelope
---

Task-specific instructions with {VARIABLE} substitution.
```

**Fields:**
- `description`: High-level task description
- `context`: Files/patterns to load from context root
- `outputs`: Expected output files (informational)
- `guarantees`: Requirements/constraints for LLM
- Body: Detailed instructions with variable substitution

### Example Tasks

See `test/context/tasks/` for example task definitions:
- `example.md` - Example task for generating a README
- `simple_readme.md` - Simple README generation task for testing

## LLM Providers

### Null (Testing)
```bash
export LLM_PROVIDER=null
```
Returns mock patch output for testing.

### Ollama (Local)
```bash
export LLM_PROVIDER=ollama
export LLM_MODEL=codellama
export LLM_BASE_URL=http://localhost:11434
```

### OpenAI / Azure
```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export LLM_BASE_URL=https://api.openai.com/v1
export LLM_API_KEY=sk-...
```

Provider interface is extensible via `LLMClient` protocol in `src/llm_provider.py`.

## Development

```bash
pipenv install --dev
pipenv run test          # Run unit tests
pipenv run e2e          # Run end-to-end tests
pipenv run task --task example  # Run locally
pipenv run container     # Build Docker image
pipenv run deploy        # Test container locally
```

### Project Structure

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
- **Non-interactive**: All configuration via env vars and arguments
- **Auditable**: Explicit task definitions, path allowlists, output contracts

## Security

Designed to run with:
- `--network=none` (unless LLM provider requires network)
- Non-root user
- No git credentials
- Limited CPU/memory
- Access only to mounted volumes

Container hardening is the caller's responsibility.
