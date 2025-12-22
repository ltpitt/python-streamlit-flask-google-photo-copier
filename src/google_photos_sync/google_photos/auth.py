"""Google Photos OAuth 2.0 authentication module.

This module handles OAuth authentication for Google Photos API with support for:
- OAuth URL generation with correct scopes (readonly for source, appendonly for target)
- Token exchange from authorization code
- Credential storage and retrieval from filesystem
- Automatic token refresh when expired
- Multiple account management (source vs target accounts)

Example:
    >>> auth = GooglePhotosAuth(
    ...     client_id="your_client_id",
    ...     client_secret="your_client_secret",
    ...     redirect_uri="http://localhost:8080/callback"
    ... )
    >>> url, state = auth.generate_auth_url(AccountType.SOURCE)
    >>> # User authorizes and you get auth code
    >>> credentials = auth.exchange_code_for_token(auth_code, AccountType.SOURCE)
    >>> auth.save_credentials(credentials, AccountType.SOURCE, "user@example.com")
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow  # type: ignore[import-untyped]


class AccountType(Enum):
    """Type of Google Photos account."""

    SOURCE = "source"
    TARGET = "target"


class AuthenticationError(Exception):
    """Raised when OAuth authentication fails."""

    pass


class TokenRefreshError(Exception):
    """Raised when token refresh fails."""

    pass


class CredentialStorageError(Exception):
    """Raised when credential storage/retrieval fails."""

    pass


class GooglePhotosAuth:
    """Handles Google Photos OAuth 2.0 authentication.

    This class manages the complete OAuth flow including URL generation,
    token exchange, credential storage, and automatic token refresh.

    Attributes:
        client_id: Google OAuth client ID
        client_secret: Google OAuth client secret
        redirect_uri: OAuth redirect URI
        credentials_dir: Directory to store credentials (default: ~/.google_photos_sync)
    """

    # OAuth scopes for different account types
    SCOPES = {
        AccountType.SOURCE: ["https://www.googleapis.com/auth/photoslibrary.readonly"],
        AccountType.TARGET: [
            "https://www.googleapis.com/auth/photoslibrary.appendonly"
        ],
    }

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        credentials_dir: Optional[Path] = None,
    ) -> None:
        """Initialize Google Photos OAuth handler.

        Args:
            client_id: Google OAuth client ID from Google Cloud Console
            client_secret: Google OAuth client secret from Google Cloud Console
            redirect_uri: OAuth redirect URI (must match console configuration)
            credentials_dir: Directory to store credentials. If None, uses
                ~/.google_photos_sync/credentials

        Raises:
            ValueError: If client_id, client_secret, or redirect_uri is empty
        """
        if not client_id:
            raise ValueError("client_id cannot be empty")
        if not client_secret:
            raise ValueError("client_secret cannot be empty")
        if not redirect_uri:
            raise ValueError("redirect_uri cannot be empty")

        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

        if credentials_dir is None:
            self._credentials_dir = Path.home() / ".google_photos_sync" / "credentials"
        else:
            self._credentials_dir = Path(credentials_dir)

    def _get_client_config(self) -> dict[str, Any]:
        """Get OAuth client configuration.

        Returns:
            Dictionary with OAuth client configuration
        """
        return {
            "web": {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "redirect_uris": [self._redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    def generate_auth_url(self, account_type: AccountType) -> Tuple[str, str]:
        """Generate OAuth authorization URL for the specified account type.

        Args:
            account_type: Type of account (SOURCE for readonly, TARGET for appendonly)

        Returns:
            Tuple of (authorization_url, state) where state should be verified
            in the callback to prevent CSRF attacks

        Raises:
            AuthenticationError: If URL generation fails

        Example:
            >>> url, state = auth.generate_auth_url(AccountType.SOURCE)
            >>> # Redirect user to url, store state for verification
        """
        try:
            scopes = self.SCOPES[account_type]
            flow = Flow.from_client_config(
                client_config=self._get_client_config(),
                scopes=scopes,
                redirect_uri=self._redirect_uri,
            )

            authorization_url, state = flow.authorization_url(
                access_type="offline",  # Get refresh token
                include_granted_scopes="true",
                prompt="consent",  # Force consent to get refresh token
            )

            return authorization_url, state

        except Exception as e:
            raise AuthenticationError(
                f"Failed to generate authorization URL: {e}"
            ) from e

    def exchange_code_for_token(
        self, authorization_code: str, account_type: AccountType
    ) -> Credentials:
        """Exchange authorization code for OAuth credentials.

        Args:
            authorization_code: Authorization code received from OAuth callback
            account_type: Type of account (SOURCE or TARGET)

        Returns:
            Google OAuth credentials with access token and refresh token

        Raises:
            AuthenticationError: If token exchange fails (invalid code,
                network error, etc.)

        Example:
            >>> credentials = auth.exchange_code_for_token(
            ...     code, AccountType.SOURCE
            ... )
            >>> auth.save_credentials(
            ...     credentials, AccountType.SOURCE, "user@example.com"
            ... )
        """
        try:
            scopes = self.SCOPES[account_type]
            flow = Flow.from_client_config(
                client_config=self._get_client_config(),
                scopes=scopes,
                redirect_uri=self._redirect_uri,
            )

            flow.fetch_token(code=authorization_code)
            return flow.credentials  # type: ignore[no-any-return]

        except Exception as e:
            raise AuthenticationError(
                f"Failed to exchange authorization code for token: {e}"
            ) from e

    def save_credentials(
        self,
        credentials: Credentials,
        account_type: AccountType,
        account_email: str,
    ) -> None:
        """Save credentials to filesystem.

        Credentials are stored as JSON files in the credentials directory.
        Filename format: {account_type}_{account_email}.json

        Args:
            credentials: OAuth credentials to save
            account_type: Type of account (SOURCE or TARGET)
            account_email: Email address of the account

        Raises:
            CredentialStorageError: If saving credentials fails

        Example:
            >>> auth.save_credentials(creds, AccountType.SOURCE, "user@example.com")
        """
        try:
            # Create credentials directory if it doesn't exist
            self._credentials_dir.mkdir(parents=True, exist_ok=True)

            # Build filename
            filename = f"{account_type.value}_{account_email}.json"
            filepath = self._credentials_dir / filename

            # Convert credentials to dictionary
            credentials_data = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
            }

            # Add expiry if it exists
            if credentials.expiry:
                # Convert to ISO format
                # Google credentials use UTC but may be timezone-naive or timezone-aware
                if credentials.expiry.tzinfo is not None:
                    # If timezone-aware, convert to UTC and make naive for consistency
                    expiry_utc = credentials.expiry.astimezone(
                        __import__("datetime").timezone.utc
                    ).replace(tzinfo=None)
                    credentials_data["expiry"] = expiry_utc.isoformat() + "Z"
                else:
                    # Already naive, just add 'Z' to indicate UTC
                    credentials_data["expiry"] = credentials.expiry.isoformat() + "Z"

            # Write to file
            with open(filepath, "w") as f:
                json.dump(credentials_data, f, indent=2)

        except Exception as e:
            raise CredentialStorageError(f"Failed to save credentials: {e}") from e

    def load_credentials(
        self, account_type: AccountType, account_email: str
    ) -> Optional[Credentials]:
        """Load credentials from filesystem.

        Args:
            account_type: Type of account (SOURCE or TARGET)
            account_email: Email address of the account

        Returns:
            OAuth credentials if file exists, None otherwise

        Raises:
            CredentialStorageError: If loading credentials fails (e.g., corrupted file)

        Example:
            >>> creds = auth.load_credentials(AccountType.SOURCE, "user@example.com")
            >>> if creds:
            ...     # Use credentials
            ... else:
            ...     # Need to authenticate
        """
        try:
            filename = f"{account_type.value}_{account_email}.json"
            filepath = self._credentials_dir / filename

            if not filepath.exists():
                return None

            with open(filepath, "r") as f:
                credentials_data = json.load(f)

            # Convert expiry string back to datetime if it exists
            expiry = None
            if "expiry" in credentials_data:
                expiry_str = credentials_data["expiry"]
                # Handle 'Z' suffix (UTC indicator) by removing it
                if expiry_str.endswith("Z"):
                    expiry_str = expiry_str[:-1]
                # Parse as naive datetime (Google credentials expect naive UTC)
                expiry = datetime.fromisoformat(expiry_str)

            # Create Credentials object
            credentials: Credentials = Credentials(  # type: ignore[no-untyped-call]
                token=credentials_data.get("token"),
                refresh_token=credentials_data.get("refresh_token"),
                token_uri=credentials_data.get("token_uri"),
                client_id=credentials_data.get("client_id"),
                client_secret=credentials_data.get("client_secret"),
                scopes=credentials_data.get("scopes"),
                expiry=expiry,
            )

            return credentials

        except FileNotFoundError:
            return None
        except Exception as e:
            raise CredentialStorageError(f"Failed to load credentials: {e}") from e

    def get_valid_credentials(
        self, account_type: AccountType, account_email: str
    ) -> Optional[Credentials]:
        """Get valid credentials, refreshing if expired.

        This method loads credentials from storage and automatically refreshes
        them if they are expired. The refreshed credentials are saved back to storage.

        Args:
            account_type: Type of account (SOURCE or TARGET)
            account_email: Email address of the account

        Returns:
            Valid OAuth credentials, or None if no credentials exist

        Raises:
            TokenRefreshError: If token refresh fails
            CredentialStorageError: If loading/saving credentials fails

        Example:
            >>> creds = auth.get_valid_credentials(
            ...     AccountType.SOURCE, "user@example.com"
            ... )
            >>> if creds:
            ...     # Use valid credentials
            ... else:
            ...     # Need to authenticate
        """
        try:
            credentials = self.load_credentials(account_type, account_email)

            if credentials is None:
                return None

            # Check if credentials are expired or expiring soon
            if credentials.expired:
                # Refresh the token
                try:
                    request: Request = Request()  # type: ignore[no-untyped-call]
                    credentials.refresh(request)
                    # Save refreshed credentials
                    self.save_credentials(credentials, account_type, account_email)
                except Exception as e:
                    raise TokenRefreshError(
                        f"Failed to refresh token for {account_email}: {e}"
                    ) from e

            return credentials

        except TokenRefreshError:
            raise
        except Exception as e:
            raise CredentialStorageError(f"Failed to get valid credentials: {e}") from e
