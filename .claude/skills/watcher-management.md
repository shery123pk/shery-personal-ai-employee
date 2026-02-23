---
name: watcher-management
description: Start, stop, and monitor the file system watcher
priority: critical
tier: bronze
---

# Skill: Watcher Management

Control the file system watcher that monitors `AI_Employee_Vault/Inbox/`.

## Capabilities

### Start file watcher
Launch the watcher process using:
```
python scripts/file_watcher.py
```
The watcher monitors `AI_Employee_Vault/Inbox/` for new files and creates action items in `AI_Employee_Vault/Needs_Action/`.

### Stop file watcher
Terminate the running watcher process gracefully (Ctrl+C / SIGINT).

### Check watcher status
Verify if the watcher process is currently running.

### View watcher logs
Read today's log file at `AI_Employee_Vault/Logs/YYYY-MM-DD.json` to see recent watcher activity.

## Usage Examples

- "Start the file watcher"
- "Is the watcher running?"
- "Show me today's watcher logs"
- "Stop the file watcher"

## Rules
- Only one watcher instance should run at a time
- Always check status before starting a new instance
- Update Dashboard.md watcher status when starting/stopping
