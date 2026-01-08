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
from google_photos_sync.utils.validators import (
    ValidationError,
    validate_account_type,
    validate_boolean,
    validate_email,
    validate_json_payload,
)

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

        # Validate JSON payload
        try:
            validated_data = validate_json_payload(data, ["account_type"])
        except ValidationError as e:
            return _error_response(str(e), "VALIDATION_ERROR", 400)

        # Validate and sanitize account_type
        try:
            account_type_str = validate_account_type(validated_data["account_type"])
        except ValidationError as e:
            return _error_response(str(e), "INVALID_ACCOUNT_TYPE", 400)

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
        return _error_response("Internal server error", "INTERNAL_SERVER_ERROR", 500)


@api_bp.route("/auth/status", methods=["GET"])
def check_auth_status() -> tuple[dict[str, Any], int]:
    """Check if account is already authenticated.

    Query parameters:
        account_type: Type of account ('source' or 'target')

    Returns:
        JSON response with authentication status and email if authenticated
    """
    try:
        account_type_str = request.args.get("account_type")

        # Validate account_type
        try:
            if not account_type_str:
                raise ValidationError("account_type parameter is required")
            account_type_str = validate_account_type(account_type_str)
        except ValidationError as e:
            return _error_response(str(e), "INVALID_ACCOUNT_TYPE", 400)

        account_type = AccountType(account_type_str)

        # Check if credentials exist for any email
        from pathlib import Path

        creds_dir = Path.home() / ".google_photos_sync" / "credentials"

        if not creds_dir.exists():
            return _success_response(
                {"authenticated": False}, "Not authenticated"
            )

        # Find credentials file for this account type
        pattern = f"{account_type.value}_*.json"
        creds_files = list(creds_dir.glob(pattern))

        if not creds_files:
            return _success_response(
                {"authenticated": False}, "Not authenticated"
            )

        # Get the most recent credentials file
        latest_creds = max(creds_files, key=lambda p: p.stat().st_mtime)

        # Extract email from filename (format: accounttype_email@domain.com.json)
        filename = latest_creds.stem  # Remove .json
        email = filename.split("_", 1)[1] if "_" in filename else "unknown"

        return _success_response(
            {
                "authenticated": True,
                "email": email,
                "account_type": account_type.value,
            },
            "Authenticated",
        )

    except Exception as e:
        logger.exception(f"Error checking auth status: {e}")
        return _error_response(
            "Internal server error", "INTERNAL_SERVER_ERROR", 500
        )


@api_bp.route("/auth/callback", methods=["GET", "POST"])
def oauth_callback() -> tuple[dict[str, Any], int] | str:  # noqa: C901
    """Handle OAuth callback and exchange code for credentials.

    Query Parameters:
        code: Authorization code from OAuth provider
        state: State token for CSRF protection
        account_type: Type of account ('source' or 'target')
        account_email: Email address of the authenticated account

    Returns:
        JSON response confirming successful authentication or HTML form for email input

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
    # Handle POST (form submission with email)
    if request.method == "POST":
        code = request.form.get("code")
        state = request.form.get("state")
        account_email = request.form.get("account_email")
        account_type_str = request.form.get("account_type")
    else:
        # Handle GET (redirect from Google)
        code = request.args.get("code")
        state = request.args.get("state")
        account_email = request.args.get("account_email")
        account_type_str = request.args.get("account_type")
    try:
        # Get query parameters
        code = request.args.get("code")
        state = request.args.get("state")
        # Optional: may come from query or form
        account_email = request.args.get("account_email")

        # Validate required parameters
        if not code:
            return _error_response("code parameter is required", "MISSING_CODE", 400)

        # Decode account_type from state (format: accounttype_randomtoken)
        account_type_str = None
        if state and "_" in state:
            account_type_str = state.split("_")[0]

        # Fallback: check query parameter (backward compatibility)
        if not account_type_str:
            account_type_str = request.args.get("account_type")

        # Validate and sanitize account_type
        try:
            if not account_type_str:
                raise ValidationError(
                    "account_type not found in state or query parameters"
                )
            account_type_str = validate_account_type(account_type_str)
        except ValidationError as e:
            return _error_response(str(e), "INVALID_ACCOUNT_TYPE", 400)

        # Convert to AccountType enum
        account_type = AccountType(account_type_str)

        # Exchange code for credentials FIRST
        auth_handler = _get_auth_handler()
        credentials = auth_handler.exchange_code_for_token(code, account_type)

        # Now extract email from credentials if not provided
        if not account_email:
            try:
                # Extract email from ID token
                if hasattr(credentials, 'id_token') and credentials.id_token:
                    # Decode JWT without verification (we trust Google's response)
                    import base64
                    import json
                    # ID token format: header.payload.signature
                    parts = credentials.id_token.split('.')
                    if len(parts) >= 2:
                        # Decode payload (add padding if needed)
                        payload = parts[1]
                        # Add padding for base64 decoding
                        padding = 4 - len(payload) % 4
                        if padding != 4:
                            payload += '=' * padding
                        decoded_bytes = base64.urlsafe_b64decode(payload)
                        decoded = json.loads(decoded_bytes)
                        account_email = decoded.get('email')
                        logger.info(f"Extracted email from ID token: {account_email}")

                if not account_email:
                    return _error_response(
                        (
                            "Could not extract email from Google account. "
                            "ID token missing or invalid."
                        ),
                        "EMAIL_EXTRACTION_FAILED",
                        400,
                    )
            except Exception as e:
                logger.exception(f"Failed to extract email: {e}")
                return _error_response(
                    f"Failed to extract email: {str(e)}",
                    "EMAIL_EXTRACTION_ERROR",
                    500
                )

        # Validate and sanitize email
        try:
            account_email = validate_email(account_email)
        except ValidationError as e:
            return _error_response(str(e), "INVALID_EMAIL", 400)

        # Save credentials
        auth_handler.save_credentials(credentials, account_type, account_email)

        logger.info(
            f"OAuth callback successful for {account_type_str} account: {account_email}"
        )

        # Check if request prefers JSON (API client) or HTML (browser)
        # Browser redirects from Google will have 'text/html' in Accept header
        accept_header = request.headers.get("Accept", "")
        if "application/json" in accept_header or request.is_json:
            # Return JSON response for API clients (tests, programmatic access)
            return _success_response(
                {
                    "account_type": account_type_str,
                    "account_email": account_email,
                },
                f"Authentication successful for {account_email}",
            )

        # Return success HTML page for browser redirects
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful - Google Photos Sync</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 500px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                    text-align: center;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #1a73e8;
                    margin-bottom: 20px;
                }}
                .success-icon {{
                    font-size: 64px;
                    margin: 20px 0;
                }}
                .account-info {{
                    background: #e8f0fe;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .next-steps {{
                    color: #5f6368;
                    margin-top: 30px;
                    font-size: 14px;
                }}
                a {{
                    color: #1a73e8;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h1>Authentication Successful!</h1>

                <div class="account-info">
                    <strong>Account Type:</strong> {account_type_str.upper()}<br>
                    <strong>Email:</strong> {account_email}
                </div>

                <p>Your Google Photos account has been successfully
                authenticated.</p>

                <div class="next-steps">
                    You can now close this window and return to the
                    Streamlit app to continue.
                </div>
            </div>
        </body>
        </html>
        """

    except AuthenticationError as e:
        logger.error(f"OAuth callback authentication failed: {e}")
        return _error_response(str(e), "AUTHENTICATION_FAILED", 401)
    except Exception as e:
        logger.exception(f"Unexpected error in OAuth callback: {e}")
        return _error_response("Internal server error", "INTERNAL_SERVER_ERROR", 500)


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

        # Validate JSON payload
        try:
            validated_data = validate_json_payload(
                data, ["source_account", "target_account"]
            )
        except ValidationError as e:
            return _error_response(str(e), "VALIDATION_ERROR", 400)

        # Validate and sanitize emails
        try:
            source_account = validate_email(validated_data["source_account"])
            target_account = validate_email(validated_data["target_account"])
        except ValidationError as e:
            return _error_response(str(e), "INVALID_EMAIL", 400)

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

        # Validate JSON payload
        try:
            validated_data = validate_json_payload(
                data, ["source_account", "target_account"]
            )
        except ValidationError as e:
            return _error_response(str(e), "VALIDATION_ERROR", 400)

        # Validate and sanitize emails
        try:
            source_account = validate_email(validated_data["source_account"])
            target_account = validate_email(validated_data["target_account"])
        except ValidationError as e:
            return _error_response(str(e), "INVALID_EMAIL", 400)

        # Validate dry_run parameter
        try:
            dry_run = validate_boolean(
                validated_data.get("dry_run"), "dry_run", default=False
            )
        except ValidationError as e:
            return _error_response(str(e), "INVALID_DRY_RUN", 400)

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
