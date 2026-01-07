"""Input validation and sanitization for Google Photos Sync application.

This module provides security-focused validators and sanitizers for:
- Email addresses
- File paths
- Account types
- JSON payloads
- URL parameters

All validators return sanitized values or raise ValueError for invalid input.

Example:
    >>> from google_photos_sync.utils.validators import validate_email
    >>> email = validate_email("user@example.com")
    >>> # Raises ValueError if invalid
"""

import re
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr


class EmailValidator(BaseModel):
    """Validate email address using Pydantic."""

    email: EmailStr


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


def validate_email(email: str) -> str:
    """Validate and sanitize email address.

    Args:
        email: Email address to validate

    Returns:
        Sanitized email address (lowercase, trimmed)

    Raises:
        ValidationError: If email is invalid

    Example:
        >>> email = validate_email("  User@Example.COM  ")
        >>> print(email)
        'user@example.com'
    """
    if not email:
        raise ValidationError("Email address is required")

    # Trim whitespace and convert to lowercase
    email = email.strip().lower()

    # Validate using Pydantic
    try:
        validator = EmailValidator(email=email)
        return validator.email
    except Exception as e:
        raise ValidationError(f"Invalid email address: {email}") from e


def validate_account_type(account_type: str) -> str:
    """Validate account type parameter.

    Args:
        account_type: Account type string ('source' or 'target')

    Returns:
        Validated account type string (lowercase)

    Raises:
        ValidationError: If account_type is invalid

    Example:
        >>> account_type = validate_account_type("SOURCE")
        >>> print(account_type)
        'source'
    """
    if not account_type:
        raise ValidationError("Account type is required")

    account_type = account_type.strip().lower()

    if account_type not in ["source", "target"]:
        raise ValidationError(
            f"Invalid account type: {account_type}. Must be 'source' or 'target'"
        )

    return account_type


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename to prevent path traversal attacks.

    Removes directory separators, null bytes, and control characters.
    Truncates to max_length characters.

    Args:
        filename: Filename to sanitize
        max_length: Maximum allowed filename length

    Returns:
        Sanitized filename safe for filesystem operations

    Raises:
        ValidationError: If filename is empty or invalid

    Example:
        >>> safe = sanitize_filename("../../../etc/passwd")
        >>> print(safe)
        'etcpasswd'
    """
    if not filename:
        raise ValidationError("Filename cannot be empty")

    # Remove path separators and null bytes
    filename = filename.replace("/", "").replace("\\", "").replace("\0", "")

    # Remove control characters and non-printable characters
    filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)

    # Trim whitespace
    filename = filename.strip()

    # Remove leading/trailing dots (hidden files on Unix)
    filename = filename.strip(".")

    # Truncate to max length
    if len(filename) > max_length:
        filename = filename[:max_length]

    if not filename:
        raise ValidationError("Sanitized filename is empty")

    return filename


def validate_file_path(path: str, base_dir: Optional[Path] = None) -> Path:
    """Validate file path to prevent directory traversal attacks.

    Ensures path is within base_dir if provided.
    Resolves path to absolute path.

    Args:
        path: File path to validate
        base_dir: Optional base directory to restrict path to

    Returns:
        Validated absolute Path object

    Raises:
        ValidationError: If path is invalid or outside base_dir

    Example:
        >>> base = Path("/home/user/.google_photos_sync")
        >>> path = validate_file_path("credentials/source_user@example.com.json", base)
    """
    if not path:
        raise ValidationError("File path cannot be empty")

    try:
        # Convert to Path and resolve to absolute path
        resolved_path = Path(path).resolve()

        # If base_dir provided, ensure path is within it
        if base_dir:
            base_resolved = base_dir.resolve()
            # Check if resolved path is relative to base_dir
            try:
                resolved_path.relative_to(base_resolved)
            except ValueError as e:
                raise ValidationError(
                    f"Path {path} is outside allowed directory {base_dir}"
                ) from e

        return resolved_path

    except Exception as e:
        raise ValidationError(f"Invalid file path: {path}") from e


def validate_json_payload(
    data: Optional[Dict[str, Any]], required_fields: list[str]
) -> Dict[str, Any]:
    """Validate JSON request payload.

    Checks that payload exists and contains all required fields.

    Args:
        data: JSON payload dictionary
        required_fields: List of required field names

    Returns:
        Validated payload dictionary

    Raises:
        ValidationError: If payload is missing or lacks required fields

    Example:
        >>> payload = {"source_account": "user@example.com"}
        >>> validated = validate_json_payload(payload, ["source_account"])
    """
    if data is None:
        raise ValidationError("Request body is required")

    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")

    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    return data


def sanitize_log_message(message: str, sensitive_patterns: list[str]) -> str:
    """Sanitize log message to prevent credential leakage.

    Replaces sensitive patterns with [REDACTED].

    Args:
        message: Log message to sanitize
        sensitive_patterns: List of sensitive strings to redact
            (e.g., tokens, passwords, secrets)

    Returns:
        Sanitized log message with sensitive data redacted

    Example:
        >>> msg = "Token: abc123def456"
        >>> safe = sanitize_log_message(msg, ["abc123def456"])
        >>> print(safe)
        'Token: [REDACTED]'
    """
    sanitized = message

    for pattern in sensitive_patterns:
        if pattern:
            sanitized = sanitized.replace(pattern, "[REDACTED]")

    return sanitized


def validate_positive_integer(value: Any, name: str, max_value: int = 1000) -> int:
    """Validate positive integer parameter.

    Args:
        value: Value to validate
        name: Parameter name for error messages
        max_value: Maximum allowed value

    Returns:
        Validated integer value

    Raises:
        ValidationError: If value is not a valid positive integer

    Example:
        >>> count = validate_positive_integer("10", "max_results", 100)
        >>> print(count)
        10
    """
    try:
        int_value = int(value)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"{name} must be an integer") from e

    if int_value < 1:
        raise ValidationError(f"{name} must be positive (got {int_value})")

    if int_value > max_value:
        raise ValidationError(f"{name} must be <= {max_value} (got {int_value})")

    return int_value


def validate_boolean(value: Any, name: str, default: bool = False) -> bool:
    """Validate boolean parameter.

    Accepts: True/False, "true"/"false", 1/0, "yes"/"no"

    Args:
        value: Value to validate
        name: Parameter name for error messages
        default: Default value if None

    Returns:
        Boolean value

    Raises:
        ValidationError: If value cannot be converted to boolean

    Example:
        >>> dry_run = validate_boolean("true", "dry_run")
        >>> print(dry_run)
        True
    """
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lower_value = value.lower().strip()
        if lower_value in ("true", "yes", "1"):
            return True
        if lower_value in ("false", "no", "0"):
            return False

    if isinstance(value, int):
        if value in (0, 1):
            return bool(value)

    raise ValidationError(f"{name} must be a boolean value (got {value})")
