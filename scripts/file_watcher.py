"""File system watcher for the AI Employee vault.

Monitors AI_Employee_Vault/Inbox/ for new files and creates
action items in AI_Employee_Vault/Needs_Action/.

Uses the watchdog library with a BaseWatcher abstract class
per the hackathon specification.

Usage:
    python scripts/file_watcher.py
"""

import abc
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

# Add parent to path so we can import logger
sys.path.insert(0, str(Path(__file__).resolve().parent))
from logger import iso_now, log_to_vault, setup_console_logger

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VAULT_DIR = PROJECT_ROOT / "AI_Employee_Vault"
INBOX_DIR = VAULT_DIR / "Inbox"
NEEDS_ACTION_DIR = VAULT_DIR / "Needs_Action"

logger = setup_console_logger("file_watcher")


# ---------------------------------------------------------------------------
# Priority parsing
# ---------------------------------------------------------------------------

PRIORITY_KEYWORDS = {"URGENT": "URGENT", "REVIEW": "REVIEW", "FYI": "FYI"}


def detect_priority(filename: str) -> str:
    """Detect priority from filename keywords."""
    upper = filename.upper()
    for keyword, priority in PRIORITY_KEYWORDS.items():
        if keyword in upper:
            return priority
    return "Medium"


# ---------------------------------------------------------------------------
# Abstract base class (hackathon requirement)
# ---------------------------------------------------------------------------


class BaseWatcher(abc.ABC):
    """Abstract base class for file system watchers."""

    @abc.abstractmethod
    def start(self) -> None:
        """Start watching."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Stop watching."""

    @abc.abstractmethod
    def on_new_file(self, file_path: Path) -> None:
        """Handle a newly detected file."""


# ---------------------------------------------------------------------------
# Inbox event handler
# ---------------------------------------------------------------------------


class InboxHandler(FileSystemEventHandler):
    """Watchdog handler that delegates to a BaseWatcher on file creation."""

    def __init__(self, watcher: "FileSystemWatcher") -> None:
        super().__init__()
        self.watcher = watcher

    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        # Skip hidden / temp files
        if file_path.name.startswith(".") or file_path.name.startswith("~"):
            return
        self.watcher.on_new_file(file_path)


# ---------------------------------------------------------------------------
# Concrete watcher
# ---------------------------------------------------------------------------


class FileSystemWatcher(BaseWatcher):
    """Monitors Inbox/ and creates action files in Needs_Action/."""

    def __init__(self) -> None:
        self._observer = Observer()
        self._running = False

    # -- lifecycle -----------------------------------------------------------

    def start(self) -> None:
        """Start the watcher. Processes any existing files first."""
        INBOX_DIR.mkdir(parents=True, exist_ok=True)
        NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)

        # Initial scan for files already present
        self._scan_existing()

        handler = InboxHandler(self)
        self._observer.schedule(handler, str(INBOX_DIR), recursive=False)
        self._observer.start()
        self._running = True

        log_to_vault("watcher_started", "file_watcher", "success")
        logger.info("Watcher started — monitoring %s", INBOX_DIR)

    def stop(self) -> None:
        """Stop the watcher gracefully."""
        if self._running:
            self._observer.stop()
            self._observer.join()
            self._running = False
            log_to_vault("watcher_stopped", "file_watcher", "success")
            logger.info("Watcher stopped.")

    # -- core logic ----------------------------------------------------------

    def on_new_file(self, file_path: Path) -> None:
        """Create an action file in Needs_Action/ for the detected file."""
        try:
            stat = file_path.stat()
            file_size = stat.st_size
        except OSError:
            file_size = 0

        priority = detect_priority(file_path.name)
        timestamp = iso_now()

        action_filename = f"FILE_{file_path.name}.md"
        action_path = NEEDS_ACTION_DIR / action_filename

        content = (
            f"# Action Item: {file_path.name}\n"
            f"\n"
            f"- **original_file:** {file_path.name}\n"
            f"- **detected_at:** {timestamp}\n"
            f"- **file_size:** {file_size} bytes\n"
            f"- **priority:** {priority}\n"
            f"- **status:** pending\n"
            f"\n"
            f"---\n"
            f"Source path: `Inbox/{file_path.name}`\n"
        )

        action_path.write_text(content, encoding="utf-8")

        log_to_vault(
            action="file_detected",
            source=file_path.name,
            result="action_created",
            priority=priority,
            action_file=action_filename,
        )
        logger.info(
            "New file detected: %s → created %s (priority: %s)",
            file_path.name,
            action_filename,
            priority,
        )

    # -- helpers -------------------------------------------------------------

    def _scan_existing(self) -> None:
        """Process files already sitting in Inbox/ at startup."""
        for item in INBOX_DIR.iterdir():
            if item.is_file() and not item.name.startswith("."):
                action_path = NEEDS_ACTION_DIR / f"FILE_{item.name}.md"
                if not action_path.exists():
                    logger.info("Found existing file: %s", item.name)
                    self.on_new_file(item)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    watcher = FileSystemWatcher()

    # Graceful shutdown on Ctrl+C
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
