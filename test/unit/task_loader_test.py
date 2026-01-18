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

    def test_load_context_files_with_variables(self):
        """Test loading context files with variable substitution."""
        # Create test files
        schemas_dir = os.path.join(self.temp_dir, ".schemas")
        os.makedirs(schemas_dir)
        test_file = os.path.join(schemas_dir, "User0.1.0.json")
        with open(test_file, "w") as f:
            f.write('{"type": "object"}')

        variables = {"COLLECTION": "User", "VERSION": "0.1.0"}
        context_files = TaskLoader.load_context_files(
            self.temp_dir, 
            ["/.schemas/{COLLECTION}{VERSION}.json"],
            variables
        )
        self.assertIn("/.schemas/User0.1.0.json", context_files)
        self.assertIn("object", context_files["/.schemas/User0.1.0.json"])

    def test_load_context_files_missing_raises_error(self):
        """Test that missing context files raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError) as cm:
            TaskLoader.load_context_files(self.temp_dir, ["nonexistent.md"])
        self.assertIn("Required context files not found", str(cm.exception))
        self.assertIn("nonexistent.md", str(cm.exception))

    def test_load_context_files_none(self):
        """Test that None context_paths raises ValueError with helpful message."""
        with self.assertRaises(ValueError) as cm:
            TaskLoader.load_context_files(self.temp_dir, None)
        self.assertIn("context_paths cannot be None", str(cm.exception))
        self.assertIn("context:", str(cm.exception))

    def test_load_context_files_invalid_type(self):
        """Test that non-list context_paths raises TypeError with helpful message."""
        with self.assertRaises(TypeError) as cm:
            TaskLoader.load_context_files(self.temp_dir, "not a list")
        self.assertIn("must be a list", str(cm.exception))
        self.assertIn("str", str(cm.exception))

    def test_load_repo_files_with_variables(self):
        """Test loading repo files with variable substitution."""
        # Create test files
        test_data_dir = os.path.join(self.temp_dir, "test_data")
        os.makedirs(test_data_dir)
        test_file = os.path.join(test_data_dir, "User0.1.0.json")
        with open(test_file, "w") as f:
            f.write('[{"id": 1}]')

        variables = {"COLLECTION": "User", "VERSION": "0.1.0"}
        repo_files = TaskLoader.load_repo_files(
            self.temp_dir,
            ["/test_data/{COLLECTION}{VERSION}.json"],
            variables
        )
        self.assertIn("repo:/test_data/User0.1.0.json", repo_files)
        self.assertIn('"id": 1', repo_files["repo:/test_data/User0.1.0.json"])

    def test_load_repo_files_missing_raises_error(self):
        """Test that missing repo files raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError) as cm:
            TaskLoader.load_repo_files(self.temp_dir, ["nonexistent.py"])
        self.assertIn("Required repository files not found", str(cm.exception))
        self.assertIn("nonexistent.py", str(cm.exception))

    def test_load_repo_files_none(self):
        """Test that None repo_paths raises ValueError with helpful message."""
        with self.assertRaises(ValueError) as cm:
            TaskLoader.load_repo_files(self.temp_dir, None)
        self.assertIn("repo_paths cannot be None", str(cm.exception))
        self.assertIn("repo:", str(cm.exception))

    def test_load_repo_files_invalid_type(self):
        """Test that non-list repo_paths raises TypeError with helpful message."""
        with self.assertRaises(TypeError) as cm:
            TaskLoader.load_repo_files(self.temp_dir, {"not": "a list"})
        self.assertIn("must be a list", str(cm.exception))
        self.assertIn("dict", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
