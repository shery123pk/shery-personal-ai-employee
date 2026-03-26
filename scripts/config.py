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
    "post_twitter",
    "delete",
    "modify_config",
]

# ---------------------------------------------------------------------------
# OpenAI settings (Gold tier)
# ---------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))

# ---------------------------------------------------------------------------
# Gold tier vault paths
# ---------------------------------------------------------------------------

BRIEFINGS_DIR = VAULT_PATH / "Briefings"
KNOWLEDGE_BASE_DIR = VAULT_PATH / "Knowledge_Base"
FINANCE_CSV_DIR = VAULT_PATH / "Finance"

# ---------------------------------------------------------------------------
# Autonomous loop settings (Gold tier)
# ---------------------------------------------------------------------------

AUTONOMOUS_MAX_ITERATIONS = int(os.getenv("AUTONOMOUS_MAX_ITERATIONS", "10"))
AUTONOMOUS_RETRY_LIMIT = int(os.getenv("AUTONOMOUS_RETRY_LIMIT", "3"))

# ---------------------------------------------------------------------------
# Process watchdog (Gold tier)
# ---------------------------------------------------------------------------

WATCHDOG_HEALTH_INTERVAL_SEC = int(os.getenv("WATCHDOG_HEALTH_INTERVAL_SEC", "60"))

# ---------------------------------------------------------------------------
# Finance watcher (Gold tier)
# ---------------------------------------------------------------------------

FINANCE_POLL_INTERVAL_SEC = int(os.getenv("FINANCE_POLL_INTERVAL_SEC", "300"))

# ---------------------------------------------------------------------------
# Scheduler Gold additions
# ---------------------------------------------------------------------------

SCHEDULER_HEALTH_CHECK_MIN = int(os.getenv("SCHEDULER_HEALTH_CHECK_MIN", "2"))
SCHEDULER_AUTONOMOUS_INTERVAL_MIN = int(os.getenv("SCHEDULER_AUTONOMOUS_INTERVAL_MIN", "15"))
SCHEDULER_WEEKLY_BRIEFING_DAY = os.getenv("SCHEDULER_WEEKLY_BRIEFING_DAY", "mon")

# ---------------------------------------------------------------------------
# DEV_MODE — synthetic responses for services without live APIs
# ---------------------------------------------------------------------------

DEV_MODE = os.getenv("DEV_MODE", "true").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Platinum tier vault paths
# ---------------------------------------------------------------------------

IN_PROGRESS_DIR = VAULT_PATH / "In_Progress"
UPDATES_DIR = VAULT_PATH / "Updates"

DOMAINS = ["email", "social", "finance", "general"]

# ---------------------------------------------------------------------------
# Work-zone settings (Platinum tier)
# ---------------------------------------------------------------------------

WORK_ZONE = os.getenv("WORK_ZONE", "local")  # "cloud" or "local"

# ---------------------------------------------------------------------------
# Vault sync settings (Platinum tier)
# ---------------------------------------------------------------------------

VAULT_SYNC_BRANCH = os.getenv("VAULT_SYNC_BRANCH", "main")
VAULT_SYNC_INTERVAL_SEC = int(os.getenv("VAULT_SYNC_INTERVAL_SEC", "300"))

# ---------------------------------------------------------------------------
# Odoo ERP settings (Platinum tier)
# ---------------------------------------------------------------------------

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")
ODOO_DEV_MODE = os.getenv("ODOO_DEV_MODE", "true").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Cloud health (Platinum tier)
# ---------------------------------------------------------------------------

CLOUD_HEALTH_PORT = int(os.getenv("CLOUD_HEALTH_PORT", "8080"))

# ---------------------------------------------------------------------------
# Scheduler Platinum additions
# ---------------------------------------------------------------------------

SCHEDULER_VAULT_SYNC_INTERVAL_MIN = int(os.getenv("SCHEDULER_VAULT_SYNC_INTERVAL_MIN", "5"))
SCHEDULER_DASHBOARD_MERGE_INTERVAL_MIN = int(os.getenv("SCHEDULER_DASHBOARD_MERGE_INTERVAL_MIN", "10"))
