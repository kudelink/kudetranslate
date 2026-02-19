import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('models', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting models: {e}")
            return []

    def check_model_exists(self, model_name: str) -> bool:
        """Check if a model exists."""
        models = self.get_models()
        return any(m.get('name', '').startswith(model_name) for m in models)

    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate completion from model."""
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream,
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating: {e}")
            raise Exception(f"Failed to generate: {str(e)}")

    def generate_stream(self, model: str, prompt: str, temperature: float = 0.3, max_tokens: int = 2048, top_p: float = 0.9):
        """Generate completion with streaming."""
        import json

        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": True,
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=120
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    yield data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating stream: {e}")
            raise Exception(f"Failed to generate: {str(e)}")

    def download_model(self, model_name: str) -> bool:
        """Download a model and wait for completion."""
        import time

        try:
            # Try the new API format first (Ollama 0.1.20+)
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=600
            )

            if response.status_code == 404:
                # Fallback to older API format
                response = self.session.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name, "stream": False},
                    timeout=600
                )

            response.raise_for_status()

            # Poll to check if model is now available
            for _ in range(30):  # Wait up to 60 seconds
                time.sleep(2)
                if self.check_model_exists(model_name):
                    logger.info(f"Model {model_name} downloaded successfully")
                    return True

            return True  # Assume success if no error during pull

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading model: {e}")
            return False
