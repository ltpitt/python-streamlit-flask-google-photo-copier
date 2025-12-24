"""Data models for Google Photos entities.

This module defines typed data structures for Google Photos API objects
such as photos and albums. These models ensure type safety and provide
clear documentation of the data structures used throughout the application.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Photo:
    """Represents a photo in Google Photos.

    This class contains all metadata associated with a photo, including
    EXIF data, location information, and Google Photos-specific attributes.
    All metadata fields are preserved during sync operations.

    Attributes:
        id: Unique Google Photos identifier for the photo
        filename: Original filename of the photo
        mime_type: MIME type (e.g., "image/jpeg", "video/mp4")
        created_time: ISO 8601 timestamp of when photo was created
        width: Width in pixels
        height: Height in pixels
        base_url: Google Photos base URL for downloading (temporary, expires)
        product_url: Permanent URL to view photo in Google Photos
        description: User-provided description/caption
        camera_make: Camera manufacturer from EXIF (e.g., "Canon")
        camera_model: Camera model from EXIF (e.g., "EOS 5D Mark IV")
        focal_length: Focal length from EXIF (e.g., "50mm")
        aperture: Aperture f-stop from EXIF (e.g., "f/2.8")
        iso: ISO sensitivity from EXIF
        latitude: GPS latitude coordinate
        longitude: GPS longitude coordinate
        location_name: Human-readable location name
        is_favorite: Whether photo is marked as favorite
    """

    id: str
    filename: str
    mime_type: str
    created_time: str
    width: int
    height: int
    base_url: Optional[str] = None
    product_url: Optional[str] = None
    description: Optional[str] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    focal_length: Optional[str] = None
    aperture: Optional[str] = None
    iso: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    is_favorite: bool = False


@dataclass
class Album:
    """Represents an album in Google Photos.

    Attributes:
        id: Unique Google Photos identifier for the album
        title: Album title
        product_url: Permanent URL to view album in Google Photos
        media_items_count: Number of media items in the album
        cover_photo_base_url: Base URL for album cover photo
    """

    id: str
    title: str
    product_url: Optional[str] = None
    media_items_count: int = 0
    cover_photo_base_url: Optional[str] = None
