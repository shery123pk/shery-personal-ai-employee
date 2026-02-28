---
name: scheduling
description: Manage the APScheduler-based periodic job scheduler
priority: required
tier: silver
---

# Skill: Scheduling

Manage the periodic job scheduler that automates recurring AI Employee tasks.

## Capabilities

### Start the scheduler
Launch the scheduler process:
```
python scripts/scheduler.py
```

Runs four periodic jobs:
1. **Check Gmail** — every 5 minutes (configurable via `SCHEDULER_GMAIL_INTERVAL_MIN`)
2. **Process Needs_Action** — every 10 minutes (configurable via `SCHEDULER_PROCESS_INTERVAL_MIN`)
3. **Check Approved** — every 5 minutes (configurable via `SCHEDULER_APPROVAL_INTERVAL_MIN`)
4. **Daily Briefing** — at configured hour (default 9:00 AM via `SCHEDULER_BRIEFING_HOUR`)

### View scheduler status
Check if the scheduler is running and list active jobs.

### Configure intervals
All intervals are set via environment variables in `.env`:
- `SCHEDULER_GMAIL_INTERVAL_MIN` — Gmail polling frequency
- `SCHEDULER_PROCESS_INTERVAL_MIN` — Queue processing frequency
- `SCHEDULER_APPROVAL_INTERVAL_MIN` — Approval checking frequency
- `SCHEDULER_BRIEFING_HOUR` — Hour for daily briefing (0-23)

### Trigger manual job run
Force-run any scheduled job immediately for testing or urgent needs.

## Usage Examples

- "Start the scheduler"
- "Is the scheduler running?"
- "What jobs are scheduled?"
- "Run the daily briefing now"
- "Change Gmail check interval to 10 minutes"

## Rules

- Only one scheduler instance should run at a time
- Always check status before starting a new instance
- Log all scheduler start/stop events
- Update Dashboard.md when scheduler status changes
- Scheduler gracefully shuts down on SIGINT/SIGTERM
