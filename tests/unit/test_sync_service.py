"""Tests for Sync Service - Idempotent Monodirectional Sync.

Following TDD approach: RED phase - write failing tests first.
These tests define the expected behavior of the Sync Service.
"""

from unittest.mock import Mock

import pytest

from google_photos_sync.core.compare_service import CompareResult, CompareService
from google_photos_sync.core.sync_service import (
    SyncAction,
    SyncResult,
    SyncService,
)
from google_photos_sync.core.transfer_manager import TransferManager, TransferResult
from google_photos_sync.google_photos.models import Photo


class TestSyncServiceInitialization:
    """Test sync service initialization and setup."""

    def test_sync_service_requires_compare_service(self):
        """Test that compare service is required."""
        mock_transfer = Mock(spec=TransferManager)

        with pytest.raises(ValueError) as exc_info:
            SyncService(compare_service=None, transfer_manager=mock_transfer)  # type: ignore[arg-type]

        assert "compare_service cannot be None" in str(exc_info.value)

    def test_sync_service_requires_transfer_manager(self):
        """Test that transfer manager is required."""
        mock_compare = Mock(spec=CompareService)

        with pytest.raises(ValueError) as exc_info:
            SyncService(compare_service=mock_compare, transfer_manager=None)  # type: ignore[arg-type]

        assert "transfer_manager cannot be None" in str(exc_info.value)

    def test_sync_service_with_valid_dependencies_succeeds(self):
        """Test that service initializes with valid dependencies."""
        mock_compare = Mock(spec=CompareService)
        mock_transfer = Mock(spec=TransferManager)

        service = SyncService(
            compare_service=mock_compare, transfer_manager=mock_transfer
        )

        assert service is not None


class TestSyncEmptySourceToNonEmptyTarget:
    """Test syncing empty source to non-empty target - target should become empty."""

    def test_sync_empty_source_to_non_empty_target_deletes_all_target_photos(self):
        """Test that all photos on target are deleted when source is empty."""
        # Arrange
        mock_compare = Mock(spec=CompareService)
        mock_transfer = Mock(spec=TransferManager)

        target_photos = [
            Photo(
                id="photo1",
                filename="vacation.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
            Photo(
                id="photo2",
                filename="beach.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-02T12:00:00Z",
                width=3840,
                height=2160,
            ),
        ]

        # Mock comparison result: source empty, target has photos
        compare_result = CompareResult(
            source_account="source@example.com",
            target_account="target@example.com",
            comparison_date="2025-01-06T10:00:00Z",
            total_source_photos=0,
            total_target_photos=2,
            missing_on_target=[],  # No photos to add
            different_metadata=[],
            extra_on_target=target_photos,  # Photos to delete
        )
        mock_compare.compare_accounts.return_value = compare_result

        service = SyncService(
            compare_service=mock_compare, transfer_manager=mock_transfer
        )

        # Act
        result = service.sync_accounts(
            source_account="source@example.com",
            target_account="target@example.com",
            dry_run=False,
        )

        # Assert
        assert result.photos_added == 0
        assert result.photos_deleted == 2
        assert result.photos_updated == 0
        assert result.total_actions == 2
        # Verify delete actions were added
        delete_actions = [a for a in result.actions if a.action == "delete"]
        assert len(delete_actions) == 2


class TestSyncNonEmptySourceToEmptyTarget:
    """Test syncing non-empty source to empty target - target gets all photos."""

    def test_sync_non_empty_source_to_empty_target_adds_all_photos(self):
        """Test that all photos from source are added to empty target."""
        # Arrange
        mock_compare = Mock(spec=CompareService)
        mock_transfer = Mock(spec=TransferManager)

        source_photos = [
            Photo(
                id="photo1",
                filename="vacation.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
            Photo(
                id="photo2",
                filename="beach.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-02T12:00:00Z",
                width=3840,
                height=2160,
            ),
        ]

        # Mock comparison result: source has photos, target empty
        compare_result = CompareResult(
            source_account="source@example.com",
            target_account="target@example.com",
            comparison_date="2025-01-06T10:00:00Z",
            total_source_photos=2,
            total_target_photos=0,
            missing_on_target=source_photos,  # Photos to add
            different_metadata=[],
            extra_on_target=[],  # No photos to delete
        )
        mock_compare.compare_accounts.return_value = compare_result

        # Mock successful transfers
        mock_transfer.transfer_photo.return_value = TransferResult(
            photo_id="photo1",
            status="success",
            bytes_transferred=1024000,
            retry_count=0,
        )

        service = SyncService(
            compare_service=mock_compare, transfer_manager=mock_transfer
        )

        # Act
        result = service.sync_accounts(
            source_account="source@example.com",
            target_account="target@example.com",
            dry_run=False,
        )

        # Assert
        assert result.photos_added == 2
        assert result.photos_deleted == 0
        assert result.photos_updated == 0
        assert result.total_actions == 2
        # Verify transfers were called
        assert mock_transfer.transfer_photo.call_count == 2


class TestSyncWithPartialOverlap:
    """Test sync with partial overlap - missing photos added, extras deleted."""

    def test_sync_with_partial_overlap_adds_missing_and_deletes_extras(self):
        """Test sync correctly handles partial overlap scenario."""
        # Arrange
        mock_compare = Mock(spec=CompareService)
        mock_transfer = Mock(spec=TransferManager)

        missing_photos = [
            Photo(
                id="photo2",
                filename="beach.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-02T12:00:00Z",
                width=3840,
                height=2160,
            ),
        ]

        extra_photos = [
            Photo(
                id="photo_extra",
                filename="extra.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-05T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        # Mock comparison result: partial overlap
        compare_result = CompareResult(
            source_account="source@example.com",
            target_account="target@example.com",
            comparison_date="2025-01-06T10:00:00Z",
            total_source_photos=2,
            total_target_photos=2,
            missing_on_target=missing_photos,  # 1 photo to add
            different_metadata=[],
            extra_on_target=extra_photos,  # 1 photo to delete
        )
        mock_compare.compare_accounts.return_value = compare_result

        # Mock successful transfer
        mock_transfer.transfer_photo.return_value = TransferResult(
            photo_id="photo2",
            status="success",
            bytes_transferred=2048000,
            retry_count=0,
        )

        service = SyncService(
            compare_service=mock_compare, transfer_manager=mock_transfer
        )

        # Act
        result = service.sync_accounts(
            source_account="source@example.com",
            target_account="target@example.com",
            dry_run=False,
        )

        # Assert
        assert result.photos_added == 1
        assert result.photos_deleted == 1
        assert result.total_actions == 2
        # Verify one transfer and one delete
        assert mock_transfer.transfer_photo.call_count == 1


class TestIdempotency:
    """Test idempotency - running sync twice has same result as running once."""

    def test_sync_is_idempotent_second_run_does_nothing(self):
        """Test sync twice on identical accounts does nothing on second run."""
        # Arrange
        mock_compare = Mock(spec=CompareService)
        mock_transfer = Mock(spec=TransferManager)

        # First sync: accounts are identical after sync
        identical_result = CompareResult(
            source_account="source@example.com",
            target_account="target@example.com",
            comparison_date="2025-01-06T10:00:00Z",
            total_source_photos=2,
            total_target_photos=2,
            missing_on_target=[],  # Nothing to add
            different_metadata=[],  # No metadata differences
            extra_on_target=[],  # Nothing to delete
        )
        mock_compare.compare_accounts.return_value = identical_result

        service = SyncService(
            compare_service=mock_compare, transfer_manager=mock_transfer
        )

        # Act - run sync twice
        result1 = service.sync_accounts(
            source_account="source@example.com",
            target_account="target@example.com",
            dry_run=False,
        )
        result2 = service.sync_accounts(
            source_account="source@example.com",
            target_account="target@example.com",
            dry_run=False,
        )

        # Assert - both runs should do nothing
        assert result1.photos_added == 0
        assert result1.photos_deleted == 0
        assert result1.photos_updated == 0
        assert result1.total_actions == 0

        assert result2.photos_added == 0
        assert result2.photos_deleted == 0
        assert result2.photos_updated == 0
        assert result2.total_actions == 0

        # No transfers should have been called
        mock_transfer.transfer_photo.assert_not_called()


class TestMetadataPreservation:
    """Test that sync preserves all photo metadata."""

    def test_sync_with_metadata_differences_updates_target_metadata(self):
        """Test that photos with different metadata are updated."""
        # Arrange
        mock_compare = Mock(spec=CompareService)
        mock_transfer = Mock(spec=TransferManager)

        # Mock comparison result: metadata differences
        compare_result = CompareResult(
            source_account="source@example.com",
            target_account="target@example.com",
            comparison_date="2025-01-06T10:00:00Z",
            total_source_photos=1,
            total_target_photos=1,
            missing_on_target=[],
            different_metadata=[
                {
                    "photo_id": "photo1",
                    "field": "filename",
                    "source_value": "vacation_original.jpg",
                    "target_value": "vacation_renamed.jpg",
                }
            ],
            extra_on_target=[],
        )
        mock_compare.compare_accounts.return_value = compare_result

        service = SyncService(
            compare_service=mock_compare, transfer_manager=mock_transfer
        )

        # Act
        result = service.sync_accounts(
            source_account="source@example.com",
            target_account="target@example.com",
            dry_run=False,
        )

        # Assert
        assert result.photos_updated == 1
        assert result.total_actions == 1


class TestDryRunMode:
    """Test dry-run mode - preview changes without executing."""

    def test_dry_run_returns_planned_actions_without_executing(self):
        """Test that dry-run mode returns actions but doesn't execute them."""
        # Arrange
        mock_compare = Mock(spec=CompareService)
        mock_transfer = Mock(spec=TransferManager)

        missing_photos = [
            Photo(
                id="photo2",
                filename="beach.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-02T12:00:00Z",
                width=3840,
                height=2160,
            ),
        ]

        extra_photos = [
            Photo(
                id="photo_extra",
                filename="extra.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-05T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        compare_result = CompareResult(
            source_account="source@example.com",
            target_account="target@example.com",
            comparison_date="2025-01-06T10:00:00Z",
            total_source_photos=2,
            total_target_photos=2,
            missing_on_target=missing_photos,
            different_metadata=[],
            extra_on_target=extra_photos,
        )
        mock_compare.compare_accounts.return_value = compare_result

        service = SyncService(
            compare_service=mock_compare, transfer_manager=mock_transfer
        )

        # Act
        result = service.sync_accounts(
            source_account="source@example.com",
            target_account="target@example.com",
            dry_run=True,  # DRY RUN MODE
        )

        # Assert - actions are planned but not executed
        assert result.dry_run is True
        assert result.photos_added == 1  # Planned to add
        assert result.photos_deleted == 1  # Planned to delete
        assert len(result.actions) == 2

        # Verify NO actual transfers or deletes were executed
        mock_transfer.transfer_photo.assert_not_called()

    def test_dry_run_lists_all_planned_actions_with_details(self):
        """Test that dry-run lists all actions with full details."""
        # Arrange
        mock_compare = Mock(spec=CompareService)
        mock_transfer = Mock(spec=TransferManager)

        missing_photo = Photo(
            id="photo2",
            filename="beach.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-02T12:00:00Z",
            width=3840,
            height=2160,
        )

        compare_result = CompareResult(
            source_account="source@example.com",
            target_account="target@example.com",
            comparison_date="2025-01-06T10:00:00Z",
            total_source_photos=2,
            total_target_photos=1,
            missing_on_target=[missing_photo],
            different_metadata=[],
            extra_on_target=[],
        )
        mock_compare.compare_accounts.return_value = compare_result

        service = SyncService(
            compare_service=mock_compare, transfer_manager=mock_transfer
        )

        # Act
        result = service.sync_accounts(
            source_account="source@example.com",
            target_account="target@example.com",
            dry_run=True,
        )

        # Assert
        assert len(result.actions) == 1
        action = result.actions[0]
        assert action.action == "add"
        assert action.photo_id == "photo2"
        assert action.photo_filename == "beach.jpg"


class TestProgressReporting:
    """Test progress reporting during sync operations."""

    def test_sync_calls_progress_callback_for_each_action(self):
        """Test that progress callback is called for each sync action."""
        # Arrange
        mock_compare = Mock(spec=CompareService)
        mock_transfer = Mock(spec=TransferManager)
        mock_progress_callback = Mock()

        source_photos = [
            Photo(
                id="photo1",
                filename="vacation.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
            Photo(
                id="photo2",
                filename="beach.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-02T12:00:00Z",
                width=3840,
                height=2160,
            ),
        ]

        compare_result = CompareResult(
            source_account="source@example.com",
            target_account="target@example.com",
            comparison_date="2025-01-06T10:00:00Z",
            total_source_photos=2,
            total_target_photos=0,
            missing_on_target=source_photos,
            different_metadata=[],
            extra_on_target=[],
        )
        mock_compare.compare_accounts.return_value = compare_result

        mock_transfer.transfer_photo.return_value = TransferResult(
            photo_id="photo1",
            status="success",
            bytes_transferred=1024000,
            retry_count=0,
        )

        service = SyncService(
            compare_service=mock_compare,
            transfer_manager=mock_transfer,
            progress_callback=mock_progress_callback,
        )

        # Act
        service.sync_accounts(
            source_account="source@example.com",
            target_account="target@example.com",
            dry_run=False,
        )

        # Assert - progress callback should be called twice (2 photos)
        assert mock_progress_callback.call_count == 2
        # Check that progress percentage increases
        calls = mock_progress_callback.call_args_list
        # First call should be at 50% (1 of 2)
        assert calls[0][0][2] == 50.0  # progress_pct
        # Second call should be at 100% (2 of 2)
        assert calls[1][0][2] == 100.0  # progress_pct

    def test_sync_reports_action_type_in_progress_callback(self):
        """Test that progress callback includes action type."""
        # Arrange
        mock_compare = Mock(spec=CompareService)
        mock_transfer = Mock(spec=TransferManager)
        mock_progress_callback = Mock()

        missing_photo = Photo(
            id="photo1",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )

        compare_result = CompareResult(
            source_account="source@example.com",
            target_account="target@example.com",
            comparison_date="2025-01-06T10:00:00Z",
            total_source_photos=1,
            total_target_photos=0,
            missing_on_target=[missing_photo],
            different_metadata=[],
            extra_on_target=[],
        )
        mock_compare.compare_accounts.return_value = compare_result

        mock_transfer.transfer_photo.return_value = TransferResult(
            photo_id="photo1",
            status="success",
            bytes_transferred=1024000,
            retry_count=0,
        )

        service = SyncService(
            compare_service=mock_compare,
            transfer_manager=mock_transfer,
            progress_callback=mock_progress_callback,
        )

        # Act
        service.sync_accounts(
            source_account="source@example.com",
            target_account="target@example.com",
            dry_run=False,
        )

        # Assert
        mock_progress_callback.assert_called_once()
        # Check callback arguments: (action, photo_id, progress_pct)
        call_args = mock_progress_callback.call_args[0]
        assert call_args[0] == "add"  # action type
        assert call_args[1] == "photo1"  # photo_id
        assert call_args[2] == 100.0  # progress_pct


class TestErrorHandling:
    """Test error handling during sync operations."""

    def test_sync_continues_on_single_transfer_failure(self):
        """Test that sync continues when a single transfer fails."""
        # Arrange
        mock_compare = Mock(spec=CompareService)
        mock_transfer = Mock(spec=TransferManager)

        source_photos = [
            Photo(
                id="photo1",
                filename="vacation.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
            Photo(
                id="photo2",
                filename="beach.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-02T12:00:00Z",
                width=3840,
                height=2160,
            ),
        ]

        compare_result = CompareResult(
            source_account="source@example.com",
            target_account="target@example.com",
            comparison_date="2025-01-06T10:00:00Z",
            total_source_photos=2,
            total_target_photos=0,
            missing_on_target=source_photos,
            different_metadata=[],
            extra_on_target=[],
        )
        mock_compare.compare_accounts.return_value = compare_result

        # First transfer fails, second succeeds
        mock_transfer.transfer_photo.side_effect = [
            TransferResult(
                photo_id="photo1",
                status="failed",
                bytes_transferred=0,
                retry_count=3,
                error_message="Network error",
            ),
            TransferResult(
                photo_id="photo2",
                status="success",
                bytes_transferred=2048000,
                retry_count=0,
            ),
        ]

        service = SyncService(
            compare_service=mock_compare, transfer_manager=mock_transfer
        )

        # Act
        result = service.sync_accounts(
            source_account="source@example.com",
            target_account="target@example.com",
            dry_run=False,
        )

        # Assert - sync should complete with partial success
        assert result.photos_added == 1  # Only successful transfer counted
        assert result.failed_actions == 1
        assert result.total_actions == 2


class TestSyncResultModel:
    """Test SyncResult data model."""

    def test_sync_result_has_required_fields(self):
        """Test that SyncResult has all required fields."""
        # Arrange & Act
        result = SyncResult(
            source_account="source@example.com",
            target_account="target@example.com",
            sync_date="2025-01-06T10:00:00Z",
            photos_added=1,
            photos_deleted=0,
            photos_updated=0,
            failed_actions=0,
            total_actions=1,
            dry_run=False,
            actions=[],
        )

        # Assert
        assert result.source_account == "source@example.com"
        assert result.target_account == "target@example.com"
        assert result.photos_added == 1
        assert result.photos_deleted == 0
        assert result.photos_updated == 0
        assert result.failed_actions == 0
        assert result.total_actions == 1
        assert result.dry_run is False


class TestSyncActionModel:
    """Test SyncAction data model."""

    def test_sync_action_has_required_fields(self):
        """Test that SyncAction has all required fields."""
        # Arrange & Act
        action = SyncAction(
            action="add",
            photo_id="photo123",
            photo_filename="vacation.jpg",
            status="completed",
        )

        # Assert
        assert action.action == "add"
        assert action.photo_id == "photo123"
        assert action.photo_filename == "vacation.jpg"
        assert action.status == "completed"
