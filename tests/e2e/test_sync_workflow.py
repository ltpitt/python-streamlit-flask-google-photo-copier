"""End-to-End tests for complete sync workflow.

This module tests complete workflows from authentication through compare and sync
operations, ensuring all components work together correctly. These tests use the
real Flask app and services but mock external Google API calls.

The E2E tests verify:
- Complete OAuth flow (mock Google OAuth)
- Full compare operation (mock Google Photos API)
- Full sync operation (mock Google Photos API)
- Error recovery scenarios
- Idempotency verification

Example:
    $ pytest tests/e2e/test_sync_workflow.py -v --cov=src
"""

from unittest import mock

import pytest
from flask import Flask
from flask.testing import FlaskClient

from google_photos_sync.api.app import create_app
from google_photos_sync.core.compare_service import CompareResult
from google_photos_sync.core.sync_service import SyncResult
from google_photos_sync.google_photos.auth import (
    AccountType,
    AuthenticationError,
    CredentialStorageError,
    TokenRefreshError,
)
from google_photos_sync.google_photos.models import Photo


@pytest.fixture
def app() -> Flask:
    """Create Flask app in testing mode for E2E tests.

    Returns:
        Flask application configured for testing
    """
    return create_app("testing")


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create Flask test client for making HTTP requests.

    Args:
        app: Flask application instance

    Returns:
        Flask test client
    """
    return app.test_client()


@pytest.fixture
def sample_source_photos() -> list[Photo]:
    """Create sample photos for source account.

    Returns:
        List of Photo objects representing source account content
    """
    return [
        Photo(
            id="source-photo-1",
            filename="vacation_beach.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
            base_url="https://lh3.googleusercontent.com/source1",
            description="Beautiful beach",
            is_favorite=True,
        ),
        Photo(
            id="source-photo-2",
            filename="mountain_hike.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-02T14:30:00Z",
            width=3840,
            height=2160,
            base_url="https://lh3.googleusercontent.com/source2",
            camera_make="Canon",
            camera_model="EOS 5D",
        ),
        Photo(
            id="source-photo-3",
            filename="family_dinner.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-03T18:00:00Z",
            width=2048,
            height=1536,
            base_url="https://lh3.googleusercontent.com/source3",
        ),
    ]


@pytest.fixture
def sample_target_photos() -> list[Photo]:
    """Create sample photos for target account.

    Returns:
        List of Photo objects representing target account content
    """
    return [
        Photo(
            id="source-photo-1",
            filename="vacation_beach.jpg",
            mime_type="image/jpeg",
            created_time="2025-01-01T10:00:00Z",
            width=1920,
            height=1080,
            base_url="https://lh3.googleusercontent.com/target1",
            description="Beautiful beach",
            is_favorite=True,
        ),
        Photo(
            id="target-only-photo",
            filename="old_photo.jpg",
            mime_type="image/jpeg",
            created_time="2024-12-01T10:00:00Z",
            width=1024,
            height=768,
            base_url="https://lh3.googleusercontent.com/target2",
        ),
    ]


@pytest.fixture
def mock_credentials():
    """Create mock OAuth credentials.

    Returns:
        Mock credentials object
    """
    creds = mock.Mock()
    creds.token = "mock-access-token"
    creds.refresh_token = "mock-refresh-token"
    creds.expired = False
    return creds


@pytest.mark.e2e
class TestCompleteOAuthFlow:
    """Test complete OAuth authentication flow end-to-end."""

    def test_oauth_flow_for_source_account_success(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test complete OAuth flow for source account from start to finish."""
        # Step 1: Initiate OAuth flow
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.generate_auth_url.return_value = (
                "https://accounts.google.com/o/oauth2/auth?client_id=test",
                "random-state-token-123",
            )

            response = client.post(
                "/api/auth/google",
                json={"account_type": "source"},
            )

            # Verify auth URL generation
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert "authorization_url" in data["data"]
            assert data["data"]["state"] == "random-state-token-123"

            # Step 2: Simulate OAuth callback with authorization code
            mock_auth.exchange_code_for_token.return_value = mock_credentials
            mock_auth.save_credentials.return_value = None

            callback_response = client.get(
                "/api/auth/callback?"
                "code=auth-code-xyz&"
                "state=random-state-token-123&"
                "account_type=source&"
                "account_email=source@example.com"
            )

            # Verify callback success
            assert callback_response.status_code == 200
            callback_data = callback_response.get_json()
            assert callback_data["success"] is True
            assert "Authentication successful" in callback_data["message"]

            # Verify credentials were saved
            mock_auth.exchange_code_for_token.assert_called_once_with(
                "auth-code-xyz", AccountType.SOURCE
            )
            mock_auth.save_credentials.assert_called_once()

    def test_oauth_flow_for_target_account_success(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test complete OAuth flow for target account."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.generate_auth_url.return_value = (
                "https://accounts.google.com/o/oauth2/auth?client_id=test",
                "state-456",
            )

            # Initiate OAuth for target
            response = client.post(
                "/api/auth/google",
                json={"account_type": "target"},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["data"]["account_type"] == "target"

            # Complete OAuth callback
            mock_auth.exchange_code_for_token.return_value = mock_credentials

            callback_response = client.get(
                "/api/auth/callback?"
                "code=target-code&"
                "state=state-456&"
                "account_type=target&"
                "account_email=target@example.com"
            )

            assert callback_response.status_code == 200
            assert callback_response.get_json()["success"] is True

    def test_oauth_flow_handles_invalid_authorization_code(
        self, client: FlaskClient
    ) -> None:
        """Test OAuth flow handles invalid authorization code gracefully."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.exchange_code_for_token.side_effect = AuthenticationError(
                "Invalid authorization code"
            )

            response = client.get(
                "/api/auth/callback?"
                "code=invalid-code&"
                "state=state-123&"
                "account_type=source&"
                "account_email=source@example.com"
            )

            assert response.status_code == 401
            data = response.get_json()
            assert data["success"] is False
            assert "Invalid authorization code" in data["error"]

    def test_oauth_flow_handles_credential_storage_failure(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test OAuth flow handles credential storage failures."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.exchange_code_for_token.return_value = mock_credentials
            mock_auth.save_credentials.side_effect = CredentialStorageError(
                "Disk full"
            )

            response = client.get(
                "/api/auth/callback?"
                "code=valid-code&"
                "state=state-123&"
                "account_type=source&"
                "account_email=source@example.com"
            )

            assert response.status_code == 500
            data = response.get_json()
            assert data["success"] is False
            # CredentialStorageError is caught by generic Exception handler
            assert "Internal server error" in data["error"]


@pytest.mark.e2e
class TestCompleteCompareWorkflow:
    """Test complete compare operation workflow end-to-end."""

    def test_complete_compare_workflow_success(
        self,
        client: FlaskClient,
        mock_credentials: mock.Mock,
        sample_source_photos: list[Photo],
        sample_target_photos: list[Photo],
    ) -> None:
        """Test complete compare workflow from authentication to results."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class, mock.patch(
            "google_photos_sync.api.routes.GooglePhotosClient"
        ) as mock_client_class, mock.patch(
            "google_photos_sync.api.routes.CompareService"
        ) as mock_compare_class:
            # Setup mocks
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = mock_credentials

            mock_source_client = mock.Mock()
            mock_target_client = mock.Mock()
            mock_client_class.side_effect = [mock_source_client, mock_target_client]

            mock_compare_service = mock.Mock()
            mock_compare_class.return_value = mock_compare_service

            # Setup compare result
            compare_result = CompareResult(
                source_account="source@example.com",
                target_account="target@example.com",
                comparison_date="2025-01-06T10:00:00Z",
                total_source_photos=3,
                total_target_photos=2,
                missing_on_target=[
                    sample_source_photos[1],
                    sample_source_photos[2],
                ],
                different_metadata=[],
                extra_on_target=[sample_target_photos[1]],
            )
            mock_compare_service.compare_accounts.return_value = compare_result

            # Execute compare operation
            response = client.post(
                "/api/compare",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                },
            )

            # Verify response
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["data"]["total_source_photos"] == 3
            assert data["data"]["total_target_photos"] == 2
            assert len(data["data"]["missing_on_target"]) == 2
            assert len(data["data"]["extra_on_target"]) == 1

            # Verify service was called correctly
            mock_compare_service.compare_accounts.assert_called_once_with(
                "source@example.com", "target@example.com"
            )

    def test_compare_workflow_handles_missing_source_credentials(
        self, client: FlaskClient
    ) -> None:
        """Test compare workflow handles missing source credentials."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = None

            response = client.post(
                "/api/compare",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                },
            )

            assert response.status_code == 401
            data = response.get_json()
            assert data["success"] is False
            assert "not authenticated" in data["error"].lower()

    def test_compare_workflow_handles_api_errors(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test compare workflow handles Google API errors gracefully."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class, mock.patch(
            "google_photos_sync.api.routes.GooglePhotosClient"
        ), mock.patch("google_photos_sync.api.routes.CompareService") as mock_compare:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = mock_credentials

            mock_compare_service = mock.Mock()
            mock_compare.return_value = mock_compare_service
            mock_compare_service.compare_accounts.side_effect = Exception(
                "API rate limit exceeded"
            )

            response = client.post(
                "/api/compare",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                },
            )

            assert response.status_code == 500
            data = response.get_json()
            assert data["success"] is False
            assert "API rate limit exceeded" in data["error"]


@pytest.mark.e2e
class TestCompleteSyncWorkflow:
    """Test complete sync operation workflow end-to-end."""

    def test_complete_sync_workflow_success(
        self,
        client: FlaskClient,
        mock_credentials: mock.Mock,
        sample_source_photos: list[Photo],
    ) -> None:
        """Test complete sync workflow from authentication to completion."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class, mock.patch(
            "google_photos_sync.api.routes.GooglePhotosClient"
        ), mock.patch(
            "google_photos_sync.api.routes.CompareService"
        ), mock.patch(
            "google_photos_sync.api.routes.TransferManager"
        ), mock.patch(
            "google_photos_sync.api.routes.SyncService"
        ) as mock_sync_class:
            # Setup authentication
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = mock_credentials

            # Setup sync service
            mock_sync_service = mock.Mock()
            mock_sync_class.return_value = mock_sync_service

            sync_result = SyncResult(
                source_account="source@example.com",
                target_account="target@example.com",
                sync_date="2025-01-06T10:00:00Z",
                photos_added=2,
                photos_deleted=1,
                photos_updated=0,
                failed_actions=0,
                total_actions=3,
                dry_run=False,
            )
            mock_sync_service.sync_accounts.return_value = sync_result

            # Execute sync operation
            response = client.post(
                "/api/sync",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                    "dry_run": False,
                },
            )

            # Verify response
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["data"]["photos_added"] == 2
            assert data["data"]["photos_deleted"] == 1
            assert data["data"]["photos_updated"] == 0
            assert data["data"]["failed_actions"] == 0
            assert data["data"]["dry_run"] is False

            # Verify sync was called correctly
            mock_sync_service.sync_accounts.assert_called_once_with(
                "source@example.com", "target@example.com", False
            )

    def test_sync_workflow_dry_run_mode(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test sync workflow in dry-run mode (preview only)."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class, mock.patch(
            "google_photos_sync.api.routes.GooglePhotosClient"
        ), mock.patch(
            "google_photos_sync.api.routes.CompareService"
        ), mock.patch(
            "google_photos_sync.api.routes.TransferManager"
        ), mock.patch(
            "google_photos_sync.api.routes.SyncService"
        ) as mock_sync_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = mock_credentials

            mock_sync_service = mock.Mock()
            mock_sync_class.return_value = mock_sync_service

            dry_run_result = SyncResult(
                source_account="source@example.com",
                target_account="target@example.com",
                sync_date="2025-01-06T10:00:00Z",
                photos_added=5,
                photos_deleted=2,
                photos_updated=1,
                failed_actions=0,
                total_actions=8,
                dry_run=True,
            )
            mock_sync_service.sync_accounts.return_value = dry_run_result

            # Execute dry-run sync
            response = client.post(
                "/api/sync",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                    "dry_run": True,
                },
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["data"]["dry_run"] is True
            assert "preview" in data["message"].lower()

            # Verify dry-run was passed to sync service
            mock_sync_service.sync_accounts.assert_called_once_with(
                "source@example.com", "target@example.com", True
            )

    def test_sync_workflow_handles_partial_failures(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test sync workflow handles partial failures correctly."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class, mock.patch(
            "google_photos_sync.api.routes.GooglePhotosClient"
        ), mock.patch(
            "google_photos_sync.api.routes.CompareService"
        ), mock.patch(
            "google_photos_sync.api.routes.TransferManager"
        ), mock.patch(
            "google_photos_sync.api.routes.SyncService"
        ) as mock_sync_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = mock_credentials

            mock_sync_service = mock.Mock()
            mock_sync_class.return_value = mock_sync_service

            # Simulate partial failure scenario
            partial_failure_result = SyncResult(
                source_account="source@example.com",
                target_account="target@example.com",
                sync_date="2025-01-06T10:00:00Z",
                photos_added=3,
                photos_deleted=1,
                photos_updated=0,
                failed_actions=2,
                total_actions=6,
                dry_run=False,
            )
            mock_sync_service.sync_accounts.return_value = partial_failure_result

            response = client.post(
                "/api/sync",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                    "dry_run": False,
                },
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["data"]["failed_actions"] == 2
            assert data["data"]["photos_added"] == 3

    def test_sync_workflow_handles_complete_failure(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test sync workflow handles complete sync failure."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class, mock.patch(
            "google_photos_sync.api.routes.GooglePhotosClient"
        ), mock.patch(
            "google_photos_sync.api.routes.CompareService"
        ), mock.patch(
            "google_photos_sync.api.routes.TransferManager"
        ), mock.patch(
            "google_photos_sync.api.routes.SyncService"
        ) as mock_sync_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = mock_credentials

            mock_sync_service = mock.Mock()
            mock_sync_class.return_value = mock_sync_service
            mock_sync_service.sync_accounts.side_effect = Exception(
                "Network timeout"
            )

            response = client.post(
                "/api/sync",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                    "dry_run": False,
                },
            )

            assert response.status_code == 500
            data = response.get_json()
            assert data["success"] is False
            assert "Network timeout" in data["error"]


@pytest.mark.e2e
class TestIdempotencyVerification:
    """Test idempotency of sync operations."""

    def test_sync_operation_is_idempotent(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test that running sync multiple times produces same result."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class, mock.patch(
            "google_photos_sync.api.routes.GooglePhotosClient"
        ), mock.patch(
            "google_photos_sync.api.routes.CompareService"
        ), mock.patch(
            "google_photos_sync.api.routes.TransferManager"
        ), mock.patch(
            "google_photos_sync.api.routes.SyncService"
        ) as mock_sync_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = mock_credentials

            mock_sync_service = mock.Mock()
            mock_sync_class.return_value = mock_sync_service

            # First sync - has work to do
            first_sync_result = SyncResult(
                source_account="source@example.com",
                target_account="target@example.com",
                sync_date="2025-01-06T10:00:00Z",
                photos_added=3,
                photos_deleted=1,
                photos_updated=0,
                failed_actions=0,
                total_actions=4,
                dry_run=False,
            )

            # Second sync - already synced, no work
            second_sync_result = SyncResult(
                source_account="source@example.com",
                target_account="target@example.com",
                sync_date="2025-01-06T10:01:00Z",
                photos_added=0,
                photos_deleted=0,
                photos_updated=0,
                failed_actions=0,
                total_actions=0,
                dry_run=False,
            )

            mock_sync_service.sync_accounts.side_effect = [
                first_sync_result,
                second_sync_result,
            ]

            # First sync execution
            response1 = client.post(
                "/api/sync",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                    "dry_run": False,
                },
            )

            assert response1.status_code == 200
            data1 = response1.get_json()
            assert data1["data"]["total_actions"] == 4

            # Second sync execution (idempotent - should have no work)
            response2 = client.post(
                "/api/sync",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                    "dry_run": False,
                },
            )

            assert response2.status_code == 200
            data2 = response2.get_json()
            assert data2["data"]["total_actions"] == 0
            assert data2["data"]["photos_added"] == 0
            assert data2["data"]["photos_deleted"] == 0

    def test_compare_operation_is_idempotent(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test that running compare multiple times produces consistent results."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class, mock.patch(
            "google_photos_sync.api.routes.GooglePhotosClient"
        ), mock.patch(
            "google_photos_sync.api.routes.CompareService"
        ) as mock_compare_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = mock_credentials

            mock_compare_service = mock.Mock()
            mock_compare_class.return_value = mock_compare_service

            compare_result = CompareResult(
                source_account="source@example.com",
                target_account="target@example.com",
                comparison_date="2025-01-06T10:00:00Z",
                total_source_photos=5,
                total_target_photos=3,
                missing_on_target=[],
                different_metadata=[],
                extra_on_target=[],
            )
            mock_compare_service.compare_accounts.return_value = compare_result

            # Run compare multiple times
            for _ in range(3):
                response = client.post(
                    "/api/compare",
                    json={
                        "source_account": "source@example.com",
                        "target_account": "target@example.com",
                    },
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data["data"]["total_source_photos"] == 5
                assert data["data"]["total_target_photos"] == 3


@pytest.mark.e2e
class TestErrorRecoveryScenarios:
    """Test error recovery and resilience scenarios."""

    def test_recovery_from_expired_credentials(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test system handles expired credentials and token refresh."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth

            # First attempt - expired credentials
            mock_auth.get_valid_credentials.side_effect = TokenRefreshError(
                "Token refresh failed"
            )

            response = client.post(
                "/api/compare",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                },
            )

            # Should fail gracefully
            assert response.status_code == 500
            data = response.get_json()
            assert data["success"] is False

    def test_recovery_from_network_errors(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test system handles network errors gracefully."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class, mock.patch(
            "google_photos_sync.api.routes.GooglePhotosClient"
        ), mock.patch(
            "google_photos_sync.api.routes.CompareService"
        ) as mock_compare_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = mock_credentials

            mock_compare_service = mock.Mock()
            mock_compare_class.return_value = mock_compare_service
            mock_compare_service.compare_accounts.side_effect = ConnectionError(
                "Network unreachable"
            )

            response = client.post(
                "/api/compare",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                },
            )

            assert response.status_code == 500
            data = response.get_json()
            assert data["success"] is False
            assert "Network unreachable" in data["error"]

    def test_handling_of_missing_both_credentials(
        self, client: FlaskClient
    ) -> None:
        """Test system handles when both source and target credentials are missing."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = None

            response = client.post(
                "/api/compare",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                },
            )

            assert response.status_code == 401
            data = response.get_json()
            assert data["success"] is False
            assert "not authenticated" in data["error"].lower()


@pytest.mark.e2e
class TestEndToEndIntegration:
    """Test complete integration scenarios combining multiple operations."""

    def test_full_workflow_auth_compare_sync(
        self,
        client: FlaskClient,
        mock_credentials: mock.Mock,
        sample_source_photos: list[Photo],
        sample_target_photos: list[Photo],
    ) -> None:
        """Test complete workflow: OAuth → Compare → Dry-run → Real Sync."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class, mock.patch(
            "google_photos_sync.api.routes.GooglePhotosClient"
        ), mock.patch(
            "google_photos_sync.api.routes.CompareService"
        ) as mock_compare_class, mock.patch(
            "google_photos_sync.api.routes.TransferManager"
        ), mock.patch(
            "google_photos_sync.api.routes.SyncService"
        ) as mock_sync_class:
            # Setup mocks
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth

            # Step 1: OAuth for source
            mock_auth.generate_auth_url.return_value = (
                "https://oauth.url",
                "state1",
            )
            response = client.post(
                "/api/auth/google", json={"account_type": "source"}
            )
            assert response.status_code == 200

            mock_auth.exchange_code_for_token.return_value = mock_credentials
            callback = client.get(
                "/api/auth/callback?code=c1&state=s1&"
                "account_type=source&account_email=source@example.com"
            )
            assert callback.status_code == 200

            # Step 2: OAuth for target
            response = client.post(
                "/api/auth/google", json={"account_type": "target"}
            )
            assert response.status_code == 200

            callback = client.get(
                "/api/auth/callback?code=c2&state=s2&"
                "account_type=target&account_email=target@example.com"
            )
            assert callback.status_code == 200

            # Step 3: Compare accounts
            mock_auth.get_valid_credentials.return_value = mock_credentials
            mock_compare_service = mock.Mock()
            mock_compare_class.return_value = mock_compare_service

            compare_result = CompareResult(
                source_account="source@example.com",
                target_account="target@example.com",
                comparison_date="2025-01-06T10:00:00Z",
                total_source_photos=3,
                total_target_photos=2,
                missing_on_target=[sample_source_photos[1]],
                different_metadata=[],
                extra_on_target=[sample_target_photos[1]],
            )
            mock_compare_service.compare_accounts.return_value = compare_result

            compare_resp = client.post(
                "/api/compare",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                },
            )
            assert compare_resp.status_code == 200
            assert compare_resp.get_json()["data"]["total_source_photos"] == 3

            # Step 4: Dry-run sync
            mock_sync_service = mock.Mock()
            mock_sync_class.return_value = mock_sync_service

            dry_run_result = SyncResult(
                source_account="source@example.com",
                target_account="target@example.com",
                sync_date="2025-01-06T10:00:00Z",
                photos_added=1,
                photos_deleted=1,
                photos_updated=0,
                failed_actions=0,
                total_actions=2,
                dry_run=True,
            )
            mock_sync_service.sync_accounts.return_value = dry_run_result

            dry_run_resp = client.post(
                "/api/sync",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                    "dry_run": True,
                },
            )
            assert dry_run_resp.status_code == 200
            assert dry_run_resp.get_json()["data"]["dry_run"] is True

            # Step 5: Real sync
            real_sync_result = SyncResult(
                source_account="source@example.com",
                target_account="target@example.com",
                sync_date="2025-01-06T10:01:00Z",
                photos_added=1,
                photos_deleted=1,
                photos_updated=0,
                failed_actions=0,
                total_actions=2,
                dry_run=False,
            )
            mock_sync_service.sync_accounts.return_value = real_sync_result

            sync_resp = client.post(
                "/api/sync",
                json={
                    "source_account": "source@example.com",
                    "target_account": "target@example.com",
                    "dry_run": False,
                },
            )
            assert sync_resp.status_code == 200
            assert sync_resp.get_json()["data"]["dry_run"] is False
            assert sync_resp.get_json()["data"]["failed_actions"] == 0

    def test_multiple_account_pairs_workflow(
        self, client: FlaskClient, mock_credentials: mock.Mock
    ) -> None:
        """Test workflow with multiple source-target account pairs."""
        with mock.patch(
            "google_photos_sync.api.routes.GooglePhotosAuth"
        ) as mock_auth_class, mock.patch(
            "google_photos_sync.api.routes.GooglePhotosClient"
        ), mock.patch(
            "google_photos_sync.api.routes.CompareService"
        ) as mock_compare_class:
            mock_auth = mock.Mock()
            mock_auth_class.return_value = mock_auth
            mock_auth.get_valid_credentials.return_value = mock_credentials

            mock_compare_service = mock.Mock()
            mock_compare_class.return_value = mock_compare_service

            # Pair 1: source1 -> target1
            result1 = CompareResult(
                source_account="source1@example.com",
                target_account="target1@example.com",
                comparison_date="2025-01-06T10:00:00Z",
                total_source_photos=10,
                total_target_photos=8,
                missing_on_target=[],
                different_metadata=[],
                extra_on_target=[],
            )
            mock_compare_service.compare_accounts.return_value = result1

            resp1 = client.post(
                "/api/compare",
                json={
                    "source_account": "source1@example.com",
                    "target_account": "target1@example.com",
                },
            )
            assert resp1.status_code == 200
            assert resp1.get_json()["data"]["total_source_photos"] == 10

            # Pair 2: source2 -> target2
            result2 = CompareResult(
                source_account="source2@example.com",
                target_account="target2@example.com",
                comparison_date="2025-01-06T10:01:00Z",
                total_source_photos=25,
                total_target_photos=20,
                missing_on_target=[],
                different_metadata=[],
                extra_on_target=[],
            )
            mock_compare_service.compare_accounts.return_value = result2

            resp2 = client.post(
                "/api/compare",
                json={
                    "source_account": "source2@example.com",
                    "target_account": "target2@example.com",
                },
            )
            assert resp2.status_code == 200
            assert resp2.get_json()["data"]["total_source_photos"] == 25
