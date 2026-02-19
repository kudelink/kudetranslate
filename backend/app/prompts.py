def build_translation_prompt(text: str, source_lang: str, target_lang: str) -> str:
    """Build the translation prompt for TranslateGemma."""

    source_name = get_language_name(source_lang)
    source_code = source_lang if source_lang != "auto" else "auto"
    target_name = get_language_name(target_lang)
    target_code = target_lang

    # TranslateGemma requires specific format with two blank lines before the text
    prompt = f"""You are a professional {source_name} ({source_code}) to {target_name} ({target_code}) translator. Your goal is to accurately convey the meaning and nuances of the original {source_name} text while adhering to {target_name} grammar, vocabulary, and cultural sensitivities. Produce only the {target_name} translation, without any additional explanations or commentary. Please translate the following {source_name} text into {target_name}:


{text}
"""

    return prompt


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
