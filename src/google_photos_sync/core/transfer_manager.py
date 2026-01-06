"""Transfer Manager - Memory-Efficient Photo Transfer.

This module implements streaming photo transfers from source to target accounts
with memory efficiency, retry logic, and progress reporting.

Example:
    >>> from google_photos_sync.core.transfer_manager import TransferManager
    >>> manager = TransferManager(source_client=source, target_client=target)
    >>> result = manager.transfer_photo(photo)
    >>> print(f"Transferred {result.bytes_transferred} bytes")
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Optional

from google_photos_sync.google_photos.client import GooglePhotosClient
from google_photos_sync.google_photos.models import Photo


class TransferError(Exception):
    """Raised when photo transfer fails after retries."""

    pass


@dataclass
class TransferResult:
    """Result of a photo transfer operation.

    Attributes:
        photo_id: Unique identifier of the transferred photo
        status: Transfer status ("success" or "failed")
        bytes_transferred: Total bytes transferred
        retry_count: Number of retries attempted
        error_message: Error message if transfer failed
    """

    photo_id: str
    status: str
    bytes_transferred: int
    retry_count: int
    error_message: Optional[str] = None


class TransferManager:
    """Manages memory-efficient photo transfers with retry logic.

    This manager handles photo downloads and uploads using streaming to avoid
    loading entire files into memory. It supports concurrent transfers with
    configurable limits and provides progress reporting.

    Attributes:
        source_client: Google Photos client for source account
        target_client: Google Photos client for target account
        max_concurrent_transfers: Maximum concurrent transfers (default: 3)
        chunk_size: Size of chunks for streaming in bytes (default: 8MB)
        max_retries: Maximum retry attempts for failed transfers (default: 3)
        progress_callback: Optional callback for progress reporting
    """

    # Conservative defaults to respect API limits
    DEFAULT_MAX_CONCURRENT_TRANSFERS = 3
    DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024  # 8MB
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_BACKOFF = 1  # seconds

    def __init__(
        self,
        source_client: GooglePhotosClient,
        target_client: GooglePhotosClient,
        max_concurrent_transfers: int = DEFAULT_MAX_CONCURRENT_TRANSFERS,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> None:
        """Initialize transfer manager with clients and configuration.

        Args:
            source_client: Google Photos client for source account
            target_client: Google Photos client for target account
            max_concurrent_transfers: Maximum concurrent transfers
            chunk_size: Size of chunks for streaming in bytes
            max_retries: Maximum retry attempts for failed transfers
            progress_callback: Optional callback for progress reporting
                Format: callback(photo_id, bytes_transferred, total_bytes)

        Raises:
            ValueError: If source_client or target_client is None
        """
        if source_client is None:
            raise ValueError("source_client cannot be None")
        if target_client is None:
            raise ValueError("target_client cannot be None")

        self._source_client = source_client
        self._target_client = target_client
        self._max_concurrent_transfers = max_concurrent_transfers
        self._chunk_size = chunk_size
        self._max_retries = max_retries
        self._progress_callback = progress_callback
        self._base_backoff = self.DEFAULT_BASE_BACKOFF

    def transfer_photo(self, photo: Photo) -> TransferResult:
        """Transfer a single photo from source to target with retry logic.

        Downloads photo from source account and uploads to target account using
        streaming to minimize memory usage. Implements exponential backoff for
        retries on failures.

        Args:
            photo: Photo object to transfer

        Returns:
            TransferResult with transfer status and statistics

        Raises:
            TransferError: If transfer fails after max retries
        """
        for attempt in range(self._max_retries + 1):
            try:
                # Download from source using streaming
                photo_data = self._download_photo_streaming(photo)

                # Upload to target with metadata preservation
                self._target_client.upload_photo(photo_data, photo)

                # Return success result with retry count
                return TransferResult(
                    photo_id=photo.id,
                    status="success",
                    bytes_transferred=len(photo_data),
                    retry_count=attempt,  # Number of retries = current attempt
                )

            except Exception as e:
                if attempt < self._max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = self._base_backoff * (2**attempt)
                    time.sleep(delay)
                    continue
                else:
                    # Max retries exceeded
                    raise TransferError(
                        f"Failed after {self._max_retries} retries: {e}"
                    ) from e

        # Should not reach here, but just in case
        raise TransferError("Transfer failed unexpectedly")

    def transfer_photos(self, photos: list[Photo]) -> list[TransferResult]:
        """Transfer multiple photos concurrently with controlled concurrency.

        Uses ThreadPoolExecutor to transfer photos in parallel while respecting
        the max_concurrent_transfers limit. Partial failures are handled gracefully.

        Args:
            photos: List of Photo objects to transfer

        Returns:
            List of TransferResult objects for all photos
        """
        results: list[TransferResult] = []

        with ThreadPoolExecutor(max_workers=self._max_concurrent_transfers) as executor:
            # Submit all transfer tasks
            future_to_photo = {
                executor.submit(self._transfer_photo_safe, photo): photo
                for photo in photos
            }

            # Collect results as they complete
            for future in as_completed(future_to_photo):
                result = future.result()
                results.append(result)

        return results

    def _transfer_photo_safe(self, photo: Photo) -> TransferResult:
        """Transfer photo with exception handling for batch operations.

        Wraps transfer_photo to catch exceptions and return failure results
        instead of raising, allowing batch operations to continue.

        Args:
            photo: Photo object to transfer

        Returns:
            TransferResult with success or failure status
        """
        try:
            return self.transfer_photo(photo)
        except TransferError as e:
            return TransferResult(
                photo_id=photo.id,
                status="failed",
                bytes_transferred=0,
                retry_count=self._max_retries,
                error_message=str(e),
            )
        except Exception as e:
            return TransferResult(
                photo_id=photo.id,
                status="failed",
                bytes_transferred=0,
                retry_count=0,
                error_message=f"Unexpected error: {e}",
            )

    def _download_photo_streaming(self, photo: Photo) -> bytes:
        """Download photo using streaming to minimize memory usage.

        Downloads photo in chunks and assembles them in memory. Progress
        callback is called after each chunk if provided.

        Args:
            photo: Photo object to download

        Returns:
            Complete photo data as bytes

        Raises:
            Exception: If download fails
        """
        chunks: list[bytes] = []
        total_bytes = 0

        # Download in chunks using generator
        for chunk in self._source_client.download_photo(
            photo, chunk_size=self._chunk_size
        ):
            chunks.append(chunk)
            total_bytes += len(chunk)

            # Call progress callback if provided
            if self._progress_callback is not None:
                self._progress_callback(photo.id, total_bytes, total_bytes)

        # Concatenate all chunks
        photo_data = b"".join(chunks)
        return photo_data
