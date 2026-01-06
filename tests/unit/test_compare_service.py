"""Tests for Compare Service - Account Comparison Logic.

Following TDD approach: RED phase - write failing tests first.
These tests define the expected behavior of the Compare Service.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from google_photos_sync.core.compare_service import CompareService
from google_photos_sync.google_photos.client import GooglePhotosClient
from google_photos_sync.google_photos.models import Photo


class TestCompareServiceInitialization:
    """Test compare service initialization and setup."""

    def test_compare_service_requires_source_client(self):
        """Test that source client is required."""
        mock_target = Mock(spec=GooglePhotosClient)

        with pytest.raises(ValueError) as exc_info:
            CompareService(source_client=None, target_client=mock_target)  # type: ignore[arg-type]

        assert "source_client cannot be None" in str(exc_info.value)

    def test_compare_service_requires_target_client(self):
        """Test that target client is required."""
        mock_source = Mock(spec=GooglePhotosClient)

        with pytest.raises(ValueError) as exc_info:
            CompareService(source_client=mock_source, target_client=None)  # type: ignore[arg-type]

        assert "target_client cannot be None" in str(exc_info.value)

    def test_compare_service_with_valid_clients_succeeds(self):
        """Test that service initializes with valid clients."""
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        service = CompareService(source_client=mock_source, target_client=mock_target)

        assert service is not None


class TestCompareAccountsBasicScenarios:
    """Test basic account comparison scenarios."""

    def test_compare_identical_accounts_returns_no_differences(self):
        """Test comparing two identical accounts returns no differences."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        identical_photos = [
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

        mock_source.list_photos.return_value = identical_photos
        mock_target.list_photos.return_value = identical_photos

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )

        # Assert
        assert result.source_account == "user@example.com"
        assert result.target_account == "backup@example.com"
        assert result.total_source_photos == 2
        assert result.total_target_photos == 2
        assert len(result.missing_on_target) == 0
        assert len(result.different_metadata) == 0
        assert len(result.extra_on_target) == 0

    def test_compare_empty_accounts_returns_no_differences(self):
        """Test comparing two empty accounts returns no differences."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        mock_source.list_photos.return_value = []
        mock_target.list_photos.return_value = []

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )

        # Assert
        assert result.total_source_photos == 0
        assert result.total_target_photos == 0
        assert len(result.missing_on_target) == 0
        assert len(result.different_metadata) == 0
        assert len(result.extra_on_target) == 0


class TestCompareMissingPhotos:
    """Test identification of photos missing on target."""

    def test_compare_identifies_photos_missing_on_target(self):
        """Test that photos on source but not on target are identified."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

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
            Photo(
                id="photo3",
                filename="sunset.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-03T18:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        target_photos = [
            Photo(
                id="photo1",
                filename="vacation.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        mock_source.list_photos.return_value = source_photos
        mock_target.list_photos.return_value = target_photos

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )

        # Assert
        assert result.total_source_photos == 3
        assert result.total_target_photos == 1
        assert len(result.missing_on_target) == 2
        assert result.missing_on_target[0].id == "photo2"
        assert result.missing_on_target[1].id == "photo3"
        assert len(result.extra_on_target) == 0

    def test_compare_with_empty_target_all_photos_missing(self):
        """Test that all source photos are missing when target is empty."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

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

        mock_source.list_photos.return_value = source_photos
        mock_target.list_photos.return_value = []

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )

        # Assert
        assert result.total_source_photos == 2
        assert result.total_target_photos == 0
        assert len(result.missing_on_target) == 2


class TestCompareExtraPhotos:
    """Test identification of extra photos on target."""

    def test_compare_identifies_extra_photos_on_target(self):
        """Test that photos on target but not on source are identified."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        source_photos = [
            Photo(
                id="photo1",
                filename="vacation.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

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
                id="photo_extra1",
                filename="extra1.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-05T10:00:00Z",
                width=1920,
                height=1080,
            ),
            Photo(
                id="photo_extra2",
                filename="extra2.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-06T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        mock_source.list_photos.return_value = source_photos
        mock_target.list_photos.return_value = target_photos

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )

        # Assert
        assert result.total_source_photos == 1
        assert result.total_target_photos == 3
        assert len(result.extra_on_target) == 2
        assert result.extra_on_target[0].id == "photo_extra1"
        assert result.extra_on_target[1].id == "photo_extra2"
        assert len(result.missing_on_target) == 0


class TestCompareDifferentMetadata:
    """Test identification of photos with different metadata."""

    def test_compare_identifies_different_filename(self):
        """Test that photos with different filenames are identified."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        source_photos = [
            Photo(
                id="photo1",
                filename="vacation_original.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        target_photos = [
            Photo(
                id="photo1",
                filename="vacation_renamed.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        mock_source.list_photos.return_value = source_photos
        mock_target.list_photos.return_value = target_photos

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )

        # Assert
        assert len(result.different_metadata) == 1
        assert result.different_metadata[0]["photo_id"] == "photo1"
        assert result.different_metadata[0]["field"] == "filename"
        assert result.different_metadata[0]["source_value"] == "vacation_original.jpg"
        assert result.different_metadata[0]["target_value"] == "vacation_renamed.jpg"

    def test_compare_identifies_different_created_time(self):
        """Test that photos with different creation times are identified."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        source_photos = [
            Photo(
                id="photo1",
                filename="vacation.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        target_photos = [
            Photo(
                id="photo1",
                filename="vacation.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T12:00:00Z",  # Different time!
                width=1920,
                height=1080,
            ),
        ]

        mock_source.list_photos.return_value = source_photos
        mock_target.list_photos.return_value = target_photos

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )

        # Assert
        assert len(result.different_metadata) == 1
        assert result.different_metadata[0]["photo_id"] == "photo1"
        assert result.different_metadata[0]["field"] == "created_time"

    def test_compare_identifies_multiple_metadata_differences(self):
        """Test that multiple metadata differences are identified for same photo."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        source_photos = [
            Photo(
                id="photo1",
                filename="vacation.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        target_photos = [
            Photo(
                id="photo1",
                filename="vacation_renamed.jpg",  # Different filename
                mime_type="image/jpeg",
                created_time="2025-01-01T12:00:00Z",  # Different time
                width=3840,  # Different width
                height=2160,  # Different height
            ),
        ]

        mock_source.list_photos.return_value = source_photos
        mock_target.list_photos.return_value = target_photos

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )

        # Assert
        assert len(result.different_metadata) == 4  # 4 different fields
        fields = [diff["field"] for diff in result.different_metadata]
        assert "filename" in fields
        assert "created_time" in fields
        assert "width" in fields
        assert "height" in fields


class TestCompareComplexScenarios:
    """Test complex scenarios with multiple types of differences."""

    def test_compare_with_missing_extra_and_different_metadata(self):
        """Test scenario with all types of differences simultaneously."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

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
            Photo(
                id="photo3",
                filename="sunset.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-03T18:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        target_photos = [
            Photo(
                id="photo1",
                filename="vacation_renamed.jpg",  # Different metadata
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
            Photo(
                id="photo_extra",
                filename="extra.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-05T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]
        # photo3 is missing on target

        mock_source.list_photos.return_value = source_photos
        mock_target.list_photos.return_value = target_photos

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )

        # Assert
        assert result.total_source_photos == 3
        assert result.total_target_photos == 3
        assert len(result.missing_on_target) == 1
        assert result.missing_on_target[0].id == "photo3"
        assert len(result.extra_on_target) == 1
        assert result.extra_on_target[0].id == "photo_extra"
        assert len(result.different_metadata) >= 1


class TestCompareResultJsonOutput:
    """Test JSON serialization of comparison results."""

    def test_compare_result_to_json_has_correct_structure(self):
        """Test that CompareResult can be serialized to JSON with correct structure."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        source_photos = [
            Photo(
                id="photo1",
                filename="vacation.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        mock_source.list_photos.return_value = source_photos
        mock_target.list_photos.return_value = []

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )
        json_output = result.to_json()

        # Assert
        assert "source_account" in json_output
        assert "target_account" in json_output
        assert "comparison_date" in json_output
        assert "total_source_photos" in json_output
        assert "total_target_photos" in json_output
        assert "missing_on_target" in json_output
        assert "different_metadata" in json_output
        assert "extra_on_target" in json_output

        assert json_output["source_account"] == "user@example.com"
        assert json_output["target_account"] == "backup@example.com"
        assert json_output["total_source_photos"] == 1
        assert json_output["total_target_photos"] == 0


class TestComparePerformance:
    """Test performance with large datasets."""

    def test_compare_handles_large_dataset_efficiently(self):
        """Test comparing 1000+ photos completes efficiently."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        # Create 1500 photos for source
        source_photos = [
            Photo(
                id=f"photo{i}",
                filename=f"photo{i}.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            )
            for i in range(1500)
        ]

        # Create 1000 photos for target (first 1000 from source)
        target_photos = source_photos[:1000]

        mock_source.list_photos.return_value = source_photos
        mock_target.list_photos.return_value = target_photos

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        import time

        start_time = time.time()
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert result.total_source_photos == 1500
        assert result.total_target_photos == 1000
        assert len(result.missing_on_target) == 500
        # Should complete in reasonable time (< 5 seconds for 1500 photos)
        assert elapsed_time < 5.0


class TestCompareEdgeCases:
    """Test edge cases and error conditions."""

    def test_compare_with_empty_source_and_full_target(self):
        """Test comparing when source is empty but target has photos."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        target_photos = [
            Photo(
                id="photo1",
                filename="vacation.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            ),
        ]

        mock_source.list_photos.return_value = []
        mock_target.list_photos.return_value = target_photos

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )

        # Assert
        assert result.total_source_photos == 0
        assert result.total_target_photos == 1
        assert len(result.missing_on_target) == 0
        assert len(result.extra_on_target) == 1

    def test_compare_result_has_valid_comparison_date(self):
        """Test that comparison result includes a valid ISO 8601 timestamp."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        mock_source.list_photos.return_value = []
        mock_target.list_photos.return_value = []

        service = CompareService(source_client=mock_source, target_client=mock_target)

        # Act
        result = service.compare_accounts(
            source_account="user@example.com", target_account="backup@example.com"
        )

        # Assert
        assert result.comparison_date is not None
        # Verify it's a valid ISO 8601 timestamp
        datetime.fromisoformat(result.comparison_date.replace("Z", "+00:00"))
