"""Sync View Component - Safe Execution of Photo Synchronization.

This module provides the comprehensive sync view component with multi-level
safety warnings and confirmations before executing destructive sync operations.

Following KISS principle and user safety requirements, this component ensures
users cannot accidentally execute sync operations without fully understanding
the consequences.

Key Safety Features:
- Multiple confirmation steps
- Clear warning messages about destructive nature
- Type-to-confirm for target account
- Real-time progress tracking
- Emergency stop button
- Detailed success/failure summary

Example:
    >>> from google_photos_sync.ui.components.sync_view import render_sync_view
    >>> render_sync_view()
"""

import time
from typing import Any

import requests
import streamlit as st

from google_photos_sync.ui.components.status_component import (
    render_comparison_summary,
    render_sync_statistics,
)


def _call_sync_api(
    source_account: str, target_account: str, dry_run: bool = False
) -> dict[str, Any]:
    """Call the Flask API /api/sync endpoint to execute sync.

    Args:
        source_account: Email of source Google Photos account
        target_account: Email of target Google Photos account
        dry_run: If True, only preview changes without executing

    Returns:
        Dictionary containing sync results from API

    Raises:
        requests.RequestException: If API call fails
    """
    # TODO: Make API base URL configurable
    api_url = "http://localhost:5000/api/sync"

    payload = {
        "source_account": source_account,
        "target_account": target_account,
        "dry_run": dry_run,
    }

    response = requests.post(api_url, json=payload, timeout=300)
    response.raise_for_status()

    return response.json()


def _render_destructive_warning(
    source_account: str,
    target_account: str,
    photos_to_add: int,
    photos_to_delete: int,
    photos_to_update: int,
) -> None:
    """Render prominent destructive operation warning.

    Displays a clear, impossible-to-miss warning about the destructive
    nature of the sync operation.

    Args:
        source_account: Email of source account
        target_account: Email of target account
        photos_to_add: Number of photos that will be added
        photos_to_delete: Number of photos that will be DELETED
        photos_to_update: Number of photos that will be updated
    """
    st.error("⚠️ DESTRUCTIVE OPERATION WARNING")

    st.warning(
        f"""
**⚠️ THE TARGET ACCOUNT ({target_account}) WILL BE PERMANENTLY MODIFIED ⚠️**

This operation will make the target account **exactly identical** to the
source account ({source_account}).

**Changes that will be made:**
- **ADD** {photos_to_add:,} photos to target account
- **DELETE** {photos_to_delete:,} photos from target account ❌
- **UPDATE** metadata for {photos_to_update:,} photos on target account

**⚠️ DELETED PHOTOS CANNOT BE RECOVERED WITHOUT A BACKUP ⚠️**

This operation is **IRREVERSIBLE** and cannot be undone.

**We strongly recommend backing up your target account first!**
    """
    )


def _render_confirmation_steps(target_account: str) -> bool:
    """Render multi-step confirmation process.

    Implements a comprehensive confirmation workflow to prevent accidental
    sync execution:
    1. Checkbox to confirm understanding
    2. Type-to-confirm with target account email

    Args:
        target_account: Email of target account (must be typed to confirm)

    Returns:
        True if user has completed all confirmation steps, False otherwise
    """
    st.subheader("🔐 Confirmation Required")
    st.write("Complete **ALL** steps below to proceed with sync:")

    # Step 1: Checkbox confirmation
    st.markdown("**Step 1:** Acknowledge the risks")
    checkbox_confirmed = st.checkbox(
        f"✓ I understand that **{target_account}** will be **permanently modified**",
        key="sync_view_confirm_checkbox",
    )

    # Step 2: Type-to-confirm
    st.markdown("**Step 2:** Type the target account email to confirm")
    st.caption(
        "This is an extra safety measure to prevent accidental clicks. "
        "Please type the exact email address of the target account."
    )

    typed_account = st.text_input(
        f"Type **'{target_account}'** to confirm:",
        key="sync_view_confirm_input",
        placeholder=target_account,
        help="Must exactly match the target account email",
    )

    # Check if both confirmations are satisfied
    is_confirmed = checkbox_confirmed and (typed_account.strip() == target_account)

    if checkbox_confirmed and typed_account and not is_confirmed:
        st.error(
            "❌ The email you typed doesn't match. "
            "Please type the exact target account email."
        )

    return is_confirmed


def _render_review_button(is_confirmed: bool) -> bool:
    """Render 'Review Sync Plan' button.

    This button is the first gate. User must click it to see the final
    confirmation dialog.

    Args:
        is_confirmed: Whether user has completed confirmation steps

    Returns:
        True if button was clicked and confirmations are complete
    """
    st.divider()

    if is_confirmed:
        if st.button(
            "📋 Review Sync Plan",
            type="primary",
            use_container_width=True,
            help="Review the final sync plan and see the execute button",
        ):
            # Set flag in session state to show execute button
            st.session_state.sync_view_review_clicked = True
            return True
    else:
        st.button(
            "Review Sync Plan",
            disabled=True,
            use_container_width=True,
            help="Complete all confirmations above to enable this button",
        )

    return False


def _render_final_warning_and_execute(
    source_account: str, target_account: str
) -> bool:
    """Render final warning dialog and execute button.

    This is the final gate before execution. Shows one more warning
    and the actual execute button.

    Args:
        source_account: Email of source account
        target_account: Email of target account

    Returns:
        True if execute button was clicked, False otherwise
    """
    st.divider()
    st.subheader("⚠️ FINAL WARNING")

    st.error(
        f"""
**YOU ARE ABOUT TO IRREVERSIBLY MODIFY {target_account}**

Once you click the button below, the sync operation will begin **immediately**.

Photos will be added, deleted, and modified on the target account.

**This action cannot be undone.**

Are you absolutely sure you want to proceed?
    """
    )

    # Execute button - RED and prominent
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "🔴 EXECUTE SYNC (IRREVERSIBLE)",
            type="primary",
            use_container_width=True,
            help=f"Start syncing from {source_account} to {target_account}",
        ):
            return True

    return False


def _render_sync_progress(
    current: int,
    total: int,
    current_photo: str = "",
    elapsed_seconds: float = 0,
) -> None:
    """Render real-time sync progress with progress bar and stats.

    Args:
        current: Current number of photos processed
        total: Total number of photos to process
        current_photo: Name of photo currently being processed
        elapsed_seconds: Time elapsed since sync started
    """
    st.subheader("🔄 Sync in Progress...")

    # Progress bar
    if total > 0:
        progress = current / total
        st.progress(progress)

        # Stats
        percentage = int(progress * 100)
        st.write(f"**Progress:** {percentage}% ({current:,} / {total:,} photos)")

        if current_photo:
            st.caption(f"📸 Currently processing: {current_photo}")

        # Estimate time remaining
        if current > 0 and elapsed_seconds > 0:
            avg_time_per_photo = elapsed_seconds / current
            remaining_photos = total - current
            eta_seconds = avg_time_per_photo * remaining_photos

            eta_minutes = int(eta_seconds // 60)
            eta_seconds_remainder = int(eta_seconds % 60)

            if eta_minutes > 0:
                eta_str = f"{eta_minutes}m {eta_seconds_remainder}s"
            else:
                eta_str = f"{eta_seconds_remainder}s"

            st.caption(f"⏱️ Estimated time remaining: {eta_str}")


def _render_emergency_stop_button() -> bool:
    """Render emergency stop button for sync operation.

    Returns:
        True if stop button was clicked, False otherwise
    """
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "🛑 EMERGENCY STOP",
            type="secondary",
            use_container_width=True,
            help=(
                "Stop the sync operation immediately "
                "(current photo may still complete)"
            ),
        ):
            return True

    return False


def _execute_sync(source_account: str, target_account: str) -> None:
    """Execute the sync operation with progress tracking.

    This function handles the actual sync execution, including:
    - Progress tracking
    - Emergency stop handling
    - Error handling
    - Success/failure reporting

    Args:
        source_account: Email of source account
        target_account: Email of target account
    """
    # Initialize sync state
    if "sync_view_in_progress" not in st.session_state:
        st.session_state.sync_view_in_progress = False

    if "sync_view_stopped" not in st.session_state:
        st.session_state.sync_view_stopped = False

    # Start sync
    st.session_state.sync_view_in_progress = True
    st.session_state.sync_view_stopped = False

    # Progress container
    progress_container = st.container()

    with progress_container:
        st.info("🚀 Starting sync operation...")

        # Emergency stop button
        if _render_emergency_stop_button():
            st.session_state.sync_view_stopped = True
            st.session_state.sync_view_in_progress = False
            st.warning("⚠️ Sync operation stopped by user!")
            return

        try:
            # Call API to execute sync
            start_time = time.time()

            # Show initial progress
            st.session_state.sync_view_progress = {
                "current": 0,
                "total": 100,  # Placeholder - API should provide this
                "current_photo": "Initializing...",
            }

            # Render progress
            _render_sync_progress(
                current=0,
                total=100,
                current_photo="Initializing sync...",
                elapsed_seconds=0,
            )

            # TODO: Implement actual progress tracking with API
            # For now, call sync API and wait for completion
            st.info("⏳ Calling sync API... This may take several minutes.")

            result = _call_sync_api(source_account, target_account, dry_run=False)

            elapsed_time = time.time() - start_time

            # Check if API call was successful
            if result.get("success"):
                st.session_state.sync_view_in_progress = False

                # Store sync result
                sync_data = result.get("data", {})
                st.session_state.sync_view_result = {
                    "photos_transferred": sync_data.get("photos_added", 0),
                    "photos_deleted": sync_data.get("photos_deleted", 0),
                    "photos_skipped": 0,  # API doesn't provide this yet
                    "elapsed_time_seconds": elapsed_time,
                }

                st.success("✅ Sync completed successfully!")

            else:
                error_msg = result.get("error", "Unknown error")
                st.error(f"❌ Sync failed: {error_msg}")
                st.session_state.sync_view_in_progress = False

        except requests.RequestException as e:
            st.error(f"❌ API Error: {str(e)}")
            st.error(
                "Make sure the Flask API is running on http://localhost:5000. "
                "Start it with: make run-api"
            )
            st.session_state.sync_view_in_progress = False
        except Exception as e:
            st.error(f"❌ Unexpected error during sync: {str(e)}")
            st.session_state.sync_view_in_progress = False


def _check_prerequisites() -> tuple[bool, str, str, dict[str, Any]]:
    """Check prerequisites for sync operation.

    Returns:
        Tuple of (prerequisites_met, source_email, target_email, comparison_result)
        If prerequisites not met, empty strings and dict are returned.
    """
    # Check comparison result exists
    if not st.session_state.get("comparison_result"):
        st.warning(
            "⚠️ Please go to the **Compare** page first to preview changes "
            "before syncing."
        )
        if st.button("Go to Compare Page", type="primary"):
            st.session_state.current_page = "Compare"
            st.rerun()
        return False, "", "", {}

    # Check authentication
    both_authenticated = (
        st.session_state.get("source_auth") is not None
        and st.session_state.get("target_auth") is not None
    )

    if not both_authenticated:
        st.error("❌ Both accounts must be authenticated to sync.")
        if st.button("Go to Compare Page to Authenticate", type="primary"):
            st.session_state.current_page = "Compare"
            st.rerun()
        return False, "", "", {}

    # Get account emails and comparison data
    source_email = st.session_state.source_auth.get("email", "source@example.com")
    target_email = st.session_state.target_auth.get("email", "target@example.com")
    result = st.session_state.comparison_result

    return True, source_email, target_email, result


def _render_account_info(source_email: str, target_email: str) -> None:
    """Render account information section.

    Args:
        source_email: Email of source account
        target_email: Email of target account
    """
    st.subheader("📋 Sync Configuration")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Source Account (Read Only):**")
        st.info(f"📧 {source_email}")

    with col2:
        st.write("**Target Account (WILL BE MODIFIED):**")
        st.error(f"📧 {target_email}")

    st.divider()


def _render_sync_results() -> None:
    """Render sync results if available."""
    if st.session_state.sync_view_result:
        st.divider()
        st.success("✅ Sync Operation Completed!")

        status = st.session_state.sync_view_result
        render_sync_statistics(
            photos_transferred=status["photos_transferred"],
            photos_deleted=status["photos_deleted"],
            photos_skipped=status["photos_skipped"],
            elapsed_time_seconds=status["elapsed_time_seconds"],
        )

        # Button to clear results and start fresh
        if st.button("🔄 Start New Sync", type="secondary"):
            st.session_state.sync_view_result = None
            st.session_state.sync_view_review_clicked = False
            st.session_state.comparison_result = None  # Force new comparison
            st.rerun()


def render_sync_view() -> None:
    """Render the complete sync view with safety warnings and execution.

    This is the main entry point for the sync view. It orchestrates all
    the safety checks, confirmations, and sync execution.

    The workflow is:
    1. Check prerequisites (authentication, comparison)
    2. Display comparison summary
    3. Show destructive operation warning
    4. Multi-step confirmation process
    5. Review button
    6. Final warning and execute button
    7. Progress tracking during sync
    8. Success/failure summary

    This function should be called from the main Streamlit app when
    rendering the Sync page.

    Example:
        >>> # In app.py
        >>> from google_photos_sync.ui.components.sync_view import render_sync_view
        >>> def render_sync_page():
        >>>     st.title("🔄 Sync Accounts")
        >>>     render_sync_view()
    """
    # Initialize session state keys
    if "sync_view_review_clicked" not in st.session_state:
        st.session_state.sync_view_review_clicked = False

    if "sync_view_result" not in st.session_state:
        st.session_state.sync_view_result = None

    # Check prerequisites
    prerequisites_met, source_email, target_email, result = _check_prerequisites()
    if not prerequisites_met:
        return

    # Display account information
    _render_account_info(source_email, target_email)

    # Display comparison summary
    st.subheader("📊 What Will Change")
    render_comparison_summary(
        total_source=result["total_source"],
        total_target=result["total_target"],
        missing=result["missing_on_target"],
        extra=result["extra_on_target"],
        different=result["different_metadata"],
    )

    st.divider()

    # Destructive operation warning
    _render_destructive_warning(
        source_account=source_email,
        target_account=target_email,
        photos_to_add=result["missing_on_target"],
        photos_to_delete=result["extra_on_target"],
        photos_to_update=result["different_metadata"],
    )

    st.divider()

    # Confirmation steps
    is_confirmed = _render_confirmation_steps(target_email)

    # Review button
    if not st.session_state.sync_view_review_clicked:
        _render_review_button(is_confirmed)
    else:
        # Show final warning and execute button
        if _render_final_warning_and_execute(source_email, target_email):
            # Clear the review flag for next time
            st.session_state.sync_view_review_clicked = False

            # Execute sync
            _execute_sync(source_email, target_email)

            # Force rerun to show results
            st.rerun()

    # Display sync results if available
    _render_sync_results()
