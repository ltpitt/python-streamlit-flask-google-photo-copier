"""Status messages and progress indicators for Streamlit UI.

This module provides reusable components for displaying status messages,
progress bars, and operation feedback in the Streamlit interface.
Components follow clean code principles as pure functions.
"""

from typing import Literal, Optional

import streamlit as st

StatusType = Literal["info", "success", "warning", "error"]


def show_status_message(
    message: str, status_type: StatusType = "info", icon: Optional[str] = None
) -> None:
    """Display a status message with appropriate styling.

    Args:
        message: Message text to display
        status_type: Type of status ("info", "success", "warning", "error")
        icon: Optional emoji icon to prepend to message

    Example:
        >>> show_status_message("Operation completed", "success", "✅")
        >>> show_status_message("Warning: High memory usage", "warning")
    """
    # Add icon if provided
    full_message = f"{icon} {message}" if icon else message

    if status_type == "info":
        st.info(full_message)
    elif status_type == "success":
        st.success(full_message)
    elif status_type == "warning":
        st.warning(full_message)
    elif status_type == "error":
        st.error(full_message)


def render_progress_bar(current: int, total: int, label: Optional[str] = None) -> None:
    """Render a progress bar with percentage and optional label.

    Args:
        current: Current progress value
        total: Total/maximum value
        label: Optional label text above progress bar

    Example:
        >>> render_progress_bar(45, 100, "Syncing photos")
    """
    if total <= 0:
        return

    progress = current / total

    if label:
        st.write(label)

    st.progress(progress)

    # Show percentage and count
    percentage = int(progress * 100)
    st.caption(f"{percentage}% ({current:,} / {total:,})")


def render_sync_statistics(
    photos_transferred: int,
    photos_deleted: int,
    photos_skipped: int,
    elapsed_time_seconds: float,
) -> None:
    """Display sync operation statistics in a clean format.

    Args:
        photos_transferred: Number of photos successfully transferred
        photos_deleted: Number of photos deleted from target
        photos_skipped: Number of photos skipped (already synced)
        elapsed_time_seconds: Total elapsed time in seconds

    Example:
        >>> render_sync_statistics(150, 5, 30, 125.5)
    """
    st.subheader("📊 Sync Statistics")

    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Transferred", value=f"{photos_transferred:,}")

    with col2:
        st.metric(label="Deleted", value=f"{photos_deleted:,}")

    with col3:
        st.metric(label="Skipped", value=f"{photos_skipped:,}")

    with col4:
        # Format elapsed time
        minutes = int(elapsed_time_seconds // 60)
        seconds = int(elapsed_time_seconds % 60)
        time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        st.metric(label="Time", value=time_str)


def render_comparison_summary(
    total_source: int, total_target: int, missing: int, extra: int, different: int
) -> None:
    """Display account comparison summary.

    Args:
        total_source: Total photos in source account
        total_target: Total photos in target account
        missing: Photos missing on target (to be added)
        extra: Photos extra on target (to be deleted)
        different: Photos with different metadata

    Example:
        >>> render_comparison_summary(500, 450, 60, 10, 5)
    """
    st.subheader("📊 Comparison Summary")

    # Source and target totals
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Source Account Photos", value=f"{total_source:,}")
    with col2:
        st.metric(label="Target Account Photos", value=f"{total_target:,}")

    st.divider()

    # Changes needed
    st.write("**Changes Required for Sync:**")
    col3, col4, col5 = st.columns(3)

    with col3:
        st.metric(
            label="To Add",
            value=f"{missing:,}",
            delta=None if missing == 0 else "Will be added",
        )

    with col4:
        st.metric(
            label="To Delete",
            value=f"{extra:,}",
            delta=None if extra == 0 else "Will be deleted",
            delta_color="inverse",
        )

    with col5:
        st.metric(
            label="Different Metadata",
            value=f"{different:,}",
            delta=None if different == 0 else "Will be updated",
        )
