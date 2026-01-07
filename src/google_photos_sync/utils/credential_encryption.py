"""Credential encryption for secure OAuth token storage.

This module provides encryption/decryption for OAuth credentials at rest
using Fernet symmetric encryption (AES-128-CBC with HMAC).

Encryption key is derived from environment variable or auto-generated.
For production use, set CREDENTIAL_ENCRYPTION_KEY environment variable.

Example:
    >>> from google_photos_sync.utils.credential_encryption import CredentialEncryption
    >>> encryptor = CredentialEncryption()
    >>> encrypted = encryptor.encrypt_credentials(credentials_dict)
    >>> decrypted = encryptor.decrypt_credentials(encrypted)
"""

import base64
import json
import os
from typing import Any, Dict

from cryptography.fernet import Fernet, InvalidToken


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""

    pass


class CredentialEncryption:
    """Handles encryption and decryption of OAuth credentials.

    Uses Fernet symmetric encryption (AES-128-CBC with HMAC).
    Encryption key is loaded from environment or auto-generated.

    Attributes:
        _fernet: Fernet encryption instance
    """

    def __init__(self, encryption_key: str | None = None) -> None:
        """Initialize credential encryption.

        Args:
            encryption_key: Base64-encoded Fernet key. If None, loads from
                CREDENTIAL_ENCRYPTION_KEY environment variable or generates new key.

        Raises:
            EncryptionError: If key is invalid

        Example:
            >>> encryptor = CredentialEncryption()
            >>> # Or provide specific key:
            >>> key = Fernet.generate_key().decode()
            >>> encryptor = CredentialEncryption(encryption_key=key)
        """
        try:
            if encryption_key is None:
                # Try to load from environment
                env_key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
                if env_key:
                    encryption_key = env_key
                else:
                    # Generate new key and warn (not secure for production!)
                    encryption_key = Fernet.generate_key().decode()
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        "No CREDENTIAL_ENCRYPTION_KEY set, using generated key. "
                        "This is NOT secure for production use. "
                        "Set CREDENTIAL_ENCRYPTION_KEY environment variable."
                    )

            # Create Fernet instance with key
            self._fernet = Fernet(encryption_key.encode())

        except Exception as e:
            raise EncryptionError(f"Failed to initialize encryption: {e}") from e

    def encrypt_credentials(self, credentials_dict: Dict[str, Any]) -> str:
        """Encrypt credentials dictionary to base64-encoded string.

        Args:
            credentials_dict: Dictionary containing OAuth credentials
                (token, refresh_token, expiry, etc.)

        Returns:
            Base64-encoded encrypted credentials string

        Raises:
            EncryptionError: If encryption fails

        Example:
            >>> creds = {"token": "abc123", "refresh_token": "xyz789"}
            >>> encrypted = encryptor.encrypt_credentials(creds)
            >>> # Store encrypted string safely
        """
        try:
            # Convert dict to JSON string
            json_data = json.dumps(credentials_dict)

            # Encrypt JSON string
            encrypted_bytes = self._fernet.encrypt(json_data.encode("utf-8"))

            # Return as base64 string
            return base64.b64encode(encrypted_bytes).decode("utf-8")

        except Exception as e:
            raise EncryptionError(f"Failed to encrypt credentials: {e}") from e

    def decrypt_credentials(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt base64-encoded encrypted credentials.

        Args:
            encrypted_data: Base64-encoded encrypted credentials string

        Returns:
            Decrypted credentials dictionary

        Raises:
            EncryptionError: If decryption fails (invalid key, corrupted data)

        Example:
            >>> encrypted = "..."  # Load from storage
            >>> creds = encryptor.decrypt_credentials(encrypted)
            >>> print(creds["token"])
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode("utf-8"))

            # Decrypt
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)

            # Parse JSON
            json_data = decrypted_bytes.decode("utf-8")
            credentials_dict: Dict[str, Any] = json.loads(json_data)

            return credentials_dict

        except InvalidToken as e:
            raise EncryptionError(
                "Failed to decrypt credentials: Invalid encryption key or corrupted data"
            ) from e
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt credentials: {e}") from e

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet encryption key.

        Returns:
            Base64-encoded Fernet key string (safe to store in .env)

        Example:
            >>> key = CredentialEncryption.generate_key()
            >>> print(f"CREDENTIAL_ENCRYPTION_KEY={key}")
            >>> # Add to .env file
        """
        return Fernet.generate_key().decode("utf-8")
