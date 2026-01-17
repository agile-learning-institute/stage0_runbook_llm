"""Tests for CLI command."""
import unittest
import os
import sys
import tempfile
import subprocess
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

    def tearDown(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir)
        for key in ["REPO_ROOT", "CONTEXT_ROOT", "TRACKING_BREADCRUMB", "LLM_PROVIDER"]:
            if key in os.environ:
                del os.environ[key]

    @patch('sys.argv', ['command', '--task', 'test_task'])
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

    @patch('sys.argv', ['command', '--task', 'nonexistent'])
    @patch('sys.exit')
    def test_main_task_not_found(self, mock_exit):
        """Test handling of non-existent task."""
        from command import main
        
        with patch('sys.stderr'):
            main()
        
        # Should exit with error code 1
        mock_exit.assert_called_once_with(1)

    @patch('sys.argv', ['command', '--task', 'test_task', '--repo-root', '/nonexistent'])
    @patch('sys.exit')
    def test_main_repo_root_not_found(self, mock_exit):
        """Test handling of non-existent repo root."""
        from command import main
        
        with patch('sys.stderr'):
            main()
        
        # Should exit with error code 1
        mock_exit.assert_called_once_with(1)

    @patch('sys.argv', ['command', '--task', 'test_task', '--context-root', '/nonexistent'])
    @patch('sys.exit')
    def test_main_context_root_not_found(self, mock_exit):
        """Test handling of non-existent context root."""
        from command import main
        
        with patch('sys.stderr'):
            main()
        
        # Should exit with error code 1
        mock_exit.assert_called_once_with(1)

    @patch('sys.argv', ['command', '--task', 'test_task', '--repo-root'])
    def test_main_missing_repo_root_value(self):
        """Test handling of missing repo-root value."""
        # argparse will handle this, but we test it doesn't crash
        from command import main
        
        # This should raise SystemExit from argparse
        with self.assertRaises(SystemExit):
            main()

    def test_argument_parsing(self):
        """Test that command line arguments are parsed correctly."""
        from command import main
        from unittest.mock import patch
        
        with patch('sys.argv', ['command', '--task', 'my_task', '--repo-root', '/custom/repo']):
            with patch('command.Executor') as mock_executor:
                mock_executor_instance = MagicMock()
                mock_executor_instance.execute_task.return_value = ("test commit", "test patch")
                mock_executor.return_value = mock_executor_instance
                
                with patch('sys.stdout'):
                    with patch('sys.exit'):
                        main()
                
                # Check that executor was called with custom repo root
                mock_executor.assert_called_once()
                args = mock_executor.call_args[0]
                self.assertEqual(args[0], "/custom/repo")


if __name__ == "__main__":
    unittest.main()
