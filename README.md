# stage0_runbook_ai_cli

A container-friendly, non-interactive CLI that executes tightly scoped LLM-powered code transformations against a mounted source repository.

The executor is designed to run as a pure change proposer in automated workflows:
- it reads a repository
- applies project- and org-specific standards
- produces a deterministic set of changes (as a patch or structured edit plan)
- emits a commit message
- and exits

All git operations, validation, branching, and commits are handled by the caller, not by this tool.

---

## Design Goals
- Deterministic + auditable
    The executor proposes changes; it does not manage git state.
- Container-first
    Intended to run via docker run with a repo mounted at a known path.
- LLM-backend agnostic
    Uses a provider interface. Ollama is supported for local/dev, but not required.
- Low-volume, high-trust
    Optimized for CI utilities, repo bootstrapping, and controlled automation.
- Strong guardrails
    Explicit task definitions, path allowlists, output contracts, and no hidden side effects.

---

## High-Level Architecture

```
┌────────────────────────────┐
│ Caller Script / CI Job     │
│                            │
│ - creates branch           │
│ - mounts repo              │
│ - injects context (env)    │
│ - runs executor            │
│ - applies patch            │
│ - runs tests / lint        │
│ - commits & pushes         │
└─────────────▲──────────────┘
              │ stdout
┌─────────────┴──────────────┐
│ LLM Executor CLI            │
│                             
│ - reads repo files          │
│ - loads standards           │
│ - runs LLM task             │
│ - outputs patch + message   │
│ - exits                     │
└─────────────▲──────────────┘
              │
┌─────────────┴──────────────┐
│ LLM Provider Interface     │
│  (Ollama, OpenAI, etc.)    │
└────────────────────────────┘
```

---

## Responsibilities (Explicit Non-Goals)

### The executor 

### DOES
- Read files from the mounted repository
- Read context from the mounted specifications repository
    - Organizational information
    - System standards
    - Prompt guides for specific tasks
- Execute a single, well-defined task
- Produce:
    - a commit message
    - a patch for the mounted repository
- Exit with a meaningful status code

### The executor 

### DOES NOT
- Run git commit, git push, or manage branches
- Install dependencies in the target repo
- Loop indefinitely or self-heal without bounds

---

## Execution Model
The executor is invoked once per task.

Each invocation:
1. Loads configuration and standards
2. Loads repo context
3. Executes a single task (e.g. “generate OpenAPI spec”)
4. Emits results to stdout
5. Exits

No interactive prompts. No background state.

---

### Patch-based output

```
---COMMIT_MSG---
feat(api): generate OpenAPI specification from JSON schemas

- Adds openapi.yaml using org-standard conventions
- Includes pagination, error envelope, and auth scheme
---PATCH---
diff --git a/openapi.yaml b/openapi.yaml
index 0000000..abc1234
--- /dev/null
+++ b/openapi.yaml
@@ ...
```

Rules:
- Exactly one commit message block
- Exactly one patch block
- Patch must apply cleanly from repo root
- No extra text outside the blocks

## Repository Mount Convention
The target repository must be mounted at:
```
/workspace/repo
```
The executor treats /workspace/repo as the repo root.

Context Mount of the Umbrella Repo with Specifications
```
/workspace/context   # standards, specs, schemas
```
Includes architecture specifications, software standards, Dated dictionaries, Schemas and more

## Configuration via Environment Variables

The executor is configured entirely via env vars.

### Required
|Variable|Description|
|---|---|
|TRACKING_BREADCRUMB|Identifier that includes user, roles, date-time, correlation_id|
|REPO_ROOT|Defaults to /workspace/repo|
|CONTEXT_ROOT|Defaults to /workspace/context|

### LLM Provider Selection
|Variable|Description|
|---|---|
|LLM_PROVIDER|ollama, openai, azure, etc.|
|LLM_MODEL|Provider-specific model name|
|LLM_BASE_URL|Required for self-hosted providers|
|LLM_API_KEY|Optional depending on provider|

---

## LLM Provider Interface
The executor defines a provider abstraction, not a hard dependency.
```
class LLMClient(Protocol):
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        ...
```

### Supported (initial)
- Ollama (dev / local)
- Null / Dry-run (for testing)
- Additional providers added via adapters

No provider-specific logic leaks into task code.

---

## Task Model
Each task is a single-purpose markdown file with a yaml block that describes the task.
Tasks are loaded from context repo in /tasks.

Example:
```
prompt: generate an OpenAPI based API explorer for the {SERVICE} domain
context:
- /mounts/specifications/README.md for system context
- /mounts/specifications/api_standards.md for API Standards
- /mounts/specifications/.schemas for data schemas
- /mounts/specifications/architecture.yaml for the {SERVICE} domain context
outputs:
- /mounts/repo/docs/index.html 
- /mounts/repo/docs/openapi.yaml
guarantees:
- OpenAPI 3.1
- Standard error envelope
- Pagination conventions
- No undocumented endpoints
```

A task:
- defines required inputs
- loads relevant repo files
- assembles the LLM prompt
- validates the response
- produces the final output

---

## Security & Isolation Expectations

The executor is designed to run with:
- --network=none (unless explicitly required)
- non-root user
- no git credentials
- limited CPU/memory
- no access outside mounted volumes

The executor assumes the caller enforces container hardening.

---

## Development Setup
```
pipenv install --dev
pipenv shell
pipenv run task - execute a specified task
pipenv run test - execute unit tests
pipenv run e2e - run black-box E2E cli test
pipenv run container - build container
pipenv run deploy - execute container script
pipenv run help 
```

### Local dev with Ollama
```
export LLM_PROVIDER=ollama
export LLM_MODEL=codellama
export LLM_BASE_URL=http://localhost:11434
```

---

## Versioning & Stability
- Output format is a public contract
- Breaking changes require a major version bump
- Tasks are versioned independently where possible

---

## Summary
This executor is intentionally boring:
- one task
- one run
- one patch
- one commit message

That constraint is what makes it safe, auditable, and easy to integrate into deterministic repo automation pipelines.