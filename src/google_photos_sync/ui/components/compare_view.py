"""Compare View Component - Display Account Comparison Results.

This module provides the compare view component that displays account comparison
results in a clear, actionable format. The compare operation is read-only and
helps users preview what sync will do before executing it.

Following clean code principles and KISS approach, this component presents
comparison data in an easy-to-understand format suitable for non-technical users.

Key Features:
- Clear account statistics and metrics
- Color-coded differences (green for additions, red for deletions)
- Collapsible detailed lists for photo differences
- JSON export capability
- Call-to-action to proceed to sync
- Graceful handling of edge cases

Example:
    >>> from google_photos_sync.ui.components.compare_view import render_compare_view
    >>> render_compare_view()
"""

import json
from datetime import datetime
from typing import Any, Optional

import requests
import streamlit as st


def _call_compare_api(source_account: str, target_account: str) -> dict[str, Any]:
    """Call the Flask API /api/compare endpoint to compare accounts.

    Args:
        source_account: Email of source Google Photos account
        target_account: Email of target Google Photos account

    Returns:
        Dictionary containing comparison results from API

    Raises:
        requests.RequestException: If API call fails
    """
    # TODO: Make API base URL configurable
    api_url = "http://localhost:5000/api/compare"

    payload = {
        "source_account": source_account,
        "target_account": target_account,
    }

    response = requests.post(api_url, json=payload, timeout=60)
    response.raise_for_status()

    result: dict[str, Any] = response.json()
    return result


def _render_account_info(source_account: str, target_account: str) -> None:
    """Render source and target account information.

    Args:
        source_account: Email of source account
        target_account: Email of target account
    """
    st.subheader("📋 Account Information")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Source Account (Read From):**")
        st.info(f"📧 {source_account}")

    with col2:
        st.markdown("**Target Account (Will Sync To):**")
        st.warning(f"📧 {target_account}")


def _render_comparison_statistics(comparison_data: dict[str, Any]) -> None:
    """Render comparison statistics using metrics.

    Args:
        comparison_data: Comparison result data from API
    """
    st.subheader("📊 Comparison Statistics")

    # Top row - totals
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="📸 Total Source Photos",
            value=f"{comparison_data['total_source_photos']:,}",
        )
    with col2:
        st.metric(
            label="📸 Total Target Photos",
            value=f"{comparison_data['total_target_photos']:,}",
        )

    st.divider()

    # Bottom row - changes
    st.markdown("**Changes Required for Sync:**")
    col3, col4, col5 = st.columns(3)

    missing_count = len(comparison_data.get("missing_on_target", []))
    extra_count = len(comparison_data.get("extra_on_target", []))
    different_count = len(comparison_data.get("different_metadata", []))

    with col3:
        st.metric(
            label="➕ To Add",
            value=f"{missing_count:,}",
            delta="Will be added" if missing_count > 0 else None,
            delta_color="normal",
        )

    with col4:
        st.metric(
            label="🗑️ To Delete",
            value=f"{extra_count:,}",
            delta="Will be deleted" if extra_count > 0 else None,
            delta_color="inverse",
        )

    with col5:
        st.metric(
            label="🔄 Different Metadata",
            value=f"{different_count:,}",
            delta="Will be updated" if different_count > 0 else None,
            delta_color="normal",
        )


def _render_photo_list(
    photos: list[dict[str, Any]], title: str, icon: str, color: str
) -> None:
    """Render a collapsible list of photos.

    Args:
        photos: List of photo dictionaries
        title: Title for the expander
        icon: Icon emoji for the title
        color: Color indicator ("success", "error", "warning", "info")
    """
    count = len(photos)

    with st.expander(f"{icon} {title} ({count:,} photos)", expanded=False):
        if count == 0:
            st.info("No photos in this category.")
            return

        # Show first 10 photos with details, rest as summary
        display_limit = 10

        for i, photo in enumerate(photos[:display_limit]):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**{photo.get('filename', 'Unknown')}**")
                st.caption(
                    f"ID: {photo.get('id', 'N/A')} | "
                    f"Created: {photo.get('created_time', 'N/A')}"
                )

            with col2:
                if photo.get("width") and photo.get("height"):
                    st.caption(f"{photo['width']}×{photo['height']}")
                st.caption(f"{photo.get('mime_type', 'Unknown type')}")

            # Display thumbnail if base_url is available
            if photo.get("base_url"):
                try:
                    # Add resolution parameter to base_url for thumbnail
                    thumbnail_url = f"{photo['base_url']}=w200-h200"
                    st.image(thumbnail_url, width=200)
                except Exception:  # nosec B110
                    # Silently skip if thumbnail fails to load (graceful degradation)
                    # This is acceptable for UI display - we don't want to break
                    # the entire comparison view if one thumbnail fails
                    pass

            if i < len(photos[:display_limit]) - 1:
                st.divider()

        # Show summary if more photos exist
        if count > display_limit:
            st.divider()
            st.info(
                f"... and {count - display_limit:,} more photos. "
                f"Download the full comparison as JSON to see all details."
            )


def _render_metadata_differences(differences: list[dict[str, Any]]) -> None:
    """Render metadata differences in a collapsible section.

    Args:
        differences: List of metadata difference dictionaries
    """
    count = len(differences)

    with st.expander(
        f"🔄 Photos with Metadata Differences ({count:,})", expanded=False
    ):
        if count == 0:
            st.info("No metadata differences found.")
            return

        # Group differences by photo_id
        by_photo: dict[str, list[dict[str, Any]]] = {}
        for diff in differences:
            photo_id = diff.get("photo_id", "unknown")
            if photo_id not in by_photo:
                by_photo[photo_id] = []
            by_photo[photo_id].append(diff)

        # Display first 5 photos with differences
        display_limit = 5
        photo_ids = list(by_photo.keys())[:display_limit]

        for i, photo_id in enumerate(photo_ids):
            st.markdown(f"**Photo ID:** `{photo_id}`")

            # Show all field differences for this photo
            for diff in by_photo[photo_id]:
                field = diff.get("field", "unknown")
                source_val = diff.get("source_value", "N/A")
                target_val = diff.get("target_value", "N/A")

                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"**{field}** (source)")
                    st.code(str(source_val))
                with col2:
                    st.caption(f"**{field}** (target)")
                    st.code(str(target_val))

            if i < len(photo_ids) - 1:
                st.divider()

        # Show summary if more photos exist
        if len(by_photo) > display_limit:
            st.divider()
            remaining = len(by_photo) - display_limit
            st.info(
                f"... and {remaining:,} more photos with differences. "
                f"Download the full comparison as JSON to see all details."
            )


def _render_json_export(comparison_data: dict[str, Any]) -> None:
    """Render JSON export download button.

    Args:
        comparison_data: Complete comparison result data
    """
    st.subheader("💾 Export Comparison Data")

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    source = comparison_data.get("source_account", "source").split("@")[0]
    target = comparison_data.get("target_account", "target").split("@")[0]
    filename = f"comparison_{source}_to_{target}_{timestamp}.json"

    # Convert to pretty-printed JSON
    json_str = json.dumps(comparison_data, indent=2, ensure_ascii=False)

    st.download_button(
        label="📥 Download Comparison as JSON",
        data=json_str,
        file_name=filename,
        mime="application/json",
        use_container_width=True,
    )

    st.caption(
        "💡 Export includes complete comparison data with all photo details "
        "and metadata differences."
    )


def _render_sync_call_to_action(has_changes: bool) -> None:
    """Render call-to-action to proceed to sync.

    Args:
        has_changes: Whether there are any changes to sync
    """
    st.divider()
    st.subheader("🚀 Next Steps")

    if not has_changes:
        st.success(
            "✅ **Accounts are already in sync!**\n\n"
            "Source and target accounts are identical. No sync is needed."
        )
    else:
        st.info(
            "ℹ️ **Ready to sync?**\n\n"
            "Review the changes above. If everything looks correct, "
            "navigate to the **Sync** page to execute the synchronization."
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "➡️ Go to Sync Page",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.current_page = "Sync"
                st.rerun()


def _render_empty_accounts_message() -> None:
    """Render message for empty or identical accounts."""
    st.info(
        "ℹ️ **No comparison results yet**\n\n"
        "Click the **Compare Accounts** button above to start the comparison."
    )


def render_compare_view(
    source_auth: Optional[dict[str, Any]] = None,
    target_auth: Optional[dict[str, Any]] = None,
) -> None:
    """Render the complete compare view component.

    This is the main entry point for the compare view. It handles the
    entire comparison workflow including API calls, result display,
    and user interactions.

    Args:
        source_auth: Source account authentication data (from session state)
        target_auth: Target account authentication data (from session state)

    Example:
        >>> render_compare_view(
        ...     source_auth=st.session_state.source_auth,
        ...     target_auth=st.session_state.target_auth
        ... )
    """
    # Check authentication
    both_authenticated = source_auth is not None and target_auth is not None

    if not both_authenticated:
        st.warning(
            "⚠️ **Authentication Required**\n\n"
            "Please authenticate both source and target accounts before comparing."
        )
        return

    # Type narrowing - at this point both are guaranteed to be non-None
    assert source_auth is not None
    assert target_auth is not None
    
    source_account = source_auth.get("email", "")
    target_account = target_auth.get("email", "")

    # Display account information
    _render_account_info(source_account, target_account)

    st.divider()

    # Compare button
    if st.button("🔍 Compare Accounts", type="primary", use_container_width=True):
        with st.spinner("🔄 Comparing accounts... This may take a moment."):
            try:
                # Call API
                api_response = _call_compare_api(source_account, target_account)

                # Check if API call was successful
                if api_response.get("success"):
                    comparison_data = api_response.get("data", {})

                    # Store in session state for persistence
                    st.session_state.comparison_result = comparison_data

                    st.success("✅ Comparison completed successfully!")
                else:
                    error_msg = api_response.get("error", "Unknown error")
                    st.error(f"❌ Comparison failed: {error_msg}")
                    return

            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ **Cannot connect to API server**\n\n"
                    "Please ensure the Flask API server is running at "
                    "http://localhost:5000\n\n"
                    "Start it with: `make run-api` or `flask run`"
                )
                return
            except requests.exceptions.Timeout:
                st.error(
                    "❌ **Request timed out**\n\n"
                    "The comparison is taking longer than expected. "
                    "This might happen with large photo libraries."
                )
                return
            except Exception as e:
                st.error(f"❌ **Unexpected error:** {str(e)}")
                return

    # Display comparison results if available
    if st.session_state.get("comparison_result"):
        st.divider()

        comparison_data = st.session_state.comparison_result

        # Render statistics
        _render_comparison_statistics(comparison_data)

        st.divider()

        # Render detailed lists
        st.subheader("📂 Detailed Comparison")

        missing = comparison_data.get("missing_on_target", [])
        extra = comparison_data.get("extra_on_target", [])
        different = comparison_data.get("different_metadata", [])

        # Photos to be added (missing on target)
        _render_photo_list(
            missing,
            "Photos to be Added to Target",
            "➕",
            "success",
        )

        # Photos to be deleted (extra on target)
        _render_photo_list(
            extra,
            "Photos to be Deleted from Target",
            "🗑️",
            "error",
        )

        # Metadata differences
        _render_metadata_differences(different)

        st.divider()

        # JSON export
        _render_json_export(comparison_data)

        # Call to action
        has_changes = len(missing) > 0 or len(extra) > 0 or len(different) > 0
        _render_sync_call_to_action(has_changes)
    else:
        st.divider()
        _render_empty_accounts_message()
