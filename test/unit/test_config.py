"""Tests for configuration management."""
import unittest
import os
import sys
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from config import Config


class TestConfig(unittest.TestCase):
    """Tests for Config class."""

    def setUp(self):
        """Set up test environment."""
        # Clear environment variables
        env_vars_to_clear = [
            "REPO_ROOT", "CONTEXT_ROOT", "LOG_LEVEL", "TRACKING_BREADCRUMB",
            "LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL", "LLM_API_KEY",
            "LLM_TEMPERATURE", "LLM_MAX_TOKENS"
        ]
        for key in env_vars_to_clear:
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        """Clean up after tests."""
        # Clear environment variables
        env_vars_to_clear = [
            "REPO_ROOT", "CONTEXT_ROOT", "LOG_LEVEL", "TRACKING_BREADCRUMB",
            "LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL", "LLM_API_KEY",
            "LLM_TEMPERATURE", "LLM_MAX_TOKENS"
        ]
        for key in env_vars_to_clear:
            if key in os.environ:
                del os.environ[key]

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = Config()
        self.assertEqual(config.REPO_ROOT, "/workspace/repo")
        self.assertEqual(config.CONTEXT_ROOT, "/workspace/context")
        self.assertEqual(config.LOG_LEVEL, logging.INFO)
        self.assertEqual(config.LLM_PROVIDER, "null")
        self.assertEqual(config.LLM_MODEL, "codellama")
        self.assertEqual(config.LLM_BASE_URL, "http://localhost:11434")
        self.assertEqual(config.LLM_TEMPERATURE, 7)
        self.assertEqual(config.LLM_MAX_TOKENS, 8192)

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        os.environ["REPO_ROOT"] = "/custom/repo"
        os.environ["LLM_PROVIDER"] = "ollama"
        os.environ["LLM_MODEL"] = "llama3"
        os.environ["LLM_TEMPERATURE"] = "8"
        os.environ["LLM_MAX_TOKENS"] = "4096"
        
        config = Config()
        
        self.assertEqual(config.REPO_ROOT, "/custom/repo")
        self.assertEqual(config.LLM_PROVIDER, "ollama")
        self.assertEqual(config.LLM_MODEL, "llama3")
        self.assertEqual(config.LLM_TEMPERATURE, 8)
        self.assertEqual(config.LLM_MAX_TOKENS, 4096)

    def test_config_items_tracking(self):
        """Test that config_items tracks all configuration values."""
        config = Config()
        self.assertGreater(len(config.config_items), 0)
        
        # Check that all config values are tracked
        config_names = [item["name"] for item in config.config_items]
        self.assertIn("REPO_ROOT", config_names)
        self.assertIn("LLM_PROVIDER", config_names)
        self.assertIn("LLM_TEMPERATURE", config_names)

    def test_secret_masking(self):
        """Test that secrets are masked in config_items."""
        os.environ["LLM_API_KEY"] = "secret-key-123"
        config = Config()
        
        api_key_item = next(item for item in config.config_items if item["name"] == "LLM_API_KEY")
        self.assertEqual(api_key_item["value"], "secret")
        self.assertEqual(config.LLM_API_KEY, "secret-key-123")  # Actual value is accessible

    def test_get_llm_temperature_as_float(self):
        """Test that get_llm_temperature returns float value."""
        os.environ["LLM_TEMPERATURE"] = "7"
        config = Config()
        
        temp = config.get_llm_temperature()
        self.assertIsInstance(temp, float)
        self.assertEqual(temp, 0.7)

    def test_get_default(self):
        """Test get_default method."""
        config = Config()
        self.assertEqual(config.get_default("REPO_ROOT"), "/workspace/repo")
        # get_default returns int for config_ints values (converted from string)
        self.assertEqual(config.get_default("LLM_TEMPERATURE"), 7)
        self.assertEqual(config.get_default("LLM_MAX_TOKENS"), 8192)
        self.assertIsNone(config.get_default("NONEXISTENT"))

    def test_logging_configuration(self):
        """Test that logging is configured."""
        config = Config()
        
        # Check that root logger level is set
        self.assertEqual(logging.root.level, config.LOG_LEVEL)

    def test_log_level_from_env(self):
        """Test that LOG_LEVEL environment variable is respected."""
        os.environ["LOG_LEVEL"] = "DEBUG"
        config = Config()
        
        self.assertEqual(config.LOG_LEVEL, logging.DEBUG)
        self.assertEqual(logging.root.level, logging.DEBUG)


if __name__ == "__main__":
    unittest.main()
