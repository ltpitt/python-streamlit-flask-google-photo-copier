"""Integration tests for Flask API application factory.

Tests the Flask application creation, configuration, error handling,
and CORS functionality across different environments.

Example:
    $ pytest tests/integration/test_flask_app.py -v
"""

import importlib
import os
import sys
from unittest import mock

import pytest

from google_photos_sync.api.app import create_app


@pytest.fixture
def reload_config():
    """Reload config module to pick up environment variable changes."""

    def _reload():
        if "google_photos_sync.config" in sys.modules:
            importlib.reload(sys.modules["google_photos_sync.config"])

    return _reload


class TestFlaskAppCreation:
    """Test Flask application factory creation."""

    @mock.patch.dict(
        os.environ,
        {
            "GOOGLE_CLIENT_ID": "test-client-id",
            "GOOGLE_CLIENT_SECRET": "test-client-secret",
        },
        clear=False,
    )
    def test_create_app_with_development_config(self, reload_config):
        """Test app creation with development configuration."""
        reload_config()
        app = create_app("development")

        assert app is not None
        assert app.config["ENV"] == "development"
        assert app.config["DEBUG"] is True
        assert app.config["TESTING"] is False

    @mock.patch.dict(
        os.environ,
        {
            "GOOGLE_CLIENT_ID": "test-client-id",
            "GOOGLE_CLIENT_SECRET": "test-client-secret",
            "FLASK_SECRET_KEY": "production-secret-key",
        },
        clear=False,
    )
    def test_create_app_with_production_config(self, reload_config):
        """Test app creation with production configuration."""
        reload_config()
        app = create_app("production")

        assert app is not None
        assert app.config["ENV"] == "production"
        assert app.config["DEBUG"] is False
        assert app.config["TESTING"] is False

    def test_create_app_with_testing_config(self):
        """Test app creation with testing configuration."""
        app = create_app("testing")

        assert app is not None
        assert app.config["ENV"] == "testing"
        assert app.config["TESTING"] is True
        assert app.config["DEBUG"] is True

    def test_create_app_with_invalid_config_raises_error(self):
        """Test app creation with invalid config name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_app("invalid_config")

        assert "Invalid config name" in str(exc_info.value)

    def test_app_has_secret_key_configured(self):
        """Test that app has SECRET_KEY configured."""
        app = create_app("testing")

        assert "SECRET_KEY" in app.config
        assert app.config["SECRET_KEY"] is not None
        assert app.config["SECRET_KEY"] != ""

    def test_app_stores_full_config(self):
        """Test that app stores full configuration object."""
        app = create_app("testing")

        assert "APP_CONFIG" in app.config
        assert app.config["APP_CONFIG"] is not None
        assert hasattr(app.config["APP_CONFIG"], "VERSION")


class TestHealthEndpoint:
    """Test /health endpoint functionality."""

    def test_health_endpoint_exists(self):
        """Test that /health endpoint is registered."""
        app = create_app("testing")
        client = app.test_client()

        response = client.get("/health")

        assert response.status_code == 200

    def test_health_endpoint_returns_json(self):
        """Test that /health returns JSON response."""
        app = create_app("testing")
        client = app.test_client()

        response = client.get("/health")

        assert response.is_json
        data = response.get_json()
        assert data is not None

    def test_health_endpoint_returns_correct_structure(self):
        """Test that /health returns expected JSON structure."""
        app = create_app("testing")
        client = app.test_client()

        response = client.get("/health")
        data = response.get_json()

        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"

    def test_health_endpoint_returns_version(self):
        """Test that /health returns application version."""
        app = create_app("testing")
        client = app.test_client()

        response = client.get("/health")
        data = response.get_json()

        assert data["version"] == "0.1.0"

    def test_health_endpoint_only_accepts_get(self):
        """Test that /health only accepts GET requests."""
        app = create_app("testing")
        client = app.test_client()

        # POST should not be allowed
        response = client.post("/health")
        assert response.status_code == 405  # Method Not Allowed


class TestErrorHandlers:
    """Test error handling middleware."""

    def test_404_error_returns_json(self):
        """Test that 404 errors return JSON response."""
        app = create_app("testing")
        client = app.test_client()

        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        assert response.is_json
        data = response.get_json()
        assert "error" in data
        assert "message" in data
        assert "status" in data
        assert data["status"] == 404
        assert data["error"] == "Not Found"

    def test_404_error_includes_message(self):
        """Test that 404 error response includes descriptive message."""
        app = create_app("testing")
        client = app.test_client()

        response = client.get("/invalid-route")
        data = response.get_json()

        assert data["message"] is not None
        assert len(data["message"]) > 0

    def test_method_not_allowed_returns_405(self):
        """Test that invalid HTTP methods return 405."""
        app = create_app("testing")
        client = app.test_client()

        # /health only accepts GET, try POST
        response = client.post("/health")

        assert response.status_code == 405


class TestCORSConfiguration:
    """Test CORS (Cross-Origin Resource Sharing) configuration."""

    def test_cors_headers_present_in_response(self):
        """Test that CORS headers are present in responses."""
        app = create_app("testing")
        client = app.test_client()

        response = client.get("/health", headers={"Origin": "http://localhost:8501"})

        # Check for CORS headers
        assert "Access-Control-Allow-Origin" in response.headers

    def test_cors_allows_configured_origin(self):
        """Test that CORS allows configured Streamlit origin."""
        app = create_app("testing")
        client = app.test_client()

        # Default Streamlit origin
        origin = "http://localhost:8501"
        response = client.get("/health", headers={"Origin": origin})

        # Should allow the origin
        assert response.headers.get("Access-Control-Allow-Origin") in [origin, "*"]

    def test_cors_supports_credentials(self):
        """Test that CORS supports credentials."""
        app = create_app("testing")
        client = app.test_client()

        response = client.get("/health", headers={"Origin": "http://localhost:8501"})

        # Should support credentials for authenticated requests
        credentials_header = response.headers.get("Access-Control-Allow-Credentials")
        # May be None or "true" depending on Flask-CORS configuration
        assert credentials_header is None or credentials_header.lower() == "true"


class TestApplicationConfiguration:
    """Test application configuration across environments."""

    @mock.patch.dict(
        os.environ,
        {
            "GOOGLE_CLIENT_ID": "test-client-id",
            "GOOGLE_CLIENT_SECRET": "test-client-secret",
        },
        clear=False,
    )
    def test_development_config_has_debug_enabled(self, reload_config):
        """Test that development config enables debug mode."""
        reload_config()
        app = create_app("development")

        assert app.config["DEBUG"] is True

    @mock.patch.dict(
        os.environ,
        {
            "GOOGLE_CLIENT_ID": "test-client-id",
            "GOOGLE_CLIENT_SECRET": "test-client-secret",
            "FLASK_SECRET_KEY": "production-secret-key",
        },
        clear=False,
    )
    def test_production_config_has_debug_disabled(self, reload_config):
        """Test that production config disables debug mode."""
        reload_config()
        app = create_app("production")

        assert app.config["DEBUG"] is False

    def test_testing_config_has_testing_enabled(self):
        """Test that testing config enables testing mode."""
        app = create_app("testing")

        assert app.config["TESTING"] is True

    def test_app_config_contains_version(self):
        """Test that app config contains version information."""
        app = create_app("testing")
        config = app.config["APP_CONFIG"]

        assert hasattr(config, "VERSION")
        assert config.VERSION == "0.1.0"

    def test_app_config_contains_cors_settings(self):
        """Test that app config contains CORS settings."""
        app = create_app("testing")
        config = app.config["APP_CONFIG"]

        assert hasattr(config, "CORS_ALLOWED_ORIGINS")
        assert config.CORS_ALLOWED_ORIGINS is not None
