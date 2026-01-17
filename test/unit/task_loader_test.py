"""Tests for task loader."""
import unittest
import tempfile
import os
import sys
import yaml
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from task_loader import TaskLoader


class TestTaskLoader(unittest.TestCase):
    """Tests for TaskLoader class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.tasks_dir = os.path.join(self.temp_dir, "tasks")
        os.makedirs(self.tasks_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_task_valid(self):
        """Test loading a valid task."""
        task_content = """---
description: Generate an API spec
context:
  - /specs/api_standards.md
outputs:
  - /docs/openapi.yaml
guarantees:
  - OpenAPI 3.1
---
Task instructions go here.
"""
        task_file = os.path.join(self.tasks_dir, "test.md")
        with open(task_file, "w") as f:
            f.write(task_content)

        task = TaskLoader.load_task(self.temp_dir, "test")
        self.assertEqual(task["description"], "Generate an API spec")
        self.assertIn("context", task)
        self.assertEqual(task["content"], "Task instructions go here.")

    def test_load_task_not_found(self):
        """Test loading a non-existent task raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            TaskLoader.load_task(self.temp_dir, "nonexistent")

    def test_load_task_missing_frontmatter(self):
        """Test that task without frontmatter raises ValueError."""
        task_file = os.path.join(self.tasks_dir, "invalid.md")
        with open(task_file, "w") as f:
            f.write("No frontmatter here")

        with self.assertRaises(ValueError):
            TaskLoader.load_task(self.temp_dir, "invalid")

    def test_load_context_files(self):
        """Test loading context files."""
        # Create a test file
        context_dir = os.path.join(self.temp_dir, "specs")
        os.makedirs(context_dir)
        test_file = os.path.join(context_dir, "api_standards.md")
        with open(test_file, "w") as f:
            f.write("# API Standards\n\nTest content")

        context_files = TaskLoader.load_context_files(self.temp_dir, ["specs/api_standards.md"])
        self.assertIn("specs/api_standards.md", context_files)
        self.assertIn("API Standards", context_files["specs/api_standards.md"])


if __name__ == "__main__":
    unittest.main()
