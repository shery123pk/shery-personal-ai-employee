"""Shared Gmail OAuth 2.0 authentication module.

Handles token loading, refreshing, and initial authorization flow.
Used by both gmail_watcher.py and mcp_email_server.py.

Setup:
    1. Go to https://console.cloud.google.com/
    2. Create a project and enable the Gmail API
    3. Create OAuth 2.0 credentials (Desktop application)
    4. Download the JSON and save as credentials.json in project root
    5. Run this module directly to complete the auth flow:
       python scripts/gmail_auth.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_gmail_service():
    """Build and return an authenticated Gmail API service.

    Loads existing token from token.json, refreshes if expired,
    or runs InstalledAppFlow for first-time authorization.

    Returns:
        googleapiclient.discovery.Resource: Gmail API service instance.

    Raises:
        FileNotFoundError: If credentials.json is missing.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None

    # Load existing token
    if GMAIL_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_FILE), SCOPES)

    # Refresh or re-authorize
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not GMAIL_CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Gmail credentials not found at {GMAIL_CREDENTIALS_FILE}. "
                    "Download OAuth credentials from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GMAIL_CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        GMAIL_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


if __name__ == "__main__":
    print("Authenticating with Gmail API...")
    service = get_gmail_service()
    profile = service.users().getProfile(userId="me").execute()
    print(f"Authenticated as: {profile['emailAddress']}")
    print(f"Token saved to: {GMAIL_TOKEN_FILE}")
