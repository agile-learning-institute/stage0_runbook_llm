"""Tests for CLI command."""
import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))


class TestCommand(unittest.TestCase):
    """Tests for command CLI entry point."""

    def setUp(self):
        """Set up test environment."""
        # Set up minimal environment
        os.environ["TRACKING_BREADCRUMB"] = "user:test,role:test,ts:2024-01-01T00:00:00Z,corr:test"
        os.environ["LLM_PROVIDER"] = "null"
        
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "repo")
        self.context_dir = os.path.join(self.temp_dir, "context")
        self.tasks_dir = os.path.join(self.context_dir, "tasks")
        
        os.makedirs(self.repo_dir)
        os.makedirs(self.tasks_dir)
        
        # Create a simple task file
        task_file = os.path.join(self.tasks_dir, "test_task.md")
        with open(task_file, "w") as f:
            f.write("""---
description: Test task
context: []
outputs: []
guarantees: []
---
Test task content.
""")
        
        os.environ["REPO_ROOT"] = self.repo_dir
        os.environ["CONTEXT_ROOT"] = self.context_dir
        os.environ["TASK_NAME"] = "test_task"

    def tearDown(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir)
        for key in ["REPO_ROOT", "CONTEXT_ROOT", "TASK_NAME", "TRACKING_BREADCRUMB", "LLM_PROVIDER"]:
            if key in os.environ:
                del os.environ[key]

    @patch('sys.stdout')
    @patch('sys.exit')
    def test_main_success(self, mock_exit, mock_stdout):
        """Test successful task execution."""
        from command import main
        
        # Mock print to capture output
        output_lines = []
        original_print = print
        
        def mock_print(*args, **kwargs):
            output_lines.append(' '.join(str(arg) for arg in args))
        
        with patch('builtins.print', side_effect=mock_print):
            main()
        
        # Check that output format is correct
        output = '\n'.join(output_lines)
        self.assertIn("---COMMIT_MSG---", output)
        self.assertIn("---PATCH---", output)
        
        # Check exit was called with 0
        mock_exit.assert_called_once_with(0)

    @patch('sys.exit')
    def test_main_task_not_found(self, mock_exit):
        """Test handling of non-existent task."""
        os.environ["TASK_NAME"] = "nonexistent"
        from command import main
        
        with patch('sys.stderr'):
            main()
        
        # Should exit with error code 1
        mock_exit.assert_called_once_with(1)

    @patch('sys.exit')
    def test_main_repo_root_not_found(self, mock_exit):
        """Test handling of non-existent repo root."""
        os.environ["REPO_ROOT"] = "/nonexistent"
        from command import main
        
        with patch('sys.stderr'):
            main()
        
        # Should exit with error code 1
        mock_exit.assert_called_once_with(1)

    @patch('sys.exit')
    def test_main_context_root_not_found(self, mock_exit):
        """Test handling of non-existent context root."""
        os.environ["CONTEXT_ROOT"] = "/nonexistent"
        from command import main
        
        with patch('sys.stderr'):
            main()
        
        # Should exit with error code 1
        mock_exit.assert_called_once_with(1)

    @patch('sys.exit')
    def test_main_missing_task_name(self, mock_exit):
        """Test handling of missing TASK_NAME environment variable."""
        if "TASK_NAME" in os.environ:
            del os.environ["TASK_NAME"]
        from command import main
        
        with patch('sys.stderr'):
            main()
        
        # Should exit with error code 1
        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
