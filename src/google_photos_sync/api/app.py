"""Flask application factory for Google Photos Sync API.

This module implements the application factory pattern for Flask,
providing a clean separation of concerns and supporting multiple
configurations (development, production, testing).

Example:
    >>> from google_photos_sync.api.app import create_app
    >>> app = create_app('development')
    >>> app.run()
"""

import logging
from typing import Any

from flask import Flask, jsonify
from flask_cors import CORS

from google_photos_sync.api.middleware import register_error_handlers
from google_photos_sync.config import Config, get_config
from google_photos_sync.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def create_app(config_name: str = "development") -> Flask:
    """Create and configure Flask application instance.

    Uses the application factory pattern to create a Flask app with
    proper configuration, logging, CORS, and error handling.

    Args:
        config_name: Configuration environment name
            ('development', 'production', 'testing')

    Returns:
        Configured Flask application instance

    Raises:
        ValueError: If configuration is invalid

    Example:
        >>> app = create_app('development')
        >>> app.config['TESTING']
        False
        >>> test_app = create_app('testing')
        >>> test_app.config['TESTING']
        True
    """
    # Create Flask instance
    app = Flask(__name__)

    # Load configuration
    config = get_config(config_name)
    config.validate()

    # Configure Flask app
    app.config["SECRET_KEY"] = config.FLASK_SECRET_KEY
    app.config["TESTING"] = config.TESTING
    app.config["DEBUG"] = getattr(config, "DEBUG", False)
    app.config["ENV"] = config.FLASK_ENV

    # Store full config for access in routes
    app.config["APP_CONFIG"] = config

    # Setup logging
    setup_logging(level=config.LOG_LEVEL, log_file=config.LOG_FILE)
    logger.info(f"Flask app created with config: {config_name}")

    # Configure CORS
    _configure_cors(app, config)

    # Register error handlers
    register_error_handlers(app)

    # Register routes
    _register_routes(app)

    logger.info(f"Flask application initialized successfully (env={config_name})")
    return app


def _configure_cors(app: Flask, config: Config) -> None:
    """Configure CORS (Cross-Origin Resource Sharing).

    Allows Streamlit frontend and other specified origins to access the API.

    Args:
        app: Flask application instance
        config: Application configuration object
    """
    # Parse CORS origins from comma-separated string
    allowed_origins = [
        origin.strip() for origin in config.CORS_ALLOWED_ORIGINS.split(",")
    ]

    # Configure CORS
    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins}},
        supports_credentials=True,
    )

    logger.info(f"CORS configured with allowed origins: {allowed_origins}")


def _register_routes(app: Flask) -> None:
    """Register API routes.

    Args:
        app: Flask application instance
    """
    from google_photos_sync.api.routes import register_routes

    @app.route("/health", methods=["GET"])
    def health_check() -> tuple[Any, int]:
        """Health check endpoint.

        Returns application health status and version.

        Returns:
            Tuple of (JSON response dict, status code)

        Example:
            >>> GET /health
            {"status": "healthy", "version": "0.1.0"}
        """
        config = app.config.get("APP_CONFIG")
        version = config.VERSION if config else "unknown"
        return (
            jsonify({"status": "healthy", "version": version}),
            200,
        )

    # Register API blueprint with routes
    register_routes(app)

    logger.info("Routes registered: /health, /api/*")
