"""Patch generator for creating unified diff patches."""
import os
import subprocess
import logging
import tempfile
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class PatchGenerator:
    """Generates patches from LLM-generated file changes."""

    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    def generate_patch(self, file_path: str, new_content: str, old_content: Optional[str] = None) -> str:
        """Generate a patch for a file change."""
        full_path = os.path.join(self.repo_root, file_path.lstrip("/"))
        rel_path = file_path.lstrip("/")

        # Create temporary file with new content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.patch') as tmp:
            tmp.write(new_content)
            tmp_path = tmp.name

        try:
            # Use git diff if available, otherwise create simple diff
            if old_content is None:
                # New file
                if os.path.exists(full_path):
                    old_content = self._read_if_exists(full_path)
                else:
                    old_content = ""

            patch_lines = self._create_diff(rel_path, old_content, new_content, os.path.exists(full_path))
            return "\n".join(patch_lines)
        finally:
            os.unlink(tmp_path)

    def _read_if_exists(self, path: str) -> str:
        """Read file if it exists."""
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read()
        return ""

    def _create_diff(self, file_path: str, old_content: str, new_content: str, file_exists: bool) -> List[str]:
        """Create a unified diff between old and new content."""
        from difflib import unified_diff

        old_lines = old_content.splitlines(keepends=True) if old_content else []
        new_lines = new_content.splitlines(keepends=True) if new_content else []

        diff_lines = list(unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}" if file_exists else "/dev/null",
            tofile=f"b/{file_path}",
            lineterm=""
        ))

        # Add git diff header
        mode = "100644"
        header = [
            f"diff --git a/{file_path} b/{file_path}",
            f"new file mode {mode}" if not file_exists else f"index 0000000..1234567",
            f"--- /dev/null" if not file_exists else f"--- a/{file_path}",
            f"+++ b/{file_path}"
        ]

        return header + diff_lines

    def extract_files_from_response(self, llm_response: str) -> Dict[str, str]:
        """Extract file changes from LLM response."""
        files = {}
        
        # Simple extraction: look for file blocks in the response
        # Format: ---FILE:path/to/file--- ... content ... ---END---
        import re
        
        pattern = r'---FILE:(.+?)---\s*(.*?)---END---'
        matches = re.findall(pattern, llm_response, re.DOTALL)
        
        for file_path, content in matches:
            files[file_path.strip()] = content.strip()
        
        return files


def parse_patch_response(response: str) -> tuple[str, str]:
    """Parse LLM response into commit message and patch."""
    # Look for ---COMMIT_MSG--- and ---PATCH--- markers
    commit_msg_start = response.find("---COMMIT_MSG---")
    patch_start = response.find("---PATCH---")
    
    if commit_msg_start == -1 or patch_start == -1:
        raise ValueError("Response must contain ---COMMIT_MSG--- and ---PATCH--- blocks")
    
    if patch_start <= commit_msg_start:
        raise ValueError("---PATCH--- must come after ---COMMIT_MSG---")
    
    # Extract commit message
    commit_msg = response[commit_msg_start + len("---COMMIT_MSG---"):patch_start].strip()
    
    # Extract patch
    patch = response[patch_start + len("---PATCH---"):].strip()
    
    return commit_msg, patch
