"""Unit tests for credential encryption.

Tests cover:
- Credential encryption
- Credential decryption
- Key generation
- Error handling
"""

import pytest
from cryptography.fernet import Fernet

from google_photos_sync.utils.credential_encryption import (
    CredentialEncryption,
    EncryptionError,
)


class TestCredentialEncryption:
    """Test credential encryption and decryption."""

    def test_encrypt_decrypt_credentials(self) -> None:
        """Test encryption and decryption roundtrip."""
        # Create encryptor with generated key
        key = Fernet.generate_key().decode()
        encryptor = CredentialEncryption(encryption_key=key)

        # Test data
        credentials = {
            "token": "test_access_token_123",
            "refresh_token": "test_refresh_token_456",
            "expiry": "2025-12-31T23:59:59Z",
            "client_id": "test_client_id",
        }

        # Encrypt
        encrypted = encryptor.encrypt_credentials(credentials)

        # Verify encrypted is a string
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

        # Decrypt
        decrypted = encryptor.decrypt_credentials(encrypted)

        # Verify decrypted matches original
        assert decrypted == credentials

    def test_encrypt_credentials_complex_data(self) -> None:
        """Test encryption handles complex nested data."""
        encryptor = CredentialEncryption(encryption_key=Fernet.generate_key().decode())

        credentials = {
            "token": "abc123",
            "metadata": {
                "user": "test@example.com",
                "scopes": ["read", "write"],
            },
            "count": 42,
            "active": True,
        }

        encrypted = encryptor.encrypt_credentials(credentials)
        decrypted = encryptor.decrypt_credentials(encrypted)

        assert decrypted == credentials
        assert decrypted["metadata"]["scopes"] == ["read", "write"]

    def test_decrypt_with_wrong_key_fails(self) -> None:
        """Test decryption fails with wrong key."""
        # Encrypt with one key
        key1 = Fernet.generate_key().decode()
        encryptor1 = CredentialEncryption(encryption_key=key1)
        credentials = {"token": "secret"}
        encrypted = encryptor1.encrypt_credentials(credentials)

        # Try to decrypt with different key
        key2 = Fernet.generate_key().decode()
        encryptor2 = CredentialEncryption(encryption_key=key2)

        with pytest.raises(EncryptionError, match="Invalid encryption key"):
            encryptor2.decrypt_credentials(encrypted)

    def test_decrypt_corrupted_data_fails(self) -> None:
        """Test decryption fails for corrupted data."""
        encryptor = CredentialEncryption(encryption_key=Fernet.generate_key().decode())

        # Corrupted base64 data
        corrupted = "this_is_not_valid_encrypted_data"

        with pytest.raises(EncryptionError, match="Failed to decrypt"):
            encryptor.decrypt_credentials(corrupted)

    def test_generate_key(self) -> None:
        """Test key generation produces valid Fernet keys."""
        key = CredentialEncryption.generate_key()

        # Verify key is a string
        assert isinstance(key, str)

        # Verify key can be used to create Fernet instance
        fernet = Fernet(key.encode())
        assert fernet is not None

        # Verify key can encrypt/decrypt
        encryptor = CredentialEncryption(encryption_key=key)
        test_data = {"test": "data"}
        encrypted = encryptor.encrypt_credentials(test_data)
        decrypted = encryptor.decrypt_credentials(encrypted)
        assert decrypted == test_data

    def test_initialization_with_invalid_key_fails(self) -> None:
        """Test initialization fails with invalid key."""
        with pytest.raises(EncryptionError, match="Failed to initialize"):
            CredentialEncryption(encryption_key="invalid_key_format")

    def test_encrypt_empty_dict(self) -> None:
        """Test encryption handles empty dictionary."""
        encryptor = CredentialEncryption(encryption_key=Fernet.generate_key().decode())

        empty_creds = {}
        encrypted = encryptor.encrypt_credentials(empty_creds)
        decrypted = encryptor.decrypt_credentials(encrypted)

        assert decrypted == empty_creds

    def test_encrypt_unicode_data(self) -> None:
        """Test encryption handles Unicode characters."""
        encryptor = CredentialEncryption(encryption_key=Fernet.generate_key().decode())

        credentials = {
            "user": "用户@example.com",
            "name": "João Silva",
            "emoji": "🔐🔒",
        }

        encrypted = encryptor.encrypt_credentials(credentials)
        decrypted = encryptor.decrypt_credentials(encrypted)

        assert decrypted == credentials
        assert decrypted["user"] == "用户@example.com"
        assert decrypted["emoji"] == "🔐🔒"

    def test_same_data_different_ciphertext(self) -> None:
        """Test same data encrypts to different ciphertext each time (IV randomness)."""
        encryptor = CredentialEncryption(encryption_key=Fernet.generate_key().decode())

        credentials = {"token": "test123"}

        # Encrypt same data twice
        encrypted1 = encryptor.encrypt_credentials(credentials)
        encrypted2 = encryptor.encrypt_credentials(credentials)

        # Ciphertexts should be different (due to random IV)
        assert encrypted1 != encrypted2

        # But both should decrypt to same data
        assert encryptor.decrypt_credentials(encrypted1) == credentials
        assert encryptor.decrypt_credentials(encrypted2) == credentials
