"""One-time Google OAuth setup — run this to authorize Calendar access.

Usage:
    python scripts/google_auth.py

Opens a browser window for you to log in with your Google account.
Saves a refresh token to credentials/google_token.json.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
import json

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://mail.google.com/",
]
ROOT = Path(__file__).resolve().parent.parent
CLIENT_SECRET = ROOT / "credentials" / "google_client_secret.json"
TOKEN_PATH = ROOT / "credentials" / "google_token.json"


def main():
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=8090)

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
    print(f"Saved token to {TOKEN_PATH}")
    print("Google Calendar access is now authorized.")


if __name__ == "__main__":
    main()
