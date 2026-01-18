"""Tests for patch generator."""
import unittest
import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from patch_generator import parse_patch_response, PatchGenerator


class TestParsePatchResponse(unittest.TestCase):
    """Tests for parse_patch_response function."""

    def test_parse_valid_response(self):
        """Test parsing a valid response with commit message and patch."""
        response = """---COMMIT_MSG---
feat: add new feature

This is a test commit message.
---PATCH---
diff --git a/test.txt b/test.txt
new file mode 100644
--- /dev/null
+++ b/test.txt
@@ -0,0 +1 @@
+test content
"""
        commit_msg, patch = parse_patch_response(response)
        self.assertIn("feat: add new feature", commit_msg)
        self.assertIn("diff --git", patch)

    def test_parse_missing_blocks(self):
        """Test that missing blocks raise ValueError."""
        response = "Just some text"
        with self.assertRaises(ValueError):
            parse_patch_response(response)

    def test_parse_wrong_order(self):
        """Test that wrong order raises ValueError."""
        response = """---PATCH---
some patch
---COMMIT_MSG---
some message
"""
        with self.assertRaises(ValueError):
            parse_patch_response(response)


class TestPatchGenerator(unittest.TestCase):
    """Tests for PatchGenerator class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = PatchGenerator(self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_generate_patch_new_file(self):
        """Test generating a patch for a new file."""
        patch = self.generator.generate_patch("new.txt", "new content")
        self.assertIn("diff --git", patch)
        self.assertIn("new file mode", patch)
        self.assertIn("/dev/null", patch)
        self.assertIn("+++ b/new.txt", patch)

    def test_generate_patch_existing_file(self):
        """Test generating a patch for an existing file."""
        # Create a file first
        test_file = os.path.join(self.temp_dir, "existing.txt")
        with open(test_file, "w") as f:
            f.write("old content")

        patch = self.generator.generate_patch("existing.txt", "new content", "old content")
        self.assertIn("diff --git", patch)
        self.assertIn("--- a/existing.txt", patch)
        self.assertIn("+++ b/existing.txt", patch)


if __name__ == "__main__":
    unittest.main()
