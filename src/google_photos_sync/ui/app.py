"""Main Streamlit application for Google Photos Sync.

This is the entry point for the Streamlit UI. It provides a user-friendly
interface for non-technical users to sync Google Photos between accounts
with maximum safety and zero possibility of mistakes.

Run with: streamlit run src/google_photos_sync/ui/app.py
"""

from typing import Literal

import streamlit as st

from google_photos_sync import __version__
from google_photos_sync.ui.components.auth_component import render_auth_section
from google_photos_sync.ui.components.compare_view import render_compare_view
from google_photos_sync.ui.components.language_selector import (
    get_current_translator,
    render_language_selector,
)
from google_photos_sync.ui.components.status_component import show_status_message
from google_photos_sync.ui.components.sync_view import render_sync_view

# Type alias for navigation pages
PageType = Literal["Home", "Compare", "Sync", "Settings"]


def initialize_session_state() -> None:
    """Initialize session state variables.

    This function sets up all required session state keys if they don't
    exist. This ensures the app doesn't crash when accessing session state.

    Session state keys:
        - language: Current UI language (default: "en")
        - source_auth: Authentication data for source account (dict or None)
        - target_auth: Authentication data for target account (dict or None)
        - comparison_result: Result of last comparison operation (dict or None)
        - sync_status: Current sync operation status (dict or None)
        - current_page: Currently selected navigation page
    """
    # Language preference (initialize first, before other components)
    if "language" not in st.session_state:
        st.session_state.language = "en"

    # Authentication state
    if "source_auth" not in st.session_state:
        st.session_state.source_auth = None

    if "target_auth" not in st.session_state:
        st.session_state.target_auth = None

    # Comparison and sync state
    if "comparison_result" not in st.session_state:
        st.session_state.comparison_result = None

    if "sync_status" not in st.session_state:
        st.session_state.sync_status = None

    # Navigation state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"


def configure_page() -> None:
    """Configure Streamlit page settings and styling.

    Sets up page title, icon, layout, and custom CSS for professional
    appearance following clean, simple design principles.
    """
    st.set_page_config(
        page_title="Google Photos Sync",
        page_icon="📸",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": (
                "https://github.com/ltpitt/python-streamlit-flask-google-photo-copier"
            ),
            "Report a bug": (
                "https://github.com/ltpitt/"
                "python-streamlit-flask-google-photo-copier/issues"
            ),
            "About": (
                f"Google Photos Sync v{__version__}\n\n"
                "A production-grade tool for syncing Google Photos between accounts."
            ),
        },
    )

    # Custom CSS for better styling
    st.markdown(
        """
        <style>
        /* Main title styling */
        .main-title {
            font-size: 3rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 1rem;
        }

        /* Subtitle styling */
        .subtitle {
            font-size: 1.2rem;
            text-align: center;
            color: #666;
            margin-bottom: 2rem;
        }

        /* Footer styling */
        .footer {
            text-align: center;
            padding: 2rem 0 1rem 0;
            color: #666;
            font-size: 0.9rem;
            border-top: 1px solid #eee;
            margin-top: 3rem;
        }

        /* Improve button styling */
        .stButton > button {
            width: 100%;
        }

        /* Warning box styling */
        .warning-box {
            padding: 1rem;
            border-left: 4px solid #ff4b4b;
            background-color: #fff3cd;
            margin: 1rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> PageType:
    """Render sidebar navigation and return selected page.

    The sidebar contains:
    - App logo and title
    - Language selector
    - Navigation menu (Home, Compare, Sync, Settings)
    - Authentication status indicators

    Returns:
        The currently selected page name
    """
    # Get translator for current language
    t = get_current_translator()

    with st.sidebar:
        # App branding
        st.markdown(f"# {t('app.icon')} {t('app.title')}")
        st.markdown("---")

        # Language selector
        render_language_selector()
        st.markdown("---")

        # Navigation menu
        st.subheader(t("nav.label"))

        # Map display names to internal page names
        nav_options = {
            t("nav.home"): "Home",
            t("nav.compare"): "Compare",
            t("nav.sync"): "Sync",
            t("nav.settings"): "Settings",
        }

        selected_display = st.radio(
            "Go to:",
            options=list(nav_options.keys()),
            index=list(nav_options.values()).index(st.session_state.current_page)
            if st.session_state.current_page in nav_options.values()
            else 0,
            key="navigation",
            label_visibility="collapsed",
        )

        # Get internal page name from display name
        page = nav_options[selected_display]

        st.markdown("---")

        # Authentication status
        st.subheader(t("auth.status_title"))

        st.caption(f"**{t('auth.source_account')}**")
        if st.session_state.source_auth:
            email = st.session_state.source_auth.get("email", "Unknown")
            st.success(f"✅ {email}")
        else:
            st.error(f"❌ {t('auth.not_signed_in')}")

        st.caption(f"**{t('auth.target_account')}**")
        if st.session_state.target_auth:
            email = st.session_state.target_auth.get("email", "Unknown")
            st.success(f"✅ {email}")
        else:
            st.error(f"❌ {t('auth.not_signed_in')}")

    return page  # type: ignore


def render_footer() -> None:
    """Render footer with version and documentation link."""
    t = get_current_translator()

    st.markdown("---")
    repo_url = "https://github.com/ltpitt/python-streamlit-flask-google-photo-copier"
    st.markdown(
        f"""
        <div class="footer">
            <p>{t("footer.version", version=__version__)}</p>
            <p>
                <a href="{repo_url}" target="_blank">
                    {t("footer.documentation")}
                </a>
                |
                <a href="{repo_url}/issues" target="_blank">
                    {t("footer.report_issue")}
                </a>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_page() -> None:
    """Render the Home page with welcome message and instructions."""
    t = get_current_translator()

    st.markdown(
        f'<h1 class="main-title">{t("home.main_title")}</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="subtitle">{t("home.subtitle")}</p>',
        unsafe_allow_html=True,
    )

    # Introduction
    st.write("---")
    st.header(t("home.what_is_title"))
    st.write(t("home.what_is_description"))

    # Key features
    st.header(t("home.features_title"))
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(t("home.feature_safe_title"))
        st.write(t("home.feature_safe_items"))

        st.subheader(t("home.feature_metadata_title"))
        st.write(t("home.feature_metadata_items"))

    with col2:
        st.subheader(t("home.feature_efficient_title"))
        st.write(t("home.feature_efficient_items"))

        st.subheader(t("home.feature_friendly_title"))
        st.write(t("home.feature_friendly_items"))

    # How it works
    st.header(t("home.how_it_works_title"))
    st.write(t("home.how_it_works_description"))

    # Getting started
    st.header(t("home.getting_started_title"))
    st.info(t("home.getting_started_description"))

    # Important warnings
    st.header(t("home.warnings_title"))
    st.warning(t("home.warnings_description"))


def render_compare_page() -> None:
    """Render the Compare page for account comparison."""
    t = get_current_translator()

    st.title(t("compare.title"))
    st.write(t("compare.description"))

    st.write("---")

    # Authentication sections
    col1, col2 = st.columns(2)

    with col1:
        render_auth_section("Source", "source_auth")

    with col2:
        render_auth_section("Target", "target_auth")

    st.write("---")

    # Use the comprehensive compare view component
    render_compare_view(
        source_auth=st.session_state.source_auth,
        target_auth=st.session_state.target_auth,
    )


def render_sync_page() -> None:
    """Render the Sync page for executing synchronization."""
    t = get_current_translator()

    st.title(t("sync.title"))
    st.write(t("sync.description"))

    st.write("---")

    # Use the comprehensive sync view component
    render_sync_view()


def render_settings_page() -> None:
    """Render the Settings page for configuration."""
    t = get_current_translator()

    st.title(t("settings.title"))
    st.write(t("settings.description"))

    st.write("---")

    # Transfer settings
    st.subheader(t("settings.transfer_title"))

    col1, col2 = st.columns(2)

    with col1:
        st.number_input(
            t("settings.max_concurrent"),
            min_value=1,
            max_value=10,
            value=3,
            help=t("settings.max_concurrent_help"),
        )

        st.number_input(
            t("settings.chunk_size"),
            min_value=1,
            max_value=32,
            value=8,
            help=t("settings.chunk_size_help"),
        )

    with col2:
        st.number_input(
            t("settings.max_retries"),
            min_value=1,
            max_value=10,
            value=3,
            help=t("settings.max_retries_help"),
        )

        st.selectbox(
            t("settings.log_level"),
            options=["DEBUG", "INFO", "WARNING", "ERROR"],
            index=1,
            help=t("settings.log_level_help"),
        )

    st.write("---")

    # Advanced settings
    st.subheader(t("settings.advanced_title"))

    st.checkbox(
        t("settings.rate_limiting"),
        value=True,
        help=t("settings.rate_limiting_help"),
    )

    st.checkbox(
        t("settings.preserve_metadata"),
        value=True,
        disabled=True,
        help=t("settings.preserve_metadata_help"),
    )

    st.checkbox(
        t("settings.dry_run"),
        value=False,
        help=t("settings.dry_run_help"),
    )

    st.write("---")

    # Save button
    if st.button(t("settings.save_button"), type="primary", use_container_width=True):
        show_status_message(t("settings.save_success"), "success", "✅")
        # TODO: Implement actual settings persistence


def main() -> None:
    """Main application entry point.

    Sets up the Streamlit app, initializes session state, and renders
    the appropriate page based on navigation selection.
    """
    # Configure page settings
    configure_page()

    # Initialize session state
    initialize_session_state()

    # Render sidebar and get current page
    current_page = render_sidebar()

    # Render appropriate page based on navigation
    if current_page == "Home":
        render_home_page()
    elif current_page == "Compare":
        render_compare_page()
    elif current_page == "Sync":
        render_sync_page()
    elif current_page == "Settings":
        render_settings_page()

    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
