"""Confirmation dialog components for destructive operations.

This module provides UI components for displaying warnings and
confirmation dialogs before executing destructive operations like
syncing (which may delete photos from target account).

Following KISS principle and user safety requirements.
"""

import streamlit as st


def render_sync_confirmation_dialog(
    source_account: str,
    target_account: str,
    photos_to_add: int,
    photos_to_delete: int,
    photos_to_update: int,
) -> bool:
    """Render comprehensive confirmation dialog for sync operation.

    This displays multiple safety measures to prevent accidental
    destructive operations:
    1. Clear warning about destructive nature
    2. Statistics of what will change
    3. Checkbox confirmation
    4. Type-to-confirm input field

    Args:
        source_account: Email of source account
        target_account: Email of target account
        photos_to_add: Number of photos that will be added to target
        photos_to_delete: Number of photos that will be deleted from target
        photos_to_update: Number of photos with metadata updates

    Returns:
        True if user has confirmed and ready to proceed, False otherwise

    Example:
        >>> confirmed = render_sync_confirmation_dialog(
        ...     "source@gmail.com",
        ...     "target@gmail.com",
        ...     150, 10, 5
        ... )
        >>> if confirmed:
        ...     execute_sync()
    """
    st.error("⚠️ DESTRUCTIVE OPERATION WARNING")

    st.warning(
        f"""
    **Target account ({target_account}) will be MODIFIED** to exactly match
    source account ({source_account}).

    This operation will make the following changes:
    - **Add** {photos_to_add:,} photos to target account
    - **DELETE** {photos_to_delete:,} photos from target account
    - **Update metadata** for {photos_to_update:,} photos on target account

    **⚠️ Deleted photos cannot be recovered unless you have a backup.**

    This operation cannot be undone.
    """
    )

    st.divider()

    # Safety confirmations
    st.subheader("Confirmation Required")

    # Checkbox confirmation
    checkbox_confirmed = st.checkbox(
        f"✓ I understand that **{target_account}** will be permanently modified",
        key="sync_confirm_checkbox",
    )

    # Type-to-confirm input
    typed_account = st.text_input(
        f"Type the target account email **'{target_account}'** to confirm:",
        key="sync_confirm_input",
        placeholder=target_account,
    )

    # Check if both confirmations are satisfied
    is_confirmed = checkbox_confirmed and (typed_account == target_account)

    return is_confirmed


def render_delete_confirmation_dialog(item_name: str, item_type: str = "item") -> bool:
    """Render simple confirmation dialog for delete operations.

    Args:
        item_name: Name of the item being deleted
        item_type: Type of item (e.g., "photo", "album", "configuration")

    Returns:
        True if user confirmed deletion, False otherwise

    Example:
        >>> if render_delete_confirmation_dialog("vacation.jpg", "photo"):
        ...     delete_photo()
    """
    st.warning(f"⚠️ Are you sure you want to delete this {item_type}?")
    st.write(f"**{item_type.capitalize()}:** {item_name}")
    st.write("This action cannot be undone.")

    return st.checkbox(f"Yes, delete '{item_name}'", key=f"delete_confirm_{item_name}")


def render_warning_banner(
    message: str, icon: str = "⚠️", severity: str = "warning"
) -> None:
    """Render a prominent warning banner.

    Args:
        message: Warning message to display
        icon: Emoji icon (default: ⚠️)
        severity: Severity level ("warning" or "error")

    Example:
        >>> render_warning_banner(
        ...     "Your session will expire in 5 minutes",
        ...     "⏰",
        ...     "warning"
        ... )
    """
    full_message = f"{icon} {message}"

    if severity == "error":
        st.error(full_message)
    else:
        st.warning(full_message)


def render_info_banner(
    message: str, icon: str = "ℹ️", dismissible: bool = False
) -> None:
    """Render an informational banner.

    Args:
        message: Information message to display
        icon: Emoji icon (default: ℹ️)
        dismissible: If True, shows a dismiss button (uses session state)

    Example:
        >>> render_info_banner(
        ...     "Sync completed successfully!",
        ...     "✅",
        ...     dismissible=True
        ... )
    """
    # Generate unique key for this banner
    banner_key = f"banner_dismissed_{hash(message)}"

    # Check if banner was dismissed
    if dismissible and st.session_state.get(banner_key, False):
        return

    full_message = f"{icon} {message}"
    st.info(full_message)

    if dismissible:
        if st.button("Dismiss", key=f"dismiss_{banner_key}"):
            st.session_state[banner_key] = True
            st.rerun()
