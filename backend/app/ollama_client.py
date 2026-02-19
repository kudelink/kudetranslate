import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

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

    def generate_stream(self, model: str, prompt: str, temperature: float = 0.3, max_tokens: int = 2048, top_p: float = 0.9, num_thread: int = 0):
        """Generate completion with streaming."""
        import json

        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "top_p": top_p,
        }
        if num_thread > 0:
            options["num_thread"] = num_thread

        payload = {
            "model": model,
            "prompt": prompt,
            "options": options,
            "stream": True,
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=(10, 300)
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
        """Download a model using streaming pull API."""
        import json as _json

        try:
            logger.info(f"Starting pull for model: {model_name}")
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name, "stream": True},
                stream=True,
                timeout=(10, 600)
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    data = _json.loads(line)
                    status = data.get('status', '')
                    total = data.get('total', 0)
                    completed = data.get('completed', 0)

                    if total > 0:
                        pct = round(completed / total * 100)
                        logger.info(f"Pulling {model_name}: {status} {pct}%")
                    elif status:
                        logger.info(f"Pulling {model_name}: {status}")

                    if data.get('error'):
                        logger.error(f"Pull error for {model_name}: {data['error']}")
                        return False

            logger.info(f"Model {model_name} pulled successfully")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading model {model_name}: {e}")
            return False
