"""Unit tests for input validators and sanitizers.

Tests cover:
- Email validation
- Account type validation
- Filename sanitization
- File path validation
- JSON payload validation
- Log message sanitization
- Integer validation
- Boolean validation
"""

from pathlib import Path

import pytest

from google_photos_sync.utils.validators import (
    ValidationError,
    sanitize_filename,
    sanitize_log_message,
    validate_account_type,
    validate_boolean,
    validate_email,
    validate_file_path,
    validate_json_payload,
    validate_positive_integer,
)


class TestEmailValidation:
    """Test email address validation."""

    def test_validate_email_valid(self) -> None:
        """Test validation of valid email addresses."""
        # Test standard email
        assert validate_email("user@example.com") == "user@example.com"

        # Test with uppercase (should normalize to lowercase)
        assert validate_email("User@Example.COM") == "user@example.com"

        # Test with whitespace (should trim)
        assert validate_email("  user@example.com  ") == "user@example.com"

        # Test with subdomain
        assert validate_email("user@mail.example.com") == "user@mail.example.com"

    def test_validate_email_empty(self) -> None:
        """Test validation fails for empty email."""
        with pytest.raises(ValidationError, match="Email address is required"):
            validate_email("")

    def test_validate_email_invalid(self) -> None:
        """Test validation fails for invalid email formats."""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user@@example.com",
            "user@example",
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError, match="Invalid email address"):
                validate_email(email)


class TestAccountTypeValidation:
    """Test account type validation."""

    def test_validate_account_type_valid(self) -> None:
        """Test validation of valid account types."""
        assert validate_account_type("source") == "source"
        assert validate_account_type("target") == "target"
        assert validate_account_type("SOURCE") == "source"  # Case insensitive
        assert validate_account_type("  target  ") == "target"  # Trim whitespace

    def test_validate_account_type_empty(self) -> None:
        """Test validation fails for empty account type."""
        with pytest.raises(ValidationError, match="Account type is required"):
            validate_account_type("")

    def test_validate_account_type_invalid(self) -> None:
        """Test validation fails for invalid account types."""
        with pytest.raises(ValidationError, match="Invalid account type"):
            validate_account_type("invalid")

        with pytest.raises(ValidationError, match="Invalid account type"):
            validate_account_type("destination")


class TestFilenameSanitization:
    """Test filename sanitization."""

    def test_sanitize_filename_valid(self) -> None:
        """Test sanitization of valid filenames."""
        assert sanitize_filename("photo.jpg") == "photo.jpg"
        assert sanitize_filename("my-photo_2025.jpg") == "my-photo_2025.jpg"

    def test_sanitize_filename_path_traversal(self) -> None:
        """Test sanitization prevents path traversal attacks."""
        # Remove path separators
        assert sanitize_filename("../../../etc/passwd") == "etcpasswd"
        assert sanitize_filename("..\\..\\windows\\system32") == "windowssystem32"

    def test_sanitize_filename_control_characters(self) -> None:
        """Test sanitization removes control characters."""
        # Null bytes and control characters should be removed
        assert sanitize_filename("file\x00name.jpg") == "filename.jpg"
        assert sanitize_filename("file\nname.jpg") == "filename.jpg"

    def test_sanitize_filename_max_length(self) -> None:
        """Test sanitization truncates to max length."""
        long_name = "a" * 300
        result = sanitize_filename(long_name, max_length=255)
        assert len(result) == 255

    def test_sanitize_filename_empty(self) -> None:
        """Test sanitization fails for empty filename."""
        with pytest.raises(ValidationError, match="Filename cannot be empty"):
            sanitize_filename("")

    def test_sanitize_filename_only_dots(self) -> None:
        """Test sanitization fails for filename with only dots."""
        with pytest.raises(ValidationError, match="Sanitized filename is empty"):
            sanitize_filename("...")


class TestFilePathValidation:
    """Test file path validation."""

    def test_validate_file_path_valid(self) -> None:
        """Test validation of valid file paths."""
        path = validate_file_path("/home/user/file.txt")
        assert isinstance(path, Path)
        assert path.is_absolute()

    def test_validate_file_path_with_base_dir(self, tmp_path: Path) -> None:
        """Test path validation with base directory restriction."""
        base_dir = tmp_path / "allowed"
        base_dir.mkdir()

        # Valid path within base_dir
        file_path = base_dir / "file.txt"
        result = validate_file_path(str(file_path), base_dir)
        assert result.is_relative_to(base_dir)

    def test_validate_file_path_outside_base_dir(self, tmp_path: Path) -> None:
        """Test validation fails for path outside base directory."""
        base_dir = tmp_path / "allowed"
        base_dir.mkdir()

        # Create another directory outside base_dir
        outside_dir = tmp_path / "not_allowed"
        outside_dir.mkdir()
        
        # Path outside base_dir
        outside_path = outside_dir / "file.txt"

        with pytest.raises(ValidationError, match="(outside allowed directory|Invalid file path)"):
            validate_file_path(str(outside_path), base_dir)

    def test_validate_file_path_empty(self) -> None:
        """Test validation fails for empty path."""
        with pytest.raises(ValidationError, match="File path cannot be empty"):
            validate_file_path("")


class TestJsonPayloadValidation:
    """Test JSON payload validation."""

    def test_validate_json_payload_valid(self) -> None:
        """Test validation of valid JSON payloads."""
        payload = {"field1": "value1", "field2": "value2"}
        result = validate_json_payload(payload, ["field1", "field2"])
        assert result == payload

    def test_validate_json_payload_extra_fields(self) -> None:
        """Test validation allows extra fields."""
        payload = {"required": "value", "extra": "also_ok"}
        result = validate_json_payload(payload, ["required"])
        assert result == payload

    def test_validate_json_payload_none(self) -> None:
        """Test validation fails for None payload."""
        with pytest.raises(ValidationError, match="Request body is required"):
            validate_json_payload(None, ["field1"])

    def test_validate_json_payload_not_dict(self) -> None:
        """Test validation fails for non-dict payload."""
        with pytest.raises(ValidationError, match="must be a JSON object"):
            validate_json_payload(["not", "a", "dict"], ["field1"])  # type: ignore[arg-type]

    def test_validate_json_payload_missing_fields(self) -> None:
        """Test validation fails when required fields are missing."""
        payload = {"field1": "value1"}

        with pytest.raises(
            ValidationError, match="Missing required fields: field2, field3"
        ):
            validate_json_payload(payload, ["field1", "field2", "field3"])


class TestLogMessageSanitization:
    """Test log message sanitization."""

    def test_sanitize_log_message_redacts_sensitive(self) -> None:
        """Test sanitization redacts sensitive patterns."""
        message = "User logged in with token: abc123def456"
        result = sanitize_log_message(message, ["abc123def456"])
        assert result == "User logged in with token: [REDACTED]"

    def test_sanitize_log_message_multiple_patterns(self) -> None:
        """Test sanitization redacts multiple patterns."""
        message = "Token: abc123, Secret: xyz789"
        result = sanitize_log_message(message, ["abc123", "xyz789"])
        assert "abc123" not in result
        assert "xyz789" not in result
        assert "[REDACTED]" in result

    def test_sanitize_log_message_no_patterns(self) -> None:
        """Test sanitization with no sensitive patterns."""
        message = "Normal log message"
        result = sanitize_log_message(message, [])
        assert result == message

    def test_sanitize_log_message_empty_pattern(self) -> None:
        """Test sanitization ignores empty patterns."""
        message = "Test message"
        result = sanitize_log_message(message, ["", "  "])
        assert result == message


class TestPositiveIntegerValidation:
    """Test positive integer validation."""

    def test_validate_positive_integer_valid(self) -> None:
        """Test validation of valid positive integers."""
        assert validate_positive_integer(10, "count") == 10
        assert validate_positive_integer("25", "limit") == 25
        assert validate_positive_integer(1, "min") == 1

    def test_validate_positive_integer_max_value(self) -> None:
        """Test validation enforces maximum value."""
        with pytest.raises(ValidationError, match="must be <= 100"):
            validate_positive_integer(150, "count", max_value=100)

    def test_validate_positive_integer_zero(self) -> None:
        """Test validation fails for zero."""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_positive_integer(0, "count")

    def test_validate_positive_integer_negative(self) -> None:
        """Test validation fails for negative values."""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_positive_integer(-5, "count")

    def test_validate_positive_integer_invalid_type(self) -> None:
        """Test validation fails for non-integer types."""
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_positive_integer("not-a-number", "count")


class TestBooleanValidation:
    """Test boolean validation."""

    def test_validate_boolean_true_values(self) -> None:
        """Test validation of various true values."""
        assert validate_boolean(True, "flag") is True
        assert validate_boolean("true", "flag") is True
        assert validate_boolean("TRUE", "flag") is True
        assert validate_boolean("yes", "flag") is True
        assert validate_boolean("1", "flag") is True
        assert validate_boolean(1, "flag") is True

    def test_validate_boolean_false_values(self) -> None:
        """Test validation of various false values."""
        assert validate_boolean(False, "flag") is False
        assert validate_boolean("false", "flag") is False
        assert validate_boolean("FALSE", "flag") is False
        assert validate_boolean("no", "flag") is False
        assert validate_boolean("0", "flag") is False
        assert validate_boolean(0, "flag") is False

    def test_validate_boolean_default(self) -> None:
        """Test validation returns default for None."""
        assert validate_boolean(None, "flag", default=True) is True
        assert validate_boolean(None, "flag", default=False) is False

    def test_validate_boolean_invalid(self) -> None:
        """Test validation fails for invalid boolean values."""
        with pytest.raises(ValidationError, match="must be a boolean value"):
            validate_boolean("maybe", "flag")

        with pytest.raises(ValidationError, match="must be a boolean value"):
            validate_boolean(2, "flag")

        with pytest.raises(ValidationError, match="must be a boolean value"):
            validate_boolean([], "flag")  # type: ignore[arg-type]
