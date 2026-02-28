"""Gmail watcher — polls Gmail API for unread important emails.

Creates action files in Needs_Action/ for each new email detected.
Extends BaseWatcher from file_watcher.py.

Usage:
    python scripts/gmail_watcher.py
"""

import json
import re
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    GMAIL_POLL_INTERVAL_SEC,
    GMAIL_QUERY,
    GMAIL_SEEN_IDS_FILE,
    NEEDS_ACTION_DIR,
)
from file_watcher import BaseWatcher
from logger import iso_now, log_to_vault, setup_console_logger

logger = setup_console_logger("gmail_watcher")


# ---------------------------------------------------------------------------
# Priority detection from Gmail labels
# ---------------------------------------------------------------------------

def detect_email_priority(label_ids: list[str]) -> str:
    """Map Gmail labels to priority levels."""
    if "STARRED" in label_ids:
        return "URGENT"
    if "IMPORTANT" in label_ids:
        return "REVIEW"
    return "FYI"


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to a filesystem-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "_", slug).strip("_")
    return slug[:max_length]


# ---------------------------------------------------------------------------
# Seen IDs persistence
# ---------------------------------------------------------------------------

def load_seen_ids() -> set[str]:
    """Load previously seen Gmail message IDs."""
    if GMAIL_SEEN_IDS_FILE.exists():
        try:
            data = json.loads(GMAIL_SEEN_IDS_FILE.read_text(encoding="utf-8"))
            return set(data)
        except (json.JSONDecodeError, OSError):
            return set()
    return set()


def save_seen_ids(seen: set[str]) -> None:
    """Persist seen Gmail message IDs."""
    GMAIL_SEEN_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    GMAIL_SEEN_IDS_FILE.write_text(
        json.dumps(sorted(seen), indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Gmail Watcher
# ---------------------------------------------------------------------------

class GmailWatcher(BaseWatcher):
    """Polls Gmail for unread important emails and creates action files."""

    def __init__(self) -> None:
        self._running = False
        self._seen_ids = load_seen_ids()
        self._service = None

    def start(self) -> None:
        """Start polling Gmail."""
        from gmail_auth import get_gmail_service

        NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)

        self._service = get_gmail_service()
        self._running = True

        log_to_vault("gmail_watcher_started", "gmail_watcher", "success")
        logger.info(
            "Gmail watcher started — polling every %ds with query: %s",
            GMAIL_POLL_INTERVAL_SEC,
            GMAIL_QUERY,
        )

        while self._running:
            try:
                self._poll()
            except Exception as exc:
                logger.error("Gmail poll error: %s", exc)
                log_to_vault("gmail_poll_error", "gmail_watcher", "error", detail=str(exc))
            time.sleep(GMAIL_POLL_INTERVAL_SEC)

    def stop(self) -> None:
        """Stop polling."""
        if self._running:
            self._running = False
            save_seen_ids(self._seen_ids)
            log_to_vault("gmail_watcher_stopped", "gmail_watcher", "success")
            logger.info("Gmail watcher stopped.")

    def on_new_file(self, file_path: Path) -> None:
        """Not used for Gmail — emails are handled via _poll()."""

    # -- internal ------------------------------------------------------------

    def _poll(self) -> None:
        """Fetch unread emails and process new ones."""
        results = (
            self._service.users()
            .messages()
            .list(userId="me", q=GMAIL_QUERY, maxResults=10)
            .execute()
        )
        messages = results.get("messages", [])

        for msg_stub in messages:
            msg_id = msg_stub["id"]
            if msg_id in self._seen_ids:
                continue

            # Fetch full message
            msg = (
                self._service.users()
                .messages()
                .get(userId="me", id=msg_id, format="metadata",
                     metadataHeaders=["Subject", "From", "Date"])
                .execute()
            )

            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject", "(no subject)")
            sender = headers.get("From", "unknown")
            date = headers.get("Date", "")
            label_ids = msg.get("labelIds", [])
            snippet = msg.get("snippet", "")

            priority = detect_email_priority(label_ids)
            self._create_action(msg_id, subject, sender, date, snippet, priority)

            self._seen_ids.add(msg_id)

        save_seen_ids(self._seen_ids)

    def _create_action(
        self,
        msg_id: str,
        subject: str,
        sender: str,
        date: str,
        snippet: str,
        priority: str,
    ) -> None:
        """Create an action file in Needs_Action/ for a new email."""
        slug = slugify(subject)
        action_filename = f"EMAIL_{slug}.md"
        action_path = NEEDS_ACTION_DIR / action_filename

        # Avoid overwriting
        counter = 1
        while action_path.exists():
            action_filename = f"EMAIL_{slug}_{counter}.md"
            action_path = NEEDS_ACTION_DIR / action_filename
            counter += 1

        timestamp = iso_now()
        content = (
            f"# Action Item: Email — {subject}\n"
            f"\n"
            f"- **type:** email\n"
            f"- **gmail_id:** {msg_id}\n"
            f"- **from:** {sender}\n"
            f"- **subject:** {subject}\n"
            f"- **date:** {date}\n"
            f"- **detected_at:** {timestamp}\n"
            f"- **priority:** {priority}\n"
            f"- **status:** pending\n"
            f"\n"
            f"---\n"
            f"\n"
            f"**Preview:** {snippet}\n"
        )

        action_path.write_text(content, encoding="utf-8")

        log_to_vault(
            action="email_detected",
            source=subject,
            result="action_created",
            priority=priority,
            gmail_id=msg_id,
            action_file=action_filename,
        )
        logger.info(
            "New email: %s from %s (priority: %s) → %s",
            subject, sender, priority, action_filename,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    watcher = GmailWatcher()

    def _signal_handler(sig: int, frame: object) -> None:
        logger.info("Shutdown signal received.")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    watcher.start()


if __name__ == "__main__":
    main()
