"""OAuth authentication UI component for Streamlit.

This module provides reusable UI components for handling Google OAuth
authentication flow in the Streamlit interface. Components are designed
as pure functions following clean code principles.
"""

import streamlit as st


def render_auth_section(account_type: str, session_key: str) -> None:
    """Render OAuth authentication section for source or target account.

    This component displays the authentication status and provides
    controls for logging in/out of Google Photos accounts.

    Args:
        account_type: Type of account ("Source" or "Target")
        session_key: Session state key for storing auth data
                    (e.g., "source_auth" or "target_auth")

    Example:
        >>> render_auth_section("Source", "source_auth")
    """
    st.subheader(f"{account_type} Account")

    # Check if already authenticated
    if session_key in st.session_state and st.session_state[session_key]:
        auth_data = st.session_state[session_key]
        email = auth_data.get("email", "Unknown")

        st.success(f"✅ Authenticated as: **{email}**")

        if st.button(f"Sign out from {account_type}", key=f"signout_{session_key}"):
            # Clear authentication from session state
            st.session_state[session_key] = None
            st.rerun()
    else:
        st.info("ℹ️ Not authenticated. Please sign in to continue.")

        if st.button(
            f"🔐 Sign in with Google ({account_type})", key=f"signin_{session_key}"
        ):
            st.warning("🚧 OAuth flow not yet implemented - Coming soon!")
            # TODO: Implement OAuth flow when backend is ready
            # This will redirect to /api/auth/google endpoint


def render_auth_status_badge(session_key: str) -> None:
    """Render compact authentication status badge.

    Displays a simple badge showing whether an account is authenticated.
    Useful for sidebar or header status indicators.

    Args:
        session_key: Session state key for auth data
                    (e.g., "source_auth" or "target_auth")

    Example:
        >>> render_auth_status_badge("source_auth")
    """
    if session_key in st.session_state and st.session_state[session_key]:
        auth_data = st.session_state[session_key]
        email = auth_data.get("email", "Unknown")
        st.success(f"✅ {email}")
    else:
        st.error("❌ Not authenticated")
