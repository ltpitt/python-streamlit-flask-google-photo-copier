"""Pytest configuration and shared fixtures for Google Photos Sync tests."""

import pytest


@pytest.fixture
def sample_photo_data():
    """Provide sample photo data for testing.

    Returns:
        dict: Sample photo metadata following Google Photos API structure
    """
    return {
        "id": "test-photo-123",
        "filename": "vacation.jpg",
        "mimeType": "image/jpeg",
        "mediaMetadata": {
            "creationTime": "2025-01-01T10:00:00Z",
            "width": "1920",
            "height": "1080",
        },
    }


@pytest.fixture
def sample_album_data():
    """Provide sample album data for testing.

    Returns:
        dict: Sample album metadata following Google Photos API structure
    """
    return {
        "id": "test-album-456",
        "title": "Summer Vacation 2025",
        "mediaItemsCount": "42",
    }
