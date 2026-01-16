"""Tests for LLM provider implementations."""
import unittest
import os
from unittest.mock import patch, Mock
from .llm_provider import NullLLMClient, OllamaClient, OpenAIClient, create_llm_client


class TestNullLLMClient(unittest.TestCase):
    """Tests for NullLLMClient."""

    def setUp(self):
        self.client = NullLLMClient()

    def test_complete_returns_mock_response(self):
        """Test that complete returns a mock response."""
        response = self.client.complete("system", "user")
        self.assertIn("---COMMIT_MSG---", response)
        self.assertIn("---PATCH---", response)


class TestOllamaClient(unittest.TestCase):
    """Tests for OllamaClient."""

    def setUp(self):
        self.client = OllamaClient("codellama", "http://localhost:11434")

    @patch('httpx.post')
    def test_complete_calls_api(self, mock_post):
        """Test that complete calls the Ollama API."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "test response"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        response = self.client.complete("system", "user")
        self.assertEqual(response, "test response")
        mock_post.assert_called_once()


class TestOpenAIClient(unittest.TestCase):
    """Tests for OpenAIClient."""

    def setUp(self):
        self.client = OpenAIClient("gpt-4", "https://api.openai.com/v1", "test-key")

    @patch('httpx.post')
    def test_complete_calls_api(self, mock_post):
        """Test that complete calls the OpenAI API."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        response = self.client.complete("system", "user")
        self.assertEqual(response, "test response")
        mock_post.assert_called_once()


class TestCreateLLMClient(unittest.TestCase):
    """Tests for create_llm_client factory."""

    def tearDown(self):
        # Clean up environment variables
        for key in ["LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL", "LLM_API_KEY"]:
            if key in os.environ:
                del os.environ[key]

    def test_create_null_client(self):
        """Test creating a null client."""
        os.environ["LLM_PROVIDER"] = "null"
        client = create_llm_client()
        self.assertIsInstance(client, NullLLMClient)

    def test_create_ollama_client(self):
        """Test creating an Ollama client."""
        os.environ["LLM_PROVIDER"] = "ollama"
        os.environ["LLM_MODEL"] = "codellama"
        client = create_llm_client()
        self.assertIsInstance(client, OllamaClient)

    def test_create_openai_client_requires_api_key(self):
        """Test that OpenAI client requires API key."""
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["LLM_MODEL"] = "gpt-4"
        with self.assertRaises(ValueError):
            create_llm_client()


if __name__ == "__main__":
    unittest.main()
