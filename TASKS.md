# Task Definitions

Tasks are markdown files with YAML frontmatter. Task files are searched in this order:
1. `{REPO_ROOT}/tasks/{name}.md` (searched first)
2. `{CONTEXT_ROOT}/tasks/{name}.md` (fallback if not found in repo)

This allows tasks to be stored either in the repository or in a separate context mount. If a task specifies context files, `CONTEXT_ROOT` must be set.

## Task File Format

```yaml
---
description: Generate an OpenAPI spec for {SERVICE}
context:
  - /specs/api_standards.md
  - /schemas/{SERVICE}.yaml
repo:
  - /src/api/routes.py
  - /examples/
environment:
  - SERVICE
  - API_VERSION
outputs:
  - /docs/openapi.yaml
guarantees:
  - OpenAPI 3.1
  - Standard error envelope
---

Task-specific instructions with {VARIABLE} substitution.
Variables from environment section will be substituted in the task content.
```

## Fields

- **`description`**: High-level task description
- **`context`**: Files/patterns to load from context root (standards, specs, templates)
  - Individual files: `- /path/to/file.md`
  - Directories: `- /path/to/directory/` (loads all files recursively)
- **`repo`**: Files/patterns to load from repository root (existing code, examples)
  - Individual files: `- /path/to/file.md`
  - Directories: `- /path/to/directory/` (loads all files recursively)
- **`environment`**: List of required environment variable names (will be validated and used for substitution)
  - Task execution will fail if any listed environment variable is not set
  - Variables are substituted in task content (e.g., `{SERVICE}` → `$SERVICE` env var value)
- **`outputs`**: Expected output files (informational only)
- **`guarantees`**: Requirements/constraints for LLM output
- **Body**: Detailed instructions with variable substitution support

## Example Tasks

See `test/context/tasks/` for example task definitions:
- `example.md` - Example task for generating a README with context and repo files
- `simple_readme.md` - Simple README generation task for testing
