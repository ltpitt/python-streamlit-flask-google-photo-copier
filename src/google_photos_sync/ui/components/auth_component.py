"""OAuth authentication UI component for Streamlit.

This module provides reusable UI components for handling Google OAuth
authentication flow in the Streamlit interface. Components are designed
as pure functions following clean code principles.
"""

import logging
import webbrowser
from typing import Optional

import requests
import streamlit as st

from google_photos_sync.ui.components.language_selector import get_current_translator

logger = logging.getLogger(__name__)


def _get_api_base_url() -> str:
    """Get the base URL for the Flask API.

    Returns:
        Base URL for API endpoints

    Note:
        This reads from environment variable API_BASE_URL or uses default
        http://localhost:5000
    """
    import os

    return os.getenv("API_BASE_URL", "http://localhost:5000")


def _initiate_oauth_flow(account_type: str) -> Optional[tuple[str, str]]:
    """Initiate OAuth flow by calling Flask API.

    Args:
        account_type: Type of account ("source" or "target")

    Returns:
        Tuple of (authorization_url, state) if successful, None otherwise
    """
    try:
        api_url = f"{_get_api_base_url()}/api/auth/google"

        response = requests.post(
            api_url, json={"account_type": account_type.lower()}, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return (
                    data["data"]["authorization_url"],
                    data["data"]["state"],
                )

        logger.error(f"OAuth initiation failed: {response.text}")
        return None

    except requests.RequestException as e:
        logger.error(f"Failed to connect to API: {e}")
        return None


def _check_auth_status(account_type: str) -> Optional[dict]:
    """Check if account is already authenticated by querying API.

    Args:
        account_type: Type of account ("source" or "target")

    Returns:
        Dict with auth info if authenticated, None otherwise
    """
    try:
        api_url = f"{_get_api_base_url()}/api/auth/status"
        response = requests.get(
            api_url, params={"account_type": account_type.lower()}, timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data", {}).get("authenticated"):
                return {
                    "email": data["data"]["email"],
                    "account_type": account_type.lower(),
                    "authenticated": True,
                }
        return None
    except Exception as e:
        logger.debug(f"Auth status check failed: {e}")
        return None


def _handle_oauth_callback(
    account_type: str, session_key: str, email: str, auth_code: str, state: str
) -> None:
    """Handle OAuth callback by exchanging auth code for credentials.

    Args:
        account_type: Type of account ("Source" or "Target")
        session_key: Session state key for storing auth data
        email: User email address
        auth_code: Authorization code from OAuth flow
        state: OAuth state parameter for validation
    """
    t = get_current_translator()

    try:
        callback_url = f"{_get_api_base_url()}/api/auth/callback"
        callback_params = {
            "code": auth_code,
            "state": state,
            "account_type": account_type.lower(),
            "account_email": email,
        }

        callback_response = requests.get(
            callback_url, params=callback_params, timeout=15
        )

        if callback_response.status_code == 200:
            callback_data = callback_response.json()
            if callback_data.get("success"):
                # Save auth data to session state
                st.session_state[session_key] = {
                    "email": email,
                    "account_type": account_type.lower(),
                    "authenticated": True,
                }
                st.success(t("auth.authentication_success", email=email))
                st.rerun()
            else:
                error_msg = callback_data.get("error", "Unknown error")
                st.error(t("auth.authentication_failed", error=error_msg))
        else:
            st.error(t("auth.authentication_failed", error=callback_response.text))

    except requests.RequestException as e:
        logger.error(f"Callback request failed: {e}")
        st.error(t("auth.api_connection_error", error=str(e)))


def _render_oauth_form(account_type: str, session_key: str, state: str) -> None:
    """Render the OAuth manual entry form.

    Args:
        account_type: Type of account ("Source" or "Target")
        session_key: Session state key for storing auth data
        state: OAuth state parameter for validation
    """
    t = get_current_translator()

    st.markdown("---")
    st.subheader(t("auth.manual_callback_title"))

    with st.form(key=f"auth_code_form_{session_key}"):
        email = st.text_input(
            t("auth.email_label"),
            placeholder="user@example.com",
            key=f"email_input_{session_key}",
        )

        auth_code = st.text_input(
            t("auth.code_label"),
            placeholder=t("auth.code_placeholder"),
            key=f"code_input_{session_key}",
        )

        submitted = st.form_submit_button(t("auth.complete_button"))

        if submitted and email and auth_code:
            _handle_oauth_callback(account_type, session_key, email, auth_code, state)


def _render_sign_in_flow(account_type: str, session_key: str) -> None:
    """Render the sign-in OAuth flow UI.

    Args:
        account_type: Type of account ("Source" or "Target")
        session_key: Session state key for storing auth data
    """
    t = get_current_translator()

    st.info(t("auth.sign_in_info"))

    if st.button(
        t("auth.sign_in_button", account_type=account_type),
        key=f"signin_{session_key}",
    ):
        with st.spinner(t("auth.initiating_oauth")):
            result = _initiate_oauth_flow(account_type)

            if result:
                auth_url, state = result
                st.session_state[f"{session_key}_oauth_state"] = state

                st.info(t("auth.oauth_instructions"))
                st.markdown(
                    f"[{t('auth.click_to_authenticate')}]({auth_url})",
                    unsafe_allow_html=False,
                )

                # Auto-open browser
                try:
                    webbrowser.open(auth_url)
                    st.success(t("auth.browser_opened"))
                except Exception as e:
                    logger.warning(f"Could not auto-open browser: {e}")
                    st.warning(t("auth.browser_manual"))

                _render_oauth_form(account_type, session_key, state)
            else:
                st.error(t("auth.oauth_init_failed"))


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
    t = get_current_translator()

    st.subheader(f"{account_type} {t('auth.status_title')}")

    # Check if already authenticated (first check session, then API)
    if session_key not in st.session_state or not st.session_state[session_key]:
        auth_status = _check_auth_status(account_type)
        if auth_status:
            st.session_state[session_key] = auth_status

    # Render authenticated or sign-in UI
    if session_key in st.session_state and st.session_state[session_key]:
        auth_data = st.session_state[session_key]
        email = auth_data.get("email", "Unknown")

        st.success(t("auth.authenticated_as", email=f"**{email}**"))

        if st.button(
            t("auth.sign_out_button", account_type=account_type),
            key=f"signout_{session_key}",
        ):
            st.session_state[session_key] = None
            st.rerun()
    else:
        _render_sign_in_flow(account_type, session_key)


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
    t = get_current_translator()

    if session_key in st.session_state and st.session_state[session_key]:
        auth_data = st.session_state[session_key]
        email = auth_data.get("email", "Unknown")
        st.success(f"✅ {email}")
    else:
        st.error(f"❌ {t('auth.not_authenticated')}")
