"""Sync watcher — periodic Git-based vault synchronisation.

Extends BaseWatcher and calls VaultSync.sync() at a configurable interval.

Usage:
    python scripts/sync_watcher.py
"""

import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import VAULT_SYNC_INTERVAL_SEC
from file_watcher import BaseWatcher
from logger import log_to_vault, setup_console_logger
from vault_sync import VaultSync

logger = setup_console_logger("sync_watcher")


class SyncWatcher(BaseWatcher):
    """Periodic vault sync watcher — polls VaultSync.sync() on an interval."""

    def __init__(self, interval_sec: int | None = None) -> None:
        self._interval = interval_sec or VAULT_SYNC_INTERVAL_SEC
        self._running = False
        self._syncer = VaultSync()

    def start(self) -> None:
        """Start the sync watcher loop."""
        self._running = True
        log_to_vault("sync_watcher_started", "sync_watcher", "success")
        logger.info("Sync watcher started (interval: %ds)", self._interval)

        while self._running:
            try:
                result = self._syncer.sync()
                logger.info(
                    "Vault sync: pulled=%d, pushed=%d, conflicts=%d",
                    result["pulled"], result["pushed"], len(result["conflicts"]),
                )
            except Exception as exc:
                logger.error("Vault sync error: %s", exc)
                log_to_vault("sync_watcher_error", "sync_watcher", "error", detail=str(exc))

            # Sleep in small increments for responsive shutdown
            for _ in range(self._interval):
                if not self._running:
                    break
                time.sleep(1)

    def stop(self) -> None:
        """Stop the sync watcher."""
        self._running = False
        log_to_vault("sync_watcher_stopped", "sync_watcher", "success")
        logger.info("Sync watcher stopped.")

    def on_new_file(self, file_path: Path) -> None:
        """Not used — sync is time-based, not event-based."""


def main() -> None:
    watcher = SyncWatcher()

    def _signal_handler(sig: int, frame: object) -> None:
        logger.info("Shutdown signal received.")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    watcher.start()


if __name__ == "__main__":
    main()
