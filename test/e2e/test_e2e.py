"""End-to-end tests for the CLI executor."""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from executor import Executor
from patch_generator import parse_patch_response
from difflib import SequenceMatcher


class TestE2E(unittest.TestCase):
    """End-to-end tests for task execution."""
    
    def setUp(self):
        """Set up test environment."""
        # Use test directories relative to this file
        test_dir = Path(__file__).parent.parent
        self.repo_root = str(test_dir / "repo")
        self.context_root = str(test_dir / "context")
        
        # Ensure directories exist
        os.makedirs(self.repo_root, exist_ok=True)
        
    def test_simple_readme_task(self):
        """Test creating a README.md from standards and info."""
        # Set up config for Ollama
        os.environ["LLM_PROVIDER"] = "ollama"
        os.environ["LLM_MODEL"] = "llama3.2"  # Smaller model
        os.environ["LLM_BASE_URL"] = "http://spark-478a.tailb0d293.ts.net:11434"
        os.environ["REPO_ROOT"] = self.repo_root
        os.environ["CONTEXT_ROOT"] = self.context_root
        os.environ["LOG_LEVEL"] = "INFO"
        os.environ["TRACKING_BREADCRUMB"] = "user:test,role:test,ts:2024-01-01T00:00:00Z,corr:test123"
        
        # Reset config singleton
        from config import Config
        Config._instance = None
        
        try:
            executor = Executor(self.repo_root, self.context_root)
            commit_message, patch = executor.execute_task("simple_readme")
            
            # Verify output format - commit_message and patch are already parsed
            self.assertIn("README.md", patch)
            
            # Verify commit message is present
            self.assertTrue(len(commit_message) > 0)
            
            # Verify patch contains expected content
            self.assertIn("diff --git", patch)
            self.assertIn("My Awesome Project", patch, "Should contain project name from Info.md")
            
            # Load expected content if available
            expected_file = Path(__file__).parent.parent / "expected" / "simple_readme_expected.md"
            if expected_file.exists():
                with open(expected_file, "r") as f:
                    expected_content = f.read()
                
                # Extract README content from patch (fuzzy match)
                # The patch should contain the README content
                # We'll do a fuzzy match on key phrases
                expected_phrases = [
                    "My Awesome Project",
                    "Description",
                    "Installation",
                    "Usage",
                ]
                
                found_phrases = sum(1 for phrase in expected_phrases if phrase in patch)
                self.assertGreater(
                    found_phrases,
                    len(expected_phrases) * 0.5,  # At least 50% of expected phrases
                    f"Patch should contain key phrases from expected output. Found {found_phrases}/{len(expected_phrases)}"
                )
                
        finally:
            # Clean up environment
            for key in ["LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL", "REPO_ROOT", "CONTEXT_ROOT", "LOG_LEVEL", "TRACKING_BREADCRUMB"]:
                if key in os.environ:
                    del os.environ[key]
            # Reset config
            Config._instance = None


if __name__ == "__main__":
    unittest.main()
