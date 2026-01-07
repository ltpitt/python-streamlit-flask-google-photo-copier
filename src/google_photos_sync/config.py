"""Configuration management for Google Photos Sync application.

This module provides configuration classes for different environments
(Development, Production, Testing) following best practices for
separation of concerns and 12-factor app methodology.

All configuration values are loaded from environment variables using
python-dotenv for security and flexibility.

Example:
    >>> from google_photos_sync.config import get_config
    >>> config = get_config('development')
    >>> print(config.FLASK_ENV)
    'development'
"""

import os
from typing import Type

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class with common settings.

    This class contains configuration shared across all environments.
    Environment-specific classes inherit from this and override as needed.

    Attributes:
        GOOGLE_CLIENT_ID: Google OAuth client ID
        GOOGLE_CLIENT_SECRET: Google OAuth client secret
        GOOGLE_REDIRECT_URI: OAuth redirect URI
        MAX_CONCURRENT_TRANSFERS: Maximum concurrent photo transfers
        CHUNK_SIZE_MB: Chunk size for streaming transfers (MB)
        MAX_RETRIES: Maximum retry attempts for failed operations
        FLASK_SECRET_KEY: Secret key for Flask sessions
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        LOG_FILE: Log file path
        CORS_ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins
        API_RATE_LIMIT_ENABLED: Enable API rate limiting
        API_RATE_LIMIT_CALLS_PER_MINUTE: Rate limit calls per minute
        VERSION: Application version
    """

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8080/oauth2callback"
    )

    # Transfer Settings
    MAX_CONCURRENT_TRANSFERS: int = int(os.getenv("MAX_CONCURRENT_TRANSFERS", "3"))
    CHUNK_SIZE_MB: int = int(os.getenv("CHUNK_SIZE_MB", "8"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

    # Flask Configuration
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "google_photos_sync.log")

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: str = os.getenv(
        "CORS_ALLOWED_ORIGINS", "http://localhost:8501"
    )

    # API Rate Limiting
    API_RATE_LIMIT_ENABLED: bool = (
        os.getenv("API_RATE_LIMIT_ENABLED", "true").lower() == "true"
    )
    API_RATE_LIMIT_CALLS_PER_MINUTE: int = int(
        os.getenv("API_RATE_LIMIT_CALLS_PER_MINUTE", "60")
    )

    # Application Version
    VERSION: str = "0.1.0"

    # Testing flag
    TESTING: bool = False

    def validate(self) -> None:
        """Validate required configuration values.

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        if not self.GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID is required")
        if not self.GOOGLE_CLIENT_SECRET:
            raise ValueError("GOOGLE_CLIENT_SECRET is required")
        if not self.FLASK_SECRET_KEY or (
            self.FLASK_SECRET_KEY == "dev-secret-key-change-me"  # nosec B105
        ):
            if self.FLASK_ENV == "production":
                raise ValueError("FLASK_SECRET_KEY must be set in production")


class DevelopmentConfig(Config):
    """Development environment configuration.

    Enables debug mode, verbose logging, and development-friendly settings.
    """

    FLASK_ENV = "development"
    DEBUG = True
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")


class ProductionConfig(Config):
    """Production environment configuration.

    Disables debug mode, enables security features, and uses production settings.
    """

    FLASK_ENV = "production"
    DEBUG = False
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")

    def validate(self) -> None:
        """Validate production configuration with stricter requirements."""
        super().validate()
        if self.FLASK_SECRET_KEY == "dev-secret-key-change-me":  # nosec B105
            raise ValueError(
                "FLASK_SECRET_KEY must be changed from default in production"
            )


class TestingConfig(Config):
    """Testing environment configuration.

    Enables testing mode and uses test-friendly settings.
    """

    FLASK_ENV = "testing"
    TESTING = True
    DEBUG = True
    LOG_LEVEL = "DEBUG"

    # Override for testing - don't require real credentials
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "test-client-id")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    FLASK_SECRET_KEY = "test-secret-key"  # nosec B105

    def validate(self) -> None:
        """Skip credential validation in testing mode."""
        pass


# Configuration mapping
config_by_name: dict[str, Type[Config]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(config_name: str = "development") -> Config:
    """Get configuration instance for specified environment.

    Args:
        config_name: Name of configuration environment
            ('development', 'production', 'testing')

    Returns:
        Configuration instance for the specified environment

    Raises:
        ValueError: If config_name is not valid

    Example:
        >>> config = get_config('development')
        >>> config.validate()
    """
    if config_name not in config_by_name:
        raise ValueError(
            f"Invalid config name: {config_name}. "
            f"Must be one of: {list(config_by_name.keys())}"
        )
    return config_by_name[config_name]()
