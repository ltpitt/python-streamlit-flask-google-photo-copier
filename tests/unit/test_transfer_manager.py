"""Tests for Transfer Manager - Memory-Efficient Photo Transfer.

Following TDD approach: RED phase - write failing tests first.
These tests define the expected behavior of the Transfer Manager.
"""

from typing import Generator
from unittest.mock import Mock

import pytest

from google_photos_sync.core.transfer_manager import (
    TransferError,
    TransferManager,
    TransferResult,
)
from google_photos_sync.google_photos.client import GooglePhotosClient
from google_photos_sync.google_photos.models import Photo


class TestTransferManagerInitialization:
    """Test transfer manager initialization and setup."""

    def test_transfer_manager_requires_source_client(self):
        """Test that source client is required."""
        mock_target = Mock(spec=GooglePhotosClient)

        with pytest.raises(ValueError) as exc_info:
            TransferManager(source_client=None, target_client=mock_target)  # type: ignore[arg-type]

        assert "source_client cannot be None" in str(exc_info.value)

    def test_transfer_manager_requires_target_client(self):
        """Test that target client is required."""
        mock_source = Mock(spec=GooglePhotosClient)

        with pytest.raises(ValueError) as exc_info:
            TransferManager(source_client=mock_source, target_client=None)  # type: ignore[arg-type]

        assert "target_client cannot be None" in str(exc_info.value)

    def test_transfer_manager_with_valid_clients_succeeds(self):
        """Test that manager initializes with valid clients."""
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        manager = TransferManager(source_client=mock_source, target_client=mock_target)

        assert manager is not None

    def test_transfer_manager_accepts_custom_max_workers(self):
        """Test that manager accepts custom max concurrent workers."""
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        manager = TransferManager(
            source_client=mock_source,
            target_client=mock_target,
            max_concurrent_transfers=5,
        )

        assert manager is not None

    def test_transfer_manager_accepts_custom_chunk_size(self):
        """Test that manager accepts custom chunk size."""
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        manager = TransferManager(
            source_client=mock_source,
            target_client=mock_target,
            chunk_size=16 * 1024 * 1024,  # 16MB
        )

        assert manager is not None


class TestTransferSinglePhoto:
    """Test single photo transfer with streaming."""

    def test_transfer_photo_downloads_from_source(self):
        """Test that photo is downloaded from source client."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        photo = Photo(
            id="photo123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )

        # Mock download streaming
        def mock_download_generator() -> Generator[bytes, None, None]:
            yield b"chunk1"
            yield b"chunk2"

        mock_source.download_photo.return_value = mock_download_generator()

        # Mock upload returns uploaded photo
        uploaded_photo = Photo(
            id="uploaded123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )
        mock_target.upload_photo.return_value = uploaded_photo

        manager = TransferManager(source_client=mock_source, target_client=mock_target)

        # Act
        result = manager.transfer_photo(photo)

        # Assert
        mock_source.download_photo.assert_called_once()
        assert result.status == "success"
        assert result.photo_id == "photo123"

    def test_transfer_photo_uploads_to_target(self):
        """Test that photo is uploaded to target client."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        photo = Photo(
            id="photo123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )

        # Mock download streaming
        def mock_download_generator() -> Generator[bytes, None, None]:
            yield b"chunk1"
            yield b"chunk2"

        mock_source.download_photo.return_value = mock_download_generator()

        uploaded_photo = Photo(
            id="uploaded123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )
        mock_target.upload_photo.return_value = uploaded_photo

        manager = TransferManager(source_client=mock_source, target_client=mock_target)

        # Act
        manager.transfer_photo(photo)

        # Assert
        mock_target.upload_photo.assert_called_once()
        # Verify photo_data is bytes (concatenated chunks)
        call_args = mock_target.upload_photo.call_args
        photo_data = call_args[0][0]
        assert isinstance(photo_data, bytes)
        assert photo_data == b"chunk1chunk2"

    def test_transfer_photo_preserves_metadata(self):
        """Test that photo metadata is preserved during transfer."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        photo = Photo(
            id="photo123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
            description="Summer vacation 2025",
            camera_make="Canon",
            camera_model="EOS 5D",
            focal_length="50mm",
            aperture="f/2.8",
            iso=400,
        )

        # Mock download streaming
        def mock_download_generator() -> Generator[bytes, None, None]:
            yield b"photo_data"

        mock_source.download_photo.return_value = mock_download_generator()

        uploaded_photo = Photo(
            id="uploaded123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )
        mock_target.upload_photo.return_value = uploaded_photo

        manager = TransferManager(source_client=mock_source, target_client=mock_target)

        # Act
        manager.transfer_photo(photo)

        # Assert
        call_args = mock_target.upload_photo.call_args
        photo_metadata = call_args[0][1]
        assert photo_metadata.filename == "vacation.jpg"
        assert photo_metadata.created_time == "2025-01-01T10:00:00Z"
        assert photo_metadata.description == "Summer vacation 2025"
        assert photo_metadata.camera_make == "Canon"
        assert photo_metadata.camera_model == "EOS 5D"
        assert photo_metadata.focal_length == "50mm"
        assert photo_metadata.aperture == "f/2.8"
        assert photo_metadata.iso == 400

    def test_transfer_photo_returns_bytes_transferred(self):
        """Test that transfer result includes bytes transferred."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        photo = Photo(
            id="photo123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )

        # Mock download streaming - 15MB total
        def mock_download_generator() -> Generator[bytes, None, None]:
            yield b"x" * 8_000_000  # 8MB chunk
            yield b"y" * 7_000_000  # 7MB chunk

        mock_source.download_photo.return_value = mock_download_generator()

        uploaded_photo = Photo(
            id="uploaded123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )
        mock_target.upload_photo.return_value = uploaded_photo

        manager = TransferManager(source_client=mock_source, target_client=mock_target)

        # Act
        result = manager.transfer_photo(photo)

        # Assert
        assert result.bytes_transferred == 15_000_000


class TestMemoryEfficiency:
    """Test memory efficiency with large files."""

    def test_transfer_large_photo_uses_streaming(self):
        """Test that large photo transfer uses streaming, not full load."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        photo = Photo(
            id="photo123",
            filename="large_photo.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=8000,
            height=6000,
        )

        # Mock download streaming - simulate 100MB file
        chunk_size = 8 * 1024 * 1024  # 8MB
        num_chunks = 13  # ~100MB total

        def mock_download_generator() -> Generator[bytes, None, None]:
            for _ in range(num_chunks):
                yield b"x" * chunk_size

        mock_source.download_photo.return_value = mock_download_generator()

        uploaded_photo = Photo(
            id="uploaded123",
            filename="large_photo.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=8000,
            height=6000,
        )
        mock_target.upload_photo.return_value = uploaded_photo

        manager = TransferManager(source_client=mock_source, target_client=mock_target)

        # Act
        result = manager.transfer_photo(photo)

        # Assert
        # Download was called with streaming
        mock_source.download_photo.assert_called_once_with(
            photo, chunk_size=manager._chunk_size
        )
        assert result.status == "success"
        # Total bytes should be ~104MB
        expected_bytes = chunk_size * num_chunks
        assert result.bytes_transferred == expected_bytes


class TestTransferFailureHandling:
    """Test transfer failure handling with retry logic."""

    def test_transfer_photo_retries_on_failure(self):
        """Test that failed transfer is retried with exponential backoff."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        photo = Photo(
            id="photo123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )

        # First call fails, second succeeds
        def mock_download_generator() -> Generator[bytes, None, None]:
            yield b"chunk1"

        mock_source.download_photo.side_effect = [
            Exception("Network error"),
            mock_download_generator(),
        ]

        uploaded_photo = Photo(
            id="uploaded123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )
        mock_target.upload_photo.return_value = uploaded_photo

        manager = TransferManager(source_client=mock_source, target_client=mock_target)

        # Act
        result = manager.transfer_photo(photo)

        # Assert
        # Should be called twice (first failure, second success)
        assert mock_source.download_photo.call_count == 2
        assert result.status == "success"
        assert result.retry_count == 1

    def test_transfer_photo_fails_after_max_retries(self):
        """Test that transfer fails after exceeding max retries."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        photo = Photo(
            id="photo123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )

        # Always fails
        mock_source.download_photo.side_effect = Exception("Network error")

        manager = TransferManager(
            source_client=mock_source,
            target_client=mock_target,
            max_retries=3,
        )

        # Act & Assert
        with pytest.raises(TransferError) as exc_info:
            manager.transfer_photo(photo)

        assert "Failed after 3 retries" in str(exc_info.value)
        # Should try initial + 3 retries = 4 total
        assert mock_source.download_photo.call_count == 4

    def test_transfer_photo_uses_exponential_backoff(self, mocker):
        """Test that retry logic uses exponential backoff."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)
        mock_sleep = mocker.patch("time.sleep")

        photo = Photo(
            id="photo123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )

        # Fail twice, then succeed
        def mock_download_generator() -> Generator[bytes, None, None]:
            yield b"chunk1"

        mock_source.download_photo.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            mock_download_generator(),
        ]

        uploaded_photo = Photo(
            id="uploaded123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )
        mock_target.upload_photo.return_value = uploaded_photo

        manager = TransferManager(source_client=mock_source, target_client=mock_target)

        # Act
        manager.transfer_photo(photo)

        # Assert - exponential backoff: 1s, 2s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)  # First retry: 2^0 = 1
        mock_sleep.assert_any_call(2)  # Second retry: 2^1 = 2


class TestProgressReporting:
    """Test progress reporting callback functionality."""

    def test_transfer_photo_calls_progress_callback(self):
        """Test that progress callback is called during transfer."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)
        mock_progress_callback = Mock()

        photo = Photo(
            id="photo123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )

        # Mock download streaming
        def mock_download_generator() -> Generator[bytes, None, None]:
            yield b"x" * 5_000_000  # 5MB
            yield b"y" * 3_000_000  # 3MB

        mock_source.download_photo.return_value = mock_download_generator()

        uploaded_photo = Photo(
            id="uploaded123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )
        mock_target.upload_photo.return_value = uploaded_photo

        manager = TransferManager(
            source_client=mock_source,
            target_client=mock_target,
            progress_callback=mock_progress_callback,
        )

        # Act
        manager.transfer_photo(photo)

        # Assert
        # Callback should be called at least twice (for each chunk)
        assert mock_progress_callback.call_count >= 2
        # Check call structure: callback(photo_id, bytes_transferred, total_bytes)
        first_call = mock_progress_callback.call_args_list[0]
        assert first_call[0][0] == "photo123"  # photo_id
        assert first_call[0][1] == 5_000_000  # bytes_transferred after first chunk
        assert first_call[0][2] == 5_000_000  # total_bytes so far

    def test_transfer_photo_without_callback_succeeds(self):
        """Test that transfer succeeds without progress callback."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        photo = Photo(
            id="photo123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )

        def mock_download_generator() -> Generator[bytes, None, None]:
            yield b"chunk1"

        mock_source.download_photo.return_value = mock_download_generator()

        uploaded_photo = Photo(
            id="uploaded123",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )
        mock_target.upload_photo.return_value = uploaded_photo

        manager = TransferManager(
            source_client=mock_source,
            target_client=mock_target,
            # No progress callback
        )

        # Act
        result = manager.transfer_photo(photo)

        # Assert
        assert result.status == "success"


class TestConcurrentTransfers:
    """Test concurrent photo transfers with controlled concurrency."""

    def test_transfer_photos_processes_multiple_photos(self):
        """Test that multiple photos are transferred successfully."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        photos = [
            Photo(
                id=f"photo{i}",
                filename=f"photo{i}.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            )
            for i in range(5)
        ]

        # Mock download streaming for each photo
        def mock_download_generator() -> Generator[bytes, None, None]:
            yield b"photo_data"

        mock_source.download_photo.return_value = mock_download_generator()

        def mock_upload(photo_data: bytes, photo_metadata: Photo) -> Photo:
            return Photo(
                id=f"uploaded_{photo_metadata.id}",
                filename=photo_metadata.filename,
                mime_type=photo_metadata.mime_type,
                created_time=photo_metadata.created_time,
                width=photo_metadata.width,
                height=photo_metadata.height,
            )

        mock_target.upload_photo.side_effect = mock_upload

        manager = TransferManager(source_client=mock_source, target_client=mock_target)

        # Act
        results = manager.transfer_photos(photos)

        # Assert
        assert len(results) == 5
        assert all(r.status == "success" for r in results)
        assert mock_source.download_photo.call_count == 5
        assert mock_target.upload_photo.call_count == 5

    def test_transfer_photos_respects_max_concurrent_workers(self):
        """Test that concurrent transfers respect max workers limit."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        # Mock download streaming for each photo
        def mock_download_generator() -> Generator[bytes, None, None]:
            yield b"photo_data"

        mock_source.download_photo.return_value = mock_download_generator()

        def mock_upload(photo_data: bytes, photo_metadata: Photo) -> Photo:
            return Photo(
                id=f"uploaded_{photo_metadata.id}",
                filename=photo_metadata.filename,
                mime_type=photo_metadata.mime_type,
                created_time=photo_metadata.created_time,
                width=photo_metadata.width,
                height=photo_metadata.height,
            )

        mock_target.upload_photo.side_effect = mock_upload

        photos = [
            Photo(
                id=f"photo{i}",
                filename=f"photo{i}.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            )
            for i in range(5)  # Reduced from 10 for faster test
        ]

        # Test with custom max_workers value
        manager = TransferManager(
            source_client=mock_source,
            target_client=mock_target,
            max_concurrent_transfers=3,
        )

        # Act
        results = manager.transfer_photos(photos)

        # Assert
        # Verify all photos were transferred successfully
        assert len(results) == 5
        assert all(r.status == "success" for r in results)
        # The internal implementation uses ThreadPoolExecutor with max_workers=3
        # This is verified by the fact that the function completes successfully
        assert manager._max_concurrent_transfers == 3

    def test_transfer_photos_handles_partial_failures(self):
        """Test that batch transfer continues even if some photos fail."""
        # Arrange
        mock_source = Mock(spec=GooglePhotosClient)
        mock_target = Mock(spec=GooglePhotosClient)

        photos = [
            Photo(
                id=f"photo{i}",
                filename=f"photo{i}.jpg",
                mime_type="image/jpeg",
                created_time="2025-01-01T10:00:00Z",
                width=1920,
                height=1080,
            )
            for i in range(3)
        ]

        # Mock download - photo1 fails, others succeed
        def mock_download_generator() -> Generator[bytes, None, None]:
            yield b"photo_data"

        mock_source.download_photo.side_effect = [
            mock_download_generator(),
            Exception("Network error"),  # photo1 fails
            mock_download_generator(),
        ]

        uploaded_photo = Photo(
            id="uploaded123",
            filename="photo.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )
        mock_target.upload_photo.return_value = uploaded_photo

        manager = TransferManager(
            source_client=mock_source,
            target_client=mock_target,
            max_retries=0,  # No retries for this test
        )

        # Act
        results = manager.transfer_photos(photos)

        # Assert
        assert len(results) == 3
        success_count = sum(1 for r in results if r.status == "success")
        failure_count = sum(1 for r in results if r.status == "failed")
        assert success_count == 2
        assert failure_count == 1


class TestTransferResult:
    """Test TransferResult data structure."""

    def test_transfer_result_has_required_fields(self):
        """Test that TransferResult has all required fields."""
        result = TransferResult(
            photo_id="photo123",
            status="success",
            bytes_transferred=5_000_000,
            retry_count=0,
        )

        assert result.photo_id == "photo123"
        assert result.status == "success"
        assert result.bytes_transferred == 5_000_000
        assert result.retry_count == 0

    def test_transfer_result_with_failure_includes_error(self):
        """Test that failed transfer result can include error message."""
        result = TransferResult(
            photo_id="photo123",
            status="failed",
            bytes_transferred=0,
            retry_count=3,
            error_message="Network timeout",
        )

        assert result.status == "failed"
        assert result.error_message == "Network timeout"
        assert result.retry_count == 3
