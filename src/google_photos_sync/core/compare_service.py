"""Compare Service for Google Photos Account Comparison.

This module provides functionality to compare two Google Photos accounts
and identify differences including missing photos, metadata differences,
and extra photos on the target account.

This is a read-only operation that helps users understand what will change
during sync before executing the actual sync operation.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from google_photos_sync.google_photos.client import GooglePhotosClient
from google_photos_sync.google_photos.models import Photo


@dataclass
class CompareResult:
    """Result of comparing two Google Photos accounts.

    This class contains all differences found between source and target accounts,
    including photos missing on target, photos with different metadata, and
    photos that exist only on target.

    Attributes:
        source_account: Email of source Google Photos account
        target_account: Email of target Google Photos account
        comparison_date: ISO 8601 timestamp when comparison was performed
        total_source_photos: Total number of photos in source account
        total_target_photos: Total number of photos in target account
        missing_on_target: List of photos that exist on source but not on target
        different_metadata: List of metadata differences for photos that exist on both
        extra_on_target: List of photos that exist on target but not on source
    """

    source_account: str
    target_account: str
    comparison_date: str
    total_source_photos: int
    total_target_photos: int
    missing_on_target: list[Photo] = field(default_factory=list)
    different_metadata: list[dict[str, Any]] = field(default_factory=list)
    extra_on_target: list[Photo] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        """Convert comparison result to JSON-serializable dictionary.

        Returns:
            Dictionary with complete comparison results in JSON-friendly format

        Example:
            >>> result = compare_service.compare_accounts(
            ...     "source@gmail.com", "target@gmail.com"
            ... )
            >>> json_data = result.to_json()
        """
        return {
            "source_account": self.source_account,
            "target_account": self.target_account,
            "comparison_date": self.comparison_date,
            "total_source_photos": self.total_source_photos,
            "total_target_photos": self.total_target_photos,
            "missing_on_target": [asdict(photo) for photo in self.missing_on_target],
            "different_metadata": self.different_metadata,
            "extra_on_target": [asdict(photo) for photo in self.extra_on_target],
        }


class CompareService:
    """Service for comparing Google Photos accounts.

    This service compares source and target Google Photos accounts to identify
    differences. It's a read-only operation that produces a detailed report
    of what would change during a sync operation.

    The comparison identifies:
    - Photos missing on target (would be added during sync)
    - Photos with different metadata (would be updated during sync)
    - Extra photos on target (would be deleted during sync)

    Attributes:
        source_client: Google Photos API client for source account
        target_client: Google Photos API client for target account

    Example:
        >>> source_client = GooglePhotosClient(source_credentials)
        >>> target_client = GooglePhotosClient(target_credentials)
        >>> service = CompareService(source_client, target_client)
        >>> result = service.compare_accounts("source@gmail.com", "target@gmail.com")
        >>> print(f"Missing on target: {len(result.missing_on_target)}")
    """

    # Fields to compare for metadata differences
    COMPARABLE_FIELDS = ["filename", "created_time", "width", "height", "mime_type"]

    def __init__(
        self,
        source_client: GooglePhotosClient,
        target_client: GooglePhotosClient,
    ) -> None:
        """Initialize compare service with Google Photos clients.

        Args:
            source_client: Client for source Google Photos account
            target_client: Client for target Google Photos account

        Raises:
            ValueError: If either client is None
        """
        if source_client is None:
            raise ValueError("source_client cannot be None")
        if target_client is None:
            raise ValueError("target_client cannot be None")

        self._source_client = source_client
        self._target_client = target_client

    def compare_accounts(
        self,
        source_account: str,
        target_account: str,
    ) -> CompareResult:
        """Compare source and target Google Photos accounts.

        This method performs a comprehensive comparison of two accounts,
        identifying all differences. The operation is read-only and safe
        to run multiple times.

        Args:
            source_account: Email of source Google Photos account
            target_account: Email of target Google Photos account

        Returns:
            CompareResult containing all identified differences

        Example:
            >>> result = service.compare_accounts("user@gmail.com", "backup@gmail.com")
            >>> if result.missing_on_target:
            ...     print(f"Need to sync {len(result.missing_on_target)} photos")
        """
        # Get current timestamp for comparison
        comparison_date = datetime.now(timezone.utc).isoformat()

        # Fetch all photos from both accounts
        source_photos = self._source_client.list_photos()
        target_photos = self._target_client.list_photos()

        # Build photo ID lookup maps for efficient comparison
        source_map = {photo.id: photo for photo in source_photos}
        target_map = {photo.id: photo for photo in target_photos}

        # Find photos missing on target (in source but not in target)
        missing_on_target = [
            photo
            for photo_id, photo in source_map.items()
            if photo_id not in target_map
        ]

        # Find extra photos on target (in target but not in source)
        extra_on_target = [
            photo
            for photo_id, photo in target_map.items()
            if photo_id not in source_map
        ]

        # Find photos with different metadata (in both but with differences)
        different_metadata = self._find_metadata_differences(source_map, target_map)

        # Create and return comparison result
        return CompareResult(
            source_account=source_account,
            target_account=target_account,
            comparison_date=comparison_date,
            total_source_photos=len(source_photos),
            total_target_photos=len(target_photos),
            missing_on_target=missing_on_target,
            different_metadata=different_metadata,
            extra_on_target=extra_on_target,
        )

    def _find_metadata_differences(
        self,
        source_map: dict[str, Photo],
        target_map: dict[str, Photo],
    ) -> list[dict[str, Any]]:
        """Find metadata differences for photos that exist in both accounts.

        Args:
            source_map: Dictionary mapping photo IDs to source photos
            target_map: Dictionary mapping photo IDs to target photos

        Returns:
            List of metadata difference dictionaries
        """
        differences: list[dict[str, Any]] = []

        # Find common photo IDs
        common_ids = set(source_map.keys()) & set(target_map.keys())

        # Compare metadata for each common photo
        for photo_id in common_ids:
            source_photo = source_map[photo_id]
            target_photo = target_map[photo_id]

            # Check each comparable field
            for field_name in self.COMPARABLE_FIELDS:
                source_value = getattr(source_photo, field_name)
                target_value = getattr(target_photo, field_name)

                if source_value != target_value:
                    differences.append(
                        {
                            "photo_id": photo_id,
                            "field": field_name,
                            "source_value": source_value,
                            "target_value": target_value,
                        }
                    )

        return differences
