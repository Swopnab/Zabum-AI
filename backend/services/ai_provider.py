"""
AI Provider Interface and Implementations for Zabum AI
Allows pluggable AI backends (Ollama, Cloudflare, OpenAI, etc.) with local-first defaults.
"""

from abc import ABC, abstractmethod
import requests
import json
import logging
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_EMBED_MODEL

logger = logging.getLogger(__name__)

class BaseAIProvider(ABC):
    """Abstract interface for AI inference providers"""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = None, options: dict = None) -> str:
        pass

    @abstractmethod
    def chat(self, messages: list, options: dict = None) -> str:
        pass

    @abstractmethod
    def get_embedding(self, text: str) -> list:
        pass

    @abstractmethod
    def is_available(self) -> tuple[bool, str]:
        pass


class OllamaProvider(BaseAIProvider):
    """Local Ollama provider implementation"""

    def __init__(self, base_url=OLLAMA_BASE_URL, model_name=OLLAMA_MODEL, embed_model=OLLAMA_EMBED_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.embed_model = embed_model
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        self.embed_url = f"{self.base_url}/api/embeddings"
        self.tags_url = f"{self.base_url}/api/tags"

    def is_available(self) -> tuple[bool, str]:
        """Check if Ollama server is running and model is present"""
        try:
            res = requests.get(self.tags_url, timeout=3)
            if res.status_code == 200:
                data = res.json()
                models = [m.get("name") for m in data.get("models", [])]
                # Check if model or tag matches
                has_model = any(self.model_name in m for m in models)
                if has_model:
                    return True, f"Ollama online with {self.model_name}"
                else:
                    available = ", ".join(models) if models else "none"
                    return True, f"Ollama online, but model '{self.model_name}' not downloaded (Available: {available}). Run 'ollama pull {self.model_name}'."
            return False, f"Ollama responded with HTTP {res.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to Ollama. Make sure 'ollama serve' is running on http://localhost:11434"
        except Exception as e:
            return False, f"Ollama check failed: {str(e)}"

    def generate(self, prompt: str, system_prompt: str = None, options: dict = None) -> str:
        """Generate response using Ollama /api/generate"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": options or {"temperature": 0.5}
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(self.generate_url, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                raise Exception(f"Ollama returned HTTP {response.status_code}: {response.text}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Ollama is not running. Please start Ollama in your terminal: 'ollama serve' and run 'ollama pull llama3.2'."
            )
        except Exception as e:
            raise Exception(f"AI Generation Error: {str(e)}")

    def chat(self, messages: list, options: dict = None) -> str:
        """Execute chat turn using Ollama /api/chat"""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": options or {"temperature": 0.5}
        }
        try:
            response = requests.post(self.chat_url, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                msg = result.get("message", {})
                return msg.get("content", "").strip()
            else:
                raise Exception(f"Ollama returned HTTP {response.status_code}: {response.text}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Ollama is not reachable at http://localhost:11434. Start it with 'ollama serve' and ensure model 'llama3.2' is downloaded."
            )
        except Exception as e:
            raise Exception(f"AI Chat Error: {str(e)}")

    def get_embedding(self, text: str) -> list:
        """Fetch embedding vector from Ollama"""
        if not text or not text.strip():
            return []
        
        # Try embed model first, fall back to chat model
        models_to_try = [self.embed_model, self.model_name]
        for model in models_to_try:
            try:
                payload = {
                    "model": model,
                    "prompt": text
                }
                res = requests.post(self.embed_url, json=payload, timeout=10)
                if res.status_code == 200:
                    emb = res.json().get("embedding")
                    if emb:
                        return emb
            except Exception:
                continue
        return []


class MockProvider(BaseAIProvider):
    """Fallback Mock Provider for development, testing, and offline modes"""

    def is_available(self) -> tuple[bool, str]:
        return True, "Mock Provider (Offline Demo Mode)"

    def generate(self, prompt: str, system_prompt: str = None, options: dict = None) -> str:
        return f"[Zabum AI Offline Demo]: Received prompt with {len(prompt)} characters. (Connect Ollama for full Llama 3.2 inference)."

    def chat(self, messages: list, options: dict = None) -> str:
        last_msg = messages[-1]["content"] if messages else ""
        return (
            f"Hello! I am **Zabum AI** (Offline Demo Mode).\n\n"
            f"I received your message: *\"{last_msg}\"*\n\n"
            f"To enable local intelligence with Llama 3.2:\n"
            f"1. Run `ollama serve`\n"
            f"2. Run `ollama pull llama3.2`"
        )

    def get_embedding(self, text: str) -> list:
        return []


_current_provider = None

def get_ai_provider() -> BaseAIProvider:
    """Singleton getter for current AI provider"""
    global _current_provider
    if _current_provider is None:
        _current_provider = OllamaProvider()
    return _current_provider
