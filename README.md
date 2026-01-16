# stage0_runbook_ai_cli

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

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TRACKING_BREADCRUMB` | Yes | - | User, role, timestamp, correlation ID |
| `REPO_ROOT` | No | `/workspace/repo` | Repository mount point |
| `CONTEXT_ROOT` | No | `/workspace/context` | Context/specifications mount point |
| `LLM_PROVIDER` | No | `null` | `null`, `ollama`, `openai`, `azure` |
| `LLM_MODEL` | No | `codellama` | Provider-specific model name |
| `LLM_BASE_URL` | Conditional | - | Required for self-hosted providers |
| `LLM_API_KEY` | Conditional | - | Required for `openai`/`azure` |
| `LOG_LEVEL` | No | `INFO` | Logging level |

### Task Definitions

Tasks are markdown files with YAML frontmatter in `{CONTEXT_ROOT}/tasks/{name}.md`:

```yaml
---
prompt: Generate an OpenAPI spec for {SERVICE}
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
- `prompt`: High-level task description
- `context`: Files/patterns to load from context root
- `outputs`: Expected output files (informational)
- `guarantees`: Requirements/constraints for LLM
- Body: Detailed instructions with variable substitution

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
pipenv run task --task example  # Run locally
pipenv run container     # Build Docker image
pipenv run deploy        # Test container locally
```

### Project Structure

```
src/
├── main.py              # CLI entry point
├── executor.py          # Task orchestration
├── llm_provider.py      # LLM abstraction & adapters
├── task_loader.py       # Task definition loader
├── repo_reader.py       # Repository file access
└── patch_generator.py   # Patch output generation
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
