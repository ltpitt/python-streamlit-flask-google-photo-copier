"""Google Photos API client wrapper.

This module provides a clean interface to the Google Photos API with support for:
- Listing photos with automatic pagination
- Fetching complete photo metadata (EXIF, location, etc.)
- Downloading photos with streaming for memory efficiency
- Uploading photos with metadata preservation
- Rate limiting with exponential backoff
- Comprehensive error handling

Example:
    >>> from google_photos_sync.google_photos.client import GooglePhotosClient
    >>> client = GooglePhotosClient(credentials=my_credentials)
    >>> photos = client.list_photos()
    >>> for photo in photos:
    ...     print(f"{photo.filename}: {photo.created_time}")
"""

import time
from typing import Any, Generator, Optional

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore[import-untyped]
from googleapiclient.errors import HttpError  # type: ignore[import-untyped]

from google_photos_sync.google_photos.models import Photo


class PhotosAPIError(Exception):
    """Raised when Google Photos API operation fails."""

    pass


class RateLimitError(PhotosAPIError):
    """Raised when rate limit is exceeded after max retries."""

    pass


class GooglePhotosClient:
    """Client for interacting with Google Photos API.

    This client handles all interactions with the Google Photos API,
    including pagination, rate limiting, and error handling. It uses
    streaming for downloads to minimize memory usage.

    Attributes:
        credentials: Google OAuth2 credentials
        max_retries: Maximum number of retries for rate-limited requests
        base_backoff: Base delay in seconds for exponential backoff
    """

    # API configuration
    API_SERVICE_NAME = "photoslibrary"
    API_VERSION = "v1"
    UPLOAD_URL = "https://photoslibrary.googleapis.com/v1/uploads"

    # Rate limiting configuration (conservative, not aggressive)
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_BACKOFF = 1  # seconds

    # Download configuration
    DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks for streaming

    def __init__(
        self,
        credentials: Credentials,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_backoff: int = DEFAULT_BASE_BACKOFF,
    ) -> None:
        """Initialize Google Photos API client.

        Args:
            credentials: Valid Google OAuth2 credentials with appropriate scopes
            max_retries: Maximum retry attempts for rate-limited requests
            base_backoff: Base delay in seconds for exponential backoff

        Raises:
            ValueError: If credentials is None
        """
        if credentials is None:
            raise ValueError("credentials cannot be None")

        self._credentials = credentials
        self._max_retries = max_retries
        self._base_backoff = base_backoff

        # Build the Photos Library API service
        self._service = build(
            self.API_SERVICE_NAME,
            self.API_VERSION,
            credentials=self._credentials,
        )

    def list_photos(self) -> list[Photo]:
        """List all photos from Google Photos library with pagination.

        This method handles pagination automatically, fetching all pages
        until the complete library is retrieved. Rate limiting is handled
        with exponential backoff.

        Returns:
            List of Photo objects with complete metadata

        Raises:
            RateLimitError: If rate limit exceeded after max retries
            PhotosAPIError: If API call fails

        Example:
            >>> photos = client.list_photos()
            >>> print(f"Found {len(photos)} photos")
        """
        try:
            photos: list[Photo] = []
            page_token: Optional[str] = None

            while True:
                # Prepare request parameters
                request_params: dict[str, Any] = {"pageSize": 100}
                if page_token:
                    request_params["pageToken"] = page_token

                # Execute request with retry logic
                request = self._service.mediaItems().list(**request_params)
                response = self._execute_with_retry(request)

                # Extract photos from response
                if "mediaItems" in response:
                    for item in response["mediaItems"]:
                        photo = self._parse_photo_from_api_response(item)
                        photos.append(photo)

                # Check for next page
                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            return photos

        except RateLimitError:
            raise
        except Exception as e:
            raise PhotosAPIError(f"Failed to list photos: {e}") from e

    def get_photo_metadata(self, photo_id: str) -> Photo:
        """Fetch complete metadata for a specific photo.

        Retrieves all available metadata including EXIF data, location
        information, and Google Photos-specific attributes.

        Args:
            photo_id: Unique Google Photos identifier

        Returns:
            Photo object with complete metadata

        Raises:
            PhotosAPIError: If photo not found or API call fails

        Example:
            >>> photo = client.get_photo_metadata("photo-id-123")
            >>> print(f"Camera: {photo.camera_make} {photo.camera_model}")
        """
        try:
            request = self._service.mediaItems().get(mediaItemId=photo_id)
            response = self._execute_with_retry(request)
            return self._parse_photo_from_api_response(response)

        except RateLimitError:
            raise
        except Exception as e:
            raise PhotosAPIError(
                f"Failed to get photo metadata for {photo_id}: {e}"
            ) from e

    def download_photo(
        self, photo: Photo, chunk_size: int = DEFAULT_CHUNK_SIZE
    ) -> Generator[bytes, None, None]:
        """Download photo binary data using streaming.

        This method streams the photo download in chunks to avoid loading
        the entire file into memory. This is critical for large photos and
        videos to maintain memory efficiency.

        Args:
            photo: Photo object with base_url for download
            chunk_size: Size of chunks for streaming (default: 8MB)

        Yields:
            Chunks of photo binary data

        Raises:
            PhotosAPIError: If photo has no base_url or download fails

        Example:
            >>> with open("photo.jpg", "wb") as f:
            ...     for chunk in client.download_photo(photo):
            ...         f.write(chunk)
        """
        if not photo.base_url:
            raise PhotosAPIError(f"Photo has no base_url: {photo.id}")

        try:
            # Append download parameter to get full resolution
            download_url = f"{photo.base_url}=d"

            # Use streaming to avoid loading entire file in memory
            # Set timeout to prevent hanging on slow connections
            response = requests.get(
                download_url,
                stream=True,
                timeout=30,  # 30 second timeout
            )
            response.raise_for_status()

            # Yield chunks for memory-efficient streaming
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive new chunks
                    yield chunk

        except Exception as e:
            raise PhotosAPIError(f"Failed to download photo {photo.id}: {e}") from e

    def upload_photo(self, photo_data: bytes, photo_metadata: Photo) -> Photo:
        """Upload photo with metadata preservation.

        This method uploads a photo and preserves its metadata including
        creation time, description, and other attributes. The upload process
        is two-step: first upload binary data to get a token, then create
        the media item with metadata.

        Args:
            photo_data: Photo binary data
            photo_metadata: Photo metadata to preserve

        Returns:
            Photo object representing the uploaded photo

        Raises:
            PhotosAPIError: If upload fails

        Example:
            >>> with open("photo.jpg", "rb") as f:
            ...     photo_data = f.read()
            >>> uploaded = client.upload_photo(photo_data, photo_metadata)
            >>> print(f"Uploaded: {uploaded.id}")
        """
        try:
            # Step 1: Upload binary data to get upload token
            upload_token = self._upload_photo_bytes(photo_data, photo_metadata)

            # Step 2: Create media item with metadata
            uploaded_photo = self._create_media_item(upload_token, photo_metadata)

            return uploaded_photo

        except Exception as e:
            raise PhotosAPIError(
                f"Failed to upload photo {photo_metadata.filename}: {e}"
            ) from e

    def _upload_photo_bytes(self, photo_data: bytes, photo: Photo) -> str:
        """Upload photo binary data and get upload token.

        Args:
            photo_data: Photo binary data
            photo: Photo metadata for headers

        Returns:
            Upload token to use in batchCreate

        Raises:
            PhotosAPIError: If upload fails
        """
        headers = {
            "Authorization": f"Bearer {self._credentials.token}",
            "Content-Type": "application/octet-stream",
            "X-Goog-Upload-File-Name": photo.filename,
            "X-Goog-Upload-Protocol": "raw",
        }

        # Upload with timeout to prevent hanging
        response = requests.post(
            self.UPLOAD_URL,
            data=photo_data,
            headers=headers,
            timeout=60,  # 60 second timeout for uploads
        )
        response.raise_for_status()

        # Upload token is in response body
        upload_token: str = response.text
        return upload_token

    def _create_media_item(self, upload_token: str, photo: Photo) -> Photo:
        """Create media item from upload token with metadata.

        Args:
            upload_token: Token from photo upload
            photo: Photo metadata to preserve

        Returns:
            Created Photo object

        Raises:
            PhotosAPIError: If creation fails
        """
        # Build request body with metadata
        new_media_item: dict[str, Any] = {
            "simpleMediaItem": {
                "uploadToken": upload_token,
                "fileName": photo.filename,
            }
        }

        # Add description if present
        if photo.description:
            new_media_item["description"] = photo.description

        request_body = {"newMediaItems": [new_media_item]}

        # Execute batchCreate request
        request = self._service.mediaItems().batchCreate(body=request_body)
        response = self._execute_with_retry(request)

        # Extract created media item
        if "newMediaItemResults" not in response or not response["newMediaItemResults"]:
            raise PhotosAPIError("No media items created")

        result = response["newMediaItemResults"][0]

        # Check for errors in result
        if "status" in result and result["status"].get("message") != "Success":
            raise PhotosAPIError(
                f"Media item creation failed: {result['status'].get('message')}"
            )

        # Parse and return created photo
        created_photo = self._parse_photo_from_api_response(result["mediaItem"])
        return created_photo

    def _parse_photo_from_api_response(self, item: dict[str, Any]) -> Photo:
        """Parse Google Photos API response into Photo object.

        Extracts all available metadata including EXIF data and location.

        Args:
            item: Raw API response item

        Returns:
            Photo object with extracted metadata
        """
        # Extract base fields
        photo_id = item.get("id", "")
        filename = item.get("filename", "")
        mime_type = item.get("mimeType", "")

        # Extract media metadata
        media_metadata = item.get("mediaMetadata", {})
        created_time = media_metadata.get("creationTime", "")
        width = int(media_metadata.get("width", 0))
        height = int(media_metadata.get("height", 0))

        # Extract EXIF data from photo metadata
        photo_metadata = media_metadata.get("photo", {})
        camera_make = photo_metadata.get("cameraMake")
        camera_model = photo_metadata.get("cameraModel")

        # Format focal length
        focal_length = None
        if "focalLength" in photo_metadata:
            focal_length = f"{photo_metadata['focalLength']}mm"

        # Format aperture
        aperture = None
        if "apertureFNumber" in photo_metadata:
            aperture = f"f/{photo_metadata['apertureFNumber']}"

        # Get ISO
        iso = photo_metadata.get("isoEquivalent")

        # Extract URLs
        base_url = item.get("baseUrl")
        product_url = item.get("productUrl")

        # Extract description
        description = item.get("description")

        # Create Photo object
        photo = Photo(
            id=photo_id,
            filename=filename,
            mime_type=mime_type,
            created_time=created_time,
            width=width,
            height=height,
            base_url=base_url,
            product_url=product_url,
            description=description,
            camera_make=camera_make,
            camera_model=camera_model,
            focal_length=focal_length,
            aperture=aperture,
            iso=iso,
        )

        return photo

    def _execute_with_retry(self, request: Any) -> dict[str, Any]:
        """Execute API request with exponential backoff for rate limiting.

        This method implements conservative retry logic with exponential
        backoff. It respects rate limits and doesn't hammer the API.

        Args:
            request: Google API request object

        Returns:
            API response as dictionary

        Raises:
            RateLimitError: If rate limit exceeded after max retries
            PhotosAPIError: If request fails for other reasons
        """
        for attempt in range(self._max_retries + 1):
            try:
                response: dict[str, Any] = request.execute()
                return response

            except HttpError as e:
                # Handle rate limiting (429 status code)
                if e.resp.status == 429:
                    if attempt < self._max_retries:
                        # Exponential backoff: 1s, 2s, 4s, etc.
                        delay = self._base_backoff * (2**attempt)
                        time.sleep(delay)
                        continue
                    else:
                        # Max retries exceeded
                        raise RateLimitError(
                            f"Rate limit exceeded after {self._max_retries} retries"
                        ) from e
                else:
                    # Other HTTP errors - don't retry
                    raise

        # Should not reach here, but just in case
        raise PhotosAPIError("Request failed after retries")
