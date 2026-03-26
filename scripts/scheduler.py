"""Scheduler — APScheduler-based periodic jobs for the AI Employee.

Runs nine periodic tasks (4 Silver + 3 Gold + 2 Platinum):
1. Check Gmail every N minutes
2. Process Needs_Action queue every N minutes
3. Check Approved folder every N minutes
4. Generate daily briefing at configured hour
5. Health check every N minutes (Gold)
6. Autonomous loop every N minutes (Gold)
7. Weekly briefing on configured day (Gold)
8. Vault sync every N minutes (Platinum)
9. Dashboard merge every N minutes (Platinum — Local only)

Usage:
    python scripts/scheduler.py
"""

import json
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    APPROVED_DIR,
    DONE_DIR,
    INBOX_DIR,
    NEEDS_ACTION_DIR,
    PENDING_APPROVAL_DIR,
    PLANS_DIR,
    SCHEDULER_APPROVAL_INTERVAL_MIN,
    SCHEDULER_AUTONOMOUS_INTERVAL_MIN,
    SCHEDULER_BRIEFING_HOUR,
    SCHEDULER_DASHBOARD_MERGE_INTERVAL_MIN,
    SCHEDULER_GMAIL_INTERVAL_MIN,
    SCHEDULER_HEALTH_CHECK_MIN,
    SCHEDULER_PROCESS_INTERVAL_MIN,
    SCHEDULER_VAULT_SYNC_INTERVAL_MIN,
    SCHEDULER_WEEKLY_BRIEFING_DAY,
    VAULT_PATH,
    WORK_ZONE,
)
from logger import iso_now, log_to_vault, setup_console_logger

logger = setup_console_logger("scheduler")


# ---------------------------------------------------------------------------
# Job: Check Gmail
# ---------------------------------------------------------------------------

def job_check_gmail() -> None:
    """Poll Gmail for new emails (delegates to gmail_watcher logic)."""
    try:
        from gmail_auth import get_gmail_service
        from gmail_watcher import GmailWatcher, load_seen_ids, save_seen_ids

        watcher = GmailWatcher()
        watcher._service = get_gmail_service()
        watcher._seen_ids = load_seen_ids()
        watcher._poll()
        save_seen_ids(watcher._seen_ids)

        logger.info("Gmail check completed.")
    except FileNotFoundError:
        logger.warning("Gmail credentials not configured — skipping Gmail check.")
    except Exception as exc:
        logger.error("Gmail check failed: %s", exc)
        log_to_vault("scheduled_gmail_check", "scheduler", "error", detail=str(exc))


# ---------------------------------------------------------------------------
# Job: Process Needs_Action queue
# ---------------------------------------------------------------------------

def job_process_queue() -> None:
    """Process pending items in Needs_Action/ by moving to Done/."""
    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    DONE_DIR.mkdir(parents=True, exist_ok=True)

    items = sorted(
        (f for f in NEEDS_ACTION_DIR.iterdir() if f.is_file() and not f.name.startswith(".")),
        key=lambda f: _extract_priority_rank(f),
    )

    if not items:
        logger.info("Needs_Action queue is empty.")
        return

    for item in items:
        try:
            content = item.read_text(encoding="utf-8")
            updated = content.replace("**status:** pending", "**status:** completed")
            updated += f"\n- **completed_at:** {iso_now()}\n"

            done_path = DONE_DIR / item.name
            done_path.write_text(updated, encoding="utf-8")
            item.unlink()

            log_to_vault(
                action="scheduled_process",
                source=item.name,
                result="completed",
            )
            logger.info("Processed: %s → Done/", item.name)
        except Exception as exc:
            logger.error("Failed to process %s: %s", item.name, exc)
            log_to_vault(
                action="scheduled_process_error",
                source=item.name,
                result="error",
                detail=str(exc),
            )

    logger.info("Queue processing completed: %d item(s).", len(items))


def _extract_priority_rank(filepath: Path) -> int:
    """Read a file's priority and return sort rank (lower = higher priority)."""
    try:
        content = filepath.read_text(encoding="utf-8")
        for line in content.splitlines():
            if "**priority:**" in line:
                priority = line.split("**priority:**")[1].strip()
                return {"URGENT": 0, "REVIEW": 1, "FYI": 2}.get(priority, 3)
    except OSError:
        pass
    return 3


# ---------------------------------------------------------------------------
# Job: Check Approved folder
# ---------------------------------------------------------------------------

def job_check_approved() -> None:
    """Process any files in the Approved/ folder."""
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)

    items = [f for f in APPROVED_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]

    if not items:
        return

    from approval_watcher import ApprovalWatcher

    watcher = ApprovalWatcher()
    for item in items:
        watcher._handle_approved(item)

    logger.info("Processed %d approved item(s).", len(items))


# ---------------------------------------------------------------------------
# Job: Daily briefing
# ---------------------------------------------------------------------------

def job_daily_briefing() -> None:
    """Generate a daily briefing and update Dashboard.md."""
    logger.info("Generating daily briefing...")

    def count_files(directory: Path) -> int:
        if not directory.exists():
            return 0
        return len([f for f in directory.iterdir() if f.is_file() and not f.name.startswith(".")])

    inbox_count = count_files(INBOX_DIR)
    needs_count = count_files(NEEDS_ACTION_DIR)
    done_count = count_files(DONE_DIR)
    pending_count = count_files(PENDING_APPROVAL_DIR)
    approved_count = count_files(APPROVED_DIR)
    plans_count = count_files(PLANS_DIR)

    # Read today's log entries
    from logger import get_today_log_path

    log_path = get_today_log_path()
    log_entries = []
    if log_path.exists():
        try:
            log_entries = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    activity_rows = ""
    for e in log_entries[-20:]:  # Last 20 entries
        activity_rows += (
            f'| {e.get("timestamp", "")} | {e.get("action", "")} '
            f'| {e.get("source", "")} | {e.get("result", "")} |\n'
        )

    dashboard = (
        "# AI Employee Dashboard\n"
        "\n"
        f"> Last updated: {iso_now()}\n"
        "\n"
        "## System Health\n"
        "\n"
        "| Component | Status | Details |\n"
        "|-----------|--------|--------|\n"
        "| File Watcher | Active | Monitoring Inbox/ |\n"
        "| Gmail Watcher | Active | Polling for emails |\n"
        "| Approval Watcher | Active | Monitoring Approved/ & Rejected/ |\n"
        "| Scheduler | Running | Periodic jobs active |\n"
        "| MCP Email Server | Ready | 4 tools available |\n"
        "| Claude Agent | Ready | 8 skills loaded |\n"
        "| Vault Access | OK | All folders accessible |\n"
        "\n"
        "## Folder Counts\n"
        "\n"
        "| Folder | Count |\n"
        "|--------|-------|\n"
        f"| Inbox | {inbox_count} |\n"
        f"| Needs_Action | {needs_count} |\n"
        f"| Done | {done_count} |\n"
        f"| Plans | {plans_count} |\n"
        f"| Pending_Approval | {pending_count} |\n"
        f"| Approved | {approved_count} |\n"
        "\n"
        "## Recent Activity\n"
        "\n"
        "| Timestamp | Action | Source | Result |\n"
        "|-----------|--------|--------|--------|\n"
        f"{activity_rows}"
    )

    dashboard_path = VAULT_PATH / "Dashboard.md"
    dashboard_path.write_text(dashboard, encoding="utf-8")

    log_to_vault("daily_briefing", "scheduler", "success")
    logger.info(
        "Daily briefing generated — Inbox: %d, Needs_Action: %d, Done: %d, Pending: %d",
        inbox_count, needs_count, done_count, pending_count,
    )


# ---------------------------------------------------------------------------
# Job: Health check (Gold)
# ---------------------------------------------------------------------------

def job_health_check() -> None:
    """Run process watchdog health check."""
    try:
        from process_watcher import ProcessWatchdog

        watchdog = ProcessWatchdog()
        report = watchdog.check_health()
        healthy = sum(1 for v in report.values() if v.get("status") == "healthy")
        logger.info("Health check: %d/%d components healthy", healthy, len(report))
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        log_to_vault("scheduled_health_check", "scheduler", "error", detail=str(exc))


# ---------------------------------------------------------------------------
# Job: Autonomous loop (Gold)
# ---------------------------------------------------------------------------

def job_autonomous_loop() -> None:
    """Run the autonomous task execution loop."""
    try:
        from autonomous_loop import run_autonomous_loop

        result = run_autonomous_loop()
        logger.info(
            "Autonomous loop: %d processed, %d errors",
            result.get("processed", 0), result.get("errors", 0),
        )
    except Exception as exc:
        logger.error("Autonomous loop failed: %s", exc)
        log_to_vault("scheduled_autonomous_loop", "scheduler", "error", detail=str(exc))


# ---------------------------------------------------------------------------
# Job: Weekly briefing (Gold)
# ---------------------------------------------------------------------------

def job_weekly_briefing() -> None:
    """Generate a weekly CEO briefing."""
    try:
        from briefing_generator import generate_weekly_briefing

        path = generate_weekly_briefing()
        logger.info("Weekly briefing generated: %s", path)
    except Exception as exc:
        logger.error("Weekly briefing failed: %s", exc)
        log_to_vault("scheduled_weekly_briefing", "scheduler", "error", detail=str(exc))


# ---------------------------------------------------------------------------
# Job: Vault sync (Platinum)
# ---------------------------------------------------------------------------

def job_vault_sync() -> None:
    """Synchronise the vault via git (pull → commit → push)."""
    try:
        from vault_sync import VaultSync

        syncer = VaultSync()
        result = syncer.sync()
        logger.info(
            "Vault sync: pulled=%d, pushed=%d, conflicts=%d",
            result["pulled"], result["pushed"], len(result["conflicts"]),
        )
    except Exception as exc:
        logger.error("Vault sync failed: %s", exc)
        log_to_vault("scheduled_vault_sync", "scheduler", "error", detail=str(exc))


# ---------------------------------------------------------------------------
# Job: Dashboard merge (Platinum — Local only)
# ---------------------------------------------------------------------------

def job_merge_dashboard() -> None:
    """Merge Cloud update signals into Dashboard.md (Local zone only)."""
    if WORK_ZONE != "local":
        return
    try:
        from dashboard_updater import DashboardUpdater

        updater = DashboardUpdater()
        count = updater.merge_updates_to_dashboard()
        if count:
            logger.info("Dashboard merge: %d update(s) merged", count)
    except Exception as exc:
        logger.error("Dashboard merge failed: %s", exc)
        log_to_vault("scheduled_dashboard_merge", "scheduler", "error", detail=str(exc))


# ---------------------------------------------------------------------------
# Scheduler setup
# ---------------------------------------------------------------------------

def create_scheduler() -> BackgroundScheduler:
    """Create and configure the scheduler with all periodic jobs."""
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        job_check_gmail,
        IntervalTrigger(minutes=SCHEDULER_GMAIL_INTERVAL_MIN),
        id="check_gmail",
        name=f"Check Gmail (every {SCHEDULER_GMAIL_INTERVAL_MIN} min)",
    )

    scheduler.add_job(
        job_process_queue,
        IntervalTrigger(minutes=SCHEDULER_PROCESS_INTERVAL_MIN),
        id="process_queue",
        name=f"Process Needs_Action (every {SCHEDULER_PROCESS_INTERVAL_MIN} min)",
    )

    scheduler.add_job(
        job_check_approved,
        IntervalTrigger(minutes=SCHEDULER_APPROVAL_INTERVAL_MIN),
        id="check_approved",
        name=f"Check Approved (every {SCHEDULER_APPROVAL_INTERVAL_MIN} min)",
    )

    scheduler.add_job(
        job_daily_briefing,
        CronTrigger(hour=SCHEDULER_BRIEFING_HOUR, minute=0),
        id="daily_briefing",
        name=f"Daily briefing (at {SCHEDULER_BRIEFING_HOUR}:00)",
    )

    # Gold tier jobs (5-7)
    scheduler.add_job(
        job_health_check,
        IntervalTrigger(minutes=SCHEDULER_HEALTH_CHECK_MIN),
        id="health_check",
        name=f"Health check (every {SCHEDULER_HEALTH_CHECK_MIN} min)",
    )

    scheduler.add_job(
        job_autonomous_loop,
        IntervalTrigger(minutes=SCHEDULER_AUTONOMOUS_INTERVAL_MIN),
        id="autonomous_loop",
        name=f"Autonomous loop (every {SCHEDULER_AUTONOMOUS_INTERVAL_MIN} min)",
    )

    # Map day names to cron day_of_week
    day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    weekly_day = day_map.get(SCHEDULER_WEEKLY_BRIEFING_DAY.lower(), 0)

    scheduler.add_job(
        job_weekly_briefing,
        CronTrigger(day_of_week=weekly_day, hour=9, minute=0),
        id="weekly_briefing",
        name=f"Weekly briefing ({SCHEDULER_WEEKLY_BRIEFING_DAY} 9:00)",
    )

    # Platinum tier jobs (8-9)
    scheduler.add_job(
        job_vault_sync,
        IntervalTrigger(minutes=SCHEDULER_VAULT_SYNC_INTERVAL_MIN),
        id="vault_sync",
        name=f"Vault sync (every {SCHEDULER_VAULT_SYNC_INTERVAL_MIN} min)",
    )

    scheduler.add_job(
        job_merge_dashboard,
        IntervalTrigger(minutes=SCHEDULER_DASHBOARD_MERGE_INTERVAL_MIN),
        id="merge_dashboard",
        name=f"Dashboard merge (every {SCHEDULER_DASHBOARD_MERGE_INTERVAL_MIN} min)",
    )

    return scheduler


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    scheduler = create_scheduler()
    scheduler.start()

    log_to_vault("scheduler_started", "scheduler", "success")
    logger.info("Scheduler started with %d jobs:", len(scheduler.get_jobs()))
    for job in scheduler.get_jobs():
        logger.info("  - %s", job.name)

    def _signal_handler(sig: int, frame: object) -> None:
        logger.info("Shutdown signal received.")
        scheduler.shutdown(wait=False)
        log_to_vault("scheduler_stopped", "scheduler", "success")
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)
        log_to_vault("scheduler_stopped", "scheduler", "success")
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
