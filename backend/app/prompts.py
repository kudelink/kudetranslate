def build_translation_prompt(text: str, source_lang: str, target_lang: str, prompt_type: str = "translategemma") -> str:
    """Build the translation prompt based on model type."""
    source_name = get_language_name(source_lang)
    target_name = get_language_name(target_lang)

    if prompt_type == "translategemma":
        return _prompt_translategemma(text, source_lang, source_name, target_lang, target_name)

    return _prompt_generic(text, source_name, target_name)


def _prompt_translategemma(text: str, source_code: str, source_name: str, target_code: str, target_name: str) -> str:
    """TranslateGemma requires a specific verbose format with two blank lines before the text."""
    source_code = source_code if source_code != "auto" else "auto"
    return f"""You are a professional {source_name} ({source_code}) to {target_name} ({target_code}) translator. Your goal is to accurately convey the meaning and nuances of the original {source_name} text while adhering to {target_name} grammar, vocabulary, and cultural sensitivities. Produce only the {target_name} translation, without any additional explanations or commentary. Please translate the following {source_name} text into {target_name}:


{text}
"""


def _prompt_generic(text: str, source_name: str, target_name: str) -> str:
    """Generic prompt for instruction-following models like Mistral."""
    return f"""Translate the following text from {source_name} to {target_name}. Output ONLY the translation, nothing else.

{text}"""


def get_language_name(code: str) -> str:
    """Get human-readable language name from code."""
    languages = {
        "auto": "the detected language",
        "es": "Spanish",
        "en": "English",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "zh": "Chinese",
        "ja": "Japanese",
        "ru": "Russian",
        "ko": "Korean",
        "ar": "Arabic",
        "nl": "Dutch",
        "pl": "Polish",
        "tr": "Turkish",
        "vi": "Vietnamese",
        "th": "Thai",
        "sv": "Swedish",
        "da": "Danish",
        "fi": "Finnish",
        "no": "Norwegian",
        "cs": "Czech",
        "el": "Greek",
        "he": "Hebrew",
        "hu": "Hungarian",
        "id": "Indonesian",
        "ms": "Malay",
        "ro": "Romanian",
        "sk": "Slovak",
        "uk": "Ukrainian",
        "gl": "Galician",
        "ca": "Catalan",
        "eu": "Basque",
    }
    return languages.get(code, code.upper())
