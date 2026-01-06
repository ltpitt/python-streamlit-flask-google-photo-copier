"""Flask REST API routes for Google Photos Sync.

This module implements REST API endpoints for OAuth authentication,
account comparison, and sync operations. All endpoints follow REST
principles with proper request validation, error handling, and
JSON responses.

Endpoints:
    POST /api/auth/google - Initiate OAuth flow
    GET /api/auth/callback - OAuth callback handler
    POST /api/compare - Compare source and target accounts
    POST /api/sync - Execute sync operation

Example:
    >>> from google_photos_sync.api.app import create_app
    >>> app = create_app('development')
    >>> client = app.test_client()
    >>> response = client.post('/api/auth/google', json={'account_type': 'source'})
"""

import logging
from typing import Any

from flask import Blueprint, current_app, request

from google_photos_sync.core.compare_service import CompareService
from google_photos_sync.core.sync_service import SyncService
from google_photos_sync.core.transfer_manager import TransferManager
from google_photos_sync.google_photos.auth import (
    AccountType,
    AuthenticationError,
    GooglePhotosAuth,
)
from google_photos_sync.google_photos.client import GooglePhotosClient

logger = logging.getLogger(__name__)

# Create blueprint for API routes
api_bp = Blueprint("api", __name__, url_prefix="/api")


def _success_response(data: Any, message: str = "") -> tuple[dict[str, Any], int]:
    """Create standardized success response.

    Args:
        data: Response data
        message: Optional success message

    Returns:
        Tuple of (response dict, status code)
    """
    response = {"success": True, "data": data}
    if message:
        response["message"] = message
    return response, 200


def _error_response(
    error: str, code: str, status_code: int = 400
) -> tuple[dict[str, Any], int]:
    """Create standardized error response.

    Args:
        error: Error description
        code: Error code for programmatic handling
        status_code: HTTP status code

    Returns:
        Tuple of (response dict, status code)
    """
    return (
        {
            "success": False,
            "error": error,
            "code": code,
        },
        status_code,
    )


def _get_auth_handler() -> GooglePhotosAuth:
    """Get configured GooglePhotosAuth instance from app config.

    Returns:
        Configured GooglePhotosAuth instance

    Raises:
        ValueError: If configuration is missing
    """
    config = current_app.config.get("APP_CONFIG")
    if not config:
        raise ValueError("APP_CONFIG not found in Flask config")

    return GooglePhotosAuth(
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        redirect_uri=config.GOOGLE_REDIRECT_URI,
    )


@api_bp.route("/auth/google", methods=["POST"])
def initiate_oauth() -> tuple[dict[str, Any], int]:
    """Initiate OAuth flow for Google Photos authentication.

    Request body (JSON):
        account_type: Type of account ('source' or 'target')

    Returns:
        JSON response with authorization URL and state token

    Status Codes:
        200: Success - returns authorization URL
        400: Bad Request - missing or invalid account_type
        500: Internal Server Error - OAuth flow initiation failed

    Example:
        >>> POST /api/auth/google
        >>> {"account_type": "source"}
        >>>
        >>> Response:
        >>> {
        >>>   "success": true,
        >>>   "data": {
        >>>     "authorization_url": "https://accounts.google.com/...",
        >>>     "state": "random-state-token"
        >>>   }
        >>> }
    """
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return _error_response(
                "Request body is required", "MISSING_REQUEST_BODY", 400
            )

        account_type_str = data.get("account_type")
        if not account_type_str:
            return _error_response(
                "account_type is required", "MISSING_ACCOUNT_TYPE", 400
            )

        # Validate account_type value
        if account_type_str not in ["source", "target"]:
            return _error_response(
                "account_type must be 'source' or 'target'",
                "INVALID_ACCOUNT_TYPE",
                400,
            )

        # Convert to AccountType enum
        account_type = AccountType(account_type_str)

        # Generate auth URL
        auth_handler = _get_auth_handler()
        authorization_url, state = auth_handler.generate_auth_url(account_type)

        logger.info(f"Generated OAuth URL for {account_type_str} account")

        return _success_response(
            {
                "authorization_url": authorization_url,
                "state": state,
                "account_type": account_type_str,
            },
            "OAuth flow initiated successfully",
        )

    except AuthenticationError as e:
        logger.error(f"OAuth initiation failed: {e}")
        return _error_response(str(e), "AUTH_INITIATION_FAILED", 500)
    except Exception as e:
        logger.exception(f"Unexpected error in OAuth initiation: {e}")
        return _error_response(
            "Internal server error", "INTERNAL_SERVER_ERROR", 500
        )


@api_bp.route("/auth/callback", methods=["GET"])
def oauth_callback() -> tuple[dict[str, Any], int]:
    """Handle OAuth callback and exchange code for credentials.

    Query Parameters:
        code: Authorization code from OAuth provider
        state: State token for CSRF protection
        account_type: Type of account ('source' or 'target')
        account_email: Email address of the authenticated account

    Returns:
        JSON response confirming successful authentication

    Status Codes:
        200: Success - credentials saved
        400: Bad Request - missing required parameters
        401: Unauthorized - authentication failed
        500: Internal Server Error

    Example:
        >>> GET /api/auth/callback?code=abc&state=xyz&account_type=source
        >>> &account_email=user@example.com
        >>>
        >>> Response:
        >>> {
        >>>   "success": true,
        >>>   "message": "Authentication successful for source@example.com"
        >>> }
    """
    try:
        # Get query parameters
        code = request.args.get("code")
        # state = request.args.get("state")  # For future CSRF validation
        account_type_str = request.args.get("account_type")
        account_email = request.args.get("account_email")

        # Validate required parameters
        if not code:
            return _error_response("code parameter is required", "MISSING_CODE", 400)
        if not account_type_str:
            return _error_response(
                "account_type parameter is required", "MISSING_ACCOUNT_TYPE", 400
            )
        if not account_email:
            return _error_response(
                "account_email parameter is required", "MISSING_ACCOUNT_EMAIL", 400
            )

        # Validate account_type value
        if account_type_str not in ["source", "target"]:
            return _error_response(
                "account_type must be 'source' or 'target'",
                "INVALID_ACCOUNT_TYPE",
                400,
            )

        # Convert to AccountType enum
        account_type = AccountType(account_type_str)

        # Exchange code for credentials
        auth_handler = _get_auth_handler()
        credentials = auth_handler.exchange_code_for_token(code, account_type)

        # Save credentials
        auth_handler.save_credentials(credentials, account_type, account_email)

        logger.info(
            f"OAuth callback successful for {account_type_str} account: {account_email}"
        )

        return _success_response(
            {"account_type": account_type_str, "account_email": account_email},
            f"Authentication successful for {account_email}",
        )

    except AuthenticationError as e:
        logger.error(f"OAuth callback authentication failed: {e}")
        return _error_response(str(e), "AUTHENTICATION_FAILED", 401)
    except Exception as e:
        logger.exception(f"Unexpected error in OAuth callback: {e}")
        return _error_response(
            "Internal server error", "INTERNAL_SERVER_ERROR", 500
        )


@api_bp.route("/compare", methods=["POST"])
def compare_accounts() -> tuple[dict[str, Any], int]:
    """Compare source and target Google Photos accounts.

    Request body (JSON):
        source_account: Email of source account
        target_account: Email of target account

    Returns:
        JSON response with comparison results

    Status Codes:
        200: Success - comparison completed
        400: Bad Request - missing required parameters
        401: Unauthorized - missing or invalid credentials
        500: Internal Server Error

    Example:
        >>> POST /api/compare
        >>> {
        >>>   "source_account": "source@example.com",
        >>>   "target_account": "target@example.com"
        >>> }
        >>>
        >>> Response:
        >>> {
        >>>   "success": true,
        >>>   "data": {
        >>>     "total_source_photos": 100,
        >>>     "total_target_photos": 50,
        >>>     "missing_on_target": [...],
        >>>     "extra_on_target": [...],
        >>>     "different_metadata": [...]
        >>>   }
        >>> }
    """
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return _error_response(
                "Request body is required", "MISSING_REQUEST_BODY", 400
            )

        source_account = data.get("source_account")
        target_account = data.get("target_account")

        if not source_account:
            return _error_response(
                "source_account is required", "MISSING_SOURCE_ACCOUNT", 400
            )
        if not target_account:
            return _error_response(
                "target_account is required", "MISSING_TARGET_ACCOUNT", 400
            )

        # Get auth handler and load credentials
        auth_handler = _get_auth_handler()

        source_creds = auth_handler.get_valid_credentials(
            AccountType.SOURCE, source_account
        )
        target_creds = auth_handler.get_valid_credentials(
            AccountType.TARGET, target_account
        )

        # Check if credentials exist
        if not source_creds:
            return _error_response(
                f"Source account {source_account} is not authenticated",
                "SOURCE_NOT_AUTHENTICATED",
                401,
            )
        if not target_creds:
            return _error_response(
                f"Target account {target_account} is not authenticated",
                "TARGET_NOT_AUTHENTICATED",
                401,
            )

        # Create Google Photos clients
        source_client = GooglePhotosClient(source_creds)
        target_client = GooglePhotosClient(target_creds)

        # Create compare service and execute comparison
        compare_service = CompareService(source_client, target_client)
        result = compare_service.compare_accounts(source_account, target_account)

        logger.info(
            f"Comparison completed: {source_account} vs {target_account} - "
            f"Missing: {len(result.missing_on_target)}, "
            f"Extra: {len(result.extra_on_target)}, "
            f"Different: {len(result.different_metadata)}"
        )

        return _success_response(result.to_json(), "Comparison completed successfully")

    except Exception as e:
        logger.exception(f"Error comparing accounts: {e}")
        return _error_response(str(e), "COMPARISON_FAILED", 500)


@api_bp.route("/sync", methods=["POST"])
def sync_accounts() -> tuple[dict[str, Any], int]:
    """Execute sync operation from source to target account.

    Request body (JSON):
        source_account: Email of source account
        target_account: Email of target account
        dry_run: Optional boolean, default False (preview mode)

    Returns:
        JSON response with sync results

    Status Codes:
        200: Success - sync completed
        400: Bad Request - missing required parameters
        401: Unauthorized - missing or invalid credentials
        500: Internal Server Error

    Example:
        >>> POST /api/sync
        >>> {
        >>>   "source_account": "source@example.com",
        >>>   "target_account": "target@example.com",
        >>>   "dry_run": false
        >>> }
        >>>
        >>> Response:
        >>> {
        >>>   "success": true,
        >>>   "data": {
        >>>     "photos_added": 50,
        >>>     "photos_deleted": 10,
        >>>     "photos_updated": 5,
        >>>     "failed_actions": 0,
        >>>     "total_actions": 65,
        >>>     "dry_run": false
        >>>   }
        >>> }
    """
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return _error_response(
                "Request body is required", "MISSING_REQUEST_BODY", 400
            )

        source_account = data.get("source_account")
        target_account = data.get("target_account")
        dry_run = data.get("dry_run", False)

        if not source_account:
            return _error_response(
                "source_account is required", "MISSING_SOURCE_ACCOUNT", 400
            )
        if not target_account:
            return _error_response(
                "target_account is required", "MISSING_TARGET_ACCOUNT", 400
            )

        # Get auth handler and load credentials
        auth_handler = _get_auth_handler()

        source_creds = auth_handler.get_valid_credentials(
            AccountType.SOURCE, source_account
        )
        target_creds = auth_handler.get_valid_credentials(
            AccountType.TARGET, target_account
        )

        # Check if credentials exist
        if not source_creds:
            return _error_response(
                f"Source account {source_account} is not authenticated",
                "SOURCE_NOT_AUTHENTICATED",
                401,
            )
        if not target_creds:
            return _error_response(
                f"Target account {target_account} is not authenticated",
                "TARGET_NOT_AUTHENTICATED",
                401,
            )

        # Create Google Photos clients
        source_client = GooglePhotosClient(source_creds)
        target_client = GooglePhotosClient(target_creds)

        # Create services
        compare_service = CompareService(source_client, target_client)
        transfer_manager = TransferManager(source_client, target_client)
        sync_service = SyncService(compare_service, transfer_manager)

        # Execute sync
        result = sync_service.sync_accounts(source_account, target_account, dry_run)

        logger.info(
            f"Sync {'preview' if dry_run else 'completed'}: "
            f"{source_account} -> {target_account} - "
            f"Added: {result.photos_added}, "
            f"Deleted: {result.photos_deleted}, "
            f"Updated: {result.photos_updated}, "
            f"Failed: {result.failed_actions}"
        )

        return _success_response(
            result.to_json(),
            f"Sync {'preview' if dry_run else 'operation'} completed successfully",
        )

    except Exception as e:
        logger.exception(f"Error syncing accounts: {e}")
        return _error_response(str(e), "SYNC_FAILED", 500)


def register_routes(app: Any) -> None:
    """Register API routes blueprint with Flask app.

    Args:
        app: Flask application instance

    Example:
        >>> from flask import Flask
        >>> from google_photos_sync.api.routes import register_routes
        >>> app = Flask(__name__)
        >>> register_routes(app)
    """
    app.register_blueprint(api_bp)
    logger.info(
        "API routes registered: /api/auth/google, /api/auth/callback, "
        "/api/compare, /api/sync"
    )
