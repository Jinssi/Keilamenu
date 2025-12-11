"""
Azure AI Translator service for multilingual menu support.
Detects browser language and translates menu items with in-memory caching.
"""
import os
from functools import lru_cache
from typing import Optional
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential

# Supported languages (ISO 639-1 codes)
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'fi': 'Finnish', 
    'sv': 'Swedish',
    'et': 'Estonian',
    'es': 'Spanish',
}

DEFAULT_LANGUAGE = 'en'

# Global client instance
_client: Optional[TextTranslationClient] = None


def get_client() -> Optional[TextTranslationClient]:
    """Get or create the translation client singleton."""
    global _client
    if _client is None:
        key = os.getenv('TRANSLATOR_KEY')
        endpoint = os.getenv('TRANSLATOR_ENDPOINT')
        region = os.getenv('TRANSLATOR_REGION', 'swedencentral')
        
        if key and endpoint:
            _client = TextTranslationClient(
                credential=AzureKeyCredential(key),
                endpoint=endpoint,
                region=region
            )
    return _client


def parse_accept_language(header: str) -> str:
    """
    Parse Accept-Language header and return best supported language.
    Example: 'fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7' -> 'fi'
    """
    if not header:
        return DEFAULT_LANGUAGE
    
    # Parse language preferences with quality values
    languages = []
    for part in header.split(','):
        part = part.strip()
        if ';q=' in part:
            lang, q = part.split(';q=')
            try:
                quality = float(q)
            except ValueError:
                quality = 1.0
        else:
            lang = part
            quality = 1.0
        
        # Extract base language code (e.g., 'fi-FI' -> 'fi')
        lang_code = lang.split('-')[0].lower()
        languages.append((lang_code, quality))
    
    # Sort by quality (highest first)
    languages.sort(key=lambda x: x[1], reverse=True)
    
    # Return first supported language
    for lang_code, _ in languages:
        if lang_code in SUPPORTED_LANGUAGES:
            return lang_code
    
    return DEFAULT_LANGUAGE


@lru_cache(maxsize=1000)
def translate_text(text: str, target_lang: str, source_lang: str = 'en') -> str:
    """
    Translate text to target language with caching.
    Returns original text if translation fails or is unavailable.
    """
    if not text or target_lang == source_lang:
        return text
    
    if target_lang not in SUPPORTED_LANGUAGES:
        return text
    
    client = get_client()
    if client is None:
        # No translator configured, return original
        return text
    
    try:
        response = client.translate(
            body=[text],
            to_language=[target_lang],
            from_language=source_lang
        )
        if response and response[0].translations:
            return response[0].translations[0].text
    except Exception as e:
        print(f"Translation error: {e}")
    
    return text


def translate_menu(menu: list, target_lang: str) -> list:
    """
    Translate all items in a menu list.
    Handles both {'label': ..., 'description': ...} and {'name': ...} formats.
    """
    if target_lang == DEFAULT_LANGUAGE:
        return menu
    
    translated = []
    for item in menu:
        new_item = dict(item)
        
        if 'label' in new_item:
            new_item['label'] = translate_text(new_item['label'], target_lang)
        if 'description' in new_item:
            new_item['description'] = translate_text(new_item['description'], target_lang)
        if 'name' in new_item:
            new_item['name'] = translate_text(new_item['name'], target_lang)
        
        translated.append(new_item)
    
    return translated


def clear_cache():
    """Clear the translation cache."""
    translate_text.cache_clear()
