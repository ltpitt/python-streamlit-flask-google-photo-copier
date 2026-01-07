"""Language selector component for Streamlit UI.

This module provides a reusable language selector widget that allows users
to switch between available languages. The selected language is persisted
in Streamlit's session state.

Following clean code principles and KISS approach, this component is
simple, focused, and easy to integrate into the Streamlit app.

Example:
    >>> from google_photos_sync.ui.components.language_selector import (
    ...     render_language_selector
    ... )
    >>> 
    >>> # In sidebar or main content
    >>> render_language_selector()
"""

import streamlit as st

from google_photos_sync.i18n import get_available_languages, get_translator


def render_language_selector() -> None:
    """Render language selector widget in Streamlit.
    
    This component displays a selectbox for choosing the UI language.
    The selected language is stored in session state and persists
    across page reloads and navigation.
    
    The component automatically:
    - Initializes language to "en" if not set
    - Displays language names in both English and native form
    - Triggers app rerun when language changes
    - Persists selection in session state
    
    Example:
        >>> # In sidebar
        >>> with st.sidebar:
        ...     render_language_selector()
        
        >>> # In main content
        >>> render_language_selector()
    """
    # Initialize language in session state if not present
    if "language" not in st.session_state:
        st.session_state.language = "en"
    
    # Get available languages
    available_languages = get_available_languages()
    
    # Language display names (in both English and native)
    language_names = {
        "en": "🇬🇧 English",
        "it": "🇮🇹 Italiano",
    }
    
    # Get translator for current language (for the label)
    t = get_translator(st.session_state.language)
    
    # Create selectbox
    selected_language = st.selectbox(
        label=t("language.selector_label"),
        options=available_languages,
        format_func=lambda lang: language_names.get(lang, lang),
        index=available_languages.index(st.session_state.language),
        key="language_selector_widget",
    )
    
    # Update session state if language changed
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        # Trigger rerun to update all UI text
        st.rerun()


def get_current_language() -> str:
    """Get the current language from session state.
    
    This is a utility function to safely get the current language,
    with fallback to English if not set.
    
    Returns:
        Current language code (e.g., "en", "it")
        
    Example:
        >>> current_lang = get_current_language()
        >>> print(current_lang)
        'en'
    """
    if "language" not in st.session_state:
        st.session_state.language = "en"
    
    return st.session_state.language  # type: ignore


def get_current_translator() -> "Translator":  # type: ignore # noqa: F821
    """Get translator instance for current language.
    
    This is a convenience function that combines get_current_language()
    and get_translator() into a single call.
    
    Returns:
        Translator instance for current language
        
    Example:
        >>> t = get_current_translator()
        >>> st.title(t("home.title"))
    """
    current_lang = get_current_language()
    return get_translator(current_lang)
