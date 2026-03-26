"""Work-zone router — Cloud/Local domain ownership.

Determines which zone handles which types of tasks. Cloud handles
read-only and draft operations; Local handles approval-gated and
sensitive operations.

Usage:
    from work_zone import WorkZoneRouter
    router = WorkZoneRouter("cloud")
    if router.can_handle("email_triage"):
        ...
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from logger import setup_console_logger

logger = setup_console_logger("work_zone")

# Cloud zone: read-only analysis, drafting, research (no send/post/pay)
CLOUD_DOMAINS = {
    "email_triage",
    "email_draft",
    "social_draft",
    "social_schedule",
    "research",
    "briefing",
}

# Local zone: approval-gated, sensitive, and dashboard operations
LOCAL_DOMAINS = {
    "approval",
    "send_email",
    "post_social",
    "payments",
    "banking",
    "dashboard",
}


class WorkZoneRouter:
    """Routes tasks to the correct zone based on domain ownership."""

    def __init__(self, zone: str = "local") -> None:
        """
        Args:
            zone: Current work zone — "cloud" or "local".
        """
        self.zone = zone.lower()
        if self.zone == "cloud":
            self.owned_domains = CLOUD_DOMAINS
        else:
            self.owned_domains = LOCAL_DOMAINS

    def can_handle(self, action: str) -> bool:
        """Check if the current zone can handle an action.

        Args:
            action: Action/domain name (e.g. "email_triage", "send_email").

        Returns:
            True if this zone owns the action.
        """
        return action in self.owned_domains

    def route_task(self, task: dict) -> str:
        """Determine which zone should handle a task.

        Args:
            task: Task dict with at least a "domain" or "action" key.

        Returns:
            "cloud", "local", or "either" if the action isn't zone-specific.
        """
        action = task.get("domain", task.get("action", ""))

        if action in CLOUD_DOMAINS:
            return "cloud"
        if action in LOCAL_DOMAINS:
            return "local"
        return "either"

    def is_cloud(self) -> bool:
        """Check if running in Cloud zone."""
        return self.zone == "cloud"

    def is_local(self) -> bool:
        """Check if running in Local zone."""
        return self.zone == "local"
