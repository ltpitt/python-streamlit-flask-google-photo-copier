"""Logging configuration for Google Photos Sync application.

This module provides centralized logging setup with structured logging,
multiple handlers (console and file), and configurable log levels.

Example:
    >>> from google_photos_sync.utils.logging_config import setup_logging
    >>> setup_logging(level='INFO', log_file='app.log')
    >>> import logging
    >>> logger = logging.getLogger(__name__)
    >>> logger.info("Application started")
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> None:
    """Configure structured logging for the application.

    Sets up logging with both console and optional file handlers,
    using a consistent format with timestamps, log levels, and module names.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, only console logging
        format_string: Optional custom format string. Uses default if None

    Example:
        >>> setup_logging(level='DEBUG', log_file='app.log')
        >>> logger = logging.getLogger(__name__)
        >>> logger.debug("Debug message")
        >>> logger.info("Info message")
    """
    # Convert string level to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Default format with timestamp, name, level, and message
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create formatter
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler - always enabled
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler - optional
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Log initial message
    root_logger.info(
        f"Logging configured: level={level}, file={log_file or 'console only'}"
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the specified module.

    This is a convenience function that returns a logger with the
    specified name, using the centralized logging configuration.

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        Logger instance configured with application settings

    Example:
        >>> from google_photos_sync.utils.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    return logging.getLogger(name)
