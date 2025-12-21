"""Basic smoke test to verify project setup."""

import pytest


def test_project_version():
    """Test that the package version is accessible."""
    from google_photos_sync import __version__

    assert __version__ == "0.1.0"


@pytest.mark.unit
def test_basic_arithmetic():
    """Basic test to verify pytest is working."""
    assert 1 + 1 == 2


@pytest.mark.unit
def test_mock_example(mocker):
    """Test that pytest-mock is working."""
    mock = mocker.Mock(return_value=42)
    assert mock() == 42
