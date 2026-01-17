"""Repository file reader."""
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class RepoReader:
    """Reads files from the mounted repository."""

    @staticmethod
    def read_file(repo_root: str, file_path: str) -> str:
        """Read a single file from the repository."""
        full_path = os.path.join(repo_root, file_path.lstrip("/"))
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found in repo: {file_path}")
        
        with open(full_path, "r") as f:
            return f.read()

    @staticmethod
    def list_files(repo_root: str, directory: str = "", pattern: str = None) -> List[str]:
        """List files in the repository, optionally matching a pattern."""
        search_dir = os.path.join(repo_root, directory.lstrip("/"))
        if not os.path.exists(search_dir):
            return []

        files = []
        for root, _, filenames in os.walk(search_dir):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), repo_root)
                if pattern is None or pattern in filename:
                    files.append(rel_path)

        return sorted(files)

    @staticmethod
    def get_repo_structure(repo_root: str, max_depth: int = 3) -> Dict[str, any]:
        """Get a tree structure of the repository."""
        structure = {}

        def build_tree(path: str, depth: int = 0):
            if depth > max_depth:
                return None
            if os.path.isfile(path):
                return os.path.getsize(path)
            elif os.path.isdir(path):
                tree = {}
                try:
                    entries = os.listdir(path)
                    for entry in entries:
                        if entry.startswith(".") and entry != ".":
                            continue
                        entry_path = os.path.join(path, entry)
                        tree[entry] = build_tree(entry_path, depth + 1)
                    return tree if tree else None
                except PermissionError:
                    return None
            return None

        structure = build_tree(repo_root) or {}
        return structure
