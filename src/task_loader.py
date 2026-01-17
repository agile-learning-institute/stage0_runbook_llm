"""Task loader for reading task definitions from context."""
import os
import yaml
import logging
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskLoader:
    """Loads and validates task definitions from context."""

    @staticmethod
    def load_task(context_root: str, task_name: str) -> Dict[str, Any]:
        """Load a task definition from the tasks directory."""
        tasks_dir = os.path.join(context_root, "tasks")
        task_file = os.path.join(tasks_dir, f"{task_name}.md")
        
        if not os.path.exists(task_file):
            raise FileNotFoundError(f"Task not found: {task_file}")

        with open(task_file, "r") as f:
            content = f.read()

        # Parse YAML frontmatter
        if not content.startswith("---"):
            raise ValueError(f"Task {task_name} must start with YAML frontmatter (---)")

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"Task {task_name} must have YAML frontmatter and content")

        try:
            task_config = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in task {task_name}: {e}")

        task_config["content"] = parts[2].strip()
        return task_config

    @staticmethod
    def load_context_files(context_root: str, context_paths: List[str]) -> Dict[str, str]:
        """Load context files from the context root."""
        context_files = {}
        
        for path_spec in context_paths:
            # Support path variables like {SERVICE}
            # For now, just resolve relative to context_root
            resolved_path = os.path.join(context_root, path_spec.lstrip("/"))
            
            if os.path.isfile(resolved_path):
                with open(resolved_path, "r") as f:
                    context_files[path_spec] = f.read()
            elif os.path.isdir(resolved_path):
                # Load all files in directory
                for root, _, files in os.walk(resolved_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, context_root)
                        with open(file_path, "r") as f:
                            context_files[rel_path] = f.read()
            else:
                logger.warning(f"Context path not found: {resolved_path}")

        return context_files

    @staticmethod
    def load_repo_files(repo_root: str, repo_paths: List[str]) -> Dict[str, str]:
        """Load repository files from the repo root."""
        repo_files = {}
        
        for path_spec in repo_paths:
            # Resolve relative to repo_root
            resolved_path = os.path.join(repo_root, path_spec.lstrip("/"))
            
            if os.path.isfile(resolved_path):
                with open(resolved_path, "r") as f:
                    # Prefix with repo: to distinguish from context files
                    repo_files[f"repo:{path_spec}"] = f.read()
            elif os.path.isdir(resolved_path):
                # Load all files in directory
                for root, _, files in os.walk(resolved_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, repo_root)
                        with open(file_path, "r") as f:
                            repo_files[f"repo:{rel_path}"] = f.read()
            else:
                logger.warning(f"Repo path not found: {resolved_path}")

        return repo_files
