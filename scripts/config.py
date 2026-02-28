"""Centralized configuration for the AI Employee.

Loads settings from .env and provides typed access to all config values.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Vault paths
# ---------------------------------------------------------------------------

VAULT_PATH = PROJECT_ROOT / os.getenv("VAULT_PATH", "AI_Employee_Vault")
INBOX_DIR = VAULT_PATH / "Inbox"
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"
DONE_DIR = VAULT_PATH / "Done"
LOGS_DIR = VAULT_PATH / "Logs"
PLANS_DIR = VAULT_PATH / "Plans"
PENDING_APPROVAL_DIR = VAULT_PATH / "Pending_Approval"
APPROVED_DIR = VAULT_PATH / "Approved"
REJECTED_DIR = VAULT_PATH / "Rejected"

# ---------------------------------------------------------------------------
# Watcher settings
# ---------------------------------------------------------------------------

WATCHER_INTERVAL = int(os.getenv("WATCHER_INTERVAL", "1"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ---------------------------------------------------------------------------
# Gmail settings
# ---------------------------------------------------------------------------

GMAIL_CREDENTIALS_FILE = PROJECT_ROOT / os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = PROJECT_ROOT / os.getenv("GMAIL_TOKEN_FILE", "token.json")
GMAIL_POLL_INTERVAL_SEC = int(os.getenv("GMAIL_POLL_INTERVAL_SEC", "300"))
GMAIL_QUERY = os.getenv("GMAIL_QUERY", "is:unread is:important")
GMAIL_SEEN_IDS_FILE = LOGS_DIR / ".gmail_seen_ids.json"

# ---------------------------------------------------------------------------
# LinkedIn settings
# ---------------------------------------------------------------------------

LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_URN = os.getenv("LINKEDIN_PERSON_URN", "")
LINKEDIN_DRY_RUN = os.getenv("LINKEDIN_DRY_RUN", "true").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Scheduler settings
# ---------------------------------------------------------------------------

SCHEDULER_GMAIL_INTERVAL_MIN = int(os.getenv("SCHEDULER_GMAIL_INTERVAL_MIN", "5"))
SCHEDULER_PROCESS_INTERVAL_MIN = int(os.getenv("SCHEDULER_PROCESS_INTERVAL_MIN", "10"))
SCHEDULER_APPROVAL_INTERVAL_MIN = int(os.getenv("SCHEDULER_APPROVAL_INTERVAL_MIN", "5"))
SCHEDULER_BRIEFING_HOUR = int(os.getenv("SCHEDULER_BRIEFING_HOUR", "9"))

# ---------------------------------------------------------------------------
# Sensitive actions (require approval)
# ---------------------------------------------------------------------------

SENSITIVE_ACTION_KEYWORDS = [
    "send_email",
    "post_linkedin",
    "delete",
    "modify_config",
]
