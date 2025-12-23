"""Tests for Google Photos API client wrapper.

Following TDD approach: RED phase - write failing tests first.
These tests define the expected behavior of the Google Photos client.
"""

from io import BytesIO
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from google_photos_sync.google_photos.client import (
    GooglePhotosClient,
    PhotosAPIError,
    RateLimitError,
)
from google_photos_sync.google_photos.models import Photo


class TestClientInitialization:
    """Test client initialization and setup."""

    def test_client_with_valid_credentials_succeeds(self, mocker):
        """Test that client initializes with valid credentials."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_build = mocker.patch(
            "google_photos_sync.google_photos.client.build"
        )
        mock_service = mocker.Mock()
        mock_build.return_value = mock_service

        # Act
        client = GooglePhotosClient(credentials=mock_credentials)

        # Assert
        assert client is not None
        mock_build.assert_called_once_with(
            "photoslibrary", "v1", credentials=mock_credentials
        )

    def test_client_with_none_credentials_raises_value_error(self):
        """Test that None credentials raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GooglePhotosClient(credentials=None)  # type: ignore[arg-type]
        assert "credentials cannot be None" in str(exc_info.value)


class TestListPhotos:
    """Test listing photos with pagination support."""

    def test_list_photos_returns_all_photos_from_single_page(self, mocker):
        """Test listing photos when all fit in single page."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        # Mock API response
        mock_list = mock_media_items.list
        mock_list.return_value.execute.return_value = {
            "mediaItems": [
                {
                    "id": "photo1",
                    "filename": "vacation.jpg",
                    "mimeType": "image/jpeg",
                    "mediaMetadata": {
                        "creationTime": "2025-01-01T10:00:00Z",
                        "width": "1920",
                        "height": "1080",
                    },
                    "baseUrl": "https://example.com/photo1",
                    "productUrl": "https://photos.google.com/photo1",
                },
                {
                    "id": "photo2",
                    "filename": "beach.jpg",
                    "mimeType": "image/jpeg",
                    "mediaMetadata": {
                        "creationTime": "2025-01-02T12:00:00Z",
                        "width": "3840",
                        "height": "2160",
                    },
                    "baseUrl": "https://example.com/photo2",
                    "productUrl": "https://photos.google.com/photo2",
                },
            ]
        }

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            client = GooglePhotosClient(credentials=mock_credentials)

            # Act
            photos = client.list_photos()

            # Assert
            assert len(photos) == 2
            assert photos[0].id == "photo1"
            assert photos[0].filename == "vacation.jpg"
            assert photos[0].mime_type == "image/jpeg"
            assert photos[1].id == "photo2"
            assert photos[1].filename == "beach.jpg"

    def test_list_photos_handles_pagination_across_multiple_pages(self, mocker):
        """Test pagination when photos span multiple pages."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        # Mock API responses with pagination
        mock_list = mock_media_items.list

        # First page with nextPageToken
        page1_response = {
            "mediaItems": [
                {
                    "id": "photo1",
                    "filename": "photo1.jpg",
                    "mimeType": "image/jpeg",
                    "mediaMetadata": {
                        "creationTime": "2025-01-01T10:00:00Z",
                        "width": "1920",
                        "height": "1080",
                    },
                    "baseUrl": "https://example.com/photo1",
                }
            ],
            "nextPageToken": "token123",
        }

        # Second page without nextPageToken (last page)
        page2_response = {
            "mediaItems": [
                {
                    "id": "photo2",
                    "filename": "photo2.jpg",
                    "mimeType": "image/jpeg",
                    "mediaMetadata": {
                        "creationTime": "2025-01-02T12:00:00Z",
                        "width": "1920",
                        "height": "1080",
                    },
                    "baseUrl": "https://example.com/photo2",
                }
            ]
        }

        # Setup mock responses for both calls to list()
        mock_request1 = Mock()
        mock_request1.execute.return_value = page1_response
        
        mock_request2 = Mock()
        mock_request2.execute.return_value = page2_response
        
        # Return different request objects for first and second call
        mock_list.side_effect = [mock_request1, mock_request2]

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            client = GooglePhotosClient(credentials=mock_credentials)

            # Act
            photos = client.list_photos()

            # Assert
            assert len(photos) == 2
            assert photos[0].id == "photo1"
            assert photos[1].id == "photo2"
            # Verify list was called twice (once for each page)
            assert mock_list.call_count == 2

    def test_list_photos_with_empty_library_returns_empty_list(self, mocker):
        """Test listing photos when library is empty."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        mock_list = mock_media_items.list
        mock_list.return_value.execute.return_value = {}

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            client = GooglePhotosClient(credentials=mock_credentials)

            # Act
            photos = client.list_photos()

            # Assert
            assert photos == []


class TestGetPhotoMetadata:
    """Test fetching complete photo metadata."""

    def test_get_photo_metadata_returns_complete_metadata(self, mocker):
        """Test that all metadata fields are correctly extracted."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        # Mock API response with complete metadata
        mock_get = mock_media_items.get
        mock_get.return_value.execute.return_value = {
            "id": "test-photo-123",
            "filename": "sunset.jpg",
            "mimeType": "image/jpeg",
            "mediaMetadata": {
                "creationTime": "2025-01-01T18:30:00Z",
                "width": "4032",
                "height": "3024",
                "photo": {
                    "cameraMake": "Canon",
                    "cameraModel": "EOS 5D Mark IV",
                    "focalLength": 50.0,
                    "apertureFNumber": 2.8,
                    "isoEquivalent": 400,
                },
            },
            "baseUrl": "https://example.com/photo",
            "productUrl": "https://photos.google.com/photo",
            "description": "Beautiful sunset over the ocean",
        }

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            client = GooglePhotosClient(credentials=mock_credentials)

            # Act
            photo = client.get_photo_metadata(photo_id="test-photo-123")

            # Assert
            assert photo.id == "test-photo-123"
            assert photo.filename == "sunset.jpg"
            assert photo.mime_type == "image/jpeg"
            assert photo.created_time == "2025-01-01T18:30:00Z"
            assert photo.width == 4032
            assert photo.height == 3024
            assert photo.camera_make == "Canon"
            assert photo.camera_model == "EOS 5D Mark IV"
            assert photo.focal_length == "50.0mm"
            assert photo.aperture == "f/2.8"
            assert photo.iso == 400
            assert photo.description == "Beautiful sunset over the ocean"

    def test_get_photo_metadata_with_location_data(self, mocker):
        """Test metadata extraction with GPS location data."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        mock_get = mock_media_items.get
        mock_get.return_value.execute.return_value = {
            "id": "photo-with-location",
            "filename": "paris.jpg",
            "mimeType": "image/jpeg",
            "mediaMetadata": {
                "creationTime": "2025-01-15T14:00:00Z",
                "width": "1920",
                "height": "1080",
                "photo": {
                    "cameraMake": "Google",
                    "cameraModel": "Pixel 8 Pro",
                },
            },
            "baseUrl": "https://example.com/photo",
            "contributorInfo": {
                "profilePictureBaseUrl": "https://example.com/profile",
                "displayName": "John Doe",
            },
        }

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            client = GooglePhotosClient(credentials=mock_credentials)

            # Act
            photo = client.get_photo_metadata(photo_id="photo-with-location")

            # Assert
            assert photo.id == "photo-with-location"
            assert photo.camera_make == "Google"
            assert photo.camera_model == "Pixel 8 Pro"

    def test_get_photo_metadata_with_invalid_id_raises_error(self, mocker):
        """Test that invalid photo ID raises PhotosAPIError."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        # Mock 404 error
        mock_get = mock_media_items.get
        mock_error = HttpError(
            resp=Mock(status=404), content=b"Photo not found"
        )
        mock_get.return_value.execute.side_effect = mock_error

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            client = GooglePhotosClient(credentials=mock_credentials)

            # Act & Assert
            with pytest.raises(PhotosAPIError) as exc_info:
                client.get_photo_metadata(photo_id="invalid-id")
            assert "Failed to get photo metadata" in str(exc_info.value)


class TestDownloadPhoto:
    """Test photo download with streaming for memory efficiency."""

    def test_download_photo_uses_streaming_to_avoid_memory_load(self, mocker):
        """Test that download uses streaming instead of loading all in memory."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()

        # Mock photo data
        photo_data = b"fake-photo-binary-data" * 1000  # Simulate larger file
        photo = Photo(
            id="stream-test-photo",
            filename="large.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=4000,
            height=3000,
            base_url="https://example.com/photo?download=true",
        )

        # Mock requests.get for streaming download
        mock_response = Mock()
        mock_response.iter_content.return_value = [photo_data[i:i+1024] for i in range(0, len(photo_data), 1024)]
        mock_response.raise_for_status.return_value = None

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            with patch("google_photos_sync.google_photos.client.requests") as mock_requests:
                mock_requests.get.return_value = mock_response

                client = GooglePhotosClient(credentials=mock_credentials)

                # Act
                result_stream = client.download_photo(photo=photo)
                
                # Consume the stream
                downloaded_data = b"".join(chunk for chunk in result_stream)

                # Assert
                assert downloaded_data == photo_data
                # Verify streaming was used
                mock_requests.get.assert_called_once()
                call_kwargs = mock_requests.get.call_args[1]
                assert call_kwargs.get("stream") is True

    def test_download_photo_with_chunk_size_parameter(self, mocker):
        """Test that chunk size can be customized for downloads."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()

        photo_data = b"fake-data" * 100
        photo = Photo(
            id="chunk-test-photo",
            filename="test.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
            base_url="https://example.com/photo",
        )

        mock_response = Mock()
        mock_response.iter_content.return_value = [photo_data]
        mock_response.raise_for_status.return_value = None

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            with patch("google_photos_sync.google_photos.client.requests") as mock_requests:
                mock_requests.get.return_value = mock_response

                client = GooglePhotosClient(credentials=mock_credentials)

                # Act
                chunk_size = 16 * 1024 * 1024  # 16MB
                result_stream = client.download_photo(
                    photo=photo, chunk_size=chunk_size
                )
                
                # Consume stream
                _ = b"".join(chunk for chunk in result_stream)

                # Assert
                mock_response.iter_content.assert_called_once_with(
                    chunk_size=chunk_size
                )

    def test_download_photo_without_base_url_raises_error(self, mocker):
        """Test that photo without base_url raises error."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()

        photo = Photo(
            id="no-url-photo",
            filename="test.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
            base_url=None,  # Missing URL
        )

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            client = GooglePhotosClient(credentials=mock_credentials)

            # Act & Assert
            with pytest.raises(PhotosAPIError) as exc_info:
                list(client.download_photo(photo=photo))
            assert "Photo has no base_url" in str(exc_info.value)


class TestUploadPhoto:
    """Test photo upload with metadata preservation."""

    def test_upload_photo_preserves_all_metadata(self, mocker):
        """Test that upload preserves creation time and description."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_credentials.token = "test-access-token"  # Add token attribute
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        photo_data = b"fake-photo-data"
        photo = Photo(
            id="source-photo-id",
            filename="vacation.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
            description="Summer vacation 2025",
        )

        # Mock upload token response
        mock_uploads = mock_service.mediaItems.return_value
        mock_upload_token = "upload-token-123"

        # Mock batchCreate response
        mock_batch_create = mock_media_items.batchCreate
        mock_batch_create.return_value.execute.return_value = {
            "newMediaItemResults": [
                {
                    "status": {"message": "Success"},
                    "mediaItem": {
                        "id": "new-photo-id",
                        "filename": "vacation.jpg",
                        "mimeType": "image/jpeg",
                        "mediaMetadata": {
                            "creationTime": "2025-01-01T10:00:00Z",
                            "width": "1920",
                            "height": "1080",
                        },
                        "description": "Summer vacation 2025",
                    },
                }
            ]
        }

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            with patch(
                "google_photos_sync.google_photos.client.requests"
            ) as mock_requests:
                # Mock upload request
                mock_upload_response = Mock()
                mock_upload_response.text = mock_upload_token
                mock_upload_response.raise_for_status.return_value = None
                mock_requests.post.return_value = mock_upload_response

                client = GooglePhotosClient(credentials=mock_credentials)

                # Act
                uploaded_photo = client.upload_photo(
                    photo_data=photo_data, photo_metadata=photo
                )

                # Assert
                assert uploaded_photo.id == "new-photo-id"
                assert uploaded_photo.filename == "vacation.jpg"
                assert uploaded_photo.description == "Summer vacation 2025"
                assert uploaded_photo.created_time == "2025-01-01T10:00:00Z"

                # Verify batchCreate was called with correct metadata
                call_args = mock_batch_create.call_args
                body = call_args[1]["body"]
                assert body["newMediaItems"][0]["description"] == "Summer vacation 2025"
                assert (
                    body["newMediaItems"][0]["simpleMediaItem"]["uploadToken"]
                    == mock_upload_token
                )

    def test_upload_photo_handles_upload_failure(self, mocker):
        """Test that upload failures are properly handled."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()

        photo_data = b"fake-data"
        photo = Photo(
            id="test-photo",
            filename="test.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        )

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            with patch(
                "google_photos_sync.google_photos.client.requests"
            ) as mock_requests:
                # Mock upload failure
                mock_requests.post.side_effect = Exception("Upload failed")

                client = GooglePhotosClient(credentials=mock_credentials)

                # Act & Assert
                with pytest.raises(PhotosAPIError) as exc_info:
                    client.upload_photo(photo_data=photo_data, photo_metadata=photo)
                assert "Failed to upload photo" in str(exc_info.value)


class TestRateLimiting:
    """Test rate limiting handling with exponential backoff."""

    def test_list_photos_handles_rate_limit_with_exponential_backoff(self, mocker):
        """Test that 429 errors trigger exponential backoff retry."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        # Mock rate limit error on first call, success on second
        mock_list = mock_media_items.list

        rate_limit_error = HttpError(
            resp=Mock(status=429), content=b"Rate limit exceeded"
        )

        success_response = {
            "mediaItems": [
                {
                    "id": "photo1",
                    "filename": "test.jpg",
                    "mimeType": "image/jpeg",
                    "mediaMetadata": {
                        "creationTime": "2025-01-01T10:00:00Z",
                        "width": "1920",
                        "height": "1080",
                    },
                    "baseUrl": "https://example.com/photo1",
                }
            ]
        }

        mock_request = Mock()
        mock_request.execute.side_effect = [rate_limit_error, success_response]
        mock_list.return_value = mock_request

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            # Mock time.sleep to avoid actual delays in tests
            with patch("google_photos_sync.google_photos.client.time") as mock_time:
                client = GooglePhotosClient(credentials=mock_credentials)

                # Act
                photos = client.list_photos()

                # Assert
                assert len(photos) == 1
                assert photos[0].id == "photo1"
                # Verify sleep was called for backoff (at least once)
                assert mock_time.sleep.call_count >= 1

    def test_rate_limit_exceeds_max_retries_raises_error(self, mocker):
        """Test that exceeding max retries raises RateLimitError."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        # Mock continuous rate limit errors
        mock_list = mock_media_items.list
        rate_limit_error = HttpError(
            resp=Mock(status=429), content=b"Rate limit exceeded"
        )

        mock_request = Mock()
        mock_request.execute.side_effect = rate_limit_error
        mock_list.return_value = mock_request

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            with patch("google_photos_sync.google_photos.client.time"):
                client = GooglePhotosClient(credentials=mock_credentials)

                # Act & Assert
                with pytest.raises(RateLimitError) as exc_info:
                    client.list_photos()
                assert "Rate limit exceeded after" in str(exc_info.value)

    def test_backoff_uses_exponential_delays(self, mocker):
        """Test that retry delays increase exponentially."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        rate_limit_error = HttpError(
            resp=Mock(status=429), content=b"Rate limit exceeded"
        )

        success_response = {
            "mediaItems": [
                {
                    "id": "photo1",
                    "filename": "test.jpg",
                    "mimeType": "image/jpeg",
                    "mediaMetadata": {
                        "creationTime": "2025-01-01T10:00:00Z",
                        "width": "1920",
                        "height": "1080",
                    },
                    "baseUrl": "https://example.com/photo1",
                }
            ]
        }

        mock_request = Mock()
        # Fail twice, then succeed
        mock_request.execute.side_effect = [
            rate_limit_error,
            rate_limit_error,
            success_response,
        ]
        mock_media_items.list.return_value = mock_request

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            with patch("google_photos_sync.google_photos.client.time") as mock_time:
                client = GooglePhotosClient(credentials=mock_credentials)

                # Act
                photos = client.list_photos()

                # Assert
                assert len(photos) == 1
                # Verify exponential backoff: 1s, 2s
                sleep_calls = [call[0][0] for call in mock_time.sleep.call_args_list]
                assert len(sleep_calls) == 2
                assert sleep_calls[0] == 1  # First retry: 1 second
                assert sleep_calls[1] == 2  # Second retry: 2 seconds


class TestErrorHandling:
    """Test error handling for various API errors."""

    def test_handles_network_errors_gracefully(self, mocker):
        """Test that network errors are caught and wrapped."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        mock_list = mock_media_items.list
        mock_list.return_value.execute.side_effect = ConnectionError(
            "Network error"
        )

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            client = GooglePhotosClient(credentials=mock_credentials)

            # Act & Assert
            with pytest.raises(PhotosAPIError) as exc_info:
                client.list_photos()
            assert "Failed to list photos" in str(exc_info.value)

    def test_handles_invalid_json_response(self, mocker):
        """Test that invalid JSON responses are handled."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        # Mock response with invalid structure
        mock_list = mock_media_items.list
        mock_list.return_value.execute.return_value = {"invalid": "structure"}

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            client = GooglePhotosClient(credentials=mock_credentials)

            # Act
            photos = client.list_photos()

            # Assert - should handle gracefully and return empty list
            assert photos == []

    def test_handles_403_permission_error(self, mocker):
        """Test that 403 permission errors are properly reported."""
        # Arrange
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_service = mocker.Mock()
        mock_media_items = mock_service.mediaItems.return_value

        mock_get = mock_media_items.get
        permission_error = HttpError(
            resp=Mock(status=403), content=b"Permission denied"
        )
        mock_get.return_value.execute.side_effect = permission_error

        with patch(
            "google_photos_sync.google_photos.client.build",
            return_value=mock_service,
        ):
            client = GooglePhotosClient(credentials=mock_credentials)

            # Act & Assert
            with pytest.raises(PhotosAPIError) as exc_info:
                client.get_photo_metadata(photo_id="test-photo")
            assert "Failed to get photo metadata" in str(exc_info.value)
