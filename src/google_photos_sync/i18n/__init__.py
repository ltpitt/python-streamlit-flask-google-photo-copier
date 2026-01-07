"""Internationalization (i18n) module for Google Photos Sync.

This module provides multilingual support following industry best practices:
- JSON-based translation files for easy maintenance
- Language-agnostic translation service
- Session-based language persistence
- Extensible architecture for adding new languages

Supported languages:
- English (en) - Default
- Italian (it)

Usage:
    >>> from google_photos_sync.i18n import get_translator
    >>> t = get_translator("it")
    >>> t("home.title")
    'Benvenuto in Google Photos Sync'

    >>> # In Streamlit app
    >>> import streamlit as st
    >>> from google_photos_sync.i18n import get_translator
    >>>
    >>> lang = st.session_state.get("language", "en")
    >>> t = get_translator(lang)
    >>> st.title(t("home.title"))
"""

from google_photos_sync.i18n.translator import (
    get_available_languages,
    get_translator,
)

__all__ = ["get_translator", "get_available_languages"]
