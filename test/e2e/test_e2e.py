"""End-to-end tests for the CLI executor."""
import unittest
import os
import sys
import subprocess
from pathlib import Path


class TestE2E(unittest.TestCase):
    """End-to-end tests for task execution."""
    
    def setUp(self):
        """Set up test environment."""
        # Use test directories relative to this file
        test_dir = Path(__file__).parent.parent
        self.repo_root = str(test_dir / "repo")
        self.context_root = str(test_dir / "context")
        self.project_root = Path(__file__).parent.parent.parent
        
        # Ensure directories exist
        os.makedirs(self.repo_root, exist_ok=True)
        
    def test_simple_readme_task_null_provider(self):
        """Test creating a README.md using null LLM provider (CLI execution)."""
        # Set up environment for null provider
        env = os.environ.copy()
        env["LLM_PROVIDER"] = "null"
        env["TASK_NAME"] = "simple_readme"
        env["REPO_ROOT"] = self.repo_root
        env["CONTEXT_ROOT"] = self.context_root
        env["LOG_LEVEL"] = "INFO"
        
        try:
            # Execute CLI command via subprocess - call Python with command module import
            # PYTHONPATH=./src python -c "import command; command.main()"
            python_cmd = "import sys; sys.path.insert(0, './src'); import command; command.main()"
            
            result = subprocess.run(
                [sys.executable, "-c", python_cmd],
                cwd=str(self.project_root),
                env=env,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Verify command succeeded
            self.assertEqual(result.returncode, 0, 
                f"CLI failed with return code {result.returncode}. stderr: {result.stderr}\nstdout: {result.stdout}")
            
            # Parse output
            output = result.stdout
            self.assertIn("---COMMIT_MSG---", output, "Output should contain commit message marker")
            self.assertIn("---PATCH---", output, "Output should contain patch marker")
            
            # Extract commit message and patch
            parts = output.split("---COMMIT_MSG---")
            self.assertEqual(len(parts), 2, "Should have exactly one COMMIT_MSG block")
            commit_patch = parts[1].split("---PATCH---")
            self.assertEqual(len(commit_patch), 2, "Should have exactly one PATCH block")
            
            commit_message = commit_patch[0].strip()
            patch = commit_patch[1].strip()
            
            # Verify commit message is present and matches null provider output
            self.assertGreater(len(commit_message), 0, "Commit message should not be empty")
            # Null provider returns "feat: mock change"
            self.assertIn("mock change", commit_message.lower(), "Should match null provider commit message")
            
            # Verify patch contains expected null provider output
            # Null provider returns patch for test.txt with "mock content"
            self.assertIn("diff --git", patch, "Patch should contain git diff header")
            self.assertIn("test.txt", patch, "Null provider patch should reference test.txt")
            self.assertIn("mock content", patch, "Null provider patch should contain mock content")
            
        finally:
            # Environment cleanup is handled by env dict copy
            pass


if __name__ == "__main__":
    unittest.main()
