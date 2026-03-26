"""Approval watcher — monitors Approved/ and Rejected/ folders.

When a file appears in Approved/, the watcher reads its metadata,
dispatches the action, moves it to Done/, and logs the result.
When a file appears in Rejected/, it logs the rejection and archives.

Extends BaseWatcher from file_watcher.py.

Usage:
    python scripts/approval_watcher.py
"""

import json
import re
import signal
import sys
import time
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import APPROVED_DIR, DOMAINS, DONE_DIR, PENDING_APPROVAL_DIR, REJECTED_DIR
from file_watcher import BaseWatcher
from logger import iso_now, log_to_vault, setup_console_logger

logger = setup_console_logger("approval_watcher")


# ---------------------------------------------------------------------------
# Metadata parsing
# ---------------------------------------------------------------------------

def parse_approval_metadata(content: str) -> dict:
    """Extract key metadata from an approval file."""
    metadata = {}
    for line in content.splitlines():
        match = re.match(r"- \*\*(\w+):\*\* (.+)", line)
        if match:
            metadata[match.group(1)] = match.group(2).strip()

    # Extract JSON action data if present
    json_match = re.search(r"```json\n(.+?)\n```", content, re.DOTALL)
    if json_match:
        try:
            metadata["action_data"] = json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    return metadata


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

class ApprovedHandler(FileSystemEventHandler):
    """Handles files moved into Approved/."""

    def __init__(self, watcher: "ApprovalWatcher") -> None:
        super().__init__()
        self.watcher = watcher

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if file_path.name.startswith("."):
            return
        self.watcher._handle_approved(file_path)


class RejectedHandler(FileSystemEventHandler):
    """Handles files moved into Rejected/."""

    def __init__(self, watcher: "ApprovalWatcher") -> None:
        super().__init__()
        self.watcher = watcher

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if file_path.name.startswith("."):
            return
        self.watcher._handle_rejected(file_path)


# ---------------------------------------------------------------------------
# Approval Watcher
# ---------------------------------------------------------------------------

class ApprovalWatcher(BaseWatcher):
    """Monitors Approved/ and Rejected/ folders for approval decisions."""

    def __init__(self) -> None:
        self._observer = Observer()
        self._running = False

    def start(self) -> None:
        """Start watching Approved/ and Rejected/ folders."""
        APPROVED_DIR.mkdir(parents=True, exist_ok=True)
        REJECTED_DIR.mkdir(parents=True, exist_ok=True)
        DONE_DIR.mkdir(parents=True, exist_ok=True)

        # Scan for files already present
        self._scan_existing()

        self._observer.schedule(ApprovedHandler(self), str(APPROVED_DIR), recursive=False)
        self._observer.schedule(RejectedHandler(self), str(REJECTED_DIR), recursive=False)
        self._observer.start()
        self._running = True

        log_to_vault("approval_watcher_started", "approval_watcher", "success")
        logger.info("Approval watcher started — monitoring Approved/ and Rejected/")

    def stop(self) -> None:
        """Stop watching."""
        if self._running:
            self._observer.stop()
            self._observer.join()
            self._running = False
            log_to_vault("approval_watcher_stopped", "approval_watcher", "success")
            logger.info("Approval watcher stopped.")

    def on_new_file(self, file_path: Path) -> None:
        """Not used directly — routing is done via handlers."""

    # -- approval handling ---------------------------------------------------

    def _scan_existing(self) -> None:
        """Process files already in Approved/, Rejected/, and Pending_Approval subdirs."""
        for item in APPROVED_DIR.iterdir():
            if item.is_file() and not item.name.startswith("."):
                self._handle_approved(item)
        for item in REJECTED_DIR.iterdir():
            if item.is_file() and not item.name.startswith("."):
                self._handle_rejected(item)

        # Scan domain subdirectories in Pending_Approval/
        for domain in DOMAINS:
            domain_dir = PENDING_APPROVAL_DIR / domain
            if not domain_dir.exists():
                continue
            for item in domain_dir.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    log_to_vault(
                        action="pending_approval_found",
                        source=item.name,
                        result="pending",
                        domain=domain,
                    )

    def _handle_approved(self, file_path: Path) -> None:
        """Process an approved action file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            metadata = parse_approval_metadata(content)
            action_type = metadata.get("action_type", "unknown")

            logger.info("Approved action: %s (%s)", action_type, file_path.name)

            # Execute the approved action
            result = self._execute_approved_action(action_type, metadata)

            # Update content and move to Done
            updated = content.replace(
                "**status:** pending_approval",
                f"**status:** approved_and_executed",
            )
            updated += f"\n- **approved_at:** {iso_now()}\n"
            updated += f"\n- **execution_result:** {result}\n"

            done_path = DONE_DIR / file_path.name
            done_path.write_text(updated, encoding="utf-8")
            file_path.unlink()

            log_to_vault(
                action="approval_executed",
                source=file_path.name,
                result="success",
                action_type=action_type,
                execution_result=result,
            )

        except Exception as exc:
            logger.error("Error processing approved file %s: %s", file_path.name, exc)
            log_to_vault(
                action="approval_execution_error",
                source=file_path.name,
                result="error",
                detail=str(exc),
            )

    def _handle_rejected(self, file_path: Path) -> None:
        """Process a rejected action file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            metadata = parse_approval_metadata(content)
            action_type = metadata.get("action_type", "unknown")

            logger.info("Rejected action: %s (%s)", action_type, file_path.name)

            # Update content and move to Done
            updated = content.replace(
                "**status:** pending_approval",
                "**status:** rejected",
            )
            updated += f"\n- **rejected_at:** {iso_now()}\n"

            done_path = DONE_DIR / file_path.name
            done_path.write_text(updated, encoding="utf-8")
            file_path.unlink()

            log_to_vault(
                action="approval_rejected",
                source=file_path.name,
                result="rejected",
                action_type=action_type,
            )

        except Exception as exc:
            logger.error("Error processing rejected file %s: %s", file_path.name, exc)
            log_to_vault(
                action="approval_rejection_error",
                source=file_path.name,
                result="error",
                detail=str(exc),
            )

    def _execute_approved_action(self, action_type: str, metadata: dict) -> str:
        """Dispatch an approved action to the appropriate handler.

        Returns a result string describing what happened.
        """
        action_data = metadata.get("action_data", {})

        if action_type == "send_email":
            return self._execute_send_email(action_data)
        elif action_type == "post_linkedin":
            return self._execute_post_linkedin(action_data)
        else:
            return f"Action '{action_type}' acknowledged (no specific handler)"

    def _execute_send_email(self, data: dict) -> str:
        """Send an email via Gmail API after approval."""
        try:
            from gmail_auth import get_gmail_service
            import base64
            from email.mime.text import MIMEText

            service = get_gmail_service()
            message = MIMEText(data.get("body", ""))
            message["to"] = data.get("to", "")
            message["subject"] = data.get("subject", "")

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()

            return f"Email sent to {data.get('to', 'unknown')}"
        except Exception as exc:
            return f"Email send failed: {exc}"

    def _execute_post_linkedin(self, data: dict) -> str:
        """Post to LinkedIn after approval."""
        try:
            from linkedin_poster import publish_to_linkedin
            from config import LINKEDIN_ACCESS_TOKEN

            content = data.get("content", "")
            return publish_to_linkedin(content, LINKEDIN_ACCESS_TOKEN)
        except Exception as exc:
            return f"LinkedIn post failed: {exc}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    watcher = ApprovalWatcher()

    def _signal_handler(sig: int, frame: object) -> None:
        logger.info("Shutdown signal received.")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    watcher.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()


if __name__ == "__main__":
    main()
