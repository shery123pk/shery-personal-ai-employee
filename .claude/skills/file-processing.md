---
name: file-processing
description: Process Needs_Action items, archive to Done, log actions
priority: required
tier: bronze
---

# Skill: File Processing

Process action items from `AI_Employee_Vault/Needs_Action/`.

## Capabilities

### Process items from Needs_Action
Scan `AI_Employee_Vault/Needs_Action/` for pending action files and process them:
1. Read the action file metadata (original filename, priority, timestamp)
2. Perform the required action based on priority and content
3. Update the action file status to `completed`
4. Move the action file to `AI_Employee_Vault/Done/`

### Parse action file metadata
Extract structured data from action files:
- `original_file`: Name of the file that triggered the action
- `detected_at`: ISO 8601 timestamp of detection
- `priority`: URGENT / REVIEW / FYI / Medium (default)
- `file_size`: Size in bytes
- `status`: pending / completed

### Move completed items to Done
After processing, move action files from Needs_Action to Done with:
- Status updated to `completed`
- Completion timestamp added

### Log all processing actions
Append a JSON entry to `AI_Employee_Vault/Logs/YYYY-MM-DD.json` for every processed item:
```json
{
  "timestamp": "2026-02-24T12:00:00Z",
  "action": "processed",
  "source": "FILE_report.md",
  "result": "completed",
  "priority": "REVIEW"
}
```

## Usage Examples

- "Process all items in Needs_Action"
- "What files are pending processing?"
- "Process only URGENT items"
- "Show processing history for today"

## Rules
- Always log every processing action
- Update Dashboard.md after processing
- Process URGENT items first, then REVIEW, then FYI
- Never delete action files — always move to Done
