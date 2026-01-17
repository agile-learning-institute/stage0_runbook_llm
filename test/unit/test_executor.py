"""Tests for executor."""
import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from executor import Executor
from llm_provider import NullLLMClient


class TestExecutor(unittest.TestCase):
    """Tests for Executor class."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "repo")
        self.context_dir = os.path.join(self.temp_dir, "context")
        self.tasks_dir = os.path.join(self.context_dir, "tasks")
        
        os.makedirs(self.repo_dir)
        os.makedirs(self.tasks_dir)
        
        # Set environment for config
        os.environ["LLM_PROVIDER"] = "null"
        os.environ["TRACKING_BREADCRUMB"] = "user:test,role:test,ts:2024-01-01T00:00:00Z,corr:test"
        
        # Reset config singleton
        from config import Config
        Config._instance = None

    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
        for key in ["LLM_PROVIDER", "TRACKING_BREADCRUMB"]:
            if key in os.environ:
                del os.environ[key]
        from config import Config
        Config._instance = None

    def test_executor_initialization(self):
        """Test executor initialization."""
        executor = Executor(self.repo_dir, self.context_dir)
        self.assertEqual(executor.repo_root, self.repo_dir)
        self.assertEqual(executor.context_root, self.context_dir)
        self.assertIsNotNone(executor.repo_reader)
        self.assertIsNotNone(executor.task_loader)
        self.assertIsNotNone(executor.llm_client)

    def test_executor_with_custom_llm_client(self):
        """Test executor with custom LLM client."""
        mock_client = Mock()
        executor = Executor(self.repo_dir, self.context_dir, llm_client=mock_client)
        self.assertIs(executor.llm_client, mock_client)

    def test_execute_task_success(self):
        """Test successful task execution."""
        # Create a simple task file
        task_file = os.path.join(self.tasks_dir, "test_task.md")
        with open(task_file, "w") as f:
            f.write("""---
description: Test task description
context: []
outputs: []
guarantees:
  - Test guarantee
---
Test task content.
""")
        
        executor = Executor(self.repo_dir, self.context_dir)
        commit_message, patch = executor.execute_task("test_task")
        
        self.assertIsInstance(commit_message, str)
        self.assertIsInstance(patch, str)
        self.assertGreater(len(commit_message), 0)
        self.assertGreater(len(patch), 0)

    def test_execute_task_with_context_files(self):
        """Test task execution with context files."""
        # Create context file
        context_file = os.path.join(self.context_dir, "standards.md")
        with open(context_file, "w") as f:
            f.write("# Standards\n\nTest standards content.")
        
        # Create task with context
        task_file = os.path.join(self.tasks_dir, "test_task.md")
        with open(task_file, "w") as f:
            f.write("""---
description: Test task with context
context:
  - standards.md
outputs: []
guarantees: []
---
Test task content.
""")
        
        executor = Executor(self.repo_dir, self.context_dir)
        commit_message, patch = executor.execute_task("test_task")
        
        self.assertIsInstance(commit_message, str)
        self.assertIsInstance(patch, str)

    def test_execute_task_with_variables(self):
        """Test task execution with variable substitution."""
        # Create task with variables
        task_file = os.path.join(self.tasks_dir, "test_task.md")
        with open(task_file, "w") as f:
            f.write("""---
description: Test task with {SERVICE}
context: []
outputs: []
guarantees: []
---
Task for {SERVICE} service.
""")
        
        executor = Executor(self.repo_dir, self.context_dir)
        commit_message, patch = executor.execute_task("test_task", task_variables={"SERVICE": "api"})
        
        self.assertIsInstance(commit_message, str)
        self.assertIsInstance(patch, str)

    def test_build_system_prompt(self):
        """Test system prompt building."""
        executor = Executor(self.repo_dir, self.context_dir)
        
        task = {
            "description": "Test description",
            "guarantees": ["Guarantee 1", "Guarantee 2"],
            "content": "Task content"
        }
        context_files = {"file1.md": "Context content"}
        
        prompt = executor._build_system_prompt(task, context_files)
        
        self.assertIn("Test description", prompt)
        self.assertIn("Guarantee 1", prompt)
        self.assertIn("Guarantee 2", prompt)
        self.assertIn("Context content", prompt)
        self.assertIn("---COMMIT_MSG---", prompt)
        self.assertIn("---PATCH---", prompt)

    def test_build_system_prompt_no_description(self):
        """Test system prompt building without description."""
        executor = Executor(self.repo_dir, self.context_dir)
        
        task = {"guarantees": ["Guarantee 1"]}
        context_files = {}
        
        prompt = executor._build_system_prompt(task, context_files)
        
        self.assertIn("Guarantee 1", prompt)
        self.assertIn("---COMMIT_MSG---", prompt)

    def test_build_user_prompt(self):
        """Test user prompt building."""
        # Create a file in repo
        repo_file = os.path.join(self.repo_dir, "test.txt")
        with open(repo_file, "w") as f:
            f.write("Test file content")
        
        executor = Executor(self.repo_dir, self.context_dir)
        
        task = {
            "content": "Create file for {SERVICE}",
            "inputs": ["test.txt"]
        }
        variables = {"SERVICE": "api"}
        
        prompt = executor._build_user_prompt(task, variables)
        
        self.assertIn("Create file for api", prompt)
        self.assertIn("Test file content", prompt)
        self.assertIn("Repository structure", prompt)

    def test_build_user_prompt_no_content(self):
        """Test user prompt building without content."""
        executor = Executor(self.repo_dir, self.context_dir)
        
        task = {}
        variables = {}
        
        prompt = executor._build_user_prompt(task, variables)
        
        self.assertIn("Repository structure", prompt)

    def test_execute_task_invalid_response(self):
        """Test handling of invalid LLM response."""
        # Create a mock client that returns invalid response
        mock_client = Mock()
        mock_client.complete.return_value = "Invalid response without markers"
        
        executor = Executor(self.repo_dir, self.context_dir, llm_client=mock_client)
        
        # Create task file
        task_file = os.path.join(self.tasks_dir, "test_task.md")
        with open(task_file, "w") as f:
            f.write("""---
description: Test task
context: []
outputs: []
guarantees: []
---
Test content.
""")
        
        with self.assertRaises(ValueError):
            executor.execute_task("test_task")


if __name__ == "__main__":
    unittest.main()
