"""Briefing generator — daily and weekly intelligence briefings.

Generates markdown briefings using LLM analysis of vault data.
Output saved to AI_Employee_Vault/Briefings/.

Usage:
    python scripts/briefing_generator.py [daily|weekly]
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    BRIEFINGS_DIR,
    DONE_DIR,
    LOGS_DIR,
    NEEDS_ACTION_DIR,
    PENDING_APPROVAL_DIR,
    VAULT_PATH,
)
from logger import iso_now, log_to_vault, setup_console_logger

logger = setup_console_logger("briefing_generator")


def generate_daily_briefing() -> Path:
    """Generate a morning intelligence summary.

    Sections: Executive Summary, Email/Task Queue, System Health, Priorities.
    Output: Briefings/gold_briefing_YYYY-MM-DD.md
    """
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = BRIEFINGS_DIR / f"gold_briefing_{date}.md"

    # Gather vault data
    pending_count = _count_files(NEEDS_ACTION_DIR)
    done_count = _count_files(DONE_DIR)
    approval_count = _count_files(PENDING_APPROVAL_DIR)
    today_log = _read_today_log()

    # Use orchestrator LLM if available, otherwise build static report
    try:
        from agents.orchestrator import OrchestratorAgent
        orchestrator = OrchestratorAgent()
        briefing_path = orchestrator.generate_daily_briefing()
        if briefing_path and briefing_path.exists():
            log_to_vault("daily_briefing_generated", "briefing_generator", "success")
            return briefing_path
    except Exception:
        pass

    # Fallback: static briefing
    actions_summary = ""
    if today_log:
        recent = today_log[-10:]
        for entry in recent:
            actions_summary += f"- {entry.get('action', '?')}: {entry.get('source', '?')} → {entry.get('result', '?')}\n"

    content = (
        f"# Daily Intelligence Briefing\n\n"
        f"> Date: {date}\n"
        f"> Generated: {iso_now()}\n\n"
        f"---\n\n"
        f"## Executive Summary\n\n"
        f"- **Pending tasks:** {pending_count}\n"
        f"- **Completed today:** {done_count}\n"
        f"- **Awaiting approval:** {approval_count}\n"
        f"- **Log entries today:** {len(today_log)}\n\n"
        f"## Task Queue\n\n"
        f"{'_No pending tasks._' if pending_count == 0 else f'{pending_count} task(s) in Needs_Action/'}\n\n"
        f"## Recent Activity\n\n"
        f"{actions_summary or '_No activity recorded yet._'}\n\n"
        f"## System Health\n\n"
        f"- Vault: {'Accessible' if VAULT_PATH.exists() else 'ERROR'}\n"
        f"- Logs: {'Active' if today_log else 'No entries'}\n\n"
        f"## Priorities for Today\n\n"
        f"1. Process pending tasks in Needs_Action/\n"
        f"2. Review items in Pending_Approval/\n"
        f"3. Monitor incoming emails\n"
    )

    path.write_text(content, encoding="utf-8")
    log_to_vault("daily_briefing_generated", "briefing_generator", "success")
    logger.info("Daily briefing saved to %s", path)
    return path


def generate_weekly_briefing() -> Path:
    """Generate a CEO strategic audit.

    Sections: Week Summary, Key Achievements, Pending Items, Recommendations.
    Output: Briefings/weekly_briefing_YYYY-MM-DD.md
    """
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = BRIEFINGS_DIR / f"weekly_briefing_{date}.md"

    # Use orchestrator LLM if available
    try:
        from agents.orchestrator import OrchestratorAgent
        orchestrator = OrchestratorAgent()
        briefing_path = orchestrator.generate_weekly_briefing()
        if briefing_path and briefing_path.exists():
            log_to_vault("weekly_briefing_generated", "briefing_generator", "success")
            return briefing_path
    except Exception:
        pass

    # Fallback: static weekly briefing
    done_count = _count_files(DONE_DIR)
    pending_count = _count_files(NEEDS_ACTION_DIR)

    content = (
        f"# Weekly Strategic Briefing\n\n"
        f"> Week ending: {date}\n"
        f"> Generated: {iso_now()}\n\n"
        f"---\n\n"
        f"## Week Summary\n\n"
        f"- Total completed tasks: {done_count}\n"
        f"- Current pending tasks: {pending_count}\n\n"
        f"## Key Achievements\n\n"
        f"- Processed {done_count} task(s) through the autonomous pipeline\n"
        f"- Maintained system health across all watchers\n\n"
        f"## Pending Items\n\n"
        f"- {pending_count} task(s) still in Needs_Action/\n\n"
        f"## Strategic Recommendations\n\n"
        f"1. Review and prioritise pending tasks using Eisenhower Matrix\n"
        f"2. Schedule follow-ups for approved actions\n"
        f"3. Consider expanding automation coverage\n"
    )

    path.write_text(content, encoding="utf-8")
    log_to_vault("weekly_briefing_generated", "briefing_generator", "success")
    logger.info("Weekly briefing saved to %s", path)
    return path


def _count_files(directory: Path) -> int:
    """Count non-hidden files in a directory."""
    if not directory.exists():
        return 0
    return len([f for f in directory.iterdir() if f.is_file() and not f.name.startswith(".")])


def _read_today_log() -> list[dict]:
    """Read today's log entries."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_path = LOGS_DIR / f"{today}.json"
    if not log_path.exists():
        return []
    try:
        return json.loads(log_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    import sys as _sys

    mode = _sys.argv[1] if len(_sys.argv) > 1 else "daily"

    if mode == "weekly":
        path = generate_weekly_briefing()
        print(f"Weekly briefing: {path}")
    else:
        path = generate_daily_briefing()
        print(f"Daily briefing: {path}")


if __name__ == "__main__":
    main()
