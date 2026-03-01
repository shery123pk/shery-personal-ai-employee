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

# ---------------------------------------------------------------------------
# Auto-reply contacts (husband/family with warm human tone)
# ---------------------------------------------------------------------------

AUTO_REPLY_CONTACTS = {
    "asif.alimusharaf@gmail.com": {
        "name": "Asif",
        "relationship": "husband",
        "sender_name": "Sharmeen",
    },
}

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

            # Auto-reply for special contacts (e.g. husband Asif)
            sender_email = re.search(r"<(.+?)>", sender)
            sender_addr = sender_email.group(1).lower() if sender_email else sender.lower()
            if sender_addr in AUTO_REPLY_CONTACTS:
                self._auto_reply(msg_id, subject, snippet, sender_addr)

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


    def _auto_reply(
        self, msg_id: str, subject: str, snippet: str, sender_addr: str
    ) -> None:
        """Draft a warm auto-reply for special contacts via approval workflow."""
        import base64
        from email.mime.text import MIMEText

        contact = AUTO_REPLY_CONTACTS[sender_addr]
        name = contact["name"]
        sender_name = contact["sender_name"]

        # Generate a warm, human-tone reply based on the email content
        reply_body = _generate_warm_reply(name, sender_name, subject, snippet)

        reply_subject = subject if subject.startswith("Re:") else f"Re: {subject}"

        # Create approval request for the reply
        from approval_utils import create_approval_request

        approval_path = create_approval_request(
            action_type="send_email",
            summary=f"Auto-reply to {name}: {reply_subject}",
            details={
                "to": sender_addr,
                "subject": reply_subject,
                "body": reply_body,
                "auto_reply": "true",
                "contact_name": name,
                "relationship": contact["relationship"],
                "original_snippet": snippet[:200],
            },
        )

        log_to_vault(
            action="auto_reply_drafted",
            source=sender_addr,
            result="approval_requested",
            contact=name,
            subject=reply_subject,
            approval_file=approval_path.name,
        )
        logger.info(
            "Auto-reply drafted for %s (%s) → %s (awaiting approval)",
            name, sender_addr, approval_path.name,
        )


def _generate_warm_reply(name: str, sender_name: str, subject: str, snippet: str) -> str:
    """Generate a warm, context-aware reply for family/close contacts.

    Reads the actual email content and generates a relevant response
    in a natural human tone.
    """
    snippet_lower = snippet.lower()
    subject_lower = subject.lower()

    # --- Hackathon / work / project questions ---
    if any(w in snippet_lower for w in ["hackathon", "tier", "completed", "project", "progress"]):
        body = (
            f"Hey {name}!\n\n"
            f"Haan ji! Alhamdulillah the hackathon is going really well. "
            f"I've completed the Silver tier — that includes Gmail integration, "
            f"LinkedIn posting, approval workflow, planning skill, MCP email server, "
            f"and a scheduler with 4 periodic jobs. All 14 e2e tests are passing!\n\n"
            f"Still have Gold tier left to do but Silver is fully done and working. "
            f"Even the Gmail auto-reply is live now as you can see haha!\n\n"
            f"Will share more details soon inshaAllah.\n"
            f"Love,\n{sender_name}"
        )

    # --- Greeting / how are you ---
    elif any(w in snippet_lower for w in ["how are you", "kaise ho", "kya hal", "hi ", "hello", "salam"]):
        body = (
            f"Hey {name}!\n\n"
            f"I'm doing great alhamdulillah, just been busy with work and some projects. "
            f"How about you? Everything okay on your end?\n\n"
            f"Talk soon inshaAllah!\n"
            f"Love,\n{sender_name}"
        )

    # --- Missing / emotional ---
    elif any(w in snippet_lower for w in ["miss you", "yaad", "love you", "thinking of"]):
        body = (
            f"Aww {name}!\n\n"
            f"Miss you too! Can't wait to catch up properly. "
            f"Let's plan something soon inshaAllah.\n\n"
            f"Love you!\n{sender_name}"
        )

    # --- Meeting / schedule ---
    elif any(w in snippet_lower for w in ["meeting", "plan", "schedule", "time", "available"]):
        body = (
            f"Hi {name}!\n\n"
            f"Got your message about this. Let me check my schedule and "
            f"I'll get back to you with a good time. InshaAllah we'll sort it out soon!\n\n"
            f"Take care,\n{sender_name}"
        )

    # --- Urgent / help ---
    elif any(w in snippet_lower for w in ["urgent", "important", "asap", "help", "emergency"]):
        body = (
            f"Hey {name}!\n\n"
            f"Just saw your message — don't worry, I'm on it! "
            f"Let me look into this and I'll get back to you as soon as possible.\n\n"
            f"Take care,\n{sender_name}"
        )

    # --- Food / dinner / lunch ---
    elif any(w in snippet_lower for w in ["dinner", "lunch", "food", "eat", "cook", "khana"]):
        body = (
            f"Hey {name}!\n\n"
            f"Haha noted! Let me see what we can do about food. "
            f"I'll figure something out inshaAllah!\n\n"
            f"Love,\n{sender_name}"
        )

    # --- Shared content / forwarded ---
    elif any(w in snippet_lower for w in ["check this", "look at", "forwarded", "fwd:", "sharing"]):
        body = (
            f"Hey {name}!\n\n"
            f"Thanks for sharing! I'll have a look at it when I get a chance "
            f"and let you know what I think inshaAllah.\n\n"
            f"Love,\n{sender_name}"
        )

    # --- Fallback: reference subject + snippet for context ---
    else:
        # Extract key topic from snippet for a more relevant reply
        topic = snippet[:80].strip().rstrip(".")
        body = (
            f"Hey {name}!\n\n"
            f"Got your message — \"{topic}\"\n\n"
            f"Let me go through it and I'll reply properly soon inshaAllah. "
            f"Hope you're having a good day!\n\n"
            f"Love,\n{sender_name}"
        )

    return body


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
