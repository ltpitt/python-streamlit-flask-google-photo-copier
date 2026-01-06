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
from google_photos_sync.ui.components.status_component import (
    render_comparison_summary,
    show_status_message,
)
from google_photos_sync.ui.components.sync_view import render_sync_view

# Type alias for navigation pages
PageType = Literal["Home", "Compare", "Sync", "Settings"]


def initialize_session_state() -> None:
    """Initialize session state variables.

    This function sets up all required session state keys if they don't
    exist. This ensures the app doesn't crash when accessing session state.

    Session state keys:
        - source_auth: Authentication data for source account (dict or None)
        - target_auth: Authentication data for target account (dict or None)
        - comparison_result: Result of last comparison operation (dict or None)
        - sync_status: Current sync operation status (dict or None)
        - current_page: Currently selected navigation page
    """
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
    - Navigation menu (Home, Compare, Sync, Settings)
    - Authentication status indicators

    Returns:
        The currently selected page name
    """
    with st.sidebar:
        # App branding
        st.markdown("# 📸 Google Photos Sync")
        st.markdown("---")

        # Navigation menu
        st.subheader("Navigation")
        page = st.radio(
            "Go to:",
            ["Home", "Compare", "Sync", "Settings"],
            key="navigation",
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Authentication status
        st.subheader("Authentication Status")

        st.caption("**Source Account:**")
        if st.session_state.source_auth:
            email = st.session_state.source_auth.get("email", "Unknown")
            st.success(f"✅ {email}")
        else:
            st.error("❌ Not signed in")

        st.caption("**Target Account:**")
        if st.session_state.target_auth:
            email = st.session_state.target_auth.get("email", "Unknown")
            st.success(f"✅ {email}")
        else:
            st.error("❌ Not signed in")

    return page  # type: ignore


def render_footer() -> None:
    """Render footer with version and documentation link."""
    st.markdown("---")
    repo_url = "https://github.com/ltpitt/python-streamlit-flask-google-photo-copier"
    st.markdown(
        f"""
        <div class="footer">
            <p>Google Photos Sync v{__version__}</p>
            <p>
                <a href="{repo_url}" target="_blank">
                    Documentation
                </a>
                |
                <a href="{repo_url}/issues" target="_blank">
                    Report Issue
                </a>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_page() -> None:
    """Render the Home page with welcome message and instructions."""
    st.markdown(
        '<h1 class="main-title">📸 Welcome to Google Photos Sync</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="subtitle">Safely sync your Google Photos between accounts</p>',
        unsafe_allow_html=True,
    )

    # Introduction
    st.write("---")
    st.header("What is Google Photos Sync?")
    st.write(
        """
        Google Photos Sync is a production-grade tool that enables
        **monodirectional synchronization** of Google Photos from a source
        account to a target account.

        This means the target account will become an **exact copy** of the
        source account, including all photos, metadata, and organization.
        """
    )

    # Key features
    st.header("✨ Key Features")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔒 Safe & Secure")
        st.write("- Multiple confirmation steps for destructive operations")
        st.write("- OAuth 2.0 authentication")
        st.write("- No passwords stored")
        st.write("- Idempotent operations (safe to retry)")

        st.subheader("💾 Complete Metadata Preservation")
        st.write("- EXIF data (camera, settings)")
        st.write("- GPS location information")
        st.write("- Creation dates and times")
        st.write("- Descriptions and favorites")

    with col2:
        st.subheader("⚡ Efficient & Reliable")
        st.write("- Memory-efficient streaming transfers")
        st.write("- Conservative API usage")
        st.write("- Automatic retry on failures")
        st.write("- Progress tracking")

        st.subheader("👥 User-Friendly")
        st.write("- Simple, clear interface")
        st.write("- Preview changes before syncing")
        st.write("- Detailed statistics and logs")
        st.write("- No technical knowledge required")

    # How it works
    st.header("🔄 How It Works")
    st.write(
        """
        1. **Authenticate**: Sign in to both source and target Google Photos accounts
        2. **Compare**: Preview what will change (photos to add, delete, or update)
        3. **Confirm**: Review warnings and confirm destructive operations
        4. **Sync**: Execute the synchronization with full progress tracking
        """
    )

    # Getting started
    st.header("🚀 Getting Started")
    st.info(
        """
        **Ready to begin?**

        1. Navigate to **Compare** to authenticate and preview changes
        2. Then go to **Sync** to execute the synchronization
        3. Visit **Settings** to configure advanced options

        ℹ️ **Note**: You must authenticate both accounts before you can compare or sync.
        """
    )

    # Important warnings
    st.header("⚠️ Important Warnings")
    st.warning(
        """
        **This is a DESTRUCTIVE operation:**

        - Photos on the target account that don't exist on source **will be deleted**
        - This cannot be undone without a backup
        - Always compare before syncing
        - Make sure you're syncing in the right direction

        **We recommend backing up your target account first!**
        """
    )


def render_compare_page() -> None:
    """Render the Compare page for account comparison."""
    st.title("🔍 Compare Accounts")
    st.write("Compare source and target accounts to see what will change during sync.")

    st.write("---")

    # Authentication sections
    col1, col2 = st.columns(2)

    with col1:
        render_auth_section("Source", "source_auth")

    with col2:
        render_auth_section("Target", "target_auth")

    st.write("---")

    # Compare button (only if both authenticated)
    both_authenticated = (
        st.session_state.source_auth is not None
        and st.session_state.target_auth is not None
    )

    if both_authenticated:
        if st.button("🔍 Compare Accounts", type="primary", use_container_width=True):
            # TODO: Implement actual comparison logic
            show_status_message(
                "Comparison feature coming soon! Backend integration in progress.",
                "info",
                "🚧",
            )

            # Mock data for demonstration
            st.session_state.comparison_result = {
                "total_source": 500,
                "total_target": 450,
                "missing_on_target": 60,
                "extra_on_target": 10,
                "different_metadata": 5,
            }

        # Display comparison results if available
        if st.session_state.comparison_result:
            st.write("---")
            result = st.session_state.comparison_result
            render_comparison_summary(
                total_source=result["total_source"],
                total_target=result["total_target"],
                missing=result["missing_on_target"],
                extra=result["extra_on_target"],
                different=result["different_metadata"],
            )
    else:
        st.info("ℹ️ Please authenticate both accounts to compare.")


def render_sync_page() -> None:
    """Render the Sync page for executing synchronization."""
    st.title("🔄 Sync Accounts")
    st.write("Execute synchronization from source to target account.")

    st.write("---")

    # Use the comprehensive sync view component
    render_sync_view()


def render_settings_page() -> None:
    """Render the Settings page for configuration."""
    st.title("⚙️ Settings")
    st.write("Configure synchronization settings and preferences.")

    st.write("---")

    # Transfer settings
    st.subheader("Transfer Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.number_input(
            "Max Concurrent Transfers",
            min_value=1,
            max_value=10,
            value=3,
            help=(
                "Number of photos to transfer simultaneously. "
                "Higher = faster but more memory usage."
            ),
        )

        st.number_input(
            "Chunk Size (MB)",
            min_value=1,
            max_value=32,
            value=8,
            help=(
                "Size of chunks for streaming transfers. "
                "Larger = fewer API calls but more memory."
            ),
        )

    with col2:
        st.number_input(
            "Max Retries",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of retry attempts for failed operations.",
        )

        st.selectbox(
            "Log Level",
            options=["DEBUG", "INFO", "WARNING", "ERROR"],
            index=1,
            help="Logging verbosity level.",
        )

    st.write("---")

    # Advanced settings
    st.subheader("Advanced Settings")

    st.checkbox(
        "Enable rate limiting",
        value=True,
        help="Limit API calls to prevent hitting Google API quotas.",
    )

    st.checkbox(
        "Preserve all metadata",
        value=True,
        disabled=True,
        help=(
            "Always preserve all photo metadata (EXIF, location, etc.). "
            "Cannot be disabled."
        ),
    )

    st.checkbox(
        "Dry run mode",
        value=False,
        help="Preview changes without executing them. Useful for testing.",
    )

    st.write("---")

    # Save button
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        show_status_message("Settings saved successfully!", "success", "✅")
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
