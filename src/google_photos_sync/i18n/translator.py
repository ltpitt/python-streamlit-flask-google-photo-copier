"""Translation service for multilingual support.

This module provides the core translation functionality following clean code
principles and SOLID design patterns. The Translator class is lightweight,
framework-agnostic, and easy to test.

Architecture:
- JSON files store translations (one file per language)
- Dot notation for nested keys ("home.title", "nav.settings")
- Fallback to English for missing translations
- Simple API: translator(key) returns translated string

Example:
    >>> translator = Translator("it")
    >>> translator("home.title")
    'Benvenuto in Google Photos Sync'
    
    >>> # Missing key falls back to English
    >>> translator("new.key.not.yet.translated")
    'English fallback text'
"""

import json
from pathlib import Path
from typing import Any


class Translator:
    """Translation service for multilingual support.
    
    Loads translations from JSON files and provides a simple API for
    retrieving translated strings using dot notation.
    
    Attributes:
        language: Current language code (e.g., "en", "it")
        translations: Dictionary of translations for current language
        fallback_translations: English translations for fallback
    """

    def __init__(self, language: str = "en") -> None:
        """Initialize translator with specified language.
        
        Args:
            language: Language code (e.g., "en", "it"). Defaults to "en".
        
        Raises:
            FileNotFoundError: If translation file doesn't exist
            json.JSONDecodeError: If translation file is invalid JSON
        """
        self.language = language
        self._locales_dir = Path(__file__).parent / "locales"
        
        # Load requested language
        self.translations = self._load_translations(language)
        
        # Load English as fallback (only if not already English)
        if language != "en":
            self.fallback_translations = self._load_translations("en")
        else:
            self.fallback_translations = self.translations

    def _load_translations(self, lang: str) -> dict[str, Any]:
        """Load translations from JSON file.
        
        Args:
            lang: Language code
            
        Returns:
            Dictionary of translations
            
        Raises:
            FileNotFoundError: If translation file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        file_path = self._locales_dir / f"{lang}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"Translation file not found: {file_path}. "
                f"Available languages: {get_available_languages()}"
            )
        
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)  # type: ignore

    def _get_nested_value(
        self, data: dict[str, Any], key: str, default: str = ""
    ) -> str:
        """Get value from nested dictionary using dot notation.
        
        Args:
            data: Dictionary to search
            key: Dot-separated key (e.g., "home.title")
            default: Default value if key not found
            
        Returns:
            Value from dictionary or default
            
        Example:
            >>> data = {"home": {"title": "Welcome"}}
            >>> _get_nested_value(data, "home.title")
            'Welcome'
        """
        keys = key.split(".")
        value: Any = data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return str(value) if value is not None else default

    def __call__(self, key: str, **kwargs: Any) -> str:
        """Get translated string for given key.
        
        This is the main API for retrieving translations. Supports:
        - Dot notation for nested keys
        - String formatting with kwargs
        - Fallback to English if key missing
        
        Args:
            key: Translation key in dot notation (e.g., "home.title")
            **kwargs: Optional format arguments for string interpolation
            
        Returns:
            Translated string, with fallback to English if key not found
            
        Example:
            >>> t = Translator("it")
            >>> t("home.welcome", name="Mario")
            'Benvenuto, Mario!'
        """
        # Try current language first
        translated = self._get_nested_value(self.translations, key)
        
        # Fallback to English if not found
        if not translated:
            translated = self._get_nested_value(
                self.fallback_translations, key, default=key
            )
        
        # Apply string formatting if kwargs provided
        if kwargs:
            try:
                translated = translated.format(**kwargs)
            except (KeyError, ValueError):
                # If formatting fails, return unformatted string
                pass
        
        return translated

    def get(self, key: str, default: str = "", **kwargs: Any) -> str:
        """Alternative method to get translation (same as __call__).
        
        Provides an explicit method name for those who prefer:
        translator.get("key") over translator("key")
        
        Args:
            key: Translation key
            default: Default value if key not found
            **kwargs: Format arguments
            
        Returns:
            Translated string
        """
        result = self(key, **kwargs)
        return result if result != key else default


def get_translator(language: str = "en") -> Translator:
    """Factory function to create a Translator instance.
    
    This is the recommended way to get a translator instance.
    It provides a clean API and allows for future enhancements
    (e.g., caching, singleton pattern).
    
    Args:
        language: Language code (e.g., "en", "it")
        
    Returns:
        Translator instance for the specified language
        
    Example:
        >>> t = get_translator("it")
        >>> t("home.title")
        'Benvenuto in Google Photos Sync'
    """
    return Translator(language)


def get_available_languages() -> list[str]:
    """Get list of available language codes.
    
    Scans the locales directory for .json files and returns
    their language codes.
    
    Returns:
        List of language codes (e.g., ["en", "it"])
        
    Example:
        >>> get_available_languages()
        ['en', 'it']
    """
    locales_dir = Path(__file__).parent / "locales"
    
    if not locales_dir.exists():
        return ["en"]  # Default fallback
    
    # Find all .json files and extract language codes
    languages = [
        f.stem for f in locales_dir.glob("*.json") if f.is_file()
    ]
    
    # Sort with English first
    languages.sort(key=lambda x: (x != "en", x))
    
    return languages
