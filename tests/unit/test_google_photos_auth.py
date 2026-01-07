"""Tests for Google Photos OAuth authentication module.

Following TDD approach: RED phase - write failing tests first.
These tests define the expected behavior of the auth module.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from google_photos_sync.google_photos.auth import (
    AccountType,
    AuthenticationError,
    CredentialStorageError,
    GooglePhotosAuth,
    TokenRefreshError,
)


class TestConstructorValidation:
    """Test constructor parameter validation."""

    def test_constructor_with_empty_client_id_raises_value_error(self):
        """Test that empty client_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GooglePhotosAuth(
                client_id="",
                client_secret="test_secret",
                redirect_uri="http://localhost:8080/callback",
            )
        assert "client_id cannot be empty" in str(exc_info.value)

    def test_constructor_with_empty_client_secret_raises_value_error(self):
        """Test that empty client_secret raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GooglePhotosAuth(
                client_id="test_client_id",
                client_secret="",
                redirect_uri="http://localhost:8080/callback",
            )
        assert "client_secret cannot be empty" in str(exc_info.value)

    def test_constructor_with_empty_redirect_uri_raises_value_error(self):
        """Test that empty redirect_uri raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GooglePhotosAuth(
                client_id="test_client_id",
                client_secret="test_secret",
                redirect_uri="",
            )
        assert "redirect_uri cannot be empty" in str(exc_info.value)

    def test_constructor_with_valid_params_succeeds(self):
        """Test that valid parameters create instance successfully."""
        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080/callback",
        )
        assert auth is not None


class TestOAuthURLGeneration:
    """Test OAuth URL generation with correct scopes."""

    def test_generate_auth_url_for_source_account_uses_readonly_scope(self, mocker):
        """Test that source account auth URL uses readonly scope."""
        # Arrange
        mock_flow = mocker.Mock(spec=Flow)
        mock_flow.authorization_url.return_value = (
            "http://auth.url",
            "mock_state_ignored",  # Implementation generates its own state
        )

        with patch(
            "google_photos_sync.google_photos.auth.Flow.from_client_config"
        ) as mock_flow_constructor:
            mock_flow_constructor.return_value = mock_flow

            auth = GooglePhotosAuth(
                client_id="test_client_id",
                client_secret="test_client_secret",
                redirect_uri="http://localhost:8080/callback",
            )

            # Act
            url, state = auth.generate_auth_url(AccountType.SOURCE)

            # Assert
            assert url == "http://auth.url"
            # Verify state format: "source_{random_token}"
            assert state.startswith("source_")
            assert len(state) > 7  # "source_" + random token
            # Verify readonly scope was used
            call_args = mock_flow_constructor.call_args
            scopes = call_args[1]["scopes"]
            assert "https://www.googleapis.com/auth/photoslibrary.readonly" in scopes
            assert "https://www.googleapis.com/auth/photoslibrary" not in scopes
            # Verify openid and email scopes are included
            assert "openid" in scopes
            assert "https://www.googleapis.com/auth/userinfo.email" in scopes

    def test_generate_auth_url_for_target_account_uses_full_access_scope(self, mocker):
        """Test that target account auth URL uses full access scope for writing."""
        # Arrange
        mock_flow = mocker.Mock(spec=Flow)
        mock_flow.authorization_url.return_value = (
            "http://auth.url",
            "mock_state_ignored",  # Implementation generates its own state
        )

        with patch(
            "google_photos_sync.google_photos.auth.Flow.from_client_config"
        ) as mock_flow_constructor:
            mock_flow_constructor.return_value = mock_flow

            auth = GooglePhotosAuth(
                client_id="test_client_id",
                client_secret="test_client_secret",
                redirect_uri="http://localhost:8080/callback",
            )

            # Act
            url, state = auth.generate_auth_url(AccountType.TARGET)

            # Assert
            assert url == "http://auth.url"
            # Verify state format: "target_{random_token}"
            assert state.startswith("target_")
            assert len(state) > 7  # "target_" + random token
            # Verify full photoslibrary scope was used (needed for writing)
            call_args = mock_flow_constructor.call_args
            scopes = call_args[1]["scopes"]
            assert "https://www.googleapis.com/auth/photoslibrary" in scopes
            readonly_scope = "https://www.googleapis.com/auth/photoslibrary.readonly"
            assert readonly_scope not in scopes
            # Verify openid and email scopes are included
            assert "openid" in scopes
            assert "https://www.googleapis.com/auth/userinfo.email" in scopes


class TestTokenExchange:
    """Test token exchange from authorization code."""

    def test_exchange_code_for_token_returns_credentials(self, mocker):
        """Test successful token exchange returns valid credentials."""
        # Arrange
        mock_flow = mocker.Mock(spec=Flow)
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_credentials.token = "access_token_123"
        mock_credentials.refresh_token = "refresh_token_123"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.client_id = "test_client_id"
        mock_credentials.client_secret = "test_client_secret"
        mock_credentials.scopes = [
            "https://www.googleapis.com/auth/photoslibrary.readonly"
        ]

        mock_flow.fetch_token.return_value = None
        mock_flow.credentials = mock_credentials

        with patch(
            "google_photos_sync.google_photos.auth.Flow.from_client_config"
        ) as mock_flow_constructor:
            mock_flow_constructor.return_value = mock_flow

            auth = GooglePhotosAuth(
                client_id="test_client_id",
                client_secret="test_client_secret",
                redirect_uri="http://localhost:8080/callback",
            )

            # Act
            credentials = auth.exchange_code_for_token(
                authorization_code="auth_code_123",
                account_type=AccountType.SOURCE,
            )

            # Assert
            assert credentials is not None
            assert credentials.token == "access_token_123"
            assert credentials.refresh_token == "refresh_token_123"
            mock_flow.fetch_token.assert_called_once_with(code="auth_code_123")

    def test_exchange_code_with_invalid_code_raises_authentication_error(self, mocker):
        """Test that invalid authorization code raises AuthenticationError."""
        # Arrange
        mock_flow = mocker.Mock(spec=Flow)
        mock_flow.fetch_token.side_effect = Exception("Invalid authorization code")

        with patch(
            "google_photos_sync.google_photos.auth.Flow.from_client_config"
        ) as mock_flow_constructor:
            mock_flow_constructor.return_value = mock_flow

            auth = GooglePhotosAuth(
                client_id="test_client_id",
                client_secret="test_client_secret",
                redirect_uri="http://localhost:8080/callback",
            )

            # Act & Assert
            with pytest.raises(AuthenticationError) as exc_info:
                auth.exchange_code_for_token(
                    authorization_code="invalid_code",
                    account_type=AccountType.SOURCE,
                )

            assert "Failed to exchange authorization code" in str(exc_info.value)


class TestCredentialStorage:
    """Test credential storage and retrieval."""

    def test_save_credentials_stores_to_file(self, tmp_path, mocker):
        """Test that credentials are saved to file correctly."""
        # Arrange
        credentials_dir = tmp_path / "credentials"
        mock_credentials = mocker.Mock(spec=Credentials)
        mock_credentials.token = "access_token_123"
        mock_credentials.refresh_token = "refresh_token_123"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.client_id = "test_client_id"
        mock_credentials.client_secret = "test_client_secret"
        mock_credentials.scopes = [
            "https://www.googleapis.com/auth/photoslibrary.readonly"
        ]
        mock_credentials.expiry = None

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act
        auth.save_credentials(
            credentials=mock_credentials,
            account_type=AccountType.SOURCE,
            account_email="source@example.com",
        )

        # Assert
        saved_file = credentials_dir / "source_source@example.com.json"
        assert saved_file.exists()

        with open(saved_file, "r") as f:
            saved_data = json.load(f)

        assert saved_data["token"] == "access_token_123"
        assert saved_data["refresh_token"] == "refresh_token_123"

    def test_save_credentials_with_io_error_raises_credential_storage_error(
        self, tmp_path, mocker
    ):
        """Test that I/O errors during save raise CredentialStorageError."""
        # Arrange
        credentials_dir = tmp_path / "readonly_dir"
        credentials_dir.mkdir()
        # Make directory read-only
        credentials_dir.chmod(0o444)

        mock_credentials = mocker.Mock(spec=Credentials)
        mock_credentials.token = "access_token_123"
        mock_credentials.refresh_token = "refresh_token_123"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.client_id = "test_client_id"
        mock_credentials.client_secret = "test_client_secret"
        mock_credentials.scopes = [
            "https://www.googleapis.com/auth/photoslibrary.readonly"
        ]
        mock_credentials.expiry = None

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act & Assert
        try:
            with pytest.raises(CredentialStorageError) as exc_info:
                auth.save_credentials(
                    credentials=mock_credentials,
                    account_type=AccountType.SOURCE,
                    account_email="source@example.com",
                )
            assert "Failed to save credentials" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            credentials_dir.chmod(0o755)

    def test_load_credentials_retrieves_from_file(self, tmp_path, mocker):
        """Test that credentials are loaded from file correctly."""
        # Arrange
        credentials_dir = tmp_path / "credentials"
        credentials_dir.mkdir()

        credentials_data = {
            "token": "access_token_123",
            "refresh_token": "refresh_token_123",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/photoslibrary.readonly"],
        }

        credentials_file = credentials_dir / "source_source@example.com.json"
        with open(credentials_file, "w") as f:
            json.dump(credentials_data, f)

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act
        credentials = auth.load_credentials(
            account_type=AccountType.SOURCE,
            account_email="source@example.com",
        )

        # Assert
        assert credentials is not None
        assert credentials.token == "access_token_123"
        assert credentials.refresh_token == "refresh_token_123"

    def test_load_credentials_with_corrupted_file_raises_credential_storage_error(
        self, tmp_path
    ):
        """Test that corrupted credentials file raises CredentialStorageError."""
        # Arrange
        credentials_dir = tmp_path / "credentials"
        credentials_dir.mkdir()

        # Write invalid JSON
        credentials_file = credentials_dir / "source_source@example.com.json"
        with open(credentials_file, "w") as f:
            f.write("invalid json {{{")

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act & Assert
        with pytest.raises(CredentialStorageError) as exc_info:
            auth.load_credentials(
                account_type=AccountType.SOURCE,
                account_email="source@example.com",
            )
        assert "Failed to load credentials" in str(exc_info.value)

    def test_load_nonexistent_credentials_returns_none(self, tmp_path):
        """Test that loading non-existent credentials returns None."""
        # Arrange
        credentials_dir = tmp_path / "credentials"

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act
        credentials = auth.load_credentials(
            account_type=AccountType.SOURCE,
            account_email="nonexistent@example.com",
        )

        # Assert
        assert credentials is None

    def test_save_credentials_creates_directory_if_missing(self, tmp_path, mocker):
        """Test that credentials directory is created if it doesn't exist."""
        # Arrange
        credentials_dir = tmp_path / "new_credentials_dir"
        assert not credentials_dir.exists()

        mock_credentials = mocker.Mock(spec=Credentials)
        mock_credentials.token = "access_token_123"
        mock_credentials.refresh_token = "refresh_token_123"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.client_id = "test_client_id"
        mock_credentials.client_secret = "test_client_secret"
        mock_credentials.scopes = [
            "https://www.googleapis.com/auth/photoslibrary.readonly"
        ]
        mock_credentials.expiry = None

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act
        auth.save_credentials(
            credentials=mock_credentials,
            account_type=AccountType.SOURCE,
            account_email="source@example.com",
        )

        # Assert
        assert credentials_dir.exists()
        assert credentials_dir.is_dir()


class TestTokenRefresh:
    """Test automatic token refresh when expired."""

    def test_get_valid_credentials_refreshes_expired_token(self, tmp_path, mocker):
        """Test that expired credentials are automatically refreshed."""
        # Arrange
        credentials_dir = tmp_path / "credentials"
        credentials_dir.mkdir()

        # Create expired credentials (use naive UTC datetime like Google does)
        from datetime import timezone

        expired_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            hours=1
        )
        credentials_data = {
            "token": "old_access_token",
            "refresh_token": "refresh_token_123",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/photoslibrary.readonly"],
            "expiry": expired_time.isoformat() + "Z",
        }

        credentials_file = credentials_dir / "source_source@example.com.json"
        with open(credentials_file, "w") as f:
            json.dump(credentials_data, f)

        # Mock the refresh
        mock_request = mocker.Mock()

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act
        with patch(
            "google_photos_sync.google_photos.auth.Request"
        ) as mock_request_class:
            mock_request_class.return_value = mock_request

            with patch.object(Credentials, "refresh") as mock_refresh:
                credentials = auth.get_valid_credentials(
                    account_type=AccountType.SOURCE,
                    account_email="source@example.com",
                )

                # Assert
                assert credentials is not None
                mock_refresh.assert_called_once_with(mock_request)

    def test_get_valid_credentials_returns_valid_token_without_refresh(
        self, tmp_path, mocker
    ):
        """Test that valid credentials are returned without refresh."""
        # Arrange
        credentials_dir = tmp_path / "credentials"
        credentials_dir.mkdir()

        # Create valid credentials (expires in future) - use naive UTC datetime
        from datetime import timezone

        future_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            hours=1
        )
        credentials_data = {
            "token": "valid_access_token",
            "refresh_token": "refresh_token_123",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/photoslibrary.readonly"],
            "expiry": future_time.isoformat() + "Z",
        }

        credentials_file = credentials_dir / "source_source@example.com.json"
        with open(credentials_file, "w") as f:
            json.dump(credentials_data, f)

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act
        with patch.object(Credentials, "refresh") as mock_refresh:
            credentials = auth.get_valid_credentials(
                account_type=AccountType.SOURCE,
                account_email="source@example.com",
            )

            # Assert
            assert credentials is not None
            assert credentials.token == "valid_access_token"
            # Should NOT have called refresh
            mock_refresh.assert_not_called()

    def test_refresh_fails_raises_token_refresh_error(self, tmp_path, mocker):
        """Test that failed token refresh raises TokenRefreshError."""
        # Arrange
        credentials_dir = tmp_path / "credentials"
        credentials_dir.mkdir()

        from datetime import timezone

        expired_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            hours=1
        )
        credentials_data = {
            "token": "old_access_token",
            "refresh_token": "invalid_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/photoslibrary.readonly"],
            "expiry": expired_time.isoformat() + "Z",
        }

        credentials_file = credentials_dir / "source_source@example.com.json"
        with open(credentials_file, "w") as f:
            json.dump(credentials_data, f)

        mock_request = mocker.Mock()

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act & Assert
        with patch(
            "google_photos_sync.google_photos.auth.Request"
        ) as mock_request_class:
            mock_request_class.return_value = mock_request

            with patch.object(
                Credentials, "refresh", side_effect=Exception("Refresh failed")
            ):
                with pytest.raises(TokenRefreshError) as exc_info:
                    auth.get_valid_credentials(
                        account_type=AccountType.SOURCE,
                        account_email="source@example.com",
                    )

                assert "Failed to refresh token" in str(exc_info.value)

    def test_get_valid_credentials_returns_none_if_no_credentials_exist(self, tmp_path):
        """Test that get_valid_credentials returns None if no credentials exist."""
        # Arrange
        credentials_dir = tmp_path / "credentials"

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act
        credentials = auth.get_valid_credentials(
            account_type=AccountType.SOURCE,
            account_email="nonexistent@example.com",
        )

        # Assert
        assert credentials is None


class TestMultipleAccountManagement:
    """Test managing multiple accounts (source vs target) simultaneously."""

    def test_can_store_both_source_and_target_credentials(self, tmp_path, mocker):
        """Test that both source and target credentials can be stored separately."""
        # Arrange
        credentials_dir = tmp_path / "credentials"

        mock_source_creds = mocker.Mock(spec=Credentials)
        mock_source_creds.token = "source_token"
        mock_source_creds.refresh_token = "source_refresh"
        mock_source_creds.token_uri = "https://oauth2.googleapis.com/token"
        mock_source_creds.client_id = "test_client_id"
        mock_source_creds.client_secret = "test_client_secret"
        mock_source_creds.scopes = [
            "https://www.googleapis.com/auth/photoslibrary.readonly"
        ]
        mock_source_creds.expiry = None

        mock_target_creds = mocker.Mock(spec=Credentials)
        mock_target_creds.token = "target_token"
        mock_target_creds.refresh_token = "target_refresh"
        mock_target_creds.token_uri = "https://oauth2.googleapis.com/token"
        mock_target_creds.client_id = "test_client_id"
        mock_target_creds.client_secret = "test_client_secret"
        mock_target_creds.scopes = [
            "https://www.googleapis.com/auth/photoslibrary.appendonly"
        ]
        mock_target_creds.expiry = None

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act
        auth.save_credentials(
            credentials=mock_source_creds,
            account_type=AccountType.SOURCE,
            account_email="source@example.com",
        )
        auth.save_credentials(
            credentials=mock_target_creds,
            account_type=AccountType.TARGET,
            account_email="target@example.com",
        )

        # Assert
        source_file = credentials_dir / "source_source@example.com.json"
        target_file = credentials_dir / "target_target@example.com.json"

        assert source_file.exists()
        assert target_file.exists()

        with open(source_file, "r") as f:
            source_data = json.load(f)
        assert source_data["token"] == "source_token"

        with open(target_file, "r") as f:
            target_data = json.load(f)
        assert target_data["token"] == "target_token"

    def test_can_load_both_source_and_target_credentials(self, tmp_path):
        """Test that both source and target credentials can be loaded separately."""
        # Arrange
        credentials_dir = tmp_path / "credentials"
        credentials_dir.mkdir()

        source_data = {
            "token": "source_token",
            "refresh_token": "source_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/photoslibrary.readonly"],
        }

        target_data = {
            "token": "target_token",
            "refresh_token": "target_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/photoslibrary.appendonly"],
        }

        with open(credentials_dir / "source_source@example.com.json", "w") as f:
            json.dump(source_data, f)

        with open(credentials_dir / "target_target@example.com.json", "w") as f:
            json.dump(target_data, f)

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act
        source_creds = auth.load_credentials(
            account_type=AccountType.SOURCE,
            account_email="source@example.com",
        )
        target_creds = auth.load_credentials(
            account_type=AccountType.TARGET,
            account_email="target@example.com",
        )

        # Assert
        assert source_creds is not None
        assert source_creds.token == "source_token"

        assert target_creds is not None
        assert target_creds.token == "target_token"

    def test_different_emails_same_account_type_stored_separately(
        self, tmp_path, mocker
    ):
        """Test that different emails for same account type are stored separately."""
        # Arrange
        credentials_dir = tmp_path / "credentials"

        mock_creds1 = mocker.Mock(spec=Credentials)
        mock_creds1.token = "token1"
        mock_creds1.refresh_token = "refresh1"
        mock_creds1.token_uri = "https://oauth2.googleapis.com/token"
        mock_creds1.client_id = "test_client_id"
        mock_creds1.client_secret = "test_client_secret"
        mock_creds1.scopes = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
        mock_creds1.expiry = None

        mock_creds2 = mocker.Mock(spec=Credentials)
        mock_creds2.token = "token2"
        mock_creds2.refresh_token = "refresh2"
        mock_creds2.token_uri = "https://oauth2.googleapis.com/token"
        mock_creds2.client_id = "test_client_id"
        mock_creds2.client_secret = "test_client_secret"
        mock_creds2.scopes = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
        mock_creds2.expiry = None

        auth = GooglePhotosAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            credentials_dir=credentials_dir,
        )

        # Act
        auth.save_credentials(
            credentials=mock_creds1,
            account_type=AccountType.SOURCE,
            account_email="user1@example.com",
        )
        auth.save_credentials(
            credentials=mock_creds2,
            account_type=AccountType.SOURCE,
            account_email="user2@example.com",
        )

        # Assert
        file1 = credentials_dir / "source_user1@example.com.json"
        file2 = credentials_dir / "source_user2@example.com.json"

        assert file1.exists()
        assert file2.exists()

        with open(file1, "r") as f:
            data1 = json.load(f)
        assert data1["token"] == "token1"

        with open(file2, "r") as f:
            data2 = json.load(f)
        assert data2["token"] == "token2"
