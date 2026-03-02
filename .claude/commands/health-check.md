Run the ProcessWatchdog to generate a system health report.

## Steps

1. Initialise the ProcessWatchdog from `scripts/process_watchdog.py`
2. Check all system components: File Watcher, Gmail Watcher, Approval Watcher, Scheduler
3. Verify vault folder accessibility
4. Check log file recency
5. Generate a markdown health report
6. Display the report to the user

Reports component status as: healthy, degraded, or unknown.
