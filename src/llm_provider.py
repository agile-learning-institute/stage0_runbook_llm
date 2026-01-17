"""LLM Provider abstraction and implementations."""
from typing import Protocol
import os
import logging

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """Protocol for LLM providers."""

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Complete a prompt and return the response."""
        ...


class NullLLMClient:
    """Null/dry-run LLM client for testing."""

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Return a mock response."""
        logger.info("NullLLMClient: Returning mock response")
        return "---COMMIT_MSG---\nfeat: mock change\n---PATCH---\ndiff --git a/test.txt b/test.txt\nnew file mode 100644\nindex 0000000..1234567\n--- /dev/null\n+++ b/test.txt\n@@ -0,0 +1 @@\n+mock content\n"


class OllamaClient:
    """Ollama LLM client implementation."""

    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/generate"

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Complete a prompt using Ollama API."""
        import httpx

        try:
            response = httpx.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                },
                timeout=300.0
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise


class OpenAIClient:
    """OpenAI-compatible LLM client implementation."""

    def __init__(self, model: str, base_url: str, api_key: str = None):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError("LLM_API_KEY required for OpenAI client")

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Complete a prompt using OpenAI-compatible API."""
        import httpx

        headers = {"Authorization": f"Bearer {self.api_key}"}
        if "openai.com" in self.base_url:
            headers["Content-Type"] = "application/json"

        try:
            response = httpx.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=300.0
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


def create_llm_client() -> LLMClient:
    """Factory function to create an LLM client based on configuration."""
    from .config import Config
    config = Config.get_instance()
    
    provider = config.LLM_PROVIDER.lower()
    model = config.LLM_MODEL
    base_url = config.LLM_BASE_URL
    api_key = config.LLM_API_KEY

    if provider == "null":
        logger.info("Using NullLLMClient (dry-run mode)")
        return NullLLMClient()
    elif provider == "ollama":
        if not base_url:
            base_url = "http://localhost:11434"
        logger.info(f"Using OllamaClient with model {model} at {base_url}")
        return OllamaClient(model, base_url)
    elif provider in ["openai", "azure"]:
        if not base_url:
            base_url = "https://api.openai.com/v1" if provider == "openai" else ""
            if not base_url:
                raise ValueError(f"LLM_BASE_URL required for {provider}")
        logger.info(f"Using OpenAIClient with model {model} at {base_url}")
        return OpenAIClient(model, base_url, api_key)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
