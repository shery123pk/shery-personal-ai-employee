"""Cloud entrypoint — single process for Cloud VM deployment.

Starts all cloud-zone components:
- GmailWatcher (email polling)
- SyncWatcher (vault git sync)
- Scheduler (cloud jobs)
- Health monitor (HTTP /health endpoint)
- Autonomous loop (orchestrator)

Signal handlers for graceful shutdown.

Usage:
    WORK_ZONE=cloud python scripts/cloud_entrypoint.py
"""

import os
import signal
import sys
import threading
import time
from pathlib import Path

# Force cloud zone
os.environ.setdefault("WORK_ZONE", "cloud")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CLOUD_HEALTH_PORT
from logger import log_to_vault, setup_console_logger

logger = setup_console_logger("cloud_entrypoint")

_shutdown = threading.Event()


def start_gmail_watcher() -> None:
    """Start Gmail polling in a background thread."""
    try:
        from gmail_watcher import GmailWatcher
        watcher = GmailWatcher()
        watcher.start()
        logger.info("GmailWatcher started.")
    except Exception as exc:
        logger.warning("GmailWatcher failed to start: %s", exc)


def start_sync_watcher() -> None:
    """Start vault sync watcher in a background thread."""
    try:
        from sync_watcher import SyncWatcher
        watcher = SyncWatcher()
        watcher.start()
    except Exception as exc:
        logger.warning("SyncWatcher failed to start: %s", exc)


def start_health_monitor() -> None:
    """Start HTTP health monitor in a background thread."""
    try:
        from health_monitor import start_health_server
        start_health_server(port=CLOUD_HEALTH_PORT)
    except Exception as exc:
        logger.warning("Health monitor failed to start: %s", exc)


def start_scheduler() -> None:
    """Start the APScheduler with cloud jobs."""
    try:
        from scheduler import create_scheduler
        scheduler = create_scheduler()
        scheduler.start()
        logger.info("Scheduler started with %d jobs.", len(scheduler.get_jobs()))
    except Exception as exc:
        logger.warning("Scheduler failed to start: %s", exc)


def run_autonomous_loop() -> None:
    """Run the autonomous orchestrator loop periodically."""
    try:
        from agents.orchestrator import OrchestratorAgent
        orchestrator = OrchestratorAgent()

        while not _shutdown.is_set():
            try:
                result = orchestrator.run_autonomous_loop(max_iterations=5)
                logger.info(
                    "Autonomous loop: %d processed, %d errors",
                    result.get("processed", 0), result.get("errors", 0),
                )
            except Exception as exc:
                logger.error("Autonomous loop error: %s", exc)

            # Wait 5 minutes between iterations
            _shutdown.wait(300)

    except Exception as exc:
        logger.error("Failed to start autonomous loop: %s", exc)


def main() -> None:
    logger.info("=" * 50)
    logger.info("AI Employee — Cloud Entrypoint")
    logger.info("WORK_ZONE=cloud")
    logger.info("=" * 50)

    log_to_vault("cloud_entrypoint_started", "cloud_entrypoint", "success")

    # Start components in background threads
    threads = [
        threading.Thread(target=start_gmail_watcher, name="gmail", daemon=True),
        threading.Thread(target=start_sync_watcher, name="sync", daemon=True),
        threading.Thread(target=start_health_monitor, name="health", daemon=True),
        threading.Thread(target=start_scheduler, name="scheduler", daemon=True),
        threading.Thread(target=run_autonomous_loop, name="orchestrator", daemon=True),
    ]

    for t in threads:
        t.start()
        logger.info("Started thread: %s", t.name)

    # Signal handlers
    def _signal_handler(sig: int, frame: object) -> None:
        logger.info("Shutdown signal received (%s).", signal.Signals(sig).name)
        _shutdown.set()
        log_to_vault("cloud_entrypoint_stopped", "cloud_entrypoint", "success")
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Keep main thread alive
    try:
        while not _shutdown.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown.set()
        log_to_vault("cloud_entrypoint_stopped", "cloud_entrypoint", "success")
        logger.info("Cloud entrypoint shut down.")


if __name__ == "__main__":
    main()
