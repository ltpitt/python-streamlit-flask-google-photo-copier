"""Integration tests for Flask REST API routes.

Tests all API endpoints including OAuth flow, compare, and sync operations
with proper mocking of Google Photos client.

Example:
    $ pytest tests/integration/test_api_routes.py -v --cov=src/google_photos_sync/api
"""

from unittest import mock

import pytest
from flask.testing import FlaskClient

from google_photos_sync.api.app import create_app
from google_photos_sync.core.compare_service import CompareResult
from google_photos_sync.core.sync_service import SyncResult
from google_photos_sync.google_photos.models import Photo


@pytest.fixture
def app():
    """Create Flask app in testing mode."""
    app = create_app("testing")
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_auth():
    """Mock Google Photos auth handler."""
    with mock.patch(
        "google_photos_sync.api.routes.GooglePhotosAuth"
    ) as mock_auth_class:
        mock_instance = mock.Mock()
        mock_auth_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_google_client():
    """Mock Google Photos client."""
    with mock.patch(
        "google_photos_sync.api.routes.GooglePhotosClient"
    ) as mock_client_class:
        mock_instance = mock.Mock()
        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_compare_service():
    """Mock compare service."""
    with mock.patch(
        "google_photos_sync.api.routes.CompareService"
    ) as mock_service_class:
        mock_instance = mock.Mock()
        mock_service_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_sync_service():
    """Mock sync service."""
    with mock.patch("google_photos_sync.api.routes.SyncService") as mock_service_class:
        mock_instance = mock.Mock()
        mock_service_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_photos():
    """Sample photo data for testing."""
    return [
        Photo(
            id="photo-1",
            filename="vacation1.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
        ),
        Photo(
            id="photo-2",
            filename="vacation2.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-02T10:00:00Z",
            width=1920,
            height=1080,
        ),
    ]


class TestAuthRoutes:
    """Test OAuth authentication endpoints."""

    def test_initiate_oauth_flow_returns_auth_url(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test POST /api/auth/google returns authorization URL."""
        # Arrange
        mock_auth.generate_auth_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?...",
            "test-state-token",
        )

        # Act
        response = client.post(
            "/api/auth/google",
            json={"account_type": "source"},
        )

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "authorization_url" in data["data"]
        assert "state" in data["data"]
        assert data["data"]["state"] == "test-state-token"

    def test_initiate_oauth_flow_handles_unexpected_error(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test POST /api/auth/google handles unexpected errors."""
        # Arrange
        mock_auth.generate_auth_url.side_effect = Exception("Unexpected error")

        # Act
        response = client.post(
            "/api/auth/google",
            json={"account_type": "source"},
        )

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    def test_initiate_oauth_flow_handles_auth_error(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test POST /api/auth/google handles authentication errors."""
        # Arrange
        from google_photos_sync.google_photos.auth import AuthenticationError

        mock_auth.generate_auth_url.side_effect = AuthenticationError(
            "OAuth setup failed"
        )

        # Act
        response = client.post(
            "/api/auth/google",
            json={"account_type": "source"},
        )

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert data["code"] == "AUTH_INITIATION_FAILED"

    def test_initiate_oauth_flow_validates_account_type(
        self, client: FlaskClient
    ) -> None:
        """Test POST /api/auth/google validates account_type parameter."""
        # Act
        response = client.post(
            "/api/auth/google",
            json={"account_type": "invalid"},
        )

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        # Accept either "account_type" or "account type" in error
        error_lower = data["error"].lower()
        assert "account" in error_lower and "type" in error_lower

    def test_initiate_oauth_flow_requires_account_type(
        self, client: FlaskClient
    ) -> None:
        """Test POST /api/auth/google requires account_type parameter."""
        # Act
        response = client.post(
            "/api/auth/google",
            json={},
        )

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_oauth_callback_exchanges_code_for_token(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test GET /api/auth/callback exchanges code for credentials."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_auth.exchange_code_for_token.return_value = mock_credentials

        # Act
        response = client.get(
            "/api/auth/callback?code=test-auth-code&state=test-state&account_type=source&account_email=user@example.com",
            headers={"Accept": "application/json"}
        )

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "message" in data
        mock_auth.save_credentials.assert_called_once()

    def test_oauth_callback_requires_code_parameter(self, client: FlaskClient) -> None:
        """Test GET /api/auth/callback requires code parameter."""
        # Act
        response = client.get(
            "/api/auth/callback?state=test-state&account_type=source&account_email=user@example.com"
        )

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_oauth_callback_requires_account_type(self, client: FlaskClient) -> None:
        """Test GET /api/auth/callback requires account_type parameter."""
        # Act
        response = client.get(
            "/api/auth/callback?code=test-code&state=test-state&account_email=user@example.com"
        )

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_oauth_callback_requires_account_email(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test GET /api/auth/callback requires account_email parameter."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_credentials.id_token = None  # No ID token to extract email from
        mock_auth.exchange_code_for_token.return_value = mock_credentials

        # Act
        response = client.get(
            "/api/auth/callback?code=test-code&state=test-state&account_type=source"
        )

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_oauth_callback_handles_auth_error(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test GET /api/auth/callback handles authentication errors."""
        # Arrange
        from google_photos_sync.google_photos.auth import AuthenticationError

        mock_auth.exchange_code_for_token.side_effect = AuthenticationError(
            "Invalid authorization code"
        )

        # Act
        response = client.get(
            "/api/auth/callback?code=invalid-code&state=test-state&account_type=source&account_email=user@example.com"
        )

        # Assert
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    def test_oauth_callback_handles_credential_storage_error(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test GET /api/auth/callback handles credential storage errors."""
        # Arrange
        from google_photos_sync.google_photos.auth import CredentialStorageError

        mock_credentials = mock.Mock()
        mock_auth.exchange_code_for_token.return_value = mock_credentials
        mock_auth.save_credentials.side_effect = CredentialStorageError(
            "Failed to save credentials"
        )

        # Act
        response = client.get(
            "/api/auth/callback?code=test-code&state=test-state&account_type=source&account_email=user@example.com",
            headers={"Accept": "application/json"}
        )

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    def test_oauth_callback_returns_html_for_browser(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test GET /api/auth/callback returns HTML for browser requests."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_auth.exchange_code_for_token.return_value = mock_credentials

        # Act - no Accept header = browser request
        response = client.get(
            "/api/auth/callback?code=test-code&state=test-state&account_type=source&account_email=user@example.com"
        )

        # Assert
        assert response.status_code == 200
        assert b"Authentication Successful" in response.data
        assert b"user@example.com" in response.data
        mock_auth.save_credentials.assert_called_once()

    def test_oauth_callback_handles_email_extraction_from_id_token(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test GET /api/auth/callback extracts email from ID token."""
        # Arrange
        import base64
        import json

        # Create a mock ID token with email
        payload = {"email": "extracted@example.com", "sub": "123456"}
        payload_bytes = json.dumps(payload).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode(
            "utf-8"
        ).rstrip("=")
        id_token = f"header.{payload_b64}.signature"

        mock_credentials = mock.Mock()
        mock_credentials.id_token = id_token
        mock_auth.exchange_code_for_token.return_value = mock_credentials

        # Act - no account_email in query, should extract from ID token
        response = client.get(
            "/api/auth/callback?code=test-code&state=test-state&account_type=source",
            headers={"Accept": "application/json"}
        )

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        # Verify it saved with the extracted email
        saved_email = mock_auth.save_credentials.call_args[0][2]
        assert saved_email == "extracted@example.com"

    def test_oauth_callback_handles_email_extraction_failure(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test GET /api/auth/callback handles ID token extraction errors."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_credentials.id_token = "invalid.token.format"  # Invalid JWT
        mock_auth.exchange_code_for_token.return_value = mock_credentials

        # Act
        response = client.get(
            "/api/auth/callback?code=test-code&state=test-state&account_type=source",
            headers={"Accept": "application/json"}
        )

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "email" in data["error"].lower()

    def test_oauth_callback_handles_invalid_email_format(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test GET /api/auth/callback validates email format."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_auth.exchange_code_for_token.return_value = mock_credentials

        # Act - invalid email format
        response = client.get(
            "/api/auth/callback?code=test-code&state=test-state&account_type=source&account_email=invalid-email",
            headers={"Accept": "application/json"}
        )

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert data["code"] == "INVALID_EMAIL"

    def test_oauth_callback_extracts_account_type_from_query_fallback(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test callback uses query parameter when state lacks account_type."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_auth.exchange_code_for_token.return_value = mock_credentials

        # Act - state without account_type prefix, rely on query parameter
        response = client.get(
            (
                "/api/auth/callback?code=test-code&state=random-token-"
                "without-prefix&account_type=target&account_email=user@example.com"
            ),
            headers={"Accept": "application/json"},
        )

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["account_type"] == "target"


class TestCompareRoute:
    """Test /api/compare endpoint."""

    def test_compare_accounts_returns_differences(
        self,
        client: FlaskClient,
        mock_auth: mock.Mock,
        mock_google_client: mock.Mock,
        mock_compare_service: mock.Mock,
        sample_photos: list[Photo],
    ) -> None:
        """Test POST /api/compare returns account comparison results."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_auth.get_valid_credentials.return_value = mock_credentials

        compare_result = CompareResult(
            source_account="source@example.com",
            target_account="target@example.com",
            comparison_date="2025-01-06T10:00:00Z",
            total_source_photos=2,
            total_target_photos=1,
            missing_on_target=[sample_photos[1]],
            different_metadata=[],
            extra_on_target=[],
        )
        mock_compare_service.compare_accounts.return_value = compare_result

        # Act
        response = client.post(
            "/api/compare",
            json={
                "source_account": "source@example.com",
                "target_account": "target@example.com",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["total_source_photos"] == 2
        assert data["data"]["total_target_photos"] == 1
        assert len(data["data"]["missing_on_target"]) == 1

    def test_compare_accounts_handles_exception_in_comparison(
        self,
        client: FlaskClient,
        mock_auth: mock.Mock,
        mock_google_client: mock.Mock,
        mock_compare_service: mock.Mock,
    ) -> None:
        """Test POST /api/compare handles exceptions during comparison."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_auth.get_valid_credentials.return_value = mock_credentials
        mock_compare_service.compare_accounts.side_effect = ValueError(
            "Invalid photo data"
        )

        # Act
        response = client.post(
            "/api/compare",
            json={
                "source_account": "source@example.com",
                "target_account": "target@example.com",
            },
        )

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "Invalid photo data" in data["error"]

    def test_compare_accounts_requires_source_account(
        self, client: FlaskClient
    ) -> None:
        """Test POST /api/compare requires source_account parameter."""
        # Act
        response = client.post(
            "/api/compare",
            json={"target_account": "target@example.com"},
        )

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_compare_accounts_requires_target_account(
        self, client: FlaskClient
    ) -> None:
        """Test POST /api/compare requires target_account parameter."""
        # Act
        response = client.post(
            "/api/compare",
            json={"source_account": "source@example.com"},
        )

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_compare_accounts_handles_missing_credentials(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test POST /api/compare handles missing credentials."""
        # Arrange
        mock_auth.get_valid_credentials.return_value = None

        # Act
        response = client.post(
            "/api/compare",
            json={
                "source_account": "source@example.com",
                "target_account": "target@example.com",
            },
        )

        # Assert
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "not authenticated" in data["error"].lower()

    def test_compare_accounts_handles_missing_target_credentials(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test POST /api/compare handles missing target credentials."""
        # Arrange
        mock_source_creds = mock.Mock()

        def get_creds_side_effect(account_type, account_email):
            from google_photos_sync.google_photos.auth import AccountType

            if account_type == AccountType.SOURCE:
                return mock_source_creds
            return None

        mock_auth.get_valid_credentials.side_effect = get_creds_side_effect

        # Act
        response = client.post(
            "/api/compare",
            json={
                "source_account": "source@example.com",
                "target_account": "target@example.com",
            },
        )

        # Assert
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "target" in data["error"].lower()
        assert "not authenticated" in data["error"].lower()

    def test_compare_accounts_handles_api_error(
        self,
        client: FlaskClient,
        mock_auth: mock.Mock,
        mock_google_client: mock.Mock,
        mock_compare_service: mock.Mock,
    ) -> None:
        """Test POST /api/compare handles API errors gracefully."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_auth.get_valid_credentials.return_value = mock_credentials
        mock_compare_service.compare_accounts.side_effect = Exception(
            "API rate limit exceeded"
        )

        # Act
        response = client.post(
            "/api/compare",
            json={
                "source_account": "source@example.com",
                "target_account": "target@example.com",
            },
        )

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False


class TestSyncRoute:
    """Test /api/sync endpoint."""

    def test_sync_accounts_executes_sync_operation(
        self,
        client: FlaskClient,
        mock_auth: mock.Mock,
        mock_google_client: mock.Mock,
        mock_compare_service: mock.Mock,
        mock_sync_service: mock.Mock,
    ) -> None:
        """Test POST /api/sync executes sync operation."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_auth.get_valid_credentials.return_value = mock_credentials

        sync_result = SyncResult(
            source_account="source@example.com",
            target_account="target@example.com",
            sync_date="2025-01-06T10:00:00Z",
            photos_added=1,
            photos_deleted=0,
            photos_updated=0,
            failed_actions=0,
            total_actions=1,
            dry_run=False,
        )
        mock_sync_service.sync_accounts.return_value = sync_result

        # Act
        response = client.post(
            "/api/sync",
            json={
                "source_account": "source@example.com",
                "target_account": "target@example.com",
                "dry_run": False,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["photos_added"] == 1
        assert data["data"]["dry_run"] is False

    def test_sync_accounts_handles_exception_in_sync(
        self,
        client: FlaskClient,
        mock_auth: mock.Mock,
        mock_google_client: mock.Mock,
        mock_sync_service: mock.Mock,
    ) -> None:
        """Test POST /api/sync handles exceptions during sync."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_auth.get_valid_credentials.return_value = mock_credentials
        mock_sync_service.sync_accounts.side_effect = RuntimeError(
            "Network error during transfer"
        )

        # Act
        response = client.post(
            "/api/sync",
            json={
                "source_account": "source@example.com",
                "target_account": "target@example.com",
                "dry_run": False,
            },
        )

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False
        assert "Network error during transfer" in data["error"]

    def test_sync_accounts_supports_dry_run_mode(
        self,
        client: FlaskClient,
        mock_auth: mock.Mock,
        mock_google_client: mock.Mock,
        mock_compare_service: mock.Mock,
        mock_sync_service: mock.Mock,
    ) -> None:
        """Test POST /api/sync supports dry_run mode."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_auth.get_valid_credentials.return_value = mock_credentials

        sync_result = SyncResult(
            source_account="source@example.com",
            target_account="target@example.com",
            sync_date="2025-01-06T10:00:00Z",
            photos_added=1,
            photos_deleted=0,
            photos_updated=0,
            failed_actions=0,
            total_actions=1,
            dry_run=True,
        )
        mock_sync_service.sync_accounts.return_value = sync_result

        # Act
        response = client.post(
            "/api/sync",
            json={
                "source_account": "source@example.com",
                "target_account": "target@example.com",
                "dry_run": True,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["dry_run"] is True

    def test_sync_accounts_requires_source_account(self, client: FlaskClient) -> None:
        """Test POST /api/sync requires source_account parameter."""
        # Act
        response = client.post(
            "/api/sync",
            json={"target_account": "target@example.com"},
        )

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_sync_accounts_requires_target_account(self, client: FlaskClient) -> None:
        """Test POST /api/sync requires target_account parameter."""
        # Act
        response = client.post(
            "/api/sync",
            json={"source_account": "source@example.com"},
        )

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_sync_accounts_handles_missing_credentials(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test POST /api/sync handles missing credentials."""
        # Arrange
        mock_auth.get_valid_credentials.return_value = None

        # Act
        response = client.post(
            "/api/sync",
            json={
                "source_account": "source@example.com",
                "target_account": "target@example.com",
            },
        )

        # Assert
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "not authenticated" in data["error"].lower()

    def test_sync_accounts_handles_missing_target_credentials(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test POST /api/sync handles missing target credentials."""
        # Arrange
        mock_source_creds = mock.Mock()

        def get_creds_side_effect(account_type, account_email):
            from google_photos_sync.google_photos.auth import AccountType

            if account_type == AccountType.SOURCE:
                return mock_source_creds
            return None

        mock_auth.get_valid_credentials.side_effect = get_creds_side_effect

        # Act
        response = client.post(
            "/api/sync",
            json={
                "source_account": "source@example.com",
                "target_account": "target@example.com",
            },
        )

        # Assert
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "target" in data["error"].lower()
        assert "not authenticated" in data["error"].lower()

    def test_sync_accounts_handles_sync_error(
        self,
        client: FlaskClient,
        mock_auth: mock.Mock,
        mock_google_client: mock.Mock,
        mock_compare_service: mock.Mock,
        mock_sync_service: mock.Mock,
    ) -> None:
        """Test POST /api/sync handles sync errors gracefully."""
        # Arrange
        mock_credentials = mock.Mock()
        mock_auth.get_valid_credentials.return_value = mock_credentials
        mock_sync_service.sync_accounts.side_effect = Exception("Sync failed")

        # Act
        response = client.post(
            "/api/sync",
            json={
                "source_account": "source@example.com",
                "target_account": "target@example.com",
            },
        )

        # Assert
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False


class TestResponseFormat:
    """Test response format consistency."""

    def test_success_response_has_standard_format(
        self, client: FlaskClient, mock_auth: mock.Mock
    ) -> None:
        """Test successful responses follow standard format."""
        # Arrange
        mock_auth.generate_auth_url.return_value = (
            "https://example.com/auth",
            "state-token",
        )

        # Act
        response = client.post(
            "/api/auth/google",
            json={"account_type": "source"},
        )

        # Assert
        data = response.get_json()
        assert "success" in data
        assert "data" in data
        assert data["success"] is True

    def test_error_response_has_standard_format(self, client: FlaskClient) -> None:
        """Test error responses follow standard format."""
        # Act
        response = client.post(
            "/api/auth/google",
            json={},
        )

        # Assert
        data = response.get_json()
        assert "success" in data
        assert "error" in data
        assert "code" in data
        assert data["success"] is False

    def test_all_responses_are_json(self, client: FlaskClient) -> None:
        """Test all responses return JSON content type."""
        # Test various endpoints
        responses = [
            client.post("/api/auth/google", json={"account_type": "source"}),
            client.post("/api/compare", json={}),
            client.post("/api/sync", json={}),
        ]

        for response in responses:
            assert response.is_json
