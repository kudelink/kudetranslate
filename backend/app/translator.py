import logging
from .ollama_client import OllamaClient
from .prompts import build_translation_prompt

logger = logging.getLogger(__name__)


class Translator:
    """Translation service using Ollama."""

    def __init__(
        self,
        ollama_host: str,
        default_model: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        top_p: float = 0.9
    ):
        self.client = OllamaClient(ollama_host)
        self.default_model = default_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p

    def get_available_models(self):
        """Get list of available models."""
        return self.client.get_models()

    def check_model_exists(self, model_name: str) -> bool:
        """Check if model exists."""
        return self.client.check_model_exists(model_name)

    def download_model(self, model_name: str) -> bool:
        """Download a model."""
        return self.client.download_model(model_name)

    def translate_stream(self, text: str, source_lang: str, target_lang: str, model: str = None):
        """Translate text with streaming."""
        if not text or not text.strip():
            return

        model = model or self.default_model

        prompt = build_translation_prompt(text, source_lang, target_lang)

        logger.info(f"Translating with model: {model}")

        for chunk in self.client.generate_stream(
            model=model,
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p
        ):
            if 'response' in chunk:
                yield chunk
