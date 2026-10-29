"""
Gmail Service Module (Objective 1 Intake Option)

Provides read-only intake from Gmail (https://www.googleapis.com/auth/gmail.readonly)
with graceful disconnected/fallback behavior when OAuth or credentials are not yet configured.
"""

import os
from typing import Dict, Any, Optional

# Narrowest scope for read-only email intake
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def get_gmail_status() -> Dict[str, Any]:
    """
    Check whether Gmail API dependencies and credentials are present.
    Returns status dictionary for the frontend and CLI without raising exceptions.
    """
    # 1. Check libraries
    libraries_installed = True
    try:
        import googleapiclient.discovery  # noqa: F401
        import google_auth_oauthlib.flow  # noqa: F401
    except ImportError:
        libraries_installed = False

    # 2. Check credential files
    has_credentials = os.path.exists(CREDENTIALS_FILE)
    has_token = os.path.exists(TOKEN_FILE)

    if not libraries_installed:
        return {
            "connected": False,
            "mode": "Fallback Mode (Manual/Samples)",
            "reason": "Missing 'google-api-python-client' or 'google-auth-oauthlib' library.",
            "instructions": "Install libraries and place OAuth 'credentials.json' in project root to enable Gmail sync.",
            "can_fetch": False
        }

    if not has_credentials and not has_token:
        return {
            "connected": False,
            "mode": "Fallback Mode (Manual/Samples)",
            "reason": "No 'credentials.json' or 'token.json' found in workspace root.",
            "instructions": "Download OAuth Client ID JSON from Google Cloud Console as 'credentials.json'.",
            "can_fetch": False
        }

    if not has_token and has_credentials:
        return {
            "connected": False,
            "mode": "Credentials Detected (Authorization Pending)",
            "reason": "'credentials.json' detected but user has not completed one-time OAuth grant.",
            "instructions": "Run authorization workflow to generate 'token.json'.",
            "can_fetch": False
        }

    return {
        "connected": True,
        "mode": "Live Gmail Connected",
        "reason": "OAuth token and read-only Gmail client are active.",
        "instructions": "Ready to pull live support messages.",
        "can_fetch": True
    }


def fetch_latest_customer_email() -> Optional[Dict[str, str]]:
    """
    Fetch the latest unread or recent message using read-only permissions.
    Returns None if Gmail is not connected or authorization fails.
    """
    status = get_gmail_status()
    if not status["can_fetch"]:
        return None

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)
        service = build("gmail", "v1", credentials=creds)

        # Query messages with read-only access
        results = service.users().messages().list(userId="me", maxResults=1).execute()
        messages = results.get("messages", [])

        if not messages:
            return None

        msg_id = messages[0]["id"]
        msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()

        headers = msg.get("payload", {}).get("headers", [])
        sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Unknown Sender")
        subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")
        snippet = msg.get("snippet", "")

        return {
            "sender": sender,
            "subject": subject,
            "body": snippet,
            "message_id": msg_id
        }

    except Exception as e:
        # Graceful fallback: do not crash application
        return None

