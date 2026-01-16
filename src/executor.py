"""Main executor that orchestrates task execution."""
import os
import logging
from typing import Dict, Any

from .llm_provider import LLMClient, create_llm_client
from .task_loader import TaskLoader
from .repo_reader import RepoReader
from .patch_generator import parse_patch_response

logger = logging.getLogger(__name__)


class Executor:
    """Main executor that runs LLM tasks."""

    def __init__(self, repo_root: str, context_root: str, llm_client: LLMClient = None):
        self.repo_root = repo_root
        self.context_root = context_root
        self.repo_reader = RepoReader(repo_root)
        self.task_loader = TaskLoader(context_root)
        self.llm_client = llm_client or create_llm_client()

    def execute_task(self, task_name: str, task_variables: Dict[str, str] = None) -> tuple[str, str]:
        """Execute a task and return (commit_message, patch)."""
        task_variables = task_variables or {}
        
        # Load task definition
        task = self.task_loader.load_task(task_name)
        logger.info(f"Loaded task: {task_name}")

        # Load context files
        context_files = {}
        if "context" in task:
            context_files = self.task_loader.load_context_files(task["context"])
            logger.info(f"Loaded {len(context_files)} context files")

        # Build system prompt from task and context
        system_prompt = self._build_system_prompt(task, context_files)
        
        # Build user prompt with repo context
        user_prompt = self._build_user_prompt(task, task_variables)

        # Execute LLM call
        logger.info("Executing LLM task...")
        response = self.llm_client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=8192
        )

        # Parse response into commit message and patch
        commit_message, patch = parse_patch_response(response)
        
        logger.info("Task execution complete")
        return commit_message, patch

    def _build_system_prompt(self, task: Dict[str, Any], context_files: Dict[str, str]) -> str:
        """Build the system prompt from task definition and context."""
        prompt_parts = []

        # Add task description
        if "prompt" in task:
            prompt_parts.append(f"Task: {task['prompt']}")
        
        # Add guarantees/requirements
        if "guarantees" in task:
            prompt_parts.append("\nRequirements:")
            for guarantee in task["guarantees"]:
                prompt_parts.append(f"- {guarantee}")

        # Add context files
        if context_files:
            prompt_parts.append("\nContext:")
            for path, content in context_files.items():
                prompt_parts.append(f"\n--- {path} ---\n{content}")

        # Add output format instructions
        prompt_parts.append("""
Output format:
1. Start with ---COMMIT_MSG---
2. Provide a commit message (conventional commits format)
3. Follow with ---PATCH---
4. Provide a git unified diff patch starting from the repository root
5. The patch must be valid and apply cleanly

Example:
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
""")

        return "\n".join(prompt_parts)

    def _build_user_prompt(self, task: Dict[str, Any], variables: Dict[str, str]) -> str:
        """Build the user prompt with repository context."""
        prompt_parts = []

        # Add variable substitutions
        task_content = task.get("content", "")
        for key, value in variables.items():
            task_content = task_content.replace(f"{{{key}}}", value)

        if task_content:
            prompt_parts.append(f"Instructions:\n{task_content}")

        # Add repository structure
        repo_structure = self.repo_reader.get_repo_structure(max_depth=2)
        if repo_structure:
            import json
            structure_str = json.dumps(repo_structure, indent=2)
            prompt_parts.append(f"\nRepository structure:\n{structure_str}")

        # Add file content hints if specified
        if "inputs" in task:
            prompt_parts.append("\nRelevant repository files:")
            for file_path in task["inputs"]:
                try:
                    content = self.repo_reader.read_file(file_path)
                    # Only include first 500 chars to avoid token limits
                    preview = content[:500] + "..." if len(content) > 500 else content
                    prompt_parts.append(f"\n--- {file_path} ---\n{preview}")
                except FileNotFoundError:
                    logger.warning(f"Input file not found: {file_path}")

        return "\n".join(prompt_parts)
