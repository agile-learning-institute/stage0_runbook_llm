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

    @staticmethod
    def execute_task(
        repo_root: str,
        task_name: str,
        context_root: str = None,
        task_variables: Dict[str, str] = None,
        llm_client: LLMClient = None
    ) -> tuple[str, str]:
        """
        Execute a task and return (commit_message, patch).
        
        Args:
            repo_root: Repository root path (required)
            task_name: Name of the task to execute
            context_root: Context root path (optional, only needed if task uses context files)
            task_variables: Optional explicit variables (merged with environment variables)
            llm_client: Optional LLM client (uses Config defaults if not provided)
        """
        task_variables = task_variables or {}
        llm_client = llm_client or create_llm_client()
        
        # Load task definition (searches repo/tasks first, then context/tasks)
        task = TaskLoader.load_task(repo_root, task_name, context_root)
        logger.info(f"Loaded task: {task_name}")

        # Validate and load required environment variables
        env_vars = Executor._load_environment_variables(task)
        if env_vars:
            logger.info(f"Loaded {len(env_vars)} environment variables for task")
        
        # Merge environment variables with explicit task_variables (explicit takes precedence)
        if task_variables:
            env_vars.update(task_variables)
        
        task_variables = env_vars

        # Load context and repo files
        context_files = {}
        if "context" in task:
            if not context_root:
                raise ValueError(
                    f"Task requires context files but CONTEXT_ROOT is not set. "
                    f"Task specifies context paths: {task['context']}"
                )
            context_files.update(TaskLoader.load_context_files(context_root, task["context"]))
            logger.info(f"Loaded {len(task['context'])} context file paths")
        
        if "repo" in task:
            repo_files = TaskLoader.load_repo_files(repo_root, task["repo"])
            context_files.update(repo_files)
            logger.info(f"Loaded {len(task['repo'])} repo file paths")
        
        if context_files:
            logger.info(f"Total context files loaded: {len(context_files)}")

        # Build system prompt from task and context
        system_prompt = Executor._build_system_prompt(task, context_files)
        
        # Build user prompt with repo context
        user_prompt = Executor._build_user_prompt(repo_root, task, task_variables)

        # Execute LLM call
        from .config import Config
        config = Config()
        
        logger.info("Executing LLM task...")
        response = llm_client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=config.get_llm_temperature(),
            max_tokens=config.LLM_MAX_TOKENS
        )

        # Parse response into commit message and patch
        commit_message, patch = parse_patch_response(response)
        
        logger.info("Task execution complete")
        return commit_message, patch

    @staticmethod
    def _build_system_prompt(task: Dict[str, Any], context_files: Dict[str, str]) -> str:
        """Build the system prompt from task definition and context."""
        prompt_parts = []

        # Add task description
        if "description" in task:
            prompt_parts.append(f"Task: {task['description']}")
        
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

    @staticmethod
    def _load_environment_variables(task: Dict[str, Any]) -> Dict[str, str]:
        """
        Load and validate required environment variables from task definition.
        
        Args:
            task: Task definition dictionary
            
        Returns:
            Dictionary of environment variable name -> value
            
        Raises:
            ValueError: If a required environment variable is missing
        """
        env_vars = {}
        
        if "environment" not in task:
            return env_vars
        
        required_vars = task.get("environment", [])
        missing_vars = []
        
        for var_name in required_vars:
            if not isinstance(var_name, str):
                logger.warning(f"Invalid environment variable name (not a string): {var_name}")
                continue
                
            value = os.getenv(var_name)
            if value is None:
                missing_vars.append(var_name)
            else:
                env_vars[var_name] = value
        
        if missing_vars:
            raise ValueError(
                f"Required environment variables not set: {', '.join(missing_vars)}. "
                f"Task '{task.get('description', 'unknown')}' requires these variables."
            )
        
        return env_vars

    @staticmethod
    def _build_user_prompt(repo_root: str, task: Dict[str, Any], variables: Dict[str, str]) -> str:
        """Build the user prompt with repository context."""
        prompt_parts = []

        # Add variable substitutions
        task_content = task.get("content", "")
        for key, value in variables.items():
            task_content = task_content.replace(f"{{{key}}}", value)

        if task_content:
            prompt_parts.append(f"Instructions:\n{task_content}")

        # Add repository structure
        repo_structure = RepoReader.get_repo_structure(repo_root, max_depth=2)
        if repo_structure:
            import json
            structure_str = json.dumps(repo_structure, indent=2)
            prompt_parts.append(f"\nRepository structure:\n{structure_str}")

        # Add file content hints if specified
        if "inputs" in task:
            prompt_parts.append("\nRelevant repository files:")
            for file_path in task["inputs"]:
                try:
                    content = RepoReader.read_file(repo_root, file_path)
                    # Only include first 500 chars to avoid token limits
                    preview = content[:500] + "..." if len(content) > 500 else content
                    prompt_parts.append(f"\n--- {file_path} ---\n{preview}")
                except FileNotFoundError:
                    logger.warning(f"Input file not found: {file_path}")

        return "\n".join(prompt_parts)
