"""Error handling middleware for Flask API.

This module provides centralized error handling for the Flask API,
converting exceptions to JSON responses with appropriate HTTP status codes.

Example:
    >>> from flask import Flask
    >>> from google_photos_sync.api.middleware import register_error_handlers
    >>> app = Flask(__name__)
    >>> register_error_handlers(app)
"""

import logging
from typing import Any

from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for Flask application.

    Configures handlers for common HTTP errors (400, 404, 500) and
    generic exception handling, returning JSON responses.

    Args:
        app: Flask application instance

    Example:
        >>> app = Flask(__name__)
        >>> register_error_handlers(app)
    """

    @app.errorhandler(400)
    def bad_request(error: HTTPException) -> tuple[Response, int]:
        """Handle 400 Bad Request errors.

        Args:
            error: HTTPException instance

        Returns:
            Tuple of (JSON response, status code)
        """
        logger.warning(f"Bad request: {error.description}")
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": error.description or "Invalid request",
                    "status": 400,
                }
            ),
            400,
        )

    @app.errorhandler(404)
    def not_found(error: HTTPException) -> tuple[Response, int]:
        """Handle 404 Not Found errors.

        Args:
            error: HTTPException instance

        Returns:
            Tuple of (JSON response, status code)
        """
        logger.warning(f"Resource not found: {error.description}")
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": error.description or "Resource not found",
                    "status": 404,
                }
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error: HTTPException) -> tuple[Response, int]:
        """Handle 500 Internal Server Error.

        Args:
            error: HTTPException instance

        Returns:
            Tuple of (JSON response, status code)
        """
        logger.error(f"Internal server error: {error.description}", exc_info=True)
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "status": 500,
                }
            ),
            500,
        )

    @app.errorhandler(Exception)
    def handle_exception(error: Exception) -> tuple[Response, int]:
        """Handle generic exceptions.

        Catches all unhandled exceptions and returns a 500 error.

        Args:
            error: Exception instance

        Returns:
            Tuple of (JSON response, status code)
        """
        # Pass through HTTP exceptions to their specific handlers
        if isinstance(error, HTTPException):
            return error  # type: ignore[return-value]

        # Log the error with full traceback
        logger.exception(f"Unhandled exception: {str(error)}")

        # Return generic error response
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "status": 500,
                }
            ),
            500,
        )
