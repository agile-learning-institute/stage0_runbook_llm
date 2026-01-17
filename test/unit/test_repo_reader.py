"""Tests for repository reader."""
import unittest
import os
import sys
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from repo_reader import RepoReader


class TestRepoReader(unittest.TestCase):
    """Tests for RepoReader class."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "repo")
        os.makedirs(self.repo_dir)

    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)

    def test_read_file(self):
        """Test reading a file from repository."""
        # Create a test file
        test_file = os.path.join(self.repo_dir, "test.txt")
        test_content = "Hello, World!"
        with open(test_file, "w") as f:
            f.write(test_content)
        
        content = RepoReader.read_file(self.repo_dir, "test.txt")
        
        self.assertEqual(content, test_content)

    def test_read_file_with_leading_slash(self):
        """Test reading file with leading slash in path."""
        test_file = os.path.join(self.repo_dir, "test.txt")
        test_content = "Hello, World!"
        with open(test_file, "w") as f:
            f.write(test_content)
        
        content = RepoReader.read_file(self.repo_dir, "/test.txt")
        
        self.assertEqual(content, test_content)

    def test_read_file_nested(self):
        """Test reading a nested file."""
        nested_dir = os.path.join(self.repo_dir, "subdir")
        os.makedirs(nested_dir)
        test_file = os.path.join(nested_dir, "nested.txt")
        test_content = "Nested content"
        with open(test_file, "w") as f:
            f.write(test_content)
        
        content = RepoReader.read_file(self.repo_dir, "subdir/nested.txt")
        
        self.assertEqual(content, test_content)

    def test_read_file_not_found(self):
        """Test reading non-existent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            RepoReader.read_file(self.repo_dir, "nonexistent.txt")

    def test_list_files(self):
        """Test listing files in repository."""
        # Create multiple files
        files = ["file1.txt", "file2.txt", "file3.py"]
        for filename in files:
            filepath = os.path.join(self.repo_dir, filename)
            with open(filepath, "w") as f:
                f.write("content")
        
        listed_files = RepoReader.list_files(self.repo_dir)
        
        self.assertEqual(len(listed_files), len(files))
        for filename in files:
            self.assertIn(filename, listed_files)

    def test_list_files_with_pattern(self):
        """Test listing files with pattern filter."""
        # Create files with different extensions
        files = ["file1.txt", "file2.txt", "file3.py"]
        for filename in files:
            filepath = os.path.join(self.repo_dir, filename)
            with open(filepath, "w") as f:
                f.write("content")
        
        txt_files = RepoReader.list_files(self.repo_dir, pattern=".txt")
        
        self.assertEqual(len(txt_files), 2)
        self.assertIn("file1.txt", txt_files)
        self.assertIn("file2.txt", txt_files)
        self.assertNotIn("file3.py", txt_files)

    def test_list_files_in_directory(self):
        """Test listing files in specific directory."""
        subdir = os.path.join(self.repo_dir, "subdir")
        os.makedirs(subdir)
        
        root_file = os.path.join(self.repo_dir, "root.txt")
        sub_file = os.path.join(subdir, "sub.txt")
        
        with open(root_file, "w") as f:
            f.write("root")
        with open(sub_file, "w") as f:
            f.write("sub")
        
        subdir_files = RepoReader.list_files(self.repo_dir, "subdir")
        
        self.assertEqual(len(subdir_files), 1)
        self.assertIn("subdir/sub.txt", subdir_files)

    def test_list_files_nonexistent_directory(self):
        """Test listing files in non-existent directory returns empty list."""
        files = RepoReader.list_files(self.repo_dir, "nonexistent")
        
        self.assertEqual(files, [])

    def test_get_repo_structure(self):
        """Test getting repository structure."""
        # Create a simple structure
        subdir = os.path.join(self.repo_dir, "subdir")
        os.makedirs(subdir)
        
        file1 = os.path.join(self.repo_dir, "file1.txt")
        file2 = os.path.join(subdir, "file2.txt")
        
        with open(file1, "w") as f:
            f.write("content1")
        with open(file2, "w") as f:
            f.write("content2")
        
        structure = RepoReader.get_repo_structure(self.repo_dir)
        
        self.assertIsInstance(structure, dict)
        self.assertIn("file1.txt", structure)
        self.assertIn("subdir", structure)

    def test_get_repo_structure_with_max_depth(self):
        """Test repository structure respects max_depth."""
        # Create nested structure
        level1 = os.path.join(self.repo_dir, "level1")
        level2 = os.path.join(level1, "level2")
        os.makedirs(level2)
        
        structure = RepoReader.get_repo_structure(self.repo_dir, max_depth=1)
        
        # Level2 should not be included
        self.assertIn("level1", structure)

    def test_get_repo_structure_hides_dotfiles(self):
        """Test that dotfiles are hidden from structure."""
        dotfile = os.path.join(self.repo_dir, ".hidden")
        normal_file = os.path.join(self.repo_dir, "visible.txt")
        
        with open(dotfile, "w") as f:
            f.write("hidden")
        with open(normal_file, "w") as f:
            f.write("visible")
        
        structure = RepoReader.get_repo_structure(self.repo_dir)
        
        self.assertIn("visible.txt", structure)
        # .hidden should not be in structure
        self.assertNotIn(".hidden", structure)


if __name__ == "__main__":
    unittest.main()
