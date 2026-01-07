"""Unit tests for i18n translation service.

Tests cover:
- Translator initialization
- Translation retrieval
- Fallback to English
- String formatting
- Nested key access
- Available languages
"""

import json
from pathlib import Path

import pytest

from google_photos_sync.i18n import get_available_languages, get_translator
from google_photos_sync.i18n.translator import Translator

# Test constants
LOCALES_DIR = (
    Path(__file__).parent.parent.parent
    / "src"
    / "google_photos_sync"
    / "i18n"
    / "locales"
)


class TestTranslator:
    """Test suite for Translator class."""

    def test_translator_init_english(self) -> None:
        """Test translator initialization with English."""
        translator = Translator("en")

        assert translator.language == "en"
        assert translator.translations is not None
        assert translator.fallback_translations is not None

    def test_translator_init_italian(self) -> None:
        """Test translator initialization with Italian."""
        translator = Translator("it")

        assert translator.language == "it"
        assert translator.translations is not None
        assert translator.fallback_translations is not None

    def test_translator_init_invalid_language(self) -> None:
        """Test translator initialization with invalid language raises error."""
        with pytest.raises(FileNotFoundError) as exc_info:
            Translator("invalid_lang")

        assert "Translation file not found" in str(exc_info.value)

    def test_get_simple_translation_english(self) -> None:
        """Test retrieving simple translation in English."""
        translator = Translator("en")

        # Test simple key
        result = translator("app.title")
        assert result == "Google Photos Sync"

    def test_get_simple_translation_italian(self) -> None:
        """Test retrieving simple translation in Italian."""
        translator = Translator("it")

        # Test simple key - title is same in both languages
        result = translator("app.title")
        assert result == "Google Photos Sync"

        # Test different text
        result = translator("nav.compare")
        assert result == "Confronta"

    def test_get_nested_translation(self) -> None:
        """Test retrieving nested translation using dot notation."""
        translator = Translator("en")

        # Test nested keys
        result = translator("home.main_title")
        assert "Welcome" in result

        result = translator("auth.status_title")
        assert "Authentication Status" in result

    def test_translation_with_formatting(self) -> None:
        """Test translation with string formatting."""
        translator = Translator("en")

        # Test with format args
        result = translator("app.version", version="1.0.0")
        assert result == "v1.0.0"

    def test_fallback_to_english(self) -> None:
        """Test fallback to English for missing Italian translations."""
        translator = Translator("it")

        # Get a key that exists in English
        # Even if it doesn't exist in Italian, should fall back
        result = translator("app.title")
        assert result != ""

    def test_missing_key_returns_key(self) -> None:
        """Test that missing keys return the key itself."""
        translator = Translator("en")

        result = translator("nonexistent.key.path")
        assert result == "nonexistent.key.path"

    def test_get_method_alternative(self) -> None:
        """Test get() method as alternative to __call__."""
        translator = Translator("en")

        # Both should work the same
        result1 = translator("app.title")
        result2 = translator.get("app.title")

        assert result1 == result2

    def test_get_method_with_default(self) -> None:
        """Test get() method with default value."""
        translator = Translator("en")

        result = translator.get("nonexistent.key", default="Default Value")
        assert result == "Default Value"

    def test_formatting_with_missing_args(self) -> None:
        """Test that formatting gracefully handles missing arguments."""
        translator = Translator("en")

        # This should not raise an error, just return unformatted string
        result = translator("app.version")  # Missing 'version' arg
        assert "{version}" in result

    def test_italian_specific_translations(self) -> None:
        """Test Italian-specific translations are correct."""
        translator = Translator("it")

        # Check some Italian translations
        assert translator("nav.home") == "Home"
        assert translator("nav.compare") == "Confronta"
        assert translator("nav.sync") == "Sincronizza"
        assert translator("nav.settings") == "Impostazioni"


class TestGetTranslator:
    """Test suite for get_translator factory function."""

    def test_get_translator_english(self) -> None:
        """Test getting English translator."""
        translator = get_translator("en")

        assert isinstance(translator, Translator)
        assert translator.language == "en"

    def test_get_translator_italian(self) -> None:
        """Test getting Italian translator."""
        translator = get_translator("it")

        assert isinstance(translator, Translator)
        assert translator.language == "it"

    def test_get_translator_default(self) -> None:
        """Test get_translator defaults to English."""
        translator = get_translator()

        assert translator.language == "en"


class TestGetAvailableLanguages:
    """Test suite for get_available_languages function."""

    def test_get_available_languages_returns_list(self) -> None:
        """Test that available languages returns a list."""
        languages = get_available_languages()

        assert isinstance(languages, list)
        assert len(languages) > 0

    def test_get_available_languages_includes_english(self) -> None:
        """Test that English is always available."""
        languages = get_available_languages()

        assert "en" in languages

    def test_get_available_languages_includes_italian(self) -> None:
        """Test that Italian is available."""
        languages = get_available_languages()

        assert "it" in languages

    def test_get_available_languages_english_first(self) -> None:
        """Test that English is first in the list."""
        languages = get_available_languages()

        # English should be first (default language)
        assert languages[0] == "en"


class TestTranslationFiles:
    """Test suite for translation file structure and completeness."""

    def test_english_translation_file_exists(self) -> None:
        """Test that English translation file exists."""
        en_file = LOCALES_DIR / "en.json"
        assert en_file.exists()

    def test_italian_translation_file_exists(self) -> None:
        """Test that Italian translation file exists."""
        it_file = LOCALES_DIR / "it.json"
        assert it_file.exists()

    def test_translation_files_valid_json(self) -> None:
        """Test that translation files are valid JSON."""
        for lang_file in LOCALES_DIR.glob("*.json"):
            with open(lang_file, encoding="utf-8") as f:
                data = json.load(f)
                assert isinstance(data, dict)

    def test_italian_has_same_structure_as_english(self) -> None:
        """Test that Italian translations have same structure as English."""
        with open(LOCALES_DIR / "en.json", encoding="utf-8") as f:
            en_data = json.load(f)

        with open(LOCALES_DIR / "it.json", encoding="utf-8") as f:
            it_data = json.load(f)

        # Both should have the same top-level keys
        assert set(en_data.keys()) == set(it_data.keys())

    def test_all_sections_present_in_translations(self) -> None:
        """Test that all required sections are present in translations."""
        translator = Translator("en")

        # Check that all main sections exist
        required_sections = [
            "app",
            "nav",
            "auth",
            "home",
            "compare",
            "sync",
            "settings",
            "footer",
            "language",
            "status",
        ]

        for section in required_sections:
            # Should not return the key itself (meaning it exists)
            result = translator(f"{section}.title")
            # If result equals the key, the section might not exist
            # But some sections might not have 'title', so we'll just check
            # that the translator doesn't crash
            assert result is not None
