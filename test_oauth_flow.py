"""Quick OAuth flow test script.

This script tests the OAuth flow end-to-end without needing Streamlit UI.
Run this to quickly iterate and debug OAuth issues.
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from google_photos_sync.google_photos.auth import GooglePhotosAuth, AccountType

load_dotenv()

# Global variable to store the callback result
callback_result = {}


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth callback."""
    
    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        # Parse query parameters
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # Store code and state
        callback_result['code'] = params.get('code', [None])[0]
        callback_result['state'] = params.get('state', [None])[0]
        callback_result['error'] = params.get('error', [None])[0]
        
        # Send response to browser
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        if callback_result['code']:
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Authorization Successful</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>✅ Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """
        else:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Authorization Failed</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>❌ Authorization Failed</h1>
                <p>Error: {callback_result['error']}</p>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """
        
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


def test_oauth_flow():
    """Test complete OAuth flow."""
    
    # Use the SAME redirect URI as Flask (already configured in Google Console)
    test_redirect_uri = "http://localhost:5000/api/auth/callback"
    
    print("\n" + "=" * 80)
    print("OAUTH FLOW TEST WITH AUTOMATIC CALLBACK")
    print("=" * 80)
    print(f"\n✅ Using redirect URI: {test_redirect_uri}")
    print("(Already configured in Google Console)")
    print("\nPress Enter to continue...")
    input()
    
    # Start local HTTP server on port 5000 to capture callback
    server = HTTPServer(('localhost', 5000), CallbackHandler)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.daemon = True
    server_thread.start()
    print("✅ Local callback server started on http://localhost:5000")
    
    # Initialize auth handler with same redirect URI as production
    auth = GooglePhotosAuth(
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        redirect_uri=test_redirect_uri
    )
    
    print("\n[STEP 1] Generating auth URL for SOURCE account...")
    auth_url, state = auth.generate_auth_url(AccountType.SOURCE)
    print(f"State: {state}")
    
    # Step 2: Open browser automatically
    print("\n[STEP 2] Opening browser for authorization...")
    print(f"Auth URL: {auth_url[:100]}...")
    webbrowser.open(auth_url)
    print("✅ Browser opened. Please authorize the app.")
    print("Waiting for callback...")
    
    # Wait for callback
    server_thread.join(timeout=120)  # Wait up to 2 minutes
    server.server_close()
    
    if not callback_result.get('code'):
        error = callback_result.get('error', 'Unknown error')
        print(f"❌ ERROR: No code received. Error: {error}")
        return
    
    code = callback_result['code']
    returned_state = callback_result['state']
    
    print(f"\n✅ Code received: {code[:20]}...")
    print(f"✅ State returned: {returned_state}")
    
    if returned_state != state:
        print(f"⚠️  WARNING: State mismatch!")
        print(f"   Expected: {state}")
        print(f"   Got: {returned_state}")
    
    # Step 3: Exchange code for credentials
    print("\n[STEP 3] Exchanging code for credentials...")
    try:
        credentials = auth.exchange_code_for_token(code, AccountType.SOURCE)
        print("✅ Credentials obtained successfully!")
        print(f"   Access token: {credentials.token[:20]}...")
        print(f"   Has refresh token: {bool(credentials.refresh_token)}")
        print(f"   Has ID token: {bool(credentials.id_token)}")
    except Exception as e:
        print(f"❌ ERROR exchanging code: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Extract email from ID token
    print("\n[STEP 4] Extracting email from ID token...")
    try:
        if credentials.id_token:
            import base64
            import json
            
            # Decode JWT
            parts = credentials.id_token.split('.')
            if len(parts) >= 2:
                payload = parts[1]
                # Add padding
                padding = 4 - len(payload) % 4
                if padding != 4:
                    payload += '=' * padding
                decoded_bytes = base64.urlsafe_b64decode(payload)
                decoded = json.loads(decoded_bytes)
                
                email = decoded.get('email')
                print(f"✅ Email extracted: {email}")
                print(f"\nFull ID token payload:")
                print(json.dumps(decoded, indent=2))
                
                # Step 5: Save credentials
                print("\n[STEP 5] Saving credentials...")
                auth.save_credentials(credentials, AccountType.SOURCE, email)
                print(f"✅ Credentials saved for {email}")
                
                # Verify saved credentials
                print("\n[STEP 6] Verifying saved credentials...")
                creds_file = Path.home() / ".google_photos_sync" / "credentials" / f"source_{email}.json"
                if creds_file.exists():
                    print(f"✅ Credentials file exists: {creds_file}")
                else:
                    print(f"❌ Credentials file not found: {creds_file}")
                
            else:
                print("❌ ERROR: Invalid ID token format")
        else:
            print("❌ ERROR: No ID token in credentials")
    except Exception as e:
        print(f"❌ ERROR extracting email: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("✅ OAUTH FLOW TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    test_oauth_flow()
