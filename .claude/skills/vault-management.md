---
name: vault-management
description: Read, write, move vault files and update Dashboard
priority: critical
tier: bronze
---

# Skill: Vault Management

Manage the Obsidian vault at `AI_Employee_Vault/`.

## Capabilities

### Read vault files
Read any file in the vault directories (Inbox, Needs_Action, Done, Logs).

### Write vault files
Create or update files in any vault directory.

### List directory contents
List files in any vault folder to check current state.

### Move files between folders
Move files from one vault folder to another (e.g., Needs_Action → Done).

### Update Dashboard
After any vault operation, update `AI_Employee_Vault/Dashboard.md`:
- Recount files in Inbox, Needs_Action, and Done folders
- Add entry to the Recent Activity table with ISO 8601 timestamp
- Update system health status if needed

## Usage Examples

- "List all files in Inbox"
- "Move FILE_report.md from Needs_Action to Done"
- "Update the dashboard with current folder counts"
- "Read the contents of Needs_Action/FILE_notes.md"

## Rules
- Always update Dashboard.md after modifying vault contents
- Use ISO 8601 timestamps for all log entries
- Never delete files — move them to Done instead
